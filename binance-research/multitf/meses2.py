"""Diez mejoras sobre la variante G para tener más meses positivos en 2026.

G = modelo de 72 h (historia desde 2020), percentil 90, régimen mixto y parar el mes al perder 3 %.

10  Proteger el mes: tras llegar a +2 %, parar si baja a +1 %.
 9  Límite de pérdida semanal (-1,5 %).
 8  Fuera de régimen no apagar: exigir percentil 98.
 7  Salidas anticipadas dentro de las 72 h (stop y objetivo por ATR).
 6  Regla de rebote tras capitulación en mercado bajista.
 5  Modelo de 7 días (168 h).
 4  Reentrenar el modelo de 72 h cada mes.
 3  Promedio de 5 modelos (semillas distintas).
 2  Cortos en mercado bajista (necesita futuros).
 1  Largo/corto neutral: cada día largo en las 2 mejores y corto en las 2 peores (necesita futuros).

Uso: python meses2.py
"""
import json
import os

import numpy as np
import pandas as pd

import estrategias as E
import meses as M
from mejoras import H, OUT, months, predict, trades, years

M.END = None                                              # usar todos los datos descargados
FIT = M.FIT_YEARS
TAG = "_v2"
MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def locks(tr, msl=0.03, wsl=None, arm=None, floor=None):
    """Controles de cuenta sobre operaciones ordenadas por entrada. msl: parar el mes al perder msl.
    wsl: parar la semana al perder wsl. arm/floor: si el mes llegó a +arm, parar cuando baje a +floor."""
    out = []
    for t in tr:
        m, w = t[1].to_period("M"), t[1].to_period("W")
        done = sorted((x for x in out if x[2] <= t[1]), key=lambda x: x[2])
        pm = [x[3] / E.SLOTS for x in done if x[2].to_period("M") == m]
        pw = sum(x[3] for x in done if x[2].to_period("W") == w) / E.SLOTS
        cum = np.cumsum(pm) if pm else np.array([0.0])
        if msl is not None and cum[-1] <= -msl:
            continue
        if wsl is not None and pw <= -wsl:
            continue
        if arm is not None and cum.max() >= arm and cum[-1] <= floor:
            continue
        out.append(t)
    return out


def barriers(P, ksl, ktp, n=72):
    """Resultado de cada posible entrada con stop a ksl ATR y objetivo a ktp ATR (None = sin él), máximo n horas.
    Si una hora toca ambos, cuenta el stop."""
    for s in E.COINS:
        h = P[s]
        ent = h.onext.values
        sl = (ksl * h.atr).values if ksl else np.full(len(h), np.inf)
        tp = (ktp * h.atr).values if ktp else np.full(len(h), np.inf)
        stop = ent * (1 - sl)
        st, ret, kx = np.zeros(len(h)), np.full(len(h), np.nan), np.full(len(h), n)
        for k in range(1, n + 1):
            lo, hi, op = (h[c].shift(-k).values for c in ("l", "h", "o"))
            a = (st == 0) & (lo <= stop)
            ret[a], st[a], kx[a] = np.minimum(stop, op)[a] / ent[a] - 1, -1, k
            b = (st == 0) & (hi >= ent * (1 + tp))
            ret[b], st[b], kx[b] = tp[b], 1, k
        yn = h[f"y{n}"].values
        ret[st == 0] = yn[st == 0]
        h["tb_ret"], h["tb_k"] = np.where(np.isnan(yn) | np.isnan(h.atr.values), np.nan, ret), kx


def neutral(P, pred, k=2, hold=72):
    """Cada día a las 00:00 UTC: largo en las k mejores predicciones y corto en las k peores, 72 h. Hay 3 tramos
    abiertos a la vez con 2k patas cada uno: cada pata usa 1/(6k) del capital."""
    df = pd.DataFrame(pred)
    hi, lo, day = df.rank(axis=1, ascending=False), df.rank(axis=1), df.index.hour == 23
    tr = []
    for s in E.COINS:
        y = P[s][f"y{hold}"]
        for sign, rk in ((1, hi), (-1, lo)):
            m = (rk[s] <= k) & day & y.notna()
            tr += [(s, t + H, t + (hold + 1) * H, sign * v - E.COST) for t, v in y[m].items()]
    tr.sort(key=lambda x: x[1])
    r = pd.Series([t[3] for t in tr], index=pd.DatetimeIndex([t[2] for t in tr]))
    return tr, r.groupby(r.index.to_period("M")).sum() / (3 * 2 * k)


