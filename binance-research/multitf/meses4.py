"""Ocho mejoras sobre la combinación 2+3+6+7 y todas sus combinaciones (2^8 = 256).

Base = modelo de 72 h reentrenado cada mes; percentil 90 (95 si BTC está bajo su media de 200 días); acuerdo con el
modelo de 24 h; objetivo a 12 ATR; comisión con BNB; parar el mes en -3 %.

Se acepta una variante solo si cumple las tres condiciones en 2026:
  C1  septiembre, octubre y noviembre mejores que los de la base
  C2  el año queda positivo
  C3  al menos 6 meses positivos de 11

8  Capital sin usar en Earn flexible (interés supuesto del 2 % anual).
7  Límite de pérdida mensual más ajustado (-2 %).
6  Máximo de posiciones abiertas a la vez.
5  Pausa por moneda tras una pérdida.
4  No entrar con volatilidad alta de BTC.
3  Solo las monedas más fuertes a 28 días.
2  Mover el stop a la entrada tras avanzar k ATR.
1  Cortos muy selectivos fuera de régimen (necesita futuros).

Uso: python meses4.py
"""
import itertools
import json
import os

import numpy as np
import pandas as pd

import estrategias as E
import meses as M
from mejoras import OUT, months, predict, trades
from meses2 import MES, TAG, locks
from meses3 import COST_BNB, year26

M.END = None
D = pd.Timedelta(days=1)
RATE_H = lambda apy: (1 + apy) ** (1 / 8760) - 1         # noqa: E731  interés por hora


def exits(P, ktp=12.0, kbe=None, n=72):
    """Para cada posible entrada: resultado con objetivo a ktp ATR y, si kbe, stop en la entrada (más el costo)
    una vez que el precio avanzó kbe ATR. El stop se activa al cierre de la hora en que se alcanza kbe."""
    out = {}
    for s in E.COINS:
        h = P[s]
        ent, a = h.onext.values, h.atr.values
        tp, be = ent * (1 + ktp * a), ent * (1 + E.COST)
        st, ret, kx, armed = np.zeros(len(h)), np.full(len(h), np.nan), np.full(len(h), n), np.zeros(len(h), bool)
        for k in range(1, n + 1):
            lo, hi, op = (h[c].shift(-k).values for c in ("l", "h", "o"))
            x = (st == 0) & armed & (lo <= be)
            ret[x], st[x], kx[x] = np.minimum(be, op)[x] / ent[x] - 1, -1, k
            y = (st == 0) & (hi >= tp)
            ret[y], st[y], kx[y] = (ktp * a)[y], 1, k
            if kbe:
                armed |= hi >= ent * (1 + kbe * a)
        yn = h[f"y{n}"].values
        ret[st == 0] = yn[st == 0]
        out[s] = (np.where(np.isnan(yn) | np.isnan(a), np.nan, ret), kx)
    return out


