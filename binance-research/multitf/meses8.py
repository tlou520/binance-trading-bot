"""Doce mejoras sobre la versión final (5c de meses7) para subir septiembre, octubre y noviembre de 2026 sin
empeorar nada de lo que ya tiene, y sus combinaciones.

Condiciones (todas contra la versión final):
  K1-K4  2023, 2024, 2025 y 2026 no ganan menos
  K5     la caída máxima (2023-2026) no es peor
  K6     los meses positivos de 47 no bajan
  K7     los meses positivos de 2026 no bajan de 7
  K8     febrero de 2026 no es negativo
  K9     ni septiembre, ni octubre, ni noviembre de 2026 empeoran
  META   la suma de septiembre, octubre y noviembre sube

12  Acuerdo con un modelo que ve la amplitud del mercado.
11  Acuerdo con un modelo entrenado con más peso a lo reciente.
10  Umbral adaptable: si las últimas N operaciones pierden, exigir percentil 95.
 9  Tamaño según volatilidad: menos tamaño cuando el ATR está sobre su mediana de 30 días.
 8  Stop de catástrofe a k ATR bajo la entrada.
 7  Salir cuando el régimen se apaga.
 6  Confirmación de BTC a corto plazo.
 5  Tendencia propia de la moneda.
 4  Percentil 95 cuando BTC cae en los últimos 7 días.
 3  Stop mensual más corto o stop semanal.
 2  Tope de posiciones cuando BTC cae en los últimos 7 días.
 1  No entrar en fin de semana.

Uso: python meses8.py [--combos]
"""
import itertools
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

import estrategias as E
import meses as M
import meses7 as S
from mejoras import H, OUT, months, predict
from meses2 import MES, TAG
from meses3 import COST_BNB

M.END = None
NS_H = S.NS_H
G = S.G
OPTS = {"mdl": [None, "mb", "w12"], "adapt": [None, 6, 10], "vs": [None, "v"], "sl": [None, 6, 8], "rx": [None, "rx", "smastrloss"],
        "bt": [None, "r24", "r7", "e50"], "ct": [None, "r7", "rank", "dema"], "st": [None, "p95"],
        "lock": [None, "m2", "w15"], "cap7": [None, 3, 4], "wk": [None, "wk"]}
BASE = {k: None for k in OPTS}
NUM = {"mdl": "12", "adapt": "10", "vs": "9", "sl": "8", "rx": "7", "bt": "6", "ct": "5", "st": "4", "lock": "3",
       "cap7": "2", "wk": "1"}
NAMES = {("mdl", "mb"): "12. Acuerdo con el modelo de amplitud de mercado",
         ("mdl", "w12"): "11. Acuerdo con el modelo de peso reciente",
         ("adapt", 6): "10a. Percentil 95 si las últimas 6 operaciones pierden en promedio",
         ("adapt", 10): "10b. Percentil 95 si las últimas 10 operaciones pierden en promedio",
         ("vs", "v"): "9. Menos tamaño cuando el ATR está sobre su mediana de 30 días",
         ("sl", 6): "8a. Stop de catástrofe a 6 ATR", ("sl", 8): "8b. Stop de catástrofe a 8 ATR",
         ("rx", "rx"): "7. Salir cuando el régimen se apaga",
         ("bt", "r24"): "6a. Régimen fuerte: BTC subió en 24 h", ("bt", "r7"): "6b. Régimen fuerte: BTC subió en 7 días",
         ("bt", "e50"): "6c. Régimen fuerte: BTC sobre su EMA de 50 horas",
         ("ct", "r7"): "5a. La moneda subió en 7 días", ("ct", "rank"): "5b. La moneda está en la mitad más fuerte (7 días)",
         ("ct", "dema"): "5c. La moneda está sobre su EMA de 50 días",
         ("st", "p95"): "4. Percentil 95 cuando BTC cae en 7 días",
         ("lock", "m2"): "3a. Parar el mes al perder 2 %", ("lock", "w15"): "3b. Parar la semana al perder 1,5 %",
         ("cap7", 3): "2a. Máximo 3 posiciones si BTC cae en 7 días", ("cap7", 4): "2b. Máximo 4 posiciones si BTC cae en 7 días",
         ("wk", "wk"): "1. No entrar en fin de semana"}


