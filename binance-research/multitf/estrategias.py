"""Tres estrategias multi-marco (minuto, hora, día, mes) sobre velas de 1 min de Binance spot. Solo largos.

E1  modelo de aprendizaje automático (LightGBM) que predice la ganancia de las próximas 24 h.
E2  fuerza relativa semanal entre monedas, con filtro de régimen de BTC.
E3  tendencia en cascada: el día da la dirección, la hora el retroceso y el gatillo.

Toda decisión usa solo velas cerradas; la entrada es en la apertura de la hora siguiente.
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("PULLBACK_DATA_DIR", os.path.join(os.path.dirname(HERE), "v3_research", "tmp", "k1m", "klines"))
COINS = ["BTC", "ETH", "BNB", "XRP", "SOL", "DOGE"]
COST = 0.0024                 # ida y vuelta: comisión 0,1 % por lado + deslizamiento 0,02 % por lado
SIDE = COST / 2
SLOTS = len(COINS)            # cada operación de E1 y E3 usa 1/6 del capital
HOLD_ML = 24                  # horas que E1 mantiene cada operación

FEATS = ["r15m", "tb1h", "rv1h", "vrel", "r1h", "r4h", "r12h", "r24h", "atr", "d_ema20", "d_ema50", "tb24h",
         "r3d", "r7d", "r30d", "d_dema50", "btc_r24h", "btc_r7d", "btc_reg", "rank7d", "hora", "dia_sem", "dia_mes"]


def load(sym: str, end=None, start=None, data=None) -> pd.DataFrame:
    """Velas de 1 hora (con datos derivados del minuto) a partir del .npy de 1 min."""
    a = np.load(os.path.join(data or DATA, f"{sym}USDT_1m.npy"))
    if end is not None:
        a = a[a[:, 0] < pd.Timestamp(end).value // 10**6]
    if start is not None:
        a = a[a[:, 0] >= pd.Timestamp(start).value // 10**6]
    m = pd.DataFrame(a[:, 1:7], columns=["o", "h", "l", "c", "v", "tb"],
                     index=pd.to_datetime(a[:, 0].astype(np.int64), unit="ms"))
    g = m.resample("1h")
    h = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "v": g.v.sum(),
                      "tb": g.tb.sum(), "n": g.c.count()})
    h["rv1h"] = np.log(m.c).diff().resample("1h").std()
    c44 = m.c[m.index.minute == 44]
    h["c44"] = pd.Series(c44.values, index=c44.index.floor("1h")).reindex(h.index)
    if h.n.iloc[-1] < 60:                                  # hora en curso: fuera
        h = h.iloc[:-1]
    c = h.c.ffill()                                        # huecos de Binance: vela plana sin volumen
    for k in "ohl":
        h[k] = h[k].fillna(c)
    h["c"] = c
    return h


def prepare(H: dict) -> dict:
    """Alinea las monedas y añade indicadores. La fila i contiene solo información hasta el cierre de la hora i."""
    idx = None
    for h in H.values():
        idx = h.index if idx is None else idx.intersection(h.index)
    out = {}
    for s, h in H.items():
        h = h.loc[idx].copy()
        c = h.c
        h["onext"] = h.o.shift(-1)
        tr = np.maximum(h.h - h.l, np.maximum((h.h - c.shift()).abs(), (h.l - c.shift()).abs()))
        h["atr_abs"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
        h["ema20"] = c.ewm(span=20, adjust=False).mean()
        h["ema50"] = c.ewm(span=50, adjust=False).mean()
        # diario: solo días cerrados. El día D queda disponible en la fila que abre a D+23h
        d = h.resample("1D").agg({"c": "last", "n": "count"})
        d = d[d.n == 24]
        dd = pd.DataFrame({"dc": d.c, "dema50": d.c.ewm(span=50, adjust=False).mean(),
                           "dsma200": d.c.rolling(200).mean()})
        dd["dema50_5"] = dd.dema50.shift(5)
        for L in (14, 28, 56):
            dd[f"mom{L}"] = d.c / d.c.shift(L) - 1
        dd.index = dd.index + pd.Timedelta(hours=23)
        h = h.join(dd.reindex(h.index, method="ffill"))
        # variables del modelo
        h["r15m"] = c / h.c44 - 1
        h["tb1h"] = (h.tb / h.v.replace(0, np.nan)).fillna(0.5)
        h["vrel"] = h.v / h.v.rolling(24).mean()
        for n, k in ((1, "r1h"), (4, "r4h"), (12, "r12h"), (24, "r24h"), (72, "r3d"), (168, "r7d"), (720, "r30d")):
            h[k] = c / c.shift(n) - 1
        h["atr"] = h.atr_abs / c
        h["d_ema20"] = c / h.ema20 - 1
        h["d_ema50"] = c / h.ema50 - 1
        h["tb24h"] = h.tb.rolling(24).sum() / h.v.rolling(24).sum()
        h["d_dema50"] = c / h.dema50 - 1
        h["hora"], h["dia_sem"], h["dia_mes"] = h.index.hour, h.index.dayofweek, h.index.day
        h["y24"] = h.onext.shift(-HOLD_ML) / h.onext - 1   # objetivo: de la apertura i+1 a la apertura i+25
        out[s] = h
    b = out["BTC"]
    r7 = pd.DataFrame({s: h.r7d for s, h in out.items()}).rank(axis=1, ascending=False)
    for L in (14, 28, 56):
        rk = pd.DataFrame({s: h[f"mom{L}"] for s, h in out.items()}).rank(axis=1, ascending=False)
        for s, h in out.items():
            h[f"rk{L}"] = rk[s]
    for s, h in out.items():
        h["btc_r24h"], h["btc_r7d"] = b.r24h, b.r7d
        h["btc_reg"] = b.dc / b.dsma200 - 1                # régimen: BTC contra su media de 200 días
        h["rank7d"] = r7[s]
    return out


# ---------------------------------------------------------------- E2: fuerza relativa semanal

def strat2(P: dict, L: int = 28, k: int = 2):
    """Cada lunes 00:00 UTC: comprar las k monedas con mayor subida en L días (si subieron) y solo si BTC está
    sobre su media de 200 días. Devuelve (operaciones, serie de ganancias semanales de la cartera)."""
    b = P["BTC"]
    rows = b.index[(b.index.dayofweek == 6) & (b.index.hour == 23) & b.onext.notna() & b.dsma200.notna()]
    px = pd.DataFrame({s: P[s].onext.loc[rows] for s in COINS})
    mom = pd.DataFrame({s: P[s][f"mom{L}"].loc[rows] for s in COINS})
    reg = (b.btc_reg.loc[rows] > 0).values
    held, trades, weekly = {}, [], []
    for j, t in enumerate(rows):
        t_in = t + pd.Timedelta(hours=1)
        m = mom.iloc[j].dropna()
        want = list(m[m > 0].sort_values(ascending=False).index[:k]) if reg[j] else []
        changes = 0
        for s in list(held):
            if s not in want:
                e, t0 = held.pop(s)
                trades.append((s, t0, t_in, px[s].iloc[j] / e - 1 - COST))
                changes += 1
        for s in want:
            if s not in held:
                held[s] = (px[s].iloc[j], t_in)
                changes += 1
        if j + 1 < len(rows):
            r = sum(px[s].iloc[j + 1] / px[s].iloc[j] - 1 for s in want) / k - changes * SIDE / k
            weekly.append((rows[j + 1] + pd.Timedelta(hours=1), r))
    for s, (e, t0) in held.items():                        # cierre de lo que quede abierto
        trades.append((s, t0, rows[-1] + pd.Timedelta(hours=1), px[s].iloc[-1] / e - 1 - COST))
    return trades, pd.Series(dict(weekly))


# ---------------------------------------------------------------- E3: tendencia en cascada

def strat3(P: dict, rr: float = 3.0, hold: int = 7 * 24, filt: dict = None):
    """Día: cierre sobre la EMA 50 diaria y EMA 50 diaria subiendo. Hora: precio sobre la EMA 50, retroceso que
    tocó la EMA 20 en las últimas 12 h y cierre sobre el máximo de las 3 horas previas. Stop bajo el mínimo del
    retroceso (distancia entre 1,5 % y 8 %), objetivo rr veces el riesgo, salida por tiempo a `hold` horas."""
    trades = []
    for s in COINS:
        h = P[s]
        sig = ((h.dc > h.dema50) & (h.dema50 > h.dema50_5) & (h.c > h.ema50) & (h.c > h.ema20)
               & ((h.l < h.ema20).astype(float).rolling(12).max() > 0) & (h.c > h.h.shift(1).rolling(3).max()))
        if filt is not None:
            sig &= filt[s]
        sb = (h.l.rolling(12).min() - 0.5 * h.atr_abs).values
        o, hi, lo, c, T = h.o.values, h.h.values, h.l.values, h.c.values, h.index
        n, free = len(h), 0
        for i in np.flatnonzero(sig.values):
            if i < free or i + 1 >= n or np.isnan(sb[i]):
                continue
            ent = o[i + 1]
            stop = min(sb[i], ent * (1 - 0.015))
            if (ent - stop) / ent > 0.08:
                continue
            tp, end = ent + rr * (ent - stop), min(i + hold, n - 1)
            j, px = i + 1, None
            while j <= end:
                if lo[j] <= stop:                          # si toca stop y objetivo en la misma hora: stop
                    px = min(stop, o[j])
                    break
                if hi[j] >= tp:
                    px = tp
                    break
                j += 1
            if px is None:
                j, px = end, c[end]
            trades.append((s, T[i + 1], T[j] + pd.Timedelta(hours=1), px / ent - 1 - COST))
            free = j + 1
    return sorted(trades, key=lambda x: x[1])


# ---------------------------------------------------------------- E1: aprendizaje automático

def ml_predict(P: dict, years, seed: int = 0) -> dict:
    """Walk-forward por años: para juzgar el año Y se entrena solo con datos anteriores a Y. El 20 % final del
    entrenamiento se aparta para fijar el umbral de entrada. Devuelve {moneda: predicción} y los umbrales."""
    import lightgbm as lgb
    X = pd.concat([P[s][FEATS + ["y24"]].assign(coin=i) for i, s in enumerate(COINS)])
    X = X.dropna(subset=["y24", "r30d"])
    pred = {s: pd.Series(np.nan, index=P[s].index) for s in COINS}
    thr = {}
    for y in years:
        y0 = pd.Timestamp(f"{y}-01-01")
        tr = X[X.index < y0 - pd.Timedelta(hours=HOLD_ML + 2)]         # el objetivo no pisa el año juzgado
        cut = tr.index.unique().sort_values()[int(tr.index.nunique() * 0.8)]
        fit, val = tr[tr.index < cut - pd.Timedelta(hours=HOLD_ML + 2)], tr[tr.index >= cut]
        mdl = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=500,
                                subsample=0.7, subsample_freq=1, colsample_bytree=0.7, reg_lambda=5.0,
                                random_state=seed, verbose=-1, n_jobs=4)
        mdl.fit(fit[FEATS], fit.y24)
        pv = mdl.predict(val[FEATS])
        thr[y] = {q: float(np.quantile(pv, q)) for q in (0.5, 0.9, 0.95, 0.98)}
        thr[y]["ic_val"] = float(np.corrcoef(pv, val.y24)[0, 1])
        for i, s in enumerate(COINS):
            te = P[s][(P[s].index >= y0) & (P[s].index < y0 + pd.DateOffset(years=1))]
            te = te[te.r30d.notna()]
            pred[s].loc[te.index] = mdl.predict(te[FEATS])
    return pred, thr


def strat1(P: dict, pred: dict, thr: dict, q: float = 0.95):
    """Entra cuando la predicción supera el costo y el percentil q de la validación. Mantiene 24 h."""
    trades = []
    for s in COINS:
        h, p = P[s], pred[s].values
        o, T, n, free = h.o.values, h.index, len(h), 0
        lim = np.array([max(COST, thr[y][q]) if y in thr else np.inf for y in T.year])
        for i in np.flatnonzero(p > lim):
            if i < free or i + 1 + HOLD_ML >= n:
                continue
            trades.append((s, T[i + 1], T[i + 1 + HOLD_ML], o[i + 1 + HOLD_ML] / o[i + 1] - 1 - COST))
            free = i + HOLD_ML
    return sorted(trades, key=lambda x: x[1])


# ---------------------------------------------------------------- contabilidad

def monthly_from_trades(trades) -> pd.Series:
    """Ganancia mensual de la cuenta: cada operación usa 1/6 del capital; se anota en el mes de salida."""
    if not trades:
        return pd.Series(dtype=float)
    s = pd.Series([t[3] for t in trades], index=pd.DatetimeIndex([t[2] for t in trades]))
    return s.groupby(s.index.to_period("M")).sum() / SLOTS


def monthly_from_weekly(w: pd.Series) -> pd.Series:
    return (1 + w).groupby(w.index.to_period("M")).prod() - 1