def main():
    P = M.build(M.COINS6)
    idx = P["BTC"].index
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    per = months(2022, 2026)
    pm, lm = M.cached("h72m" + TAG, lambda: predict(P, per, target="y72", gap=74))
    p24, _ = M.cached("h24m" + TAG, lambda: predict(P, per, target="y24", gap=26))
    b = P["BTC"]
    mix = M.regime(P, "mixto")
    strong = (b.btc_reg > 0).fillna(False)
    lim = lm.copy()
    lim[0.9] = lm[0.9].where(strong, lm[0.95])                       # sugerencia 3 de la ronda anterior
    volq = {q: b.atr < b.atr.rolling(2160).quantile(q) for q in (0.8, 0.9)}   # ATR de BTC contra sus últimos 90 días
    EX = {None: exits(P), 6: exits(P, kbe=6), 4: exits(P, kbe=4)}
    Pn = {s: P[s].assign(y72=-P[s].y72) for s in E.COINS}
    pn = {s: -pm[s] for s in E.COINS}
    ln = pd.DataFrame({0.95: -lm[0.05], 0.98: -lm[0.02]})
    off = {s: ~mix[s] for s in E.COINS}
    SH = {q: [(s, a, c, r + E.COST - COST_BNB) for s, a, c, r in trades(Pn, pn, ln, q, filt=off, hold=72)]
          for q in (0.95, 0.98)}
    hours = pd.Series(1.0, index=idx).groupby(idx.to_period("M")).sum()

    def make(earn=None, msl=0.03, maxpos=None, cool=None, vol=None, rs=None, be=None, short=None):
        filt = {}
        for s in E.COINS:
            f = mix[s] & (p24[s] > 0).fillna(False)
            if vol:
                f &= volq[vol].fillna(False)
            if rs:
                f &= (P[s].rk28 <= rs).fillna(False)
            filt[s] = f
            P[s]["tb_ret"], P[s]["tb_k"] = EX[be][s]
        tr = [(s, a, c, r + E.COST - COST_BNB) for s, a, c, r in trades(P, pm, lim, 0.9, filt=filt, barrier=True)]
        if short:
            tr = sorted(tr + SH[short], key=lambda x: x[1])
        if cool or maxpos:
            out, until = [], {}
            for t in tr:
                if cool and t[1] < until.get(t[0], pd.Timestamp.min):
                    continue
                if maxpos and sum(1 for x in out if x[2] > t[1]) >= maxpos:
                    continue
                out.append(t)
                if cool and t[3] < 0:
                    until[t[0]] = t[2] + cool * D
            tr = out
        tr = locks(tr, msl=msl)
        m = M.full_months(E.monthly_from_trades(tr), idx)
        if earn:                                           # interés sobre la parte del capital sin posición
            held = pd.Series([(t[2] - t[1]) / pd.Timedelta(hours=1) for t in tr],
                             index=pd.DatetimeIndex([t[2] for t in tr]))
            held = held.groupby(held.index.to_period("M")).sum().reindex(m.index).fillna(0.0)
            m = m + RATE_H(earn) * (hours.reindex(m.index) - held / E.SLOTS)
        return tr, m

    base = {}

    def check(m):
        m26 = (100 * year26(m)).round(2)
        g = 100 * ((1 + year26(m)).prod() - 1)
        r = {"meses": m26.tolist(), "pos": int((m26 > 0).sum()), "gan": round(g, 2)}
        if base:
            r["C1"] = all(m26.iloc[i] > base["meses"][i] for i in (8, 9, 10))
            r["C2"], r["C3"] = g > 0, r["pos"] >= 6
            r["cumple"] = r["C1"] and r["C2"] and r["C3"]
        return r

    rows = {}

    def show(key, name, **kw):
        tr, m = make(**kw)
        M.run(key, name, tr, idx, m)
        r = check(m)
        if not base:
            base.update(r)
        rows[key] = {"nombre": name, **r}
        print("2026 por mes (%): " + "  ".join(f"{MES[i]} {v:+.2f}" for i, v in enumerate(r["meses"]))
              + f"   -> positivos {r['pos']}/11, año {r['gan']:+.2f} %", flush=True)
        if "cumple" in r:
            print("  ".join(f"{c} {'sí' if r[c] else 'no'}" for c in ("C1", "C2", "C3"))
                  + f"  ->  {'CUMPLE LAS TRES' if r['cumple'] else 'no cumple'}", flush=True)

    show("base", "Base: combinación 2+3+6+7")
    show("8", "8. Capital sin usar en Earn flexible (2 % anual supuesto)", earn=0.02)
    show("8b", "8b. Earn flexible al 4 % anual supuesto", earn=0.04)
    show("7", "7. Parar el mes al perder 2 %", msl=0.02)
    show("7b", "7b. Parar el mes al perder 1,5 %", msl=0.015)
    show("6", "6. Máximo 3 posiciones abiertas", maxpos=3)
    show("6b", "6b. Máximo 2 posiciones abiertas", maxpos=2)
    show("5", "5. Pausa de 3 días en la moneda tras una pérdida", cool=3)
    show("5b", "5b. Pausa de 7 días en la moneda tras una pérdida", cool=7)
    show("4", "4. No entrar si la volatilidad de BTC está en su 10 % más alto de 90 días", vol=0.9)
    show("4b", "4b. No entrar si la volatilidad de BTC está en su 20 % más alto", vol=0.8)
    show("3", "3. Solo las 3 monedas más fuertes a 28 días", rs=3)
    show("3b", "3b. Solo las 2 monedas más fuertes a 28 días", rs=2)
    show("2", "2. Stop a la entrada tras avanzar 6 ATR", be=6)
    show("2b", "2b. Stop a la entrada tras avanzar 4 ATR", be=4)
    show("1", "1. Cortos fuera de régimen bajo el percentil 2 (futuros)", short=0.98)
    show("1b", "1b. Cortos fuera de régimen bajo el percentil 5 (futuros)", short=0.95)

    opts = {"short": [None, 0.98], "be": [None, 6], "rs": [None, 3], "vol": [None, 0.9], "cool": [None, 3],
            "maxpos": [None, 3], "msl": [0.03, 0.02], "earn": [None, 0.02]}
    tag = dict(zip(opts, "12345678"))
    out, ser = [], {}
    for vals in itertools.product(*opts.values()):
        kw = dict(zip(opts, vals))
        on = [tag[k] for k, v in kw.items() if v != opts[k][0]]
        if len(on) < 2:
            continue
        name = "+".join(on)
        _, m = make(**kw)
        r = check(m)
        mt = m[[p.year in M.YEARS for p in m.index]]
        eq = (1 + mt).cumprod()
        out.append({"combinación": name, **{str(y): round(100 * ((1 + m[[p.year == y for p in m.index]]).prod() - 1), 1)
                                           for y in M.YEARS[:3]},
                    "gan_2026": r["gan"], "pos_2026": r["pos"], "sep": r["meses"][8], "oct": r["meses"][9],
                    "nov": r["meses"][10], "C1": r["C1"], "C2": r["C2"], "C3": r["C3"], "cumple": r["cumple"],
                    "pos_47": int((mt > 0).sum()), "caída_max": round(100 * (eq / eq.cummax() - 1).min(), 1)})
        ser[name] = m
    df = pd.DataFrame(out).sort_values(["cumple", "pos_2026", "gan_2026"], ascending=False)
    print(f"\n### Combinaciones: {int(df.cumple.sum())} de {len(df)} cumplen las tres condiciones "
          f"({int((df.cumple & ~df['combinación'].str.contains('1')).sum())} sin futuros). Las 20 mejores:")
    print(df.head(20).to_string(index=False), flush=True)
    for name in df.head(10)["combinación"]:
        print(f"{name}: " + "  ".join(f"{MES[i]} {100 * v:+.2f}" for i, v in enumerate(year26(ser[name]).values)), flush=True)
    ind = pd.DataFrame([{"variante": k, "pos_2026": r["pos"], "gan_2026": r["gan"], "sep": r["meses"][8],
                         "oct": r["meses"][9], "nov": r["meses"][10], **{c: r.get(c) for c in ("C1", "C2", "C3", "cumple")}}
                        for k, r in rows.items()])
    print("\n### Individuales\n" + ind.to_string(index=False))
    M.summary("Resumen 2023-2026 de las individuales (ganancia % de la cuenta)")
    json.dump({"individuales": rows, "combinaciones": df.to_dict("records")},
              open(os.path.join(OUT, "meses4_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)
    pd.DataFrame({**M.SER, **{k: ser[k] for k in df.head(10)["combinación"]}}).to_csv(
        os.path.join(OUT, "meses4_mensual.csv"), float_format="%.5f")


if __name__ == "__main__":
    main()