def show(key, name, tr, idx, monthly=None):
    M.run(key, name, tr, idx, monthly)
    m = M.SER[key]
    m26 = m[[p.year == 2026 for p in m.index]]
    print("2026 por mes (%): " + "  ".join(f"{MES[p.month - 1]} {100 * v:+.2f}" for p, v in m26.items())
          + f"   -> positivos {int((m26 > 0).sum())}/{len(m26)}", flush=True)
    return tr


def main():
    P = M.build(M.COINS6)
    for h in P.values():
        h["y168"] = h.onext.shift(-168) / h.onext - 1
    idx = P["BTC"].index
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    p72, l72 = M.cached("h72" + TAG, lambda: predict(P, years(FIT), target="y72", gap=74))
    mix = M.regime(P, "mixto")
    off = {s: ~mix[s] for s in E.COINS}
    up = mix["BTC"]

    def longs(pred=p72, lim=l72, filt=mix, q=0.9, hold=72, **kw):
        return trades(P, pred, lim, q, filt=filt, hold=hold, **kw)

    raw = longs()
    show("G", "Base G (72 h, percentil 90, régimen mixto, parar el mes en -3 %)", locks(raw), idx)

    show("10", "10. Proteger el mes: tras +2 %, parar si baja a +1 %", locks(raw, arm=0.02, floor=0.01), idx)
    show("10b", "10b. Proteger el mes: tras +1 %, parar si baja a +0,5 %", locks(raw, arm=0.01, floor=0.005), idx)

    show("9", "9. Límite de pérdida semanal (-1,5 %) además del mensual", locks(raw, wsl=0.015), idx)

    for k, q in (("8", 0.98), ("8b", 0.95)):
        lq = l72.copy()
        lq[0.9] = l72[0.9].where(up, l72[q])
        show(k, f"8{k[1:]}. Fuera de régimen no apagar: exigir percentil {int(q * 100)}",
             locks(longs(lim=lq, filt=None)), idx)

    for k, (a, b, n) in {"7a": (6, None, "solo stop a 6 ATR"), "7b": (None, 12, "solo objetivo a 12 ATR"),
                         "7": (6, 12, "stop a 6 ATR y objetivo a 12 ATR"),
                         "7c": (4, 8, "stop a 4 ATR y objetivo a 8 ATR")}.items():
        barriers(P, a, b)
        show(k, f"{k}. Salida anticipada: {n}", locks(longs(barrier=True)), idx)

    cap = {s: ((P[s].r7d <= -0.15) & (P[s].c > P[s].h.shift(1).rolling(3).max()) & off[s]).astype(float)
           for s in E.COINS}
    half = pd.DataFrame(0.5, index=idx, columns=[0.9])
    reb = trades(P, cap, half, 0.9, hold=72)
    show("6b", "6b. Solo la regla de rebote (caída de 15 % en 7 días y giro al alza, fuera de régimen)", reb, idx)
    show("6", "6. G + regla de rebote", locks(sorted(raw + reb, key=lambda x: x[1])), idx)

    p168, l168 = M.cached("h168" + TAG, lambda: predict(P, years(FIT), target="y168", gap=170))
    r168 = longs(p168, l168, hold=168)
    show("5", "5. Modelo de 7 días en lugar del de 72 h", locks(r168), idx)
    a, b = locks(raw), locks(r168)
    show("5b", "5b. Mitad 72 h y mitad 7 días", sorted(a + b, key=lambda x: x[1]), idx,
         (M.full_months(E.monthly_from_trades(a), idx) + M.full_months(E.monthly_from_trades(b), idx)) / 2)

    pm, lm = M.cached("h72m" + TAG, lambda: predict(P, months(2022, 2026), target="y72", gap=74))
    show("4", "4. Reentrenar el modelo de 72 h cada mes", locks(longs(pm, lm)), idx)

    pe, le = M.cached("h72s5" + TAG, lambda: predict(P, years(FIT), target="y72", gap=74, seeds=range(5)))
    show("3", "3. Promedio de 5 modelos", locks(longs(pe, le)), idx)

    # cortos: se simulan con el mismo costo que una compra (0,24 %); en la práctica requieren futuros
    Pn = {s: P[s].assign(y72=-P[s].y72) for s in E.COINS}
    pn = {s: -p72[s] for s in E.COINS}
    ln = pd.DataFrame({0.9: -l72[0.1], 0.95: -l72[0.05], 0.98: -l72[0.02]})
    sh = trades(Pn, pn, ln, 0.9, filt=off, hold=72)
    show("2b", "2b. Solo cortos fuera de régimen (predicción bajo el percentil 10)", locks(sh), idx)
    show("2", "2. G + cortos fuera de régimen", locks(sorted(raw + sh, key=lambda x: x[1])), idx)
    sh_all = trades(Pn, pn, ln, 0.9, hold=72)
    show("2c", "2c. Largos y cortos sin filtro de régimen", locks(sorted(longs(filt=None) + sh_all,
                                                                          key=lambda x: x[1])), idx)

    tn, mn = neutral(P, p72)
    show("1", "1. Largo/corto neutral diario (2 mejores contra 2 peores)", tn, idx, M.full_months(mn, idx))
    tn1, mn1 = neutral(P, p72, 1)
    show("1b", "1b. Largo/corto neutral diario (la mejor contra la peor)", tn1, idx, M.full_months(mn1, idx))

    # ---- combinaciones: reentreno mensual (4) con percentil 98 fuera de régimen (8), rebote (6), objetivo (7b)
    # y cortos fuera de régimen (2)
    def srt(*parts):
        return sorted(sum(parts, []), key=lambda x: x[1])

    lq = lm.copy()
    lq[0.9] = lm[0.9].where(up, lm[0.98])
    base4, wide4 = longs(pm, lm), longs(pm, lq, filt=None)
    pnm = {s: -pm[s] for s in E.COINS}
    lnm = pd.DataFrame({0.9: -lm[0.1], 0.95: -lm[0.05], 0.98: -lm[0.02]})
    sh4 = trades(Pn, pnm, lnm, 0.9, filt=off, hold=72)
    sh4s = trades(Pn, pnm, lnm, 0.98, filt=off, hold=72)
    barriers(P, None, 12)
    tp4 = longs(pm, lm, barrier=True)
    show("K1", "K1. Reentreno mensual + percentil 98 fuera de régimen (solo compras)", locks(wide4), idx)
    show("K2", "K2. Reentreno mensual + regla de rebote (solo compras)", locks(srt(base4, reb)), idx)
    show("K3", "K3. Reentreno mensual + objetivo a 12 ATR (solo compras)", locks(tp4), idx)
    show("K4", "K4. Reentreno mensual + cortos fuera de régimen (futuros)", locks(srt(base4, sh4)), idx)
    show("K5", "K5. Reentreno mensual + cortos muy selectivos, percentil 2 (futuros)", locks(srt(base4, sh4s)), idx)
    show("K6", "K6. K1 + cortos fuera de régimen (futuros)", locks(srt(wide4, sh4)), idx)
    show("K7", "K7. K3 + cortos fuera de régimen (futuros)", locks(srt(tp4, sh4)), idx)

    df = M.summary("Resumen 2023-2026 (ganancia % de la cuenta)")
    m26 = pd.DataFrame({k: (100 * m[[p.year == 2026 for p in m.index]]).round(2) for k, m in M.SER.items()}).T
    m26.columns = [MES[p.month - 1] for p in m26.columns]
    m26["positivos"] = (m26 > 0).sum(axis=1)
    print("\n### 2026 mes a mes (%)\n" + m26.to_string(), flush=True)
    json.dump({"tablas": M.RES, "resumen": df.to_dict("records"), "meses_2026": m26.T.to_dict()},
              open(os.path.join(OUT, "meses2_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)
    pd.DataFrame(M.SER).to_csv(os.path.join(OUT, "meses2_mensual.csv"), float_format="%.5f")


if __name__ == "__main__":
    main()
