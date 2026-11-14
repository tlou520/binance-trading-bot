"""Ajustes a la combinación 4+5b+6+9 para quitarle sus tres costos, y todas sus combinaciones.

Referencia para las condiciones: la combinación 2+3+6+7 (la "base").
  C1  septiembre, octubre y noviembre de 2026 mejores que los de la base
  C2  2026 positivo
  C3  febrero de 2026 no negativo
  C4  2024 no gana menos que la base
  C5  la caída máxima (2023-2026) no es peor que la de la base   <- la más importante

7  Quitar las compras fuera de régimen.
6  Fuera de régimen solo si BTC subió en los últimos 7 días.
5  Fuera de régimen solo si BTC subió en las últimas 24 h.
4  Fuera de régimen solo si el modelo de 24 h predice subida mayor que el costo.
3  Fuera de régimen con media posición.
2  Fuera de régimen: tras una pérdida, no volver a comprar fuera de régimen ese mes.
1  Orden límite con entrada a mercado si no se llena en 6 h (no se pierde la operación).

Uso: python meses6.py
"""
import itertools
import json
import os

import numpy as np
import pandas as pd

import estrategias as E
import meses as M
from mejoras import H, OUT, months, predict
from meses2 import MES, TAG, locks
from meses3 import COST_BNB, year26
from meses5 import NEWS, build_trades, exits

M.END = None
OFF = {"no": "sin compras fuera de régimen", "sí": "fuera de régimen (percentil 98)", "btc7": "fuera de régimen si BTC subió en 7 días",
       "btc24": "fuera de régimen si BTC subió en 24 h", "m24": "fuera de régimen si el modelo de 24 h supera el costo",
       "media": "fuera de régimen con media posición", "tope": "fuera de régimen, una sola pérdida por mes"}
