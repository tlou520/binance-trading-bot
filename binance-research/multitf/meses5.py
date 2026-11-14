"""Diez mejoras solo de trading sobre la combinación 2+3+6+7, y sus combinaciones.

Condiciones para aceptar (2026): C1 septiembre, octubre y noviembre mejores que los de la base; C2 año positivo.
(C3, al menos 6 meses positivos de 11, se muestra pero ya no es obligatoria.)

10  No entrar en fin de semana.
 9  No entrar cerca de noticias (FOMC y empleo de EE. UU.).
 8  Confirmación: BTC subió en las últimas 24 h.
 7  BTC a favor: el modelo también predice subida de BTC.
 6  Renovar la posición sin pagar costo si la señal sigue al vencer las 72 h.
 5  Entrada con orden límite en un retroceso de 0,5 ATR (hasta 6 h).
 4  Compras muy selectivas fuera de régimen (percentil 98).
 3  Salida anticipada cuando el modelo de 24 h se vuelve negativo.
 2  Umbral propio de cada moneda (percentil de sus últimos 90 días).
 1  Entrenar dando más peso a los datos recientes.

Uso: python meses5.py [--combos]
"""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

import estrategias as E
import meses as M
from mejoras import H, OUT, months, predict
from meses2 import MES, TAG, locks
from meses3 import COST_BNB, year26

M.END = None
NEWS = os.path.join(os.path.dirname(E.HERE), "pullback", "noticias.csv")


def exits(P, ktp=12.0, bad=None, n=72):
    """Resultado de cada posible entrada: objetivo a ktp ATR, salida si `bad` (modelo de 24 h negativo) al cierre
    de una hora, o a las n horas."""
    out = {}
    for s in E.COINS:
        h = P[s]
        ent, a = h.onext.values, h.atr.values
        tp = ent * (1 + ktp * a)
        st, ret, kx = np.zeros(len(h)), np.full(len(h), np.nan), np.full(len(h), n)
        for k in range(1, n + 1):
            y = (st == 0) & (h.h.shift(-k).values >= tp)
            ret[y], st[y], kx[y] = (ktp * a)[y], 1, k
            if bad is not None and k < n:
                z = (st == 0) & bad[s].shift(-k).eq(True).values
                ret[z], st[z], kx[z] = (h.o.shift(-k - 1).values / ent - 1)[z], 2, k
        yn = h[f"y{n}"].values
        ret[st == 0] = yn[st == 0]
        out[s] = (np.where(np.isnan(yn) | np.isnan(a) | np.isnan(ret), np.nan, ret), kx)
    return out


def build_trades(P, pred, limc, filt, ex):
    """Una operación a la vez por moneda; entra si la predicción supera su umbral y el costo."""
    out = []
    for s in E.COINS:
        sig = (pred[s].values > np.maximum(limc[s], E.COST)) & filt[s].values
        r, k = ex[s]
        T, free = P[s].index, 0
        for i in np.flatnonzero(sig):
            if i < free or np.isnan(r[i]):
                continue
            out.append((s, T[i] + H, T[i] + (k[i] + 1) * H, r[i] - COST_BNB))
            free = i + k[i]
    return sorted(out, key=lambda x: x[1])


