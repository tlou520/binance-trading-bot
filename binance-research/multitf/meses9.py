"""Diez mejoras sobre la versión final (7e de meses8) para subir octubre y noviembre de 2026 sin empeorar nada de
lo que ya tiene, y sus combinaciones.

Condiciones (todas contra la versión final):
  K1-K4  2023, 2024, 2025 y 2026 no ganan menos
  K5     la caída máxima (2023-2026) no es peor
  K6     los meses positivos de 47 no bajan
  K7     los meses positivos de 2026 no bajan de 7
  K8     ningún mes de 2026 que hoy es positivo pasa a negativo
  K9     ni octubre ni noviembre de 2026 empeoran
  META   octubre y noviembre suben; lo ideal es octubre positivo

De menor a mayor complejidad:
 1  Margen en el modelo de 24 h: debe predecir una subida mayor que un mínimo, no solo mayor que cero.
 2  Margen sobre el percentil: la predicción de 72 h debe superar el umbral por un porcentaje.
 3  Freno por caída de BTC: sin compras dentro de régimen si BTC cayó más de x % en 24 h.
 4  Filtro de volatilidad: sin compras si el ATR de la moneda está lejos de su mediana de 30 días.
 5  Persistencia: la señal debe llevar n horas seguidas activa.
 6  Corte por tiempo: a las k horas, vender si la compra pierde más de x ATR.
 7  Salida por señal: vender una compra que va perdiendo si el modelo pasa a predecir caída.
 8  No sumar a pérdidas: sin compras nuevas si las posiciones abiertas pierden en promedio más de x %.
 9  Reentreno quincenal: modelos nuevos el día 1 y el día 16.
10  Segundo modelo: probabilidad de que la operación termine ganando con las reglas de salida reales.

Segunda ronda, con versiones más finas de las dos que quedaron más cerca: 2d y 2e (el margen solo en régimen
fuerte) y 3d, 3e y 3f (el freno solo cuando BTC está cerca de su media de 200 días).

Tercera ronda: una búsqueda de reglas (604 condiciones sobre 28 variables y 131.995 pares) encontró una familia
que sí mueve octubre, y se añadió como sugerencia 11:
11  Monedas moviéndose igual con BTC extendido: sin compras en régimen fuerte si la dispersión de las subidas de
    7 días de las seis monedas (su desviación estándar) es menor que d y BTC está más de x sobre su media de 200 días.

Uso: python meses9.py [--combos]
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
KEYS = ["m24", "mg", "crash", "vol", "pers", "tcut", "sx", "nodown", "mdl", "clf", "disp"]
NUM = dict(zip(KEYS, "1 2 3 4 5 6 7 8 9 10 11".split()))
OPTS = {"m24": [None, 0.0002, 0.0005, 0.001], "mg": [None, 0.03, 0.05, 0.1, "s0.05", "s0.06"],
        "crash": [None, 0.02, 0.03, 0.04, "n3-0", "n3-2", "n5-2"],
        "vol": [None, "lo0.6", "lo0.75", "hi1.5"], "pers": [None, 2, 3], "tcut": [None, (24, 4), (24, 6), (48, 4), (48, 6)],
        "sx": [None, "p10", "p05", "neg"], "nodown": [None, 0.01, 0.02, 0.03], "mdl": [None, "q"],
        "clf": [None, 0.5, 0.55, "p90"], "disp": [None, (0.02, 0.1), (0.025, 0.1), (0.03, 0.1), (0.025, 0.125)]}
GRID = {"pers": [None], "mdl": [None], "disp": [None]}    # combinaciones de las diez (5 y 9 empeoran casi todo)
GRID2 = {"m24": [None, 0.0002], "mg": [None, "s0.05", "s0.06"], "crash": [None, "n3-0", "n3-2", "n5-2"], "vol": [None],
         "pers": [None], "tcut": [None, (24, 6)], "sx": [None, "p05"], "nodown": [None], "mdl": [None], "clf": [None, 0.5]}
#        combinaciones de la 11 con las que quedaron más cerca
NAMES = {("m24", 0.0002): "1a. El modelo de 24 h predice más de +0,02 %",
         ("m24", 0.0005): "1b. El modelo de 24 h predice más de +0,05 %",
         ("m24", 0.001): "1c. El modelo de 24 h predice más de +0,10 %",
         ("mg", 0.03): "2a. Predicción 3 % sobre el umbral", ("mg", 0.05): "2b. Predicción 5 % sobre el umbral",
         ("mg", 0.1): "2c. Predicción 10 % sobre el umbral",
         ("mg", "s0.05"): "2d. Predicción 5 % sobre el umbral, solo en régimen fuerte",
         ("mg", "s0.06"): "2e. Predicción 6 % sobre el umbral, solo en régimen fuerte",
         ("crash", 0.02): "3a. Sin compras en régimen si BTC cayó más de 2 % en 24 h",
         ("crash", 0.03): "3b. Sin compras en régimen si BTC cayó más de 3 % en 24 h",
         ("crash", 0.04): "3c. Sin compras en régimen si BTC cayó más de 4 % en 24 h",
         ("crash", "n3-0"): "3d. Régimen fuerte: sin compras si BTC está a menos de 3 % de su media de 200 días y cayó en 24 h",
         ("crash", "n3-2"): "3e. Régimen fuerte: sin compras si BTC está a menos de 3 % de su media y cayó más de 2 % en 24 h",
         ("crash", "n5-2"): "3f. Régimen fuerte: sin compras si BTC está a menos de 5 % de su media y cayó más de 2 % en 24 h",
         ("vol", "lo0.6"): "4a. Sin compras si el ATR está bajo 0,6 veces su mediana de 30 días",
         ("vol", "lo0.75"): "4b. Sin compras si el ATR está bajo 0,75 veces su mediana de 30 días",
         ("vol", "hi1.5"): "4c. Sin compras si el ATR está sobre 1,5 veces su mediana de 30 días",
         ("pers", 2): "5a. Señal activa 2 horas seguidas", ("pers", 3): "5b. Señal activa 3 horas seguidas",
         ("tcut", (24, 4)): "6a. A las 24 h, vender si pierde más de 4 ATR",
         ("tcut", (24, 6)): "6b. A las 24 h, vender si pierde más de 6 ATR",
         ("tcut", (48, 4)): "6c. A las 48 h, vender si pierde más de 4 ATR",
         ("tcut", (48, 6)): "6d. A las 48 h, vender si pierde más de 6 ATR",
         ("sx", "p10"): "7a. Vender si va perdiendo y la predicción cae al 10 % más bajo",
         ("sx", "p05"): "7b. Vender si va perdiendo y la predicción cae al 5 % más bajo",
         ("sx", "neg"): "7c. Vender si va perdiendo y los modelos de 72 h y 24 h predicen caída",
         ("nodown", 0.01): "8a. Sin compras nuevas si las abiertas pierden más de 1 % en promedio",
         ("nodown", 0.02): "8b. Sin compras nuevas si las abiertas pierden más de 2 % en promedio",
         ("nodown", 0.03): "8c. Sin compras nuevas si las abiertas pierden más de 3 % en promedio",
         ("mdl", "q"): "9. Reentreno quincenal (días 1 y 16)",
         ("clf", 0.5): "10a. Segundo modelo: probabilidad de ganar mayor que 50 %",
         ("clf", 0.55): "10b. Segundo modelo: probabilidad de ganar mayor que 55 %",
         ("clf", "p90"): "10c. Segundo modelo: probabilidad de ganar sobre su percentil 90",
         ("disp", (0.02, 0.1)): "11a. Régimen fuerte: sin compras si la dispersión es menor que 2 % y BTC está más de 10 % sobre su media",
         ("disp", (0.025, 0.1)): "11b. Régimen fuerte: sin compras si la dispersión es menor que 2,5 % y BTC está más de 10 % sobre su media",
         ("disp", (0.03, 0.1)): "11c. Régimen fuerte: sin compras si la dispersión es menor que 3 % y BTC está más de 10 % sobre su media",
         ("disp", (0.025, 0.125)): "11d. Régimen fuerte: sin compras si la dispersión es menor que 2,5 % y BTC está más de 12,5 % sobre su media"}


CAND = {"2d+3e": dict(mg="s0.05", crash="n3-2"), "3e+11b": dict(crash="n3-2", disp=(0.025, 0.1)),
        "2d+3e+11b": dict(mg="s0.05", crash="n3-2", disp=(0.025, 0.1))}


def code(k, v):
    return NUM[k] + ("" if len(OPTS[k]) == 2 else chr(ord("a") + OPTS[k].index(v) - 1))


def label(kw):
    return "+".join(code(k, v) for k, v in kw.items() if v is not None) or "base"


def halves(y0, y1):
    """Periodos de medio mes: del 1 al 15 y del 16 al final."""
    out = []
    for a, b in months(y0, y1):
        mid = a + pd.Timedelta(days=15)
        out += [(a, mid), (mid, b)]
    return out


def exits(P, strong, extra=None, tcut=None, ktp=12.0, n=72):
    """Resultado de cada posible entrada con las salidas de la versión final: objetivo a ktp ATR, salida de
    protección (compras hechas con BTC sobre su media de 200 días: si una hora cierra con BTC bajo esa media y la
    moneda bajo el precio de compra, se vende en la apertura siguiente) y salida a las n horas.
    `extra` ({moneda: serie booleana}): otra condición de salida, solo si la compra va perdiendo.
    `tcut` (k, x): al cerrar la hora k, vender si el cierre está más de x ATR bajo la entrada."""
    out = {}
    s_in = strong.values
    for s in E.COINS:
        h = P[s]
        ent, a = h.onext.values, h.atr.values
        tp = ent * (1 + ktp * a)
        st, ret, kx = np.zeros(len(h)), np.full(len(h), np.nan), np.full(len(h), n)
        for k in range(1, n + 1):
            y = (st == 0) & (h.h.shift(-k).values >= tp)
            ret[y], st[y], kx[y] = (ktp * a)[y], 1, k
            if k < n:
                c_k = h.c.shift(-k).values
                bad = s_in & strong.shift(-k).eq(False).values
                if extra is not None:
                    bad = bad | extra[s].shift(-k).eq(True).values
                z = (st == 0) & bad & (c_k < ent)
                if tcut and k == tcut[0]:
                    z |= (st == 0) & (c_k < ent * (1 - tcut[1] * a))
                ret[z], st[z], kx[z] = (h.o.shift(-k - 1).values / ent - 1)[z], 3, k
        yn = h.onext.shift(-n).values / ent - 1
        ret[st == 0] = yn[st == 0]
        out[s] = (np.where(np.isnan(yn) | np.isnan(a) | np.isnan(ret), np.nan, ret), kx, n)
    return out


def candidates(P, pred, lim, filt, ex, kind, pers=None, relax=None):
    """Una a la vez por moneda: (moneda, fila de entrada, salida en ns, neta, tipo, exceso, venció, precio).
    `relax` ({moneda: serie booleana}): al vencer una compra sin señal activa, se mantiene igual si relax es
    verdadero en esa hora."""
    out = []
    for j, s in enumerate(E.COINS):
        pv = pred[s].values
        sig = (pv > np.maximum(lim[s], E.COST)) & filt[s].values
        if pers:
            z = sig.copy()
            for d in range(1, pers):
                z[d:] &= sig[:-d]
                z[:d] = False
            sig = z
        r, k, n = ex[s]
        sig &= ~np.isnan(r)
        rl = (relax[s].values & ~np.isnan(r)) if relax is not None else None
        T, ent, ii, L = G["T"], P[s].onext.values, np.flatnonzero(sig), len(sig)
        q = 0
        while q < len(ii):
            i = ii[q]
            while True:
                out.append((j, i + 1, T[i] + (k[i] + 1) * NS_H, r[i] - COST_BNB, kind[s][i], pv[i] - lim[s][i],
                            k[i] == n, ent[i]))
                free = i + k[i]
                if rl is not None and k[i] == n and free < L and not sig[free] and rl[free]:
                    i = free                               # renovación con la condición relajada
                    continue
                break
            q = np.searchsorted(ii, free)
    return out


def portfolio(cands, caps, nodown=None, msl=0.03):
    """Controles de cuenta. caps: {tipo: máximo de posiciones abiertas al entrar con ese tipo}. nodown: no comprar
    si las posiciones abiertas pierden en promedio más de esa fracción (al cierre de la hora de la decisión)."""
    T, CL = G["T"], G["CL"]
    cands = sorted(cands, key=lambda x: (x[1], -x[5]))
    n = len(cands)
    C, R, Mx, J, EP = (np.zeros(n, np.int64), np.zeros(n), np.zeros(n, np.int64), np.zeros(n, np.int64), np.zeros(n))
    acc, last, k = [], {}, 0
    for j, ia, c, r, kind, _, tmo, ent in cands:
        a = T[ia]
        if k:
            done = C[:k] <= a
            cap = caps.get(kind)
            nopen = k - done.sum()
            if cap is not None and nopen >= cap:
                continue
            m = int(np.datetime64(int(a), "ns").astype("datetime64[M]").astype(int))
            dm = done & (Mx[:k] == m)
            if dm.any() and R[:k][dm].sum() <= -msl:
                continue
            if nodown is not None and nopen:
                op = ~done
                if (CL[J[:k][op], ia - 1] / EP[:k][op] - 1).mean() < -nodown:
                    continue
        p = last.get(j)
        if p is not None and p[0] == a and p[1]:           # la señal sigue al vencer: se mantiene sin pagar otra vez
            r += COST_BNB
        last[j] = (c, tmo)
        acc.append((j, a, c, r, kind, 1.0))
        C[k], R[k], J[k], EP[k] = c, r / E.SLOTS, j, ent
        Mx[k] = int(np.datetime64(int(c), "ns").astype("datetime64[M]").astype(int))
        k += 1
    return acc


def setup():
    build = M.build

    def build168(coins):                                   # meses7 necesita el objetivo de 7 días
        P = build(coins)
        for h in P.values():
            h["y168"] = h.onext.shift(-168) / h.onext - 1
        return P
    M.build = build168
    S.setup()
    M.build = build
    P, idx, strong = G["P"], G["idx"], G["strong"]
    G["disp7"] = pd.DataFrame({s: P[s].r7d for s in E.COINS}).std(axis=1)
    G["T"] = idx.as_unit("ns").asi8
    G["CL"] = np.array([P[s].c.values for s in E.COINS])
    G["EX9"], G["C9"] = {}, {}
    half = halves(2022, 2026)
    G["pmq"], G["lmq"] = M.cached("h72q" + TAG, lambda: predict(P, half, target="y72", gap=74))
    G["p24q"], _ = M.cached("h24q" + TAG, lambda: predict(P, half, target="y24", gap=26))
    plain = exits(P, strong)
    for s in E.COINS:                                      # etiqueta: la operación con las salidas reales gana
        r = plain[s][0]
        P[s]["win72"] = np.where(np.isnan(r), np.nan, (r - COST_BNB > 0).astype(float))
    G["pw"], G["lw"] = M.cached("h72win" + TAG, lambda: predict(P, months(2022, 2026), target="win72", clf=True, gap=74))


def get_ex(tcut, sx, mdl):
    key = (tcut, sx, mdl if sx else None)
    if key not in G["EX9"]:
        P = G["P"]
        pm, lm, p24 = (G["pmq"], G["lmq"], G["p24q"]) if mdl == "q" else (G["pm"], G["lm"], G["p24"])
        extra = None
        if sx == "neg":
            extra = {s: (pm[s] < 0) & (p24[s] < 0) for s in E.COINS}
        elif sx:
            extra = {s: pm[s] < lm[{"p10": 0.1, "p05": 0.05}[sx]] for s in E.COINS}
        G["EX9"][key] = exits(P, G["strong"], extra, tcut)
    return G["EX9"][key]


def cands_for(m24, mg, crash, vol, pers, tcut, sx, mdl, clf, disp=None):
    key = (m24, mg, crash, vol, pers, tcut, sx, mdl, clf, disp)
    if key in G["C9"]:
        return G["C9"][key]
    P, idx, b = G["P"], G["idx"], G["b"]
    pm, lm, p24 = (G["pmq"], G["lmq"], G["p24q"]) if mdl == "q" else (G["pm"], G["lm"], G["p24"])
    mix, strong, news_ok = G["mix"], G["strong"], G["news_ok"]
    X = get_ex(tcut, sx, mdl)
    up24 = b.r24h > 0
    solo_fuerte = isinstance(mg, str)                      # "s0.05": el margen solo se pide en régimen fuerte
    k_mg = 1 + (float(mg[1:]) if solo_fuerte else (mg or 0))
    lim_in, lim98, f_in, f_off, kind, k_off = {}, {}, {}, {}, {}, {}
    for s in E.COINS:
        h = P[s]
        ok24 = (p24[s] > (m24 or 0)).fillna(False)
        lim_in[s] = np.where(strong, lm[0.9] * k_mg, lm[0.95] * (1 if solo_fuerte else k_mg))
        lim98[s] = lm[0.98].values * (1 if solo_fuerte else k_mg)
        f = news_ok.copy()
        if vol:
            ratio = h.atr / h.atr.rolling(720).median()
            f &= (ratio >= float(vol[2:])).fillna(True) if vol.startswith("lo") else (ratio <= float(vol[2:])).fillna(True)
        if clf:
            f &= (G["pw"][s] > (G["lw"][0.9] if clf == "p90" else clf)).fillna(False)
        fi = mix[s] & ok24 & f
        if isinstance(crash, str):                         # "n3-2": BTC cerca de su media de 200 días y cayendo
            near, drop = (float(x) / 100 for x in crash[1:].split("-"))
            fi &= ~(strong & (b.btc_reg < near) & (b.r24h < -drop))
        elif crash:
            fi &= (b.r24h > -crash).fillna(False)
        if disp:                                           # las seis monedas se mueven igual y BTC está extendido
            fi &= ~(strong & (G["disp7"] < disp[0]) & (b.btc_reg > disp[1]))
        f_in[s], f_off[s] = fi, ~mix[s] & up24 & ok24 & f
        kind[s] = np.where(mix[s] & ~strong, 1, 0)         # 1 régimen débil, 0 fuerte, 2 fuera de régimen
        k_off[s] = np.full(len(idx), 2)
    out = candidates(P, pm, lim_in, f_in, X, kind, pers) + candidates(P, pm, lim98, f_off, X, k_off, pers)
    if len(G["C9"]) > 64:
        G["C9"].clear()
    G["C9"][key] = out
    return out


def make(m24=None, mg=None, crash=None, vol=None, pers=None, tcut=None, sx=None, nodown=None, mdl=None, clf=None,
         disp=None):
    acc = portfolio(cands_for(m24, mg, crash, vol, pers, tcut, sx, mdl, clf, disp), {1: 3}, nodown)
    return S.monthly(acc)


def measure(m):
    r = S.measure(m)
    r["todos"] = (100 * m[[p.year in M.YEARS for p in m.index]]).round(2).tolist()
    r["2022"] = round(100 * ((1 + m[[p.year == 2022 for p in m.index]]).prod() - 1), 2)
    r["oct"], r["nov"] = r["meses"][9], r["meses"][10]
    r["on"] = round(100 * ((1 + r["oct"] / 100) * (1 + r["nov"] / 100) - 1), 2)
    return r


KS = [f"K{i}" for i in range(1, 10)]


def check(r, base):
    for i, y in enumerate(M.YEARS):
        r[f"K{i + 1}"] = bool(r[str(y)] >= base[str(y)] - 0.005)
    r["K5"] = bool(r["dd"] >= base["dd"] - 0.005)
    r["K6"] = bool(r["pos47"] >= base["pos47"])
    r["K7"] = bool(r["pos"] >= base["pos"])
    r["K8"] = all(v >= 0 for v, v0 in zip(r["meses"], base["meses"]) if v0 > 0)
    r["K9"] = all(r["meses"][i] >= base["meses"][i] - 0.005 for i in (9, 10))
    r["fallan"] = " ".join(k for k in KS if not r[k]) or "-"
    r["mantiene"] = r["fallan"] == "-"
    r["sube"] = bool(r["on"] > base["on"] + 0.005)
    r["cumple"] = r["mantiene"] and r["oct"] > base["oct"] + 0.005 and r["nov"] > base["nov"] + 0.005
    return r


def work(vals):
    kw = dict(zip(KEYS, vals))
    _, m = make(**kw)
    r = measure(m)
    r.pop("todos")
    return label(kw), r


COLS = ["2022", "2023", "2024", "2025", "2026", "total", "dd", "pos47", "pos", "oct", "nov", "on"]


def main(combos=False):
    setup()
    idx = G["idx"]
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    rows, ser = {}, {}
    tr, m = make()
    base = measure(m)
    M.run("base", "Versión final (punto de partida: 7e de meses8)", tr, idx, m)
    rows["base"], ser["base"] = {"nombre": "Versión final", **base}, m
    d = pd.DataFrame(tr, columns=["moneda", "entrada", "salida", "neta_%"])
    d = d[d.salida >= "2026-10-01"]
    d["neta_%"] = (100 * d["neta_%"]).round(2)
    print("Operaciones del punto de partida con salida desde octubre de 2026:\n" + d.to_string(index=False), flush=True)
    for (k, v), name in NAMES.items():
        tr, m = make(**{k: v})
        M.run(code(k, v), name, tr, idx, m)
        r = check(measure(m), base)
        rows[code(k, v)], ser[code(k, v)] = {"nombre": name, **r}, m
        print(f"2026 por mes (%): {S.fmt(r)}   oct+nov {r['on']:+.2f} %   fallan: {r['fallan']}", flush=True)
    for key, kw in CAND.items():                           # candidatas: las que cumplen todo, juntas
        tr, m = make(**kw)
        M.run(key, "Candidata " + key, tr, idx, m)
        r = check(measure(m), base)
        rows[key], ser[key] = {"nombre": "Candidata " + key, **r}, m
        print(f"2026 por mes (%): {S.fmt(r)}   oct+nov {r['on']:+.2f} %   fallan: {r['fallan']}", flush=True)
    pd.set_option("display.width", 320, "display.max_columns", 40, "display.max_rows", 500, "display.max_colwidth", 60)
    ind = pd.DataFrame([{"variante": k, **{c: r[c] for c in COLS}, "fallan": r.get("fallan", "")} for k, r in rows.items()])
    print("\n### Individuales\n" + ind.to_string(index=False), flush=True)
    res = {"base": base, "individuales": rows}

    if combos:
        grid = list(itertools.product(*[GRID.get(k, v) for k, v in OPTS.items()]))
        grid2 = [v for v in itertools.product(*[GRID2.get(k, v) for k, v in OPTS.items()]) if v[-1] is not None]
        with Pool(4) as pool:
            done = pool.map(work, grid, chunksize=512) + pool.map(work, grid2, chunksize=16)
        out = []
        for name, r in done:
            r = check(r, base)
            out.append({"combinación": name, **{c: r[c] for c in COLS}, "fallan": r["fallan"],
                        "n_fallan": len(r["fallan"].split()) if r["fallan"] != "-" else 0,
                        "mantiene": r["mantiene"], "cumple": r["cumple"],
                        **{MES[i]: v for i, v in enumerate(r["meses"])}})
        df = pd.DataFrame(out)
        drop = ["mantiene", "cumple", "n_fallan"]
        ok = df[df.cumple].sort_values(["on", "total"], ascending=False)
        keep = df[df.mantiene]
        print(f"\n### Combinaciones probadas: {len(df)}")
        print(f"No empeoran nada (K1-K9): {len(keep)}.  Además suben octubre y noviembre: {len(ok)}")
        print(ok.head(30).drop(columns=drop).to_string(index=False))
        part = keep[(keep.on > base["on"] + 0.005) & ~keep.cumple].sort_values(["on", "total"], ascending=False)
        print(f"\nNo empeoran nada y suben la suma de octubre y noviembre (uno de los dos queda igual): {len(part)}")
        print(part.head(30).drop(columns=drop).to_string(index=False))
        near = df[(df.on > base["on"] + 0.005) & ~df.mantiene].sort_values(["n_fallan", "on"], ascending=[True, False])
        print(f"\nSuben octubre y noviembre pero rompen algo: {len(near)}. Las 25 que menos rompen:")
        print(near.head(25).drop(columns=drop).to_string(index=False), flush=True)
        pos = df[df.oct > 0].sort_values(["n_fallan", "total"], ascending=[True, False])
        print(f"\nDejan octubre en positivo: {len(pos)}. Las 25 que menos rompen:")
        print(pos.head(25).drop(columns=drop).to_string(index=False), flush=True)
        pd.concat([ok, part, near.head(500), pos.head(200)]).drop_duplicates("combinación").to_csv(
            os.path.join(OUT, "meses9_combinaciones.csv"), index=False)
        res["combinaciones"] = {"probadas": len(df), "sin_empeorar": len(keep), "cumplen": ok.head(100).to_dict("records"),
                                "suben_la_suma": part.head(100).to_dict("records"),
                                "casi": near.head(50).to_dict("records"), "octubre_positivo": pos.head(50).to_dict("records")}
    pd.DataFrame(ser).to_csv(os.path.join(OUT, "meses9_mensual.csv"), float_format="%.5f")
    json.dump(res, open(os.path.join(OUT, "meses9_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main("--combos" in sys.argv)