LIM = {None: "entrada a mercado", "lim": "orden límite 0,25 ATR", "lim+": "orden límite 0,25 ATR, o a mercado a las 6 h"}


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
    t_in = idx + H
    news_ok = pd.Series(True, index=idx)
    for t in pd.to_datetime(pd.read_csv(NEWS).fecha_utc):
        news_ok[(t_in >= t - 24 * H) & (t_in <= t + 2 * H)] = False
    EX = exits(P)
    arr = {s: {c: P[s][c].values for c in ("o", "l", "atr")} for s in E.COINS}
    pos = pd.Series(np.arange(len(idx)), index=idx)
    limc = {s: np.where(strong, lm[0.9], lm[0.95]) for s in E.COINS}
    lim98 = {s: lm[0.98].values for s in E.COINS}

    def make(off="no", limit=None, renew=False, news=False):
        f0 = news_ok if news else pd.Series(True, index=idx)
        ok24 = {s: (p24[s] > 0).fillna(False) for s in E.COINS}
        tr = [t + (False,) for t in build_trades(P, pm, limc, {s: mix[s] & ok24[s] & f0 for s in E.COINS}, EX)]
        if off != "no":
            extra = {"btc7": b.r7d > 0, "btc24": b.r24h > 0}.get(off, pd.Series(True, index=idx))
            fo = {s: ~mix[s] & f0 & extra & ((p24[s] > E.COST).fillna(False) if off == "m24" else ok24[s])
                  for s in E.COINS}
            tr = sorted(tr + [t + (True,) for t in build_trades(P, pm, lim98, fo, EX)], key=lambda x: x[1])
        if limit:
            out = []
            for s, a, c, r, o_ in tr:
                i = pos[a] - 1
                o, lo, at = arr[s]["o"], arr[s]["l"], arr[s]["atr"]
                px, kexit = o[i + 1] * (1 - 0.25 * at[i]), int((c - a) / H)
                fill = next((k for k in range(1, 7) if i + k < len(o) and lo[i + k] <= px), None)
                if fill is None and limit == "lim+" and kexit >= 7 and i + 7 < len(o):
                    fill, px = 7, o[i + 7]                 # no se llenó: compra a mercado al abrir la hora 7
                if fill is None or fill > kexit:
                    continue
                out.append((s, a + (fill - 1) * H, c, (1 + r + COST_BNB) * o[i + 1] / px - 1 - COST_BNB, o_))
            tr = out
        if renew:
            out, last = [], {}
            for s, a, c, r, o_ in tr:
                p = last.get(s)
                if p is not None and p[0] == a and p[1]:
                    r += COST_BNB
                out.append((s, a, c, r, o_))
                last[s] = (c, (c - a) == 72 * H)
            tr = out
        if off == "media":
            tr = [(s, a, c, r * (0.5 if o_ else 1.0), o_) for s, a, c, r, o_ in tr]
        if off == "tope":
            out = []
            for t in tr:
                m = t[1].to_period("M")
                if t[4] and any(x[4] and x[3] < 0 and x[2] <= t[1] and x[2].to_period("M") == m for x in out):
                    continue
                out.append(t)
            tr = out
        tr = locks([t[:4] for t in tr])
        return tr, M.full_months(E.monthly_from_trades(tr), idx)

    def measure(m):
        m26 = (100 * year26(m)).round(2)
        mt = m[[p.year in M.YEARS for p in m.index]]
        eq = (1 + mt).cumprod()
        r = {"meses": m26.tolist(), "pos": int((m26 > 0).sum()), "gan": round(100 * ((1 + year26(m)).prod() - 1), 2),
             "dd": round(100 * (eq / eq.cummax() - 1).min(), 2), "pos47": int((mt > 0).sum())}
        for y in M.YEARS[:3]:
            r[str(y)] = round(100 * ((1 + m[[p.year == y for p in m.index]]).prod() - 1), 1)
        return r

    base = measure(make()[1])

    def check(r):
        r["C1"] = all(r["meses"][i] > base["meses"][i] for i in (8, 9, 10))
        r["C2"], r["C3"] = r["gan"] > 0, r["meses"][1] >= 0
        r["C4"], r["C5"] = r["2024"] >= base["2024"], r["dd"] >= base["dd"] - 0.005
        r["cumple"] = all(r[c] for c in ("C1", "C2", "C3", "C4", "C5"))
        return r

    rows = {}

    def show(key, name, **kw):
        tr, m = make(**kw)
        M.run(key, name, tr, idx, m)
        r = measure(m) if key == "base" else check(measure(m))
        rows[key] = {"nombre": name, **r}
        print("2026 por mes (%): " + "  ".join(f"{MES[i]} {v:+.2f}" for i, v in enumerate(r["meses"]))
              + f"   -> positivos {r['pos']}/11, año {r['gan']:+.2f} %, 2024 {r['2024']:+.1f} %, caída máx. {r['dd']:.2f} %",
              flush=True)
        if "cumple" in r:
            print("  ".join(f"{c} {'sí' if r[c] else 'no'}" for c in ("C1", "C2", "C3", "C4", "C5"))
                  + f"  ->  {'CUMPLE TODO' if r['cumple'] else 'no cumple'}", flush=True)

    ref = dict(off="sí", limit="lim", renew=True, news=True)
    show("base", "Base de las condiciones: 2+3+6+7")
    show("ref", "Punto de partida: 4+5b+6+9", **ref)
    show("7", "7. Quitar las compras fuera de régimen", **{**ref, "off": "no"})
    show("6", "6. Fuera de régimen solo si BTC subió en 7 días", **{**ref, "off": "btc7"})
    show("5", "5. Fuera de régimen solo si BTC subió en 24 h", **{**ref, "off": "btc24"})
    show("4", "4. Fuera de régimen solo si el modelo de 24 h supera el costo", **{**ref, "off": "m24"})
    show("3", "3. Fuera de régimen con media posición", **{**ref, "off": "media"})
    show("2", "2. Fuera de régimen: una sola pérdida por mes", **{**ref, "off": "tope"})
    show("1", "1. Orden límite, o a mercado si no se llena en 6 h", **{**ref, "limit": "lim+"})

    out, ser = [], {}
    for off, limit, renew, news in itertools.product(OFF, LIM, (False, True), (False, True)):
        if (off, limit, renew, news) == ("no", None, False, False):
            continue
        name = "; ".join([OFF[off], LIM[limit]] + (["renovar sin costo"] if renew else [])
                         + (["sin noticias"] if news else []))
        _, m = make(off, limit, renew, news)
        r = check(measure(m))
        out.append({"id": len(out) + 1, "combinación": name, "2023": r["2023"], "2024": r["2024"], "2025": r["2025"],
                    "gan_2026": r["gan"], "pos_2026": r["pos"], "feb": r["meses"][1], "sep": r["meses"][8],
                    "oct": r["meses"][9], "nov": r["meses"][10], "caída_max": r["dd"], "pos_47": r["pos47"],
                    **{c: r[c] for c in ("C1", "C2", "C3", "C4", "C5", "cumple")}})
        ser[out[-1]["id"]] = (name, m)
    df = pd.DataFrame(out).sort_values(["cumple", "nov", "gan_2026"], ascending=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 95)
    print(f"\n### Combinaciones: {int(df.cumple.sum())} de {len(df)} cumplen las cinco condiciones.")
    print(df[df.cumple].drop(columns=["C1", "C2", "C3", "C4", "C5", "cumple"]).to_string(index=False), flush=True)
    print("\nLas 10 mejores que no cumplen (qué condición falla):")
    print(df[~df.cumple].sort_values("gan_2026", ascending=False).head(10).drop(columns=["cumple"]).to_string(index=False))
    for i in df[df.cumple]["id"]:
        print(f"[{i}] " + "  ".join(f"{MES[k]} {100 * v:+.2f}" for k, v in enumerate(year26(ser[i][1]).values)), flush=True)
    json.dump({"base": base, "individuales": rows, "combinaciones": df.to_dict("records")},
              open(os.path.join(OUT, "meses6_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)
    keep = {**M.SER, **{f"[{i}] {ser[i][0]}": ser[i][1] for i in df[df.cumple]["id"]}}
    pd.DataFrame(keep).to_csv(os.path.join(OUT, "meses6_mensual.csv"), float_format="%.5f")


if __name__ == "__main__":
    main()
