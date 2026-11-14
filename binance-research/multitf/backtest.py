"""Backtest de E1, E2 y E3 por separado y combinadas. Uso: python backtest.py"""
import json
import os

import numpy as np
import pandas as pd

import estrategias as E

OUT = os.path.join(E.HERE, "output")
YEARS_ML = [2024, 2025, 2026]


def table(name, trades, monthly, years):
    """Filas por año: operaciones, acierto, ganancia media neta, ganancia del año y meses en positivo."""
    rows = []
    tr = pd.DataFrame(trades, columns=["coin", "t0", "t1", "ret"]) if trades else pd.DataFrame(
        columns=["coin", "t0", "t1", "ret"])
    for y in list(years) + ["Total"]:
        t = tr if y == "Total" else tr[pd.DatetimeIndex(tr.t1).year == y]
        m = monthly[[p.year in years for p in monthly.index]] if y == "Total" else monthly[
            [p.year == y for p in monthly.index]]
        rows.append({"año": y, "operaciones": len(t), "acierto_%": round(100 * (t.ret > 0).mean(), 1) if len(t) else None,
                     "media_neta_%": round(100 * t.ret.mean(), 3) if len(t) else None,
                     "ganancia_%": round(100 * ((1 + m).prod() - 1), 2),
                     "meses_positivos": f"{int((m > 0).sum())}/{len(m)}"})
    df = pd.DataFrame(rows)
    print(f"\n### {name}\n" + df.to_string(index=False))
    return df.to_dict("records")


def full_months(monthly, idx):
    """Rellena con 0 los meses sin operaciones, para contar bien los meses positivos."""
    allm = pd.period_range(idx[0], idx[-1], freq="M")
    return monthly.reindex(allm).fillna(0.0)