def code(k, v):
    if k == "mdl":
        return "12" if v == "mb" else "11"
    if k == "rx":
        return "7" if v == "rx" else "7e"
    return NUM[k] + ("" if len(OPTS[k]) == 2 else chr(ord("a") + OPTS[k].index(v) - 1))


def exits(P, ktp=12.0, n=72, sl=None, bad=None, losing=False):
    """Objetivo a ktp ATR o salida a las n horas. `sl`: stop a sl ATR bajo la entrada (si una hora toca stop y
    objetivo, cuenta el stop). `bad`: salir en la apertura siguiente a una hora cerrada con bad verdadero."""
    out = {}
    for s in E.COINS:
        h = P[s]
        ent, a = h.onext.values, h.atr.values
        tp = ent * (1 + ktp * a)
        stop = ent * (1 - sl * a) if sl else None
        st, ret, kx = np.zeros(len(h)), np.full(len(h), np.nan), np.full(len(h), n)
        for k in range(1, n + 1):
            hi, lo, op = (h[c].shift(-k).values for c in ("h", "l", "o"))
            if sl:
                z = (st == 0) & (lo <= stop)
                ret[z], st[z], kx[z] = (np.minimum(stop, op) / ent - 1)[z], 2, k
            y = (st == 0) & (hi >= tp)
            ret[y], st[y], kx[y] = (ktp * a)[y], 1, k
            if bad is not None and k < n:
                z = (st == 0) & bad[s].shift(-k).eq(True).values
                if losing:                                 # solo si la posición va perdiendo al cierre de esa hora
                    z &= h.c.shift(-k).values < ent
                ret[z], st[z], kx[z] = (h.o.shift(-k - 1).values / ent - 1)[z], 3, k
        yn = h.onext.shift(-n).values / ent - 1
        ret[st == 0] = yn[st == 0]
        out[s] = (np.where(np.isnan(yn) | np.isnan(a) | np.isnan(ret), np.nan, ret), kx, n)
    return out


def candidates(P, pred, lim, lim95, filt, ex, kind, size):
    """Una a la vez por moneda: (moneda, entrada, salida, neta, tipo, tamaño, exceso, venció, exceso sobre p95)."""
    out = []
    for j, s in enumerate(E.COINS):
        pv = pred[s].values
        sig = (pv > np.maximum(lim[s], E.COST)) & filt[s].values
        r, k, n = ex[s]
        T, free = P[s].index.as_unit("ns").asi8, 0
        for i in np.flatnonzero(sig):
            if i < free or np.isnan(r[i]):
                continue
            out.append((j, T[i] + NS_H, T[i] + (k[i] + 1) * NS_H, r[i] - COST_BNB, kind[s][i], size[s][i],
                        pv[i] - lim[s][i], k[i] == n, pv[i] - lim95[i]))
            free = i + k[i]
    return out


