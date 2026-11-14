"""Siete mejoras para tener más meses positivos, sobre la variante 4+6a (historia desde 2020 + filtro de régimen).

7  Umbral más bajo (percentil 90): más operaciones por mes.
6  Bloqueo mensual: dejar de operar el mes al llegar a una ganancia o a una pérdida.
5  Filtro de régimen más rápido (para no quedar meses enteros sin operar).
4  Selección diaria: cada día las 2 mejores predicciones, en vez de un umbral fijo.
3  Más monedas (12 en lugar de 6).
2  Modelo propio para mercado bajista (en lugar de no operar).
1  Conjunto de horizontes: modelos de 6 h, 24 h y 72 h, un tercio del capital cada uno.

Uso: python meses.py     (necesita las velas desde 2020 de las 12 monedas: ver README)
"""
import json
import os
import pickle

import numpy as np
import pandas as pd

import estrategias as E
from backtest import full_months
from mejoras import DATA20, END, H, OUT, predict, trades, years

YEARS = [2023, 2024, 2025, 2026]
FIT_YEARS = [2022] + YEARS
COINS6 = list(E.COINS)
COINS12 = COINS6 + ["ADA", "LINK", "AVAX", "LTC", "TRX", "DOT"]
CACHE = os.path.join(os.path.dirname(DATA20), "cache")


def cached(name, f):
    """Guarda las predicciones en disco para no reentrenar en cada corrida (borrar la carpeta para rehacer)."""
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name + ".pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    r = f()
    pickle.dump(r, open(p, "wb"))
    return r


def universe(coins):
    E.COINS, E.SLOTS = list(coins), len(coins)


def build(coins):
    universe(coins)
    P = E.prepare({s: E.load(s, END, None, DATA20) for s in coins})
    for h in P.values():
        for n in (6, 72):
            h[f"y{n}"] = h.onext.shift(-n) / h.onext - 1
    return P


def regime(P, kind="sma200"):
    """Filtros de régimen. sma200: BTC sobre su media de 200 días (el de 4+6a). ema50: BTC sobre su EMA de 50
    días. propia: cada moneda sobre su EMA de 50 días y esta subiendo. mixto: sma200, o BTC sobre su EMA de 50
    días con la EMA subiendo."""
    b = P["BTC"]
    f = {"sma200": lambda h: b.btc_reg > 0,
         "ema50": lambda h: b.dc > b.dema50,
         "propia": lambda h: (h.dc > h.dema50) & (h.dema50 > h.dema50_5),
         "mixto": lambda h: (b.btc_reg > 0) | ((b.dc > b.dema50) & (b.dema50 > b.dema50_5)),
         "ninguno": lambda h: pd.Series(True, index=h.index)}[kind]
    return {s: f(P[s]).fillna(False) for s in E.COINS}


def daily_top(P, pred, k=2):
    """Solo la hora 23 UTC (entrada a las 00:00) y solo las k monedas con mejor predicción ese día."""
    rk = pd.DataFrame(pred).rank(axis=1, ascending=False)
    return {s: ((rk[s] <= k) & (rk.index.hour == 23)).fillna(False) for s in E.COINS}


def no_lim(P):
    return pd.DataFrame(-np.inf, index=P["BTC"].index, columns=[0.9, 0.95, 0.98])


def month_lock(tr, tp=None, sl=None):
    """Deja de abrir operaciones en el mes cuando lo ya cerrado ese mes llega a +tp o a -sl de la cuenta."""
    out = []
    for t in tr:
        m = t[1].to_period("M")
        pnl = sum(x[3] for x in out if x[2] <= t[1] and x[2].to_period("M") == m) / E.SLOTS
        if (tp is not None and pnl >= tp) or (sl is not None and pnl <= -sl):
            continue
        out.append(t)
    return out


def bear_merge(P, pred, lim, pb, lb):
    """Modelo base cuando BTC está sobre su media de 200 días; modelo bajista cuando está debajo."""
    up = (P["BTC"].btc_reg > 0)
    p = {s: pred[s].where(up, pb[s]) for s in E.COINS}
    return p, lim.where(up, lb, axis=0)


RES, SER, TR = {}, {}, {}