def main(combos=False):
    P = M.build(M.COINS6)
    idx = P["BTC"].index
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    per = months(2022, 2026)
    pm, lm = M.cached("h72m" + TAG, lambda: predict(P, per, target="y72", gap=74))
    p24, l24 = M.cached("h24m" + TAG, lambda: predict(P, per, target="y24", gap=26))
    pw, lw = M.cached("h72mw12" + TAG, lambda: predict(P, per, target="y72", gap=74, halflife=12))
    pw6, lw6 = M.cached("h72mw6" + TAG, lambda: predict(P, per, target="y72", gap=74, halflife=6))
    b = P["BTC"]
    mix = M.regime(P, "mixto")
    strong = (b.btc_reg > 0).fillna(False)
    t_in = idx + H                                         # hora de entrada de cada fila de decisión
    wkday = pd.Series(t_in.dayofweek < 5, index=idx)
    ev = pd.to_datetime(pd.read_csv(NEWS).fecha_utc)
    news_ok = pd.Series(True, index=idx)
    for t in ev:
        news_ok[(t_in >= t - 24 * H) & (t_in <= t + 2 * H)] = False
    MODELS = {None: (pm, lm), 12: (pw, lw), 6: (pw6, lw6)}
    BAD = {"costo": {s: p24[s] < -E.COST for s in E.COINS}, "p10": {s: p24[s] < l24[0.1] for s in E.COINS}}
    EX = {None: exits(P), "costo": exits(P, bad=BAD["costo"]), "p10": exits(P, bad=BAD["p10"])}
    arr = {s: {c: P[s][c].values for c in ("o", "l", "atr")} for s in E.COINS}
    pos = {s: pd.Series(np.arange(len(idx)), index=idx) for s in E.COINS}

    def make(w=None, own=False, mexit=None, offreg=False, limit=None, renew=False, btcpred=None, btc24=False,
             news=False, weekend=False):
        pred, lim = MODELS[w]
        f0 = pd.Series(True, index=idx)
        if btcpred is not None:
            f0 &= (pred["BTC"] > btcpred).fillna(False)
        if btc24:
            f0 &= b.r24h > 0
        if news:
            f0 &= news_ok
        if weekend:
            f0 &= wkday
        filt, limc = {}, {}
        for s in E.COINS:
            filt[s] = mix[s] & (p24[s] > 0).fillna(False) & f0
            if own:                                        # percentil propio de la moneda en sus últimos 90 días
                r = pred[s].rolling(2160, min_periods=720)
                limc[s] = np.where(strong, r.quantile(0.9).shift(1), r.quantile(0.95).shift(1))
            else:
                limc[s] = np.where(strong, lim[0.9], lim[0.95])
        tr = build_trades(P, pred, limc, filt, EX[mexit])
        if offreg:
            fo = {s: ~mix[s] & (p24[s] > 0).fillna(False) & f0 for s in E.COINS}
            tr = sorted(tr + build_trades(P, pred, {s: lim[0.98].values for s in E.COINS}, fo, EX[mexit]),
                        key=lambda x: x[1])
        if limit:                                          # orden límite: llena solo si el precio retrocede
            out = []
            for s, a, c, r in tr:
                i = pos[s][a] - 1                          # fila de decisión
                o, lo, at = arr[s]["o"], arr[s]["l"], arr[s]["atr"]
                px = o[i + 1] * (1 - limit * at[i])
                kexit = int((c - a) / H)
                fill = next((k for k in range(1, 7) if i + k < len(o) and lo[i + k] <= px), None)
                if fill is None or fill > kexit:
                    continue
                gross = (1 + r + COST_BNB) * o[i + 1] / px - 1
                out.append((s, a + (fill - 1) * H, c, gross - COST_BNB))
            tr = out
        if renew:                                          # si al vencer las 72 h se vuelve a entrar, no se paga costo
            out, last = [], {}
            for s, a, c, r in tr:
                p = last.get(s)
                if p is not None and p[0] == a and p[1]:
                    r += COST_BNB
                out.append((s, a, c, r))
                last[s] = (c, (c - a) == 72 * H)
            tr = out
        tr = locks(tr)
        return tr, M.full_months(E.monthly_from_trades(tr), idx)

    base = {}

    def check(m):
        m26 = (100 * year26(m)).round(2)
        g = 100 * ((1 + year26(m)).prod() - 1)
        r = {"meses": m26.tolist(), "pos": int((m26 > 0).sum()), "gan": round(g, 2)}
        if base:
            r["C1"] = all(m26.iloc[i] > base["meses"][i] for i in (8, 9, 10))
            r["C2"], r["C3"] = g > 0, r["pos"] >= 6
            r["cumple"] = r["C1"] and r["C2"]
        return r

    rows = {}

    def show(key, name, **kw):
        tr, m = make(**kw)
        M.run(key, name, tr, idx, m)
        r = check(m)
        if not base:
            base.update(r)
            d = pd.DataFrame(tr, columns=["moneda", "entrada", "salida", "neta_%"])
            d = d[d.salida >= "2026-09-01"]
            d["neta_%"] = (100 * d["neta_%"]).round(2)
            print("Operaciones de la base desde septiembre de 2026:\n" + d.to_string(index=False), flush=True)
        rows[key] = {"nombre": name, **r}
        print("2026 por mes (%): " + "  ".join(f"{MES[i]} {v:+.2f}" for i, v in enumerate(r["meses"]))
              + f"   -> positivos {r['pos']}/11, año {r['gan']:+.2f} %", flush=True)
        if "cumple" in r:
            print("  ".join(f"{c} {'sí' if r[c] else 'no'}" for c in ("C1", "C2", "C3"))
                  + f"  ->  {'CUMPLE C1 y C2' if r['cumple'] else 'no cumple'}", flush=True)

    show("base", "Base: combinación 2+3+6+7")
    show("10", "10. No entrar en fin de semana", weekend=True)
    show("9", "9. No entrar desde 24 h antes hasta 2 h después de FOMC o empleo de EE. UU.", news=True)
    show("8", "8. Confirmación: BTC subió en las últimas 24 h", btc24=True)
    show("7", "7. BTC a favor: el modelo predice subida de BTC", btcpred=0.0)
    show("7b", "7b. BTC a favor: el modelo predice subida de BTC mayor que el costo", btcpred=E.COST)
    show("6", "6. Renovar la posición sin costo si la señal sigue a las 72 h", renew=True)
    show("5", "5. Entrada con orden límite 0,5 ATR por debajo (hasta 6 h)", limit=0.5)
    show("5b", "5b. Entrada con orden límite 0,25 ATR por debajo", limit=0.25)
    show("4", "4. Compras fuera de régimen solo sobre el percentil 98", offreg=True)
    show("3", "3. Salir si el modelo de 24 h predice una caída mayor que el costo", mexit="costo")
    show("3b", "3b. Salir si el modelo de 24 h cae a su 10 % más bajo", mexit="p10")
    show("2", "2. Umbral propio de cada moneda (sus últimos 90 días)", own=True)
    show("1", "1. Entrenar con más peso a lo reciente (vida media 12 meses)", w=12)
    show("1b", "1b. Entrenar con más peso a lo reciente (vida media 6 meses)", w=6)

    ind = pd.DataFrame([{"variante": k, "pos_2026": r["pos"], "gan_2026": r["gan"], "sep": r["meses"][8],
                         "oct": r["meses"][9], "nov": r["meses"][10], **{c: r.get(c) for c in ("C1", "C2", "C3", "cumple")}}
                        for k, r in rows.items()])
    print("\n### Individuales\n" + ind.to_string(index=False))
    M.summary("Resumen 2023-2026 de las individuales (ganancia % de la cuenta)")
    res = {"individuales": rows}

    if combos:
        # las sugerencias 1, 2, 3 y 7 empeoran los tres meses por separado: no entran en las combinaciones
        opts = {"offreg": [False, True], "limit": [None, 0.25, 0.5], "renew": [False, True], "btc24": [False, True],
                "news": [False, True], "weekend": [False, True]}
        tag = {"offreg": "4", "limit": "5", "renew": "6", "btc24": "8", "news": "9", "weekend": "10"}
        out, ser = [], {}
        for vals in itertools.product(*opts.values()):
            kw = dict(zip(opts, vals))
            on = [tag[k] + ("b" if v == 0.25 else "") for k, v in kw.items() if v != opts[k][0]]
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
                        "nov": r["meses"][10], "C1": r["C1"], "C3": r["C3"], "cumple": r["cumple"],
                        "pos_47": int((mt > 0).sum()), "caída_max": round(100 * (eq / eq.cummax() - 1).min(), 1)})
            ser[name] = m
        df = pd.DataFrame(out).sort_values(["cumple", "gan_2026"], ascending=False)
        print(f"\n### Combinaciones: {int(df.cumple.sum())} de {len(df)} cumplen C1 y C2. Las 30 mejores por ganancia de 2026:")
        print(df.head(30).to_string(index=False), flush=True)
        for name in df.head(30)["combinación"]:
            print(f"{name}: " + "  ".join(f"{MES[i]} {100 * v:+.2f}" for i, v in enumerate(year26(ser[name]).values)),
                  flush=True)
        res["combinaciones"] = df.to_dict("records")
        pd.DataFrame({**M.SER, **{k: ser[k] for k in df.head(30)["combinación"]}}).to_csv(
            os.path.join(OUT, "meses5_mensual.csv"), float_format="%.5f")
    json.dump(res, open(os.path.join(OUT, "meses5_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main("--combos" in sys.argv)
