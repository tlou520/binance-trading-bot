"""Ocho mejoras sobre la versión final (variante A de meses6) para subir los meses positivos de 2026 de 5 a 7 de 11,
sin empeorar nada de lo que ya tiene, y todas sus combinaciones.

Condiciones (todas contra la versión final):
  K1-K4  2023, 2024, 2025 y 2026 no ganan menos
  K5     la caída máxima (2023-2026) no es peor
  K6     los meses positivos de 47 no bajan
  K7     septiembre, octubre y noviembre de 2026 no empeoran
  K8     febrero de 2026 no es negativo
  META   al menos 7 meses positivos de 11 en 2026

8  Segundo modelo (24 h) que opera fuera de régimen.
7  Acuerdo con el modelo de 7 días.
6  Stop en el punto de equilibrio tras ganar k ATR.
5  Tope de posiciones abiertas a la vez (entran las de mayor predicción).
4  Régimen débil más estricto.
3  Proteger el mes: tras llegar a +a %, parar si baja a +b %.
2  Pausa tras pérdidas.
1  Otro objetivo de venta o duración.

Uso: python meses7.py [--combos]
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
from mejoras import H, OUT, months, predict, years
from meses2 import FIT, MES, TAG
from meses3 import COST_BNB
from meses5 import NEWS

M.END = None
NS_H = 3600 * 10**9
BASE = dict(sleeve=None, agree=None, be=None, cap=None, weak=None, wex=None, protect=None, cool=None, ex=(12, 72))
OPTS = {"sleeve": [None, "s24", "s24b"], "agree": [None, "in", "all"], "be": [None, 3, 5],
        "cap": [None, 3, 4, "w3", "w4"], "weak": [None, "p98", "btc24", "half"], "wex": [None, 8],
        "protect": [None, (0.005, 0.001), (0.01, 0.003), (0.02, 0.01)],
        "cool": [None, "coin48", "acct48"], "ex": [(12, 72), (8, 72), (16, 72), (12, 48)]}
NUM = {"sleeve": "8", "agree": "7", "be": "6", "cap": "5", "weak": "4", "wex": "4x", "protect": "3", "cool": "2", "ex": "1"}
GRID = {"sleeve": [None, "s24b"], "agree": [None, "in"], "cool": [None, "coin48"]}   # lo que entra en combinaciones
G = {}                                                    # datos compartidos con los procesos hijos


def exits(P, ktp=12.0, n=72, be=None):
    """Resultado de cada posible entrada: objetivo a ktp ATR o salida a las n horas. `be`: cuando una hora ya
    cerrada llegó a ganar be ATR, se pone un stop en el precio de entrada más el costo."""
    out = {}
    for s in E.COINS:
        h = P[s]
        ent, a = h.onext.values, h.atr.values
        tp, stop = ent * (1 + ktp * a), ent * (1 + COST_BNB)
        st, ret, kx = np.zeros(len(h)), np.full(len(h), np.nan), np.full(len(h), n)
        armed = np.zeros(len(h), bool)
        for k in range(1, n + 1):
            hi, lo, op = (h[c].shift(-k).values for c in ("h", "l", "o"))
            if be is not None:
                z = (st == 0) & armed & (lo <= stop)
                ret[z], st[z], kx[z] = (np.minimum(stop, op) / ent - 1)[z], 2, k
            y = (st == 0) & (hi >= tp)
            ret[y], st[y], kx[y] = (ktp * a)[y], 1, k
            if be is not None:
                armed |= hi >= ent * (1 + be * a)
        yn = h.onext.shift(-n).values / ent - 1
        ret[st == 0] = yn[st == 0]
        out[s] = (np.where(np.isnan(yn) | np.isnan(a) | np.isnan(ret), np.nan, ret), kx, n)
    return out


def candidates(P, pred, lim, filt, ex, kind, size=1.0):
    """Una a la vez por moneda. Devuelve (moneda, entrada, salida, neta, tipo, tamaño, exceso, venció)."""
    out = []
    for j, s in enumerate(E.COINS):
        pv = pred[s].values
        sig = (pv > np.maximum(lim[s], E.COST)) & filt[s].values
        r, k, n = ex[s]
        T, free = P[s].index.as_unit("ns").asi8, 0
        sz = size[s] if isinstance(size, dict) else np.full(len(T), size)
        kd = kind[s] if isinstance(kind, dict) else np.full(len(T), kind)
        for i in np.flatnonzero(sig):
            if i < free or np.isnan(r[i]):
                continue
            out.append((j, T[i] + NS_H, T[i] + (k[i] + 1) * NS_H, r[i] - COST_BNB, kd[i], sz[i], pv[i] - lim[s][i],
                        k[i] == n))
            free = i + k[i]
    return out


def portfolio(cands, cap=None, cool=None, protect=None, msl=0.03, one=False):
    """Recorre las operaciones por hora de entrada y aplica los controles de cuenta. Devuelve las aceptadas."""
    cands = sorted(cands, key=lambda x: (x[1], -x[6]))
    month = (np.array([c[1] for c in cands]).astype("datetime64[ns]").astype("datetime64[M]").astype(int))
    acc, A, C, R, Mx, S = [], [], [], [], [], []
    last = {}
    wcap = isinstance(cap, str)                           # "w3": el tope solo frena entradas en régimen débil
    cap = int(cap[1:]) if wcap else cap
    for t, m in zip(cands, month):
        j, a, c, r, kind, sz, _, tmo = t
        if A:
            a_, c_, r_, m_, s_ = (np.array(x) for x in (A, C, R, Mx, S))
            done = c_ <= a
            if (cap is not None and (kind == 1 or not wcap) and (~done).sum() >= cap) or (one and ((~done) & (s_ == j)).any()):
                continue
            dm = done & (m_ == m)                         # cerradas antes, con salida en el mes de esta entrada
            o = np.argsort(c_[dm], kind="stable")
            cum = np.cumsum(r_[dm][o]) if dm.any() else np.array([0.0])
            if cum[-1] <= -msl:
                continue
            if protect and cum.max() >= protect[0] and cum[-1] <= protect[1]:
                continue
            if cool == "coin48":                          # tras perder en una moneda, 48 h sin volver a ella
                z = done & (s_ == j) & (r_ < 0) & (c_ > a - 48 * NS_H)
                if z.any():
                    continue
            if cool == "acct48" and done.sum() >= 2:      # tras dos pérdidas seguidas en la cuenta, 48 h sin comprar
                od = np.argsort(c_[done], kind="stable")[-2:]
                if (r_[done][od] < 0).all() and c_[done][od][-1] > a - 48 * NS_H:
                    continue
        p = last.get((j, kind >= 3))
        if p is not None and p[0] == a and p[1]:          # la señal sigue al vencer: se mantiene, sin pagar otra vez
            r += COST_BNB
        last[(j, kind >= 3)] = (c, tmo)
        acc.append((j, a, c, r, kind, sz))
        A.append(a), C.append(c), R.append(r * sz / E.SLOTS), S.append(j)
        Mx.append(int(np.datetime64(int(c), "ns").astype("datetime64[M]").astype(int)))
    return acc


def setup():
    P = M.build(M.COINS6)
    idx = P["BTC"].index
    per = months(2022, 2026)
    pm, lm = M.cached("h72m" + TAG, lambda: predict(P, per, target="y72", gap=74))
    p24, l24 = M.cached("h24m" + TAG, lambda: predict(P, per, target="y24", gap=26))
    p168, _ = M.cached("h168" + TAG, lambda: predict(P, years(FIT), target="y168", gap=170))
    b = P["BTC"]
    mix = M.regime(P, "mixto")
    strong = (b.btc_reg > 0).fillna(False)
    t_in = idx + H
    news_ok = pd.Series(True, index=idx)
    for t in pd.to_datetime(pd.read_csv(NEWS).fecha_utc):
        news_ok[(t_in >= t - 24 * H) & (t_in <= t + 2 * H)] = False
    G.update(P=P, idx=idx, pm=pm, lm=lm, p24=p24, l24=l24, p168=p168, b=b, mix=mix, strong=strong, news_ok=news_ok,
             EX={}, CACHE={})


def get_ex(ktp, n, be):
    k = (ktp, n, be)
    if k not in G["EX"]:
        G["EX"][k] = exits(G["P"], ktp, n, be)
    return G["EX"][k]


def cands_for(sleeve, agree, be, weak, ex, wex=None):
    """Operaciones candidatas antes de los controles de cuenta."""
    key = (sleeve, agree, be, weak, ex, wex)
    if key in G["CACHE"]:
        return G["CACHE"][key]
    P, idx, pm, lm, p24, l24, b = (G[k] for k in ("P", "idx", "pm", "lm", "p24", "l24", "b"))
    mix, strong, news_ok = G["mix"], G["strong"], G["news_ok"]
    X = get_ex(ex[0], ex[1], be)
    up24 = b.r24h > 0
    out = []
    Xw = get_ex(wex, ex[1], be) if wex else X          # en régimen débil, otro objetivo de venta
    lim_in, lim98, f_in, f_off, size, kind, Xin = {}, {}, {}, {}, {}, {}, {}
    for s in E.COINS:
        ok24 = (p24[s] > 0).fillna(False)
        ok7 = (G["p168"][s] > 0).fillna(False)
        wk = mix[s] & ~strong
        lim_in[s] = np.where(strong, lm[0.9], lm[0.98] if weak == "p98" else lm[0.95])
        lim98[s] = lm[0.98].values
        f_in[s] = mix[s] & ok24 & news_ok
        if weak == "btc24":
            f_in[s] &= ~wk | up24
        if agree in ("in", "all"):
            f_in[s] &= ok7
        f_off[s] = ~mix[s] & news_ok & up24 & ok24
        if agree == "all":
            f_off[s] &= ok7
        size[s] = np.where(wk, 0.5, 1.0) if weak == "half" else np.ones(len(idx))
        kind[s] = np.where(wk, 1, 0)
        Xin[s] = (np.where(wk, Xw[s][0], X[s][0]), np.where(wk, Xw[s][1], X[s][1]), ex[1])
    out += candidates(P, pm, lim_in, f_in, Xin, kind, size)
    out += candidates(P, pm, lim98, f_off, X, 2)
    if sleeve:                                            # segundo modelo: 24 h, solo fuera de régimen, percentil 98
        X24 = get_ex(1e9, 24, None)
        fs = {s: ~mix[s] & news_ok & (up24 if sleeve == "s24b" else True) for s in E.COINS}
        out += candidates(P, p24, {s: l24[0.98].values for s in E.COINS}, fs, X24, 3)
    G["CACHE"][key] = out
    return out


def monthly(acc):
    idx = G["idx"]
    tr = [(E.COINS[j], pd.Timestamp(a), pd.Timestamp(c), r * sz) for j, a, c, r, _, sz in acc]
    return tr, M.full_months(E.monthly_from_trades(tr), idx)


def make(sleeve=None, agree=None, be=None, cap=None, weak=None, wex=None, protect=None, cool=None, ex=(12, 72)):
    acc = portfolio(cands_for(sleeve, agree, be, weak, ex, wex), cap, cool, protect, one=bool(sleeve))
    return monthly(acc)


def measure(m):
    mt = m[[p.year in M.YEARS for p in m.index]]
    m26 = (100 * mt[[p.year == 2026 for p in mt.index]]).round(2)
    eq = (1 + mt).cumprod()
    r = {"meses": m26.tolist(), "pos": int((m26 > 0).sum()), "dd": round(100 * (eq / eq.cummax() - 1).min(), 2),
         "pos47": int((mt > 0).sum()), "total": round(100 * (eq.iloc[-1] - 1), 1)}
    for y in M.YEARS:
        r[str(y)] = round(100 * ((1 + m[[p.year == y for p in m.index]]).prod() - 1), 2)
    return r


def check(r, base):
    for i, y in enumerate(M.YEARS):
        r[f"K{i + 1}"] = bool(r[str(y)] >= base[str(y)] - 0.005)
    r["K5"] = bool(r["dd"] >= base["dd"] - 0.005)
    r["K6"] = bool(r["pos47"] >= base["pos47"])
    r["K7"] = all(r["meses"][i] >= base["meses"][i] - 0.005 for i in (8, 9, 10))
    r["K8"] = bool(r["meses"][1] >= 0)
    r["fallan"] = " ".join(k for k in KS if not r[k]) or "-"
    r["mantiene"] = r["fallan"] == "-"
    r["cumple"] = r["mantiene"] and r["pos"] >= 7
    return r


KS = [f"K{i}" for i in range(1, 9)]


def label(kw):
    on = []
    for k, v in kw.items():
        if v != BASE[k]:
            on.append(NUM[k] + ("" if k == "wex" else chr(ord("a") + OPTS[k].index(v) - 1)))
    return "+".join(sorted(on, reverse=True)) or "base"


def work(vals):
    kw = dict(zip(OPTS, vals))
    _, m = make(**kw)
    return label(kw), measure(m), m


def fmt(r):
    return "  ".join(f"{MES[i]} {v:+.2f}" for i, v in enumerate(r["meses"]))


def main(combos=False):
    setup()
    idx = G["idx"]
    print(f"Datos: {idx[0]} a {idx[-1]} UTC", flush=True)
    rows = {}
    tr, m = make()
    base = measure(m)

    def show(key, name, **kw):
        tr, m = make(**{**BASE, **kw})
        M.run(key, name, tr, idx, m)
        r = measure(m) if key == "base" else check(measure(m), base)
        rows[key] = {"nombre": name, **r}
        print(f"2026 por mes (%): {fmt(r)}   -> positivos {r['pos']}/11, caída máx. {r['dd']:.2f} %", flush=True)
        if key != "base":
            print(f"Condiciones que fallan: {r['fallan']}   META {'sí' if r['pos'] >= 7 else 'no'}", flush=True)

    show("base", "Versión final (punto de partida)")
    show("1a", "1a. Objetivo de venta a 8 ATR", ex=(8, 72))
    show("1b", "1b. Objetivo de venta a 16 ATR", ex=(16, 72))
    show("1c", "1c. Duración máxima de 48 h", ex=(12, 48))
    show("2a", "2a. Tras perder en una moneda, 48 h sin volver a ella", cool="coin48")
    show("2b", "2b. Tras dos pérdidas seguidas, 48 h sin comprar", cool="acct48")
    show("3a", "3a. Proteger el mes: tras +0,5 %, parar si baja a +0,1 %", protect=(0.005, 0.001))
    show("3b", "3b. Proteger el mes: tras +1 %, parar si baja a +0,3 %", protect=(0.01, 0.003))
    show("3c", "3c. Proteger el mes: tras +2 %, parar si baja a +1 %", protect=(0.02, 0.01))
    show("4a", "4a. Régimen débil: exigir percentil 98", weak="p98")
    show("4b", "4b. Régimen débil: exigir que BTC subió en 24 h", weak="btc24")
    show("4c", "4c. Régimen débil: media posición", weak="half")
    show("4x", "4x. Régimen débil: objetivo de venta a 8 ATR", wex=8)
    show("5c", "5c. Máximo 3 posiciones abiertas al entrar en régimen débil", cap="w3")
    show("5d", "5d. Máximo 4 posiciones abiertas al entrar en régimen débil", cap="w4")
    show("5a", "5a. Máximo 3 posiciones abiertas a la vez", cap=3)
    show("5b", "5b. Máximo 4 posiciones abiertas a la vez", cap=4)
    show("6a", "6a. Stop en el punto de equilibrio tras ganar 3 ATR", be=3)
    show("6b", "6b. Stop en el punto de equilibrio tras ganar 5 ATR", be=5)
    show("7a", "7a. El modelo de 7 días también predice subida (dentro de régimen)", agree="in")
    show("7b", "7b. El modelo de 7 días también predice subida (siempre)", agree="all")
    show("8a", "8a. Segundo modelo de 24 h fuera de régimen (percentil 98)", sleeve="s24")
    show("8b", "8b. Segundo modelo de 24 h fuera de régimen, si BTC subió en 24 h", sleeve="s24b")

    cols = ["2023", "2024", "2025", "2026", "total", "dd", "pos47", "pos"]
    ind = pd.DataFrame([{"variante": k, **{c: r[c] for c in cols}, "fallan": r.get("fallan", ""),
                         **{MES[i]: v for i, v in enumerate(r["meses"])}} for k, r in rows.items()])
    pd.set_option("display.width", 320, "display.max_columns", 40, "display.max_rows", 500)
    print("\n### Individuales\n" + ind.to_string(index=False), flush=True)
    res = {"base": base, "individuales": rows}

    if combos:
        grid = [v for v in itertools.product(*[GRID.get(k, v) for k, v in OPTS.items()])]
        with Pool(4) as pool:                             # los hijos heredan los datos ya cargados
            done = pool.map(work, grid, chunksize=64)
        out, ser = [], {}
        for name, r, m in done:
            r = check(r, base)
            out.append({"combinación": name, **{c: r[c] for c in cols}, "fallan": r["fallan"],
                        "n_fallan": len(r["fallan"].split()) if r["fallan"] != "-" else 0,
                        "mantiene": r["mantiene"], "cumple": r["cumple"],
                        **{MES[i]: v for i, v in enumerate(r["meses"])}})
            ser[name] = m
        df = pd.DataFrame(out)
        df[df.pos >= 6].to_csv(os.path.join(OUT, "meses7_combinaciones.csv"), index=False)   # las de 6 o más
        print(f"\n### Combinaciones probadas: {len(df)}")
        print("Cuántas llegan a cada número de meses positivos en 2026 (todas / las que no empeoran nada):")
        print(pd.DataFrame({"todas": df.pos.value_counts(), "sin_empeorar": df[df.mantiene].pos.value_counts()})
              .fillna(0).astype(int).sort_index().to_string())
        drop = ["mantiene", "cumple", "n_fallan"]
        ok = df[df.cumple].sort_values(["pos", "2026"], ascending=False)
        print(f"\nCumplen todo (K1-K8 y META): {len(ok)}")
        print(ok.head(25).drop(columns=drop).to_string(index=False))
        keep = df[df.mantiene].sort_values(["pos", "pos47", "total"], ascending=False)
        print(f"\nNo empeoran nada (K1-K8): {len(keep)}. Las 15 con más meses positivos en 2026:")
        print(keep.head(15).drop(columns=drop).to_string(index=False))
        near = df[df.pos >= 7].sort_values(["n_fallan", "total"], ascending=[True, False])
        print(f"\nLlegan a 7 o más meses positivos: {len(near)}. Las 25 que menos condiciones rompen:")
        print(near.head(25).drop(columns=drop).to_string(index=False), flush=True)
        res["combinaciones"] = {"probadas": len(df), "cumplen": ok.to_dict("records")[:50],
                                "sin_empeorar": keep.head(50).to_dict("records"),
                                "siete_o_mas": near.head(50).to_dict("records")}
        best = list(ok.head(10)["combinación"]) + list(keep.head(5)["combinación"]) + list(near.head(5)["combinación"])
        pd.DataFrame({**M.SER, **{k: ser[k] for k in dict.fromkeys(best)}}).to_csv(
            os.path.join(OUT, "meses7_mensual.csv"), float_format="%.5f")
    json.dump(res, open(os.path.join(OUT, "meses7_resumen.json"), "w"), indent=1, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main("--combos" in sys.argv)
