"""Seis mejoras de E1 (modelo de 24 h), cada una probada por separado sobre la misma base.

6  Filtro de régimen de BTC y umbral más exigente.
5  Interruptor por rendimiento reciente.
4  Entrenar con más historia (desde 2020).
3  Reentrenar cada mes con ventana móvil.
2  Objetivo "llega al objetivo antes que al stop" y operar con ese stop.
1  Segundo modelo que decide si creerle al primero.

Uso: python mejoras.py     (necesita las velas desde 2020: ver README)
"""
import json
import os

import numpy as np
import pandas as pd

import estrategias as E
from backtest import full_months, table

DATA20 = os.environ.get("MULTITF_DATA_DIR", os.path.join(os.path.dirname(E.HERE), "v3_research", "tmp", "k1m_2020",
                                                         "klines"))
OUT = os.path.join(E.HERE, "output")
END = "2026-11-13"
YEARS = [2024, 2025, 2026]
H = pd.Timedelta(hours=1)
QS = (0.9, 0.95, 0.98)
META = ["pred", "exc", "perf30", "win30", "n30", "btc_reg", "atr", "r7d", "r30d", "btc_r7d", "rv1h", "d_dema50"]


def years(ys):
    return [(pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")) for y in ys]


def months(y0, y1):
    m = pd.date_range(f"{y0}-01-01", f"{y1 + 1}-01-01", freq="MS")
    return list(zip(m[:-1], m[1:]))


def add_barriers(P, ksl=2.0, ktp=4.0):
    """Para cada hora: resultado de comprar en la apertura siguiente con stop a ksl ATR y objetivo a ktp ATR,
    máximo 24 h. Si una hora toca ambos, cuenta el stop."""
    for s in E.COINS:
        h = P[s]
        ent, sl, tp = h.onext.values, (ksl * h.atr).values, (ktp * h.atr).values
        stop = ent * (1 - sl)
        n = len(h)
        st, ret, k_exit = np.zeros(n), np.full(n, np.nan), np.full(n, 24)
        for k in range(1, 25):
            lo, hi, op = (h[c].shift(-k).values for c in ("l", "h", "o"))
            a = (st == 0) & (lo <= stop)
            ret[a], st[a], k_exit[a] = np.minimum(stop, op)[a] / ent[a] - 1, -1, k
            b = (st == 0) & (hi >= ent * (1 + tp))
            ret[b], st[b], k_exit[b] = tp[b], 1, k
        o25 = h.o.shift(-25).values
        ret[st == 0] = (o25 / ent - 1)[st == 0]
        ok = ~np.isnan(o25) & ~np.isnan(sl)
        h["tb_ret"] = np.where(ok, ret, np.nan)
        h["tb"] = np.where(ok, (st == 1).astype(float), np.nan)
        h["tb_k"] = k_exit
        h["tb_be"] = (sl + E.COST) / (sl + tp)             # probabilidad mínima para no perder


def predict(P, periods, target="y24", window=None, clf=False):
    """Para cada periodo (t0, t1) entrena solo con datos anteriores a t0 (los últimos `window` meses si se indica)
    y predice el periodo. El 20 % final del entrenamiento fija los umbrales. Devuelve predicciones y umbrales."""
    import lightgbm as lgb
    X = pd.concat([P[s][E.FEATS + [target]] for s in E.COINS]).dropna(subset=[target, "r30d"])
    pred = {s: pd.Series(np.nan, index=P[s].index) for s in E.COINS}
    lim = pd.DataFrame(np.nan, index=P["BTC"].index, columns=list(QS))
    kw = dict(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=500, subsample=0.7,
              subsample_freq=1, colsample_bytree=0.7, reg_lambda=5.0, random_state=0, verbose=-1, n_jobs=4)
    for t0, t1 in periods:
        tr = X[X.index < t0 - 26 * H]
        if window:
            tr = tr[tr.index >= t0 - pd.DateOffset(months=window)]
        u = tr.index.unique().sort_values()
        cut = u[int(len(u) * 0.8)]
        fit, val = tr[tr.index < cut - 26 * H], tr[tr.index >= cut]
        mdl = (lgb.LGBMClassifier if clf else lgb.LGBMRegressor)(**kw).fit(fit[E.FEATS], fit[target])
        f = (lambda x: mdl.predict_proba(x)[:, 1]) if clf else mdl.predict
        lim.loc[(lim.index >= t0) & (lim.index < t1)] = np.quantile(f(val[E.FEATS]), QS)
        for s in E.COINS:
            te = P[s][(P[s].index >= t0) & (P[s].index < t1) & P[s].r30d.notna()]
            if len(te):
                pred[s].loc[te.index] = f(te[E.FEATS])
    return pred, lim


def trades(P, pred, lim, q=0.95, filt=None, barrier=False, prob=False):
    """Una operación a la vez por moneda. Entra si la predicción supera el umbral de validación y el mínimo
    rentable (el costo, o la probabilidad de equilibrio si el modelo predice probabilidad: `prob`).
    Con `barrier` sale por stop u objetivo en vez de a las 24 h."""
    out = []
    for s in E.COINS:
        h = P[s]
        floor = h.tb_be.values if prob else E.COST
        sig = pred[s].values > np.maximum(lim[q].values, floor)
        if filt is not None:
            sig &= filt[s].values
        r = (h.tb_ret if barrier else h.y24).values
        k = h.tb_k.values if barrier else np.full(len(h), 24)
        T, free = h.index, 0
        for i in np.flatnonzero(sig):
            if i < free or np.isnan(r[i]):
                continue
            out.append((s, T[i] + H, T[i] + (k[i] + 1) * H, r[i] - E.COST))
            free = i + k[i]
    return sorted(out, key=lambda x: x[1])


def killswitch(tr, n=30):
    """Las señales siguen en papel; solo se compra si las últimas n operaciones ya cerradas ganaron en promedio."""
    out, closed = [], []
    for t in tr:                                           # ordenadas por entrada
        known = sorted((x for x in closed if x[2] <= t[1]), key=lambda x: x[2])[-n:]
        if len(known) < n or np.mean([x[3] for x in known]) > 0:
            out.append(t)
        closed.append(t)
    return out


def meta_filter(P, pred, lim, test_years):
    """Segundo modelo: con las señales de los años anteriores aprende cuándo la señal del primero acaba en
    ganancia. Usa el rendimiento reciente de las señales (solo resultados ya conocidos) y el estado del mercado."""
    import lightgbm as lgb
    rows = []
    for s in E.COINS:
        h = P[s]
        m = (pred[s] > np.maximum(lim[0.95], E.COST)) & h.y24.notna()
        d = h.loc[m, ["btc_reg", "atr", "r7d", "r30d", "btc_r7d", "rv1h", "d_dema50"]].copy()
        d["pred"], d["exc"], d["net"], d["coin"] = pred[s][m], (pred[s] - lim[0.95])[m], h.y24[m] - E.COST, s
        rows.append(d)
    S = pd.concat(rows).sort_index()
    k = pd.Series(S.net.values, index=S.index + 26 * H).sort_index()       # cuándo se conoce cada resultado
    roll = pd.DataFrame({"perf30": k.rolling("30D").mean(), "win30": (k > 0).astype(float).rolling("30D").mean(),
                         "n30": k.rolling("30D").count()})
    roll = roll[~roll.index.duplicated(keep="last")]
    S = S.join(roll.reindex(S.index, method="ffill"))
    filt = {s: pd.Series(True, index=P[s].index) for s in E.COINS}         # sin datos previos: no filtra
    for y in test_years:
        y0 = pd.Timestamp(f"{y}-01-01")
        tr = S[S.index < y0 - 26 * H].dropna(subset=["perf30"])
        te = S[(S.index >= y0) & (S.index < y0 + pd.DateOffset(years=1))]
        mdl = lgb.LGBMClassifier(n_estimators=100, learning_rate=0.03, num_leaves=7, min_child_samples=100,
                                 subsample=0.7, subsample_freq=1, reg_lambda=5.0, random_state=0, verbose=-1)
        mdl.fit(tr[META], (tr.net > 0).astype(int))
        ok = pd.Series(mdl.predict_proba(te[META])[:, 1] > 0.5, index=te.index)
        for s in E.COINS:
            f = filt[s]
            f[(f.index >= y0) & (f.index < y0 + pd.DateOffset(years=1))] = False
            f.loc[te.index[(te.coin == s).values]] = ok[(te.coin == s).values].values
    return filt


def main():
    P = E.prepare({s: E.load(s, END, "2023-01-01", DATA20) for s in E.COINS})
    add_barriers(P)
    idx = P["BTC"].index
    res, series = {}, {}

    def run(key, name, tr, ys=YEARS, index=idx):
        m = full_months(E.monthly_from_trades(tr), index)
        res[key] = table(name, tr, m, ys)
        series[key] = m
        return tr

    pred, lim = predict(P, years(YEARS))
    base = run("base", "Base: E1 sin cambios", trades(P, pred, lim))

    reg = {s: (P[s].btc_reg > 0).fillna(False) for s in E.COINS}
    run("6a", "6a. Solo filtro de régimen (BTC sobre su media de 200 días)", trades(P, pred, lim, filt=reg))
    run("6b", "6b. Solo umbral más exigente (percentil 98)", trades(P, pred, lim, 0.98))
    run("6", "6. Filtro de régimen + percentil 98", trades(P, pred, lim, 0.98, filt=reg))

    run("5", "5. Interruptor: operar solo si las últimas 30 operaciones en papel ganaron", killswitch(base))
    print("Sensibilidad 5 (n: operaciones, media neta %):",
          {n: (len(t), float(round(100 * np.mean([x[3] for x in t]), 3))) for n in (15, 30, 60) for t in [killswitch(base, n)]})

    P20 = E.prepare({s: E.load(s, END, None, DATA20) for s in E.COINS})
    print(f"\nHistoria ampliada: {P20['BTC'].index[0]} a {P20['BTC'].index[-1]}")
    p4, l4 = predict(P20, years([2022, 2023] + YEARS))
    run("4", "4. Entrenar con historia desde 2020", trades(P20, p4, l4), [2022, 2023] + YEARS, P20["BTC"].index)

    p3, l3 = predict(P, months(2024, 2026), window=24)
    run("3", "3. Reentrenar cada mes (ventana móvil de 24 meses)", trades(P, p3, l3))
    p3b, l3b = predict(P, months(2024, 2026))
    run("3b", "3b. Reentrenar cada mes (toda la historia disponible)", trades(P, p3b, l3b))

    p2, l2 = predict(P, years(YEARS), target="tb", clf=True)
    run("2", "2. Predecir 'objetivo (4 ATR) antes que stop (2 ATR)' y operar con ese stop",
        trades(P, p2, l2, barrier=True, prob=True))
    run("2b", "2b. Mismo modelo de la base, pero saliendo con stop y objetivo", trades(P, pred, lim, barrier=True))

    mf = meta_filter(P, pred, lim, [2025, 2026])
    run("1", "1. Segundo modelo (2024 sin filtro: no hay señales previas para entrenarlo)",
        trades(P, pred, lim, filt=mf))

    # combinaciones de las que mejoran: más historia (4) + reentreno mensual (3), y además el filtro de régimen (6a)
    p34, l34 = predict(P20, months(2022, 2026), window=24)
    i20, y5 = P20["BTC"].index, [2022, 2023] + YEARS
    run("3+4", "3+4. Historia desde 2020 y reentreno mensual (24 meses)", trades(P20, p34, l34), y5, i20)
    reg20 = {s: (P20[s].btc_reg > 0).fillna(False) for s in E.COINS}
    run("3+4+6a", "3+4+6a. Lo anterior más filtro de régimen", trades(P20, p34, l34, filt=reg20), y5, i20)
    run("4+6a", "4+6a. Historia desde 2020 (reentreno anual) más filtro de régimen",
        trades(P20, p4, l4, filt=reg20), y5, i20)

    rows = []
    for k, m in series.items():
        r = {"variante": k}
        for y in YEARS:
            r[str(y)] = round(100 * ((1 + m[[p.year == y for p in m.index]]).prod() - 1), 2)
        mt = m[[p.year in YEARS for p in m.index]]
        eq = (1 + mt).cumprod()
        r.update({"total_%": round(100 * (eq.iloc[-1] - 1), 2), "meses_positivos": f"{int((mt > 0).sum())}/{len(mt)}",
                  "caida_max_%": round(100 * (eq / eq.cummax() - 1).min(), 2)})
        rows.append(r)
    df = pd.DataFrame(rows)
    print("\n### Resumen 2024-2026 (ganancia % de la cuenta)\n" + df.to_string(index=False))
    res["resumen"] = df.to_dict("records")
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(series).to_csv(os.path.join(OUT, "mejoras_mensual.csv"), float_format="%.5f")
    with open(os.path.join(OUT, "mejoras_resumen.json"), "w") as f:
        json.dump(res, f, indent=1, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main()
