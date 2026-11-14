"""Siete mejoras sobre la variante 4 (modelo de 72 h reentrenado cada mes) y todas sus combinaciones.

Una variante se acepta solo si cumple las tres condiciones en 2026 frente a la base:
  C1  mejora más meses de los que empeora
  C2  tiene más meses positivos
  C3  gana más en el año

7  Pagar la comisión con BNB (costo de 0,24 % a 0,19 % por operación).
6  Objetivo de ganancia a k ATR dentro de las 72 h.
5  Confirmación en 1 h antes de entrar.
4  Tamaño según la fuerza de la señal.
3  Umbral más exigente cuando el régimen es débil.
2  Acuerdo con un modelo de 24 h.
1  Variables de amplitud de mercado en el modelo.

Uso: python meses3.py
"""
import itertools
import json
import os

import numpy as np
import pandas as pd

import estrategias as E
import meses as M
from mejoras import H, OUT, months, predict, trades
from meses2 import MES, TAG, barriers, locks

M.END = None
COST_BNB = 0.0019            # 0,075 % por lado con descuento de BNB + 0,02 % de deslizamiento por lado
BREADTH = ["br_ema", "br_r24", "br_r7", "disp7"]


def year26(m):
    return m[[p.year == 2026 for p in m.index]]


def main():
    P = M.build(M.COINS6)
    idx = P["BTC"].index
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    per = months(2022, 2026)
    pm, lm = M.cached("h72m" + TAG, lambda: predict(P, per, target="y72", gap=74))
    p24, _ = M.cached("h24m" + TAG, lambda: predict(P, per, target="y24", gap=26))

    # amplitud de mercado: cuántas monedas están sobre su EMA diaria, y media y dispersión de sus subidas
    P["BTC"]  # noqa
    above = pd.DataFrame({s: (P[s].dc > P[s].dema50).astype(float) for s in E.COINS})
    r24, r7 = pd.DataFrame({s: P[s].r24h for s in E.COINS}), pd.DataFrame({s: P[s].r7d for s in E.COINS})
    for h in P.values():
        h["br_ema"], h["br_r24"], h["br_r7"], h["disp7"] = above.mean(axis=1), r24.mean(axis=1), r7.mean(axis=1), r7.std(axis=1)
    feats = list(E.FEATS)

    def with_breadth():
        E.FEATS = feats + BREADTH
        try:
            return predict(P, per, target="y72", gap=74)
        finally:
            E.FEATS = feats

    pb, lb = M.cached("h72mb" + TAG, with_breadth)

    mix = M.regime(P, "mixto")
    strong = (P["BTC"].btc_reg > 0).fillna(False)

    def make(model="base", agree=None, dyn=None, size=False, confirm=None, tp=None, bnb=False):
        pred, lim = (pb, lb) if model == "amplitud" else (pm, lm)
        if dyn:                                            # régimen débil (solo EMA de 50 días): percentil más alto
            lim = lim.copy()
            lim[0.9] = lim[0.9].where(strong, lim[dyn])
        filt = {s: mix[s].copy() for s in E.COINS}
        for s in E.COINS:
            if agree is not None:
                filt[s] &= (p24[s] > agree).fillna(False)
            if confirm == "ema20":
                filt[s] &= P[s].c > P[s].ema20
            elif confirm == "btc24":
                filt[s] &= P["BTC"].r24h > 0
            elif confirm == "r1h":
                filt[s] &= P[s].r1h > 0
        if tp:
            barriers(P, None, tp)
        tr = trades(P, pred, lim, 0.9, filt=filt, hold=72, barrier=bool(tp))
        if bnb:
            tr = [(s, a, b, r + E.COST - COST_BNB) for s, a, b, r in tr]
        if size:                                           # media posición si la señal no llega al percentil 95
            tr = [(s, a, b, r * (1.0 if pred[s][a - H] > lim[0.95][a - H] else 0.5)) for s, a, b, r in tr]
        return locks(tr)

    rows = {}

    def show(key, name, **kw):
        tr = make(**kw)
        M.run(key, name, tr, idx)
        m = year26(M.SER[key])
        g = 100 * ((1 + m).prod() - 1)
        r = {"nombre": name, "kw": kw, "meses": (100 * m).round(2).tolist(), "pos": int((m > 0).sum()), "gan": g}
        if "base" in rows:
            b = np.array(rows["base"]["meses"])
            d = np.array(r["meses"]) - b
            r.update({"mejoran": int((d > 0.005).sum()), "empeoran": int((d < -0.005).sum())})
            r["C1"], r["C2"], r["C3"] = r["mejoran"] > r["empeoran"], r["pos"] > rows["base"]["pos"], g > rows["base"]["gan"]
            r["cumple"] = r["C1"] and r["C2"] and r["C3"]
        rows[key] = r
        print("2026 por mes (%): " + "  ".join(f"{MES[i]} {v:+.2f}" for i, v in enumerate(r["meses"]))
              + f"   -> positivos {r['pos']}/{len(m)}, año {g:+.2f} %", flush=True)
        if "cumple" in r:
            print(f"Frente a la base: mejoran {r['mejoran']} meses, empeoran {r['empeoran']} | C1 {'sí' if r['C1'] else 'no'}"
                  f"  C2 {'sí' if r['C2'] else 'no'}  C3 {'sí' if r['C3'] else 'no'}  ->  "
                  f"{'CUMPLE LAS TRES' if r['cumple'] else 'no cumple'}", flush=True)

    show("base", "Base: variante 4 (72 h, reentreno mensual, percentil 90, régimen mixto, mes -3 %)")
    show("7", "7. Comisión pagada con BNB (costo 0,19 %)", bnb=True)
    for k in (10, 12, 15):
        show(f"6_{k}", f"6. Objetivo de ganancia a {k} ATR", tp=k)
    show("5a", "5a. Confirmación: cierre de 1 h sobre su EMA 20", confirm="ema20")
    show("5b", "5b. Confirmación: BTC subió en las últimas 24 h", confirm="btc24")
    show("5c", "5c. Confirmación: la última hora cerró al alza", confirm="r1h")
    show("4", "4. Media posición si la señal no llega al percentil 95", size=True)
    show("3a", "3a. Régimen débil: exigir percentil 95", dyn=0.95)
    show("3b", "3b. Régimen débil: exigir percentil 98", dyn=0.98)
    show("2a", "2a. Acuerdo: el modelo de 24 h también predice subida", agree=0.0)
    show("2b", "2b. Acuerdo: el modelo de 24 h predice subida mayor que el costo", agree=E.COST)
    show("1", "1. Modelo con variables de amplitud de mercado", model="amplitud")

    # ---- todas las combinaciones (2^7 = 128) con una opción fija por sugerencia
    opts = {"model": ["base", "amplitud"], "agree": [None, 0.0], "dyn": [None, 0.95], "size": [False, True],
            "confirm": [None, "btc24"], "tp": [None, 12], "bnb": [False, True]}
    tag = {"model": "1", "agree": "2", "dyn": "3", "size": "4", "confirm": "5", "tp": "6", "bnb": "7"}
    b26, ser = rows["base"], {}
    out = []
    for vals in itertools.product(*opts.values()):
        kw = dict(zip(opts, vals))
        on = [tag[k] for k, v in kw.items() if not (v is None or v is False or v == "base")]
        if len(on) < 2:
            continue
        name = "+".join(sorted(on))
        m = M.full_months(E.monthly_from_trades(make(**kw)), idx)
        m26 = year26(m)
        d = (100 * m26).round(2).values - np.array(b26["meses"])
        yr = {y: round(100 * ((1 + m[[p.year == y for p in m.index]]).prod() - 1), 1) for y in M.YEARS}
        mt = m[[p.year in M.YEARS for p in m.index]]
        eq = (1 + mt).cumprod()
        r = {"combinación": name, **{str(y): v for y, v in yr.items()}, "pos_2026": int((m26 > 0).sum()),
             "gan_2026": round(100 * ((1 + m26).prod() - 1), 2), "mejoran": int((d > 0.005).sum()),
             "empeoran": int((d < -0.005).sum()), "pos_47": int((mt > 0).sum()),
             "caída_max": round(100 * (eq / eq.cummax() - 1).min(), 1)}
        r["cumple"] = r["mejoran"] > r["empeoran"] and r["pos_2026"] > b26["pos"] and r["gan_2026"] > b26["gan"]
        out.append(r)
        ser[name] = m
    df = pd.DataFrame(out).sort_values(["cumple", "pos_2026", "gan_2026"], ascending=False)
    print(f"\n### Combinaciones: {int(df.cumple.sum())} de {len(df)} cumplen las tres condiciones. Las 15 mejores:")
    print(df.head(15).to_string(index=False), flush=True)
    for name in df.head(8)["combinación"]:
        m26 = year26(ser[name])
        print(f"{name}: " + "  ".join(f"{MES[i]} {100 * v:+.2f}" for i, v in enumerate(m26.values)), flush=True)

    ind = pd.DataFrame([{"variante": k, "pos_2026": r["pos"], "gan_2026": round(r["gan"], 2),
                         "mejoran": r.get("mejoran"), "empeoran": r.get("empeoran"), "cumple": r.get("cumple")}
                        for k, r in rows.items()])
    print("\n### Individuales\n" + ind.to_string(index=False))
    M.summary("Resumen 2023-2026 de las individuales (ganancia % de la cuenta)")
    json.dump({"individuales": rows, "combinaciones": df.to_dict("records")},
              open(os.path.join(OUT, "meses3_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)
    pd.DataFrame({**M.SER, **{k: ser[k] for k in df.head(10)["combinación"]}}).to_csv(
        os.path.join(OUT, "meses3_mensual.csv"), float_format="%.5f")


if __name__ == "__main__":
    main()