def portfolio(cands, caps, adapt=None, msl=0.03, wsl=None):
    """Controles de cuenta. caps: {tipo: máximo de posiciones abiertas al entrar con ese tipo}."""
    cands = sorted(cands, key=lambda x: (x[1], -x[6]))
    t_in = np.array([c[1] for c in cands]).astype("datetime64[ns]")
    month = t_in.astype("datetime64[M]").astype(int)
    week = ((t_in.astype("datetime64[D]").astype(int) + 3) // 7)     # semanas de lunes a domingo
    acc, A, C, R, Mx, Wx = [], [], [], [], [], []
    last = {}
    for t, m, w in zip(cands, month, week):
        j, a, c, r, kind, sz, _, tmo, e95 = t
        if A:
            a_, c_, r_, m_, w_ = (np.array(x) for x in (A, C, R, Mx, Wx))
            done = c_ <= a
            cap = caps.get(kind)
            if cap is not None and (~done).sum() >= cap:
                continue
            dm = done & (m_ == m)
            if dm.any() and r_[dm].sum() <= -msl:
                continue
            if wsl is not None and r_[done & (w_ == w)].sum() <= -wsl:
                continue
            if adapt and done.sum() >= adapt and e95 <= 0:
                od = np.argsort(c_[done], kind="stable")[-adapt:]
                if r_[done][od].mean() < 0:
                    continue
        p = last.get(j)
        if p is not None and p[0] == a and p[1]:
            r += COST_BNB
        last[j] = (c, tmo)
        acc.append((j, a, c, r, kind, sz))
        d = np.datetime64(int(c), "ns")
        A.append(a), C.append(c), R.append(r * sz / E.SLOTS)
        Mx.append(int(d.astype("datetime64[M]").astype(int))), Wx.append((int(d.astype("datetime64[D]").astype(int)) + 3) // 7)
    return acc


def setup():
    S.setup()
    P, idx = G["P"], G["idx"]
    per = months(2022, 2026)
    G["mb"], _ = M.cached("h72mb" + TAG, lambda: 1 / 0)
    G["w12"], _ = M.cached("h72mw12" + TAG, lambda: predict(P, per, target="y72", gap=74, halflife=12))
    G["wkday"] = pd.Series((idx + H).dayofweek < 5, index=idx)
    G["med7"] = pd.DataFrame({s: P[s].r7d for s in E.COINS}).median(axis=1)
    G["EX8"], G["C8"] = {}, {}


def cands_for(mdl, vs, sl, rx, bt, ct, st, wk):
    key = (mdl, vs, sl, rx, bt, ct, st, wk)
    if key in G["C8"]:
        return G["C8"][key]
    P, idx, pm, lm, p24, b = (G[k] for k in ("P", "idx", "pm", "lm", "p24", "b"))
    mix, strong, news_ok = G["mix"], G["strong"], G["news_ok"]

    def ex(sl, bad, losing=False):
        k = (sl, bad is not None, losing)
        if k not in G["EX8"]:
            G["EX8"][k] = exits(P, 12.0, 72, sl, bad, losing)
        return G["EX8"][k]
    X_off = ex(sl, None)
    if rx and "sma" in rx:                                # salir cuando BTC pierde su media de 200 días
        if ("sma", sl) not in G["EX8"]:
            G["EX8"][("sma", sl)] = exits(P, 12.0, 72, sl, {s: ~strong for s in E.COINS}, True)
        X_in = G["EX8"][("sma", sl)]
    else:
        X_in = ex(sl, {s: ~mix[s] for s in E.COINS}, "loss" in rx) if rx else X_off
    if rx and "str" in rx:                                # solo para compras hechas en régimen fuerte
        X_in = {s: (np.where(strong, X_in[s][0], X_off[s][0]), np.where(strong, X_in[s][1], X_off[s][1]), 72)
                for s in E.COINS}
    up24, dn7 = b.r24h > 0, (b.r7d < 0).fillna(False)
    lim_in, lim98, f_in, f_off, size, kind, k_off = {}, {}, {}, {}, {}, {}, {}
    for s in E.COINS:
        h = P[s]
        ok24 = (p24[s] > 0).fillna(False)
        wk_ = mix[s] & ~strong
        base_lim = np.where(strong, lm[0.9], lm[0.95])
        lim_in[s] = np.where(strong & dn7, lm[0.95], base_lim) if st else base_lim
        lim98[s] = lm[0.98].values
        f = news_ok.copy()
        if mdl in ("mb", "w12"):
            f &= (G[mdl][s] > E.COST).fillna(False)
        elif mdl:                                          # variantes del acuerdo con el modelo de amplitud
            okb = (G["mb"][s] > (0 if mdl == "mb0" else E.COST)).fillna(False)
            f &= okb | {"mb0": False, "mbd": ~dn7, "mbs": ~strong, "mbw": strong}[mdl]
        if wk == "wk":
            f &= G["wkday"]
        elif wk == "wkd":                                  # sin fin de semana solo si BTC cae en 7 días
            f &= G["wkday"] | ~dn7
        if ct:
            f &= {"r7": h.r7d > 0, "rank": h.r7d >= G["med7"], "dema": h.dc > h.dema50}[ct].fillna(False)
        fi = mix[s] & ok24 & f
        if bt:
            fi &= ~strong | {"r24": up24, "r7": b.r7d > 0, "e50": b.d_ema50 > 0}[bt].fillna(False)
        f_in[s], f_off[s] = fi, ~mix[s] & up24 & ok24 & f
        if vs:
            ratio = h.atr / h.atr.rolling(720).median()
            size[s] = (1 / ratio).clip(0.5, 1.0).fillna(1.0).values
        else:
            size[s] = np.ones(len(idx))
        kind[s] = np.where(wk_, 1, np.where(dn7, 4, 0))    # 1 débil, 4 fuerte con BTC cayendo en 7 días, 0 fuerte
        k_off[s] = np.full(len(idx), 2)
    l95 = lm[0.95].values
    out = candidates(P, pm, lim_in, l95, f_in, X_in, kind, size)
    out += candidates(P, pm, lim98, l95, f_off, X_off, k_off, size)
    G["C8"][key] = out
    return out


def make(mdl=None, adapt=None, vs=None, sl=None, rx=None, bt=None, ct=None, st=None, lock=None, cap7=None, wk=None):
    caps = {1: 3}
    if cap7:
        caps[4] = cap7
    acc = portfolio(cands_for(mdl, vs, sl, rx, bt, ct, st, wk), caps, adapt,
                    msl={"m2": 0.02, "m25": 0.025}.get(lock, 0.03), wsl=0.015 if lock == "w15" else None)
    return S.monthly(acc)


def measure(m):
    r = S.measure(m)
    v = np.array(r["meses"][8:11]) / 100
    r["son"] = round(100 * ((1 + v).prod() - 1), 2)
    return r


KS = [f"K{i}" for i in range(1, 10)]


def check(r, base):
    for i, y in enumerate(M.YEARS):
        r[f"K{i + 1}"] = bool(r[str(y)] >= base[str(y)] - 0.005)
    r["K5"] = bool(r["dd"] >= base["dd"] - 0.005)
    r["K6"] = bool(r["pos47"] >= base["pos47"])
    r["K7"] = bool(r["pos"] >= base["pos"])
    r["K8"] = bool(r["meses"][1] >= 0)
    r["K9"] = all(r["meses"][i] >= base["meses"][i] - 0.005 for i in (8, 9, 10))
    r["fallan"] = " ".join(k for k in KS if not r[k]) or "-"
    r["mantiene"] = r["fallan"] == "-"
    r["cumple"] = r["mantiene"] and r["son"] > base["son"] + 0.005
    return r


OPTS2 = {"mdl": [None, "mb", "mb0", "mbd", "mbs", "mbw"], "rx": [None, "rx", "str", "loss", "strloss", "smastrloss"],
         "lock": [None, "m2", "m25"], "wk": [None, "wk", "wkd"]}
N2 = {"mb": "12", "mb0": "12b", "mbd": "12c", "mbs": "12d", "mbw": "12e", "rx": "7", "str": "7b", "loss": "7c",
      "strloss": "7d", "smastrloss": "7e", "m2": "3a", "m25": "3c", "wk": "1", "wkd": "1b"}
NAMES2 = {"12b": "12b. Modelo de amplitud: basta con que prediga subida", "12c": "12c. Modelo de amplitud solo si BTC cae en 7 días",
          "12d": "12d. Modelo de amplitud solo en régimen fuerte", "12e": "12e. Modelo de amplitud solo fuera del régimen fuerte",
          "7b": "7b. Salir al apagarse el régimen, solo compras hechas en régimen fuerte",
          "7c": "7c. Salir al apagarse el régimen solo si la posición va perdiendo",
          "7d": "7d. Como 7b, y solo si la posición va perdiendo",
          "7e": "7e. Salir si BTC pierde su media de 200 días y la posición va perdiendo (compras en régimen fuerte)",
          "3c": "3c. Parar el mes al perder 2,5 %", "1b": "1b. Sin fin de semana solo si BTC cae en 7 días"}


def label2(kw):
    return "+".join(N2[v] for v in kw.values() if v is not None) or "base"


def work2(vals):
    kw = dict(zip(OPTS2, vals))
    _, m = make(**kw)
    return label2(kw), measure(m), m


def label(kw):
    return "+".join(code(k, v) for k, v in kw.items() if v is not None) or "base"


def work(vals):
    kw = dict(zip(OPTS, vals))
    _, m = make(**kw)
    return label(kw), measure(m), m


def main(combos=False):
    setup()
    idx = G["idx"]
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    rows = {}
    tr, m = make()
    base = measure(m)
    M.run("base", "Versión final (punto de partida: 5c de meses7)", tr, idx, m)
    rows["base"] = {"nombre": "Versión final", **base}
    d = pd.DataFrame(tr, columns=["moneda", "entrada", "salida", "neta_%"])
    d = d[d.salida >= "2026-09-01"]
    d["neta_%"] = (100 * d["neta_%"]).round(2)
    print("Operaciones del punto de partida desde septiembre de 2026:\n" + d.to_string(index=False), flush=True)
    for (k, v), name in reversed(list(NAMES.items())):
        tr, m = make(**{k: v})
        M.run(code(k, v), name, tr, idx, m)
        r = check(measure(m), base)
        rows[code(k, v)] = {"nombre": name, **r}
        print(f"2026 por mes (%): {S.fmt(r)}   sep-nov {r['son']:+.2f} %   fallan: {r['fallan']}", flush=True)

    for k, opts in OPTS2.items():                          # segunda ronda: versiones más finas de 12, 7, 3 y 1
        for v in opts:
            if v is not None and N2[v] in NAMES2:
                tr, m = make(**{k: v})
                M.run(N2[v], NAMES2[N2[v]], tr, idx, m)
                r = check(measure(m), base)
                rows[N2[v]] = {"nombre": NAMES2[N2[v]], **r}
                print(f"2026 por mes (%): {S.fmt(r)}   sep-nov {r['son']:+.2f} %   fallan: {r['fallan']}", flush=True)

    cols = ["2023", "2024", "2025", "2026", "total", "dd", "pos47", "pos", "son"]
    pd.set_option("display.width", 320, "display.max_columns", 40, "display.max_rows", 500, "display.max_colwidth", 60)
    ind = pd.DataFrame([{"variante": k, **{c: r[c] for c in cols}, "fallan": r.get("fallan", ""),
                         **{MES[i]: v for i, v in enumerate(r["meses"])}} for k, r in rows.items()])
    print("\n### Individuales\n" + ind.to_string(index=False), flush=True)
    res = {"base": base, "individuales": rows}

    if combos:
        with Pool(4) as pool:
            done = pool.map(work, list(itertools.product(*OPTS.values())), chunksize=256)
            done2 = pool.map(work2, list(itertools.product(*OPTS2.values())), chunksize=16)
        seen = {d[0] for d in done}
        done += [d for d in done2 if d[0] not in seen]
        out, ser = [], {}
        for name, r, m in done:
            r = check(r, base)
            out.append({"combinación": name, **{c: r[c] for c in cols}, "fallan": r["fallan"],
                        "n_fallan": len(r["fallan"].split()) if r["fallan"] != "-" else 0,
                        "mantiene": r["mantiene"], "cumple": r["cumple"],
                        **{MES[i]: v for i, v in enumerate(r["meses"])}})
            ser[name] = m
        df = pd.DataFrame(out)
        drop = ["mantiene", "cumple", "n_fallan"]
        ok = df[df.cumple].sort_values(["son", "total"], ascending=False)
        keep = df[df.mantiene]
        print(f"\n### Combinaciones probadas: {len(df)}")
        print(f"No empeoran nada (K1-K9): {len(keep)}.  Además suben septiembre-noviembre: {len(ok)}")
        print(ok.head(30).drop(columns=drop).to_string(index=False))
        near = df[(df.son > base["son"]) & ~df.mantiene].sort_values(["n_fallan", "son"], ascending=[True, False])
        print(f"\nSuben septiembre-noviembre pero rompen algo: {len(near)}. Las 25 que menos rompen:")
        print(near.head(25).drop(columns=drop).to_string(index=False), flush=True)
        top = df.sort_values("son", ascending=False)
        print("\nLas 10 con mejor septiembre-noviembre, cumplan o no:")
        print(top.head(10).drop(columns=drop).to_string(index=False), flush=True)
        pd.concat([ok, near.head(500)]).to_csv(os.path.join(OUT, "meses8_combinaciones.csv"), index=False)
        res["combinaciones"] = {"probadas": len(df), "sin_empeorar": len(keep), "cumplen": ok.head(100).to_dict("records"),
                                "casi": near.head(50).to_dict("records")}
        best = list(ok.head(10)["combinación"]) + list(near.head(5)["combinación"])
        pd.DataFrame({**M.SER, **{k: ser[k] for k in dict.fromkeys(best)}}).to_csv(
            os.path.join(OUT, "meses8_mensual.csv"), float_format="%.5f")
    json.dump(res, open(os.path.join(OUT, "meses8_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main("--combos" in sys.argv)