def run(key, name, tr=None, idx=None, monthly=None):
    """Tabla por año de una variante. `monthly` permite pasar la ganancia mensual ya calculada (conjuntos)."""
    m = full_months(E.monthly_from_trades(tr), idx) if monthly is None else monthly
    d = pd.DataFrame(tr, columns=["coin", "t0", "t1", "ret"])
    rows = []
    for y in YEARS + ["Total"]:
        t = d if y == "Total" else d[pd.DatetimeIndex(d.t1).year == y]
        if y == "Total":
            t = d[pd.DatetimeIndex(d.t1).year >= YEARS[0]]
        mm = m[[(p.year in YEARS) if y == "Total" else (p.year == y) for p in m.index]]
        rows.append({"año": y, "operaciones": len(t), "acierto_%": round(100 * (t.ret > 0).mean(), 1) if len(t) else None,
                     "media_neta_%": round(100 * t.ret.mean(), 3) if len(t) else None,
                     "ganancia_%": round(100 * ((1 + mm).prod() - 1), 2),
                     "meses_positivos": f"{int((mm > 0).sum())}/{len(mm)}",
                     "meses_negativos": int((mm < 0).sum()), "meses_sin_operar": int((mm == 0).sum())})
    df = pd.DataFrame(rows)
    print(f"\n### {name}\n" + df.to_string(index=False), flush=True)
    RES[key], SER[key], TR[key] = df.to_dict("records"), m, tr
    return tr


def summary(title):
    rows = []
    for k, m in SER.items():
        r = {"variante": k}
        for y in YEARS:
            r[str(y)] = round(100 * ((1 + m[[p.year == y for p in m.index]]).prod() - 1), 1)
        mt = m[[p.year in YEARS for p in m.index]]
        eq = (1 + mt).cumprod()
        m26 = mt[[p.year == 2026 for p in mt.index]]
        r.update({"total_%": round(100 * (eq.iloc[-1] - 1), 1), "meses_pos": f"{int((mt > 0).sum())}/{len(mt)}",
                  "meses_pos_2026": f"{int((m26 > 0).sum())}/{len(m26)}", "peor_mes_%": round(100 * mt.min(), 1),
                  "caida_max_%": round(100 * (eq / eq.cummax() - 1).min(), 1)})
        rows.append(r)
    df = pd.DataFrame(rows)
    print(f"\n### {title}\n" + df.to_string(index=False), flush=True)
    return df