def main():
    os.makedirs(OUT, exist_ok=True)
    P = E.prepare({s: E.load(s) for s in E.COINS})
    idx = P["BTC"].index
    print(f"Datos: {idx[0]} a {idx[-1]} UTC, {len(idx)} horas, {len(E.COINS)} monedas")
    res = {"datos": [str(idx[0]), str(idx[-1])]}
    ALL = [2023, 2024, 2025, 2026]

    # ---- E1
    pred, thr = E.ml_predict(P, YEARS_ML)
    t1 = E.strat1(P, pred, thr)
    m1 = full_months(E.monthly_from_trades(t1), idx)
    res["E1"] = table("E1 Aprendizaje automático (24 h, percentil 95)", t1, m1, YEARS_ML)
    ic = {}
    for y in YEARS_ML:
        a = pd.concat([pd.DataFrame({"p": pred[s], "y": P[s].y24}) for s in E.COINS]).dropna()
        a = a[a.index.year == y]
        ic[y] = round(float(np.corrcoef(a.p, a.y)[0, 1]), 4)
    res["E1_correlacion_prediccion_real"] = ic
    # referencia: comprar a cualquier hora y mantener 24 h, con el mismo costo
    azar = {y: round(100 * float(np.mean([(P[s].y24[P[s].index.year == y] - E.COST).mean() for s in E.COINS])), 3)
            for y in YEARS_ML}
    res["E1_entrada_a_cualquier_hora_%"] = azar
    print("Media neta de entrar a cualquier hora (24 h):", azar)
    res["E1_umbrales"] = {y: {str(k): round(v, 5) for k, v in d.items()} for y, d in thr.items()}
    print("Correlación predicción / resultado real por año:", ic)
    res["E1_sensibilidad"] = {}
    for q in (0.5, 0.9, 0.95, 0.98):
        t = E.strat1(P, pred, thr, q)
        r = np.array([x[3] for x in t])
        res["E1_sensibilidad"][q] = {"n": len(t), "media_%": float(round(100 * r.mean(), 3)) if len(t) else None}
    print("Sensibilidad E1 (percentil: n, media neta):", res["E1_sensibilidad"])

    # ---- E2
    t2, w2 = E.strat2(P)
    m2 = full_months(E.monthly_from_weekly(w2), idx)
    res["E2"] = table("E2 Fuerza relativa semanal (28 días, 2 monedas, BTC sobre media de 200 días)", t2, m2, ALL)
    res["E2_sensibilidad"] = {}
    for L in (14, 28, 56):
        for k in (1, 2, 3):
            _, w = E.strat2(P, L, k)
            mm = E.monthly_from_weekly(w)
            res["E2_sensibilidad"][f"L{L}_k{k}"] = {
                str(y): round(100 * ((1 + mm[[p.year == y for p in mm.index]]).prod() - 1), 1) for y in ALL}
    print("Sensibilidad E2 (ganancia % por año):")
    print(pd.DataFrame(res["E2_sensibilidad"]).T.to_string())

    # ---- E3
    t3 = E.strat3(P)
    m3 = full_months(E.monthly_from_trades(t3), idx)
    res["E3"] = table("E3 Tendencia en cascada (día, hora; objetivo 3R, máximo 7 días)", t3, m3, ALL)
    res["E3_sensibilidad"] = {}
    for rr in (2.0, 3.0, 4.0):
        for hold in (72, 168, 336):
            t = E.strat3(P, rr, hold)
            r = pd.Series([x[3] for x in t], index=pd.DatetimeIndex([x[2] for x in t]))
            res["E3_sensibilidad"][f"rr{rr:g}_h{hold}"] = {"n": len(t), "media_%": round(100 * r.mean(), 3), **{
                str(y): round(100 * r[r.index.year == y].mean(), 3) for y in ALL}}
    print("Sensibilidad E3 (media neta % por operación):")
    print(pd.DataFrame(res["E3_sensibilidad"]).T.to_string())

    # ---- Combinadas
    # Integrada: señal de E3, solo si la moneda está entre las 2 más fuertes a 28 días con BTC en régimen
    # alcista (E2) y el modelo predice ganancia positiva a 24 h (E1).
    filt = {s: ((P[s].rk28 <= 2) & (P[s].mom28 > 0) & (P[s].btc_reg > 0) & (pred[s] > 0)).fillna(False)
            for s in E.COINS}
    tc = E.strat3(P, filt=filt)
    mc = full_months(E.monthly_from_trades(tc), idx)
    res["integrada"] = table("Integrada: E3 filtrada por E2 y E1", tc, mc, YEARS_ML)
    f23 = {s: ((P[s].rk28 <= 2) & (P[s].mom28 > 0) & (P[s].btc_reg > 0)).fillna(False) for s in E.COINS}
    t23 = E.strat3(P, filt=f23)
    m23 = full_months(E.monthly_from_trades(t23), idx)
    res["E3_con_E2"] = table("E3 filtrada solo por E2 (sin modelo)", t23, m23, ALL)
    mp = (m1 + m2 + m3) / 3                                # cartera: un tercio del capital en cada una
    res["cartera"] = table("Cartera: un tercio en cada estrategia", [], mp, YEARS_ML)

    hold = {}
    for s in ("BTC",):
        c = P[s].c
        hold[s] = full_months((c.groupby(c.index.to_period("M")).last().pct_change()).dropna(), idx)
    eq = pd.DataFrame({s: P[s].c.groupby(P[s].index.to_period("M")).last().pct_change() for s in E.COINS}).mean(axis=1)
    series = {"E1": m1, "E2": m2, "E3": m3, "Integrada": mc, "E3+E2": m23, "Cartera 1/3": mp,
              "Comprar y mantener BTC": hold["BTC"], "Comprar y mantener las 6": full_months(eq.dropna(), idx)}
    rows = []
    for k, m in series.items():
        r = {"estrategia": k}
        for y in YEARS_ML:
            my = m[[p.year == y for p in m.index]]
            r[str(y)] = round(100 * ((1 + my).prod() - 1), 2)
        mt = m[[p.year in YEARS_ML for p in m.index]]
        eqv = (1 + mt).cumprod()
        r["total_%"] = round(100 * (eqv.iloc[-1] - 1), 2)
        r["meses_positivos"] = f"{int((mt > 0).sum())}/{len(mt)}"
        r["peor_mes_%"] = round(100 * mt.min(), 2)
        r["caida_max_%"] = round(100 * (eqv / eqv.cummax() - 1).min(), 2)
        rows.append(r)
    df = pd.DataFrame(rows)
    print("\n### Resumen 2024-2026 (ganancia % de la cuenta)\n" + df.to_string(index=False))
    res["resumen"] = df.to_dict("records")

    pd.DataFrame(series).to_csv(os.path.join(OUT, "mensual.csv"), float_format="%.5f")
    for name, t in (("E1", t1), ("E2", t2), ("E3", t3), ("integrada", tc)):
        pd.DataFrame(t, columns=["moneda", "entrada", "salida", "ganancia_neta"]).to_csv(
            os.path.join(OUT, f"operaciones_{name}.csv"), index=False, float_format="%.6f")
    with open(os.path.join(OUT, "resumen.json"), "w") as f:
        json.dump(res, f, indent=1, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main()