def main():
    P = build(COINS6)
    idx = P["BTC"].index
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    pred, lim = cached("base6", lambda: predict(P, years(FIT_YEARS)))
    reg = regime(P)
    base = run("base", "Base: 4+6a (historia desde 2020 + BTC sobre su media de 200 días)",
               trades(P, pred, lim, filt=reg), idx)

    run("7", "7. Umbral más bajo (percentil 90)", trades(P, pred, lim, 0.9, filt=reg), idx)

    run("6a", "6a. Bloqueo de ganancia: parar el mes al llegar a +3 %", month_lock(base, tp=0.03), idx)
    run("6b", "6b. Límite de pérdida: parar el mes al llegar a -3 %", month_lock(base, sl=0.03), idx)
    run("6", "6. Ambos (+3 % / -3 %)", month_lock(base, 0.03, 0.03), idx)

    for k, n in (("5a", "BTC sobre su EMA de 50 días"), ("5b", "cada moneda sobre su propia EMA de 50 días"),
                 ("5c", "mixto: media de 200 días, o EMA de 50 días subiendo"), ("5d", "sin filtro de régimen")):
        kind = {"5a": "ema50", "5b": "propia", "5c": "mixto", "5d": "ninguno"}[k]
        run(k, f"{k}. Filtro de régimen: {n}", trades(P, pred, lim, filt=regime(P, kind)), idx)

    top = daily_top(P, pred)
    run("4", "4. Selección diaria: las 2 mejores predicciones del día (con filtro de régimen)",
        trades(P, pred, no_lim(P), filt={s: top[s] & reg[s] for s in E.COINS}), idx)
    run("4b", "4b. Selección diaria sin filtro de régimen", trades(P, pred, no_lim(P), filt=top), idx)

    bear = {s: (P["BTC"].btc_reg <= 0).fillna(False) for s in E.COINS}
    pb, lb = cached("bear6", lambda: predict(P, years(FIT_YEARS), mask=bear))
    run("2b", "2b. Solo el modelo bajista (opera cuando BTC está bajo su media de 200 días)",
        trades(P, pb, lb, filt=bear), idx)
    pm, lm = bear_merge(P, pred, lim, pb, lb)
    run("2", "2. Base en mercado alcista + modelo bajista en mercado bajista", trades(P, pm, lm), idx)

    hz = {24: (pred, lim)}
    for n in (6, 72):
        hz[n] = cached(f"h{n}_6", lambda n=n: predict(P, years(FIT_YEARS), target=f"y{n}", gap=n + 2))
    parts = {n: trades(P, p, l, filt=reg, hold=n) for n, (p, l) in hz.items()}
    for n in (6, 72):
        run(f"1_{n}h", f"1 (parte). Solo el modelo de {n} h", parts[n], idx)
    mens = sum(full_months(E.monthly_from_trades(t), idx) for t in parts.values()) / 3
    run("1", "1. Conjunto de horizontes 6 h + 24 h + 72 h (un tercio cada uno)",
        sorted(sum(parts.values(), []), key=lambda x: x[1]), idx, mens)

    # ---- combinaciones de lo que ayudó: horizonte de 72 h (1), límite de pérdida mensual (6b), régimen mixto (5c)
    # y percentil 90 (7)
    mix = regime(P, "mixto")
    p72, l72 = hz[72]

    def half(a, b):
        return (full_months(E.monthly_from_trades(a), idx) + full_months(E.monthly_from_trades(b), idx)) / 2

    def both(a, b):
        return sorted(a + b, key=lambda x: x[1])

    c = {"A": ("A. 24 h + límite de pérdida + régimen mixto", month_lock(trades(P, pred, lim, filt=mix), sl=0.03)),
         "B": ("B. 72 h + límite de pérdida", month_lock(parts[72], sl=0.03)),
         "C": ("C. 72 h + límite de pérdida + régimen mixto",
               month_lock(trades(P, p72, l72, filt=mix, hold=72), sl=0.03)),
         "E": ("E. 24 h + percentil 90 + límite de pérdida", month_lock(trades(P, pred, lim, 0.9, filt=reg), sl=0.03)),
         "F": ("F. 72 h + percentil 90 + límite de pérdida",
               month_lock(trades(P, p72, l72, 0.9, filt=reg, hold=72), sl=0.03)),
         "G": ("G. 72 h + percentil 90 + límite de pérdida + régimen mixto",
               month_lock(trades(P, p72, l72, 0.9, filt=mix, hold=72), sl=0.03))}
    for k, (n, t) in c.items():
        run(k, n, t, idx)
    d1, d2 = month_lock(base, sl=0.03), c["B"][1]
    run("D", "D. Mitad 24 h y mitad 72 h, cada una con límite de pérdida", both(d1, d2), idx, half(d1, d2))
    h1, h2 = c["E"][1], c["F"][1]
    run("H", "H. Mitad 24 h y mitad 72 h, percentil 90 y límite de pérdida", both(h1, h2), idx, half(h1, h2))
    i1, i2 = month_lock(trades(P, pred, lim, 0.9, filt=mix), sl=0.03), c["G"][1]
    run("I", "I. Como H, con régimen mixto", both(i1, i2), idx, half(i1, i2))

    # 3: más monedas (se hace al final porque cambia el universo)
    P12 = build(COINS12)
    i12 = P12["BTC"].index
    p12, l12 = cached("base12", lambda: predict(P12, years(FIT_YEARS)))
    reg12 = regime(P12)
    run("3", "3. Doce monedas (cada operación usa 1/12 del capital)", trades(P12, p12, l12, filt=reg12), i12)

    df = summary("Resumen 2023-2026 (ganancia % de la cuenta)")
    json.dump({"tablas": RES, "resumen": df.to_dict("records")},
              open(os.path.join(OUT, "meses_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)
    pd.DataFrame(SER).to_csv(os.path.join(OUT, "meses_mensual.csv"), float_format="%.5f")


if __name__ == "__main__":
    main()
