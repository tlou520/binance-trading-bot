"""Backtest de la estrategia de retrocesos con velas reales de 1 min de Binance spot (2023-01-01 a ayer).

Pasos:
1. Rejilla: cada combinación de señal (modo A/B/C, gatillo 1m/5m, tamaño del impulso, lado), salida (stop, objetivo,
   gestión, duración) y filtros (horario, noticias, BTC) se simula en las 6 monedas. Se guardan los resultados por año.
2. Walk-forward: para juzgar 2024 se elige la combinación con mejor t por día usando solo 2023; para 2025, con
   2023-2024; para 2026, con 2023-2025. Se juntan las operaciones de los tres años juzgados. Se hace por separado
   para solo largos (lo único que puede usar el bot en spot) y para largos o cortos.
3. Referencias: la lectura literal del video y entradas al azar con las mismas salidas.

Criterio para usarla (el mismo de extremos): en los años juzgados, ganancia media neta E > 0, n >= 100, t >= 2 y
t >= 2 contando cada día una sola vez.

Uso:
    python backtest.py               # todo (unos minutos con 4 núcleos)
    python backtest.py --hilos 2
Datos: velas de 1 min de descargar.py en v3_research/tmp/k1m/klines (o PULLBACK_DATA_DIR).
Salidas en output/: rejilla.csv, resumen.json, operaciones_*.csv.
"""
import argparse
import csv
import dataclasses
import datetime as dt
import itertools
import json
import math
import multiprocessing as mp
import os
import time

import numpy as np

import estrategia as E

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("PULLBACK_DATA_DIR", os.path.join(os.path.dirname(HERE), "v3_research", "tmp", "k1m", "klines"))
OUT = os.path.join(HERE, "output")
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT"]
YEARS = [2023, 2024, 2025, 2026]
FOLDS = [2024, 2025, 2026]
MIN_N_TRAIN = 60

SENALES = [E.Senal(m, tf, k, lado) for m, tf, k, lado in
           itertools.product("ABC", ["1m", "5m"], [2.0, 3.0], ["largo", "corto"])]
SALIDAS = [E.Salida(s, rr, g, h) for s, rr, g, h in
           itertools.product([None, 0.006, 0.012, 0.02], [1.0, 1.5, 2.0, 3.0], [False, True], [4, 24])]
FILTROS = [dict(sesion=s, noticias=n, btc=b) for s, n, b in itertools.product(["todo", "europa"], [False, True],
                                                                               [False, True])]
VIDEO = (dict(modos="ABC", tf="1m", k_imp=2.0), E.Salida(None, 1.0, True, 4), dict(sesion="europa", noticias=True,
                                                                                   btc=False))
MON = {}
NEWS = None
BTC_UP = None


def iso(ms):
    return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def year_of(ms):
    return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).year


def load_all():
    global NEWS, BTC_UP
    for s in COINS:
        p = os.path.join(DATA, f"{s}_1m.npy")
        a = np.load(p)
        d = {"T": a[:, 0].astype(np.int64), "O": a[:, 1], "H": a[:, 2], "L": a[:, 3], "C": a[:, 4]}
        MON[s] = E.Moneda(s, d)
    rows = list(csv.DictReader(open(os.path.join(HERE, "noticias.csv"))))
    NEWS = np.sort(np.array([int(dt.datetime.strptime(r["fecha_utc"], "%Y-%m-%d %H:%M")
                                 .replace(tzinfo=dt.timezone.utc).timestamp() * 1000) for r in rows], dtype=np.int64))
    h = MON["BTCUSDT"].vista("1h", "largo")
    BTC_UP = (h["T"], h["C"] > h["e50"])


# ---------------------------------------------------------------------------------------------------- tablas
def to_arrays(trades):
    if not trades:
        return None
    f = lambda k, dt_=np.float64: np.array([getattr(t, k) for t in trades], dtype=dt_)
    t_in = f("t_entrada", np.int64)
    coin = np.array([COINS.index(t.moneda) for t in trades])
    largo = np.array([t.lado == "largo" for t in trades])
    hour = (t_in // E.HOUR) % 24
    i = np.searchsorted(NEWS, t_in)
    nxt = np.where(i < len(NEWS), NEWS[np.minimum(i, len(NEWS) - 1)], np.iinfo(np.int64).max)
    prv = np.where(i > 0, NEWS[np.maximum(i - 1, 0)], np.iinfo(np.int64).min // 2)
    news = (nxt - t_in <= 30 * E.MIN) | (t_in - prv <= 60 * E.MIN)
    bi = np.searchsorted(BTC_UP[0] + E.HOUR, t_in, "right") - 1
    up = BTC_UP[1][np.maximum(bi, 0)]
    btc_ok = (coin == 0) | (up == largo)
    years = np.array([year_of(x) for x in t_in])
    return dict(t_in=t_in, ret=f("ret"), day=t_in // E.DAY, year=years, europa=(hour >= 6) & (hour < 16),
                news=news, btc_ok=btc_ok)


def mask(A, flt):
    m = np.ones(len(A["ret"]), bool)
    if flt["sesion"] == "europa":
        m &= A["europa"]
    if flt["noticias"]:
        m &= ~A["news"]
    if flt["btc"]:
        m &= A["btc_ok"]
    return m


def per_year(A, m):
    """Sumas aditivas por año: n, s1, s2 de las operaciones y de los promedios diarios."""
    out = {}
    for y in YEARS:
        k = m & (A["year"] == y)
        r = A["ret"][k]
        if not len(r):
            out[y] = (0, 0.0, 0.0, 0, 0.0, 0.0)
            continue
        u, inv = np.unique(A["day"][k], return_inverse=True)
        dm = np.bincount(inv, r) / np.bincount(inv)
        out[y] = (len(r), float(r.sum()), float((r * r).sum()), len(u), float(dm.sum()), float((dm * dm).sum()))
    return out


def comb(py, years):
    n, s1, s2, nd, d1, d2 = (sum(py[y][i] for y in years) for i in range(6))
    def t(n, s1, s2):
        if n < 2:
            return None
        v = (s2 - s1 * s1 / n) / (n - 1)
        return s1 / n / math.sqrt(v / n) if v > 0 else None
    return dict(n=n, e=s1 / n * 100 if n else None, t=t(n, s1, s2), dias=nd, t_dia=t(nd, d1, d2))


def stats(trades, riesgo=0.01):
    if not trades:
        return {"n": 0}
    r = np.array([t.ret for t in trades])
    n = len(r)
    by = {}
    for t in trades:
        by.setdefault(t.t_entrada // E.DAY, []).append(t.ret)
    dm = np.array([np.mean(v) for v in by.values()])
    tt = lambda a: float(a.mean() / (a.std(ddof=1) / math.sqrt(len(a)))) if len(a) > 1 and a.std(ddof=1) > 0 else None
    eq, peak, dd = 100.0, 100.0, 0.0
    for t in sorted(trades, key=lambda t: t.t_entrada):
        frac = min(riesgo / t.stop_pct, 1.0)          # spot: la posición no puede superar el saldo
        eq *= 1 + frac * t.ret
        peak = max(peak, eq)
        dd = max(dd, 1 - eq / peak)
    motivos = {}
    for t in trades:
        motivos[t.motivo] = motivos.get(t.motivo, 0) + 1
    return {"n": n, "acierto": round(float((r > 0).mean()), 3), "e": round(float(r.mean()) * 100, 3),
            "t": None if tt(r) is None else round(tt(r), 2), "dias": len(dm),
            "t_dia": None if tt(dm) is None else round(tt(dm), 2), "r_medio": round(float(np.mean([t.r_mult for t in trades])), 3),
            "saldo_100_usdt_riesgo_1pct": round(eq, 2), "caida_max_pct": round(dd * 100, 1), "motivos": motivos}


def by_year(trades):
    return {y: stats([t for t in trades if year_of(t.t_entrada) == y]) for y in YEARS}


def reglas_video(trades, max_dia=2, parar_r=2.0):
    """Una posición a la vez entre todas las monedas, máximo 2 por día y no operar más ese día tras ganar >= 2 R."""
    out, busy, cnt, rday = [], -1, {}, {}
    for t in sorted(trades, key=lambda t: t.t_entrada):
        d = t.t_entrada // E.DAY
        if t.t_entrada < busy or cnt.get(d, 0) >= max_dia or rday.get(d, 0) >= parar_r:
            continue
        out.append(t)
        busy = t.t_salida
        cnt[d] = cnt.get(d, 0) + 1
        rday[d] = rday.get(d, 0) + t.r_mult
    return out


# ---------------------------------------------------------------------------------------------------- rejilla
def trades_for(s: E.Senal, z: E.Salida, filtro=None):
    tr = []
    for c in COINS:
        tr += E.simular(MON[c], s, z)
    if filtro is None:
        return tr
    A = to_arrays(tr)
    if A is None:
        return []
    m = mask(A, filtro)
    return [t for t, k in zip(tr, m) if k]


def work(si):
    s = SENALES[si]
    rows = []
    for zi, z in enumerate(SALIDAS):
        tr = []
        for c in COINS:
            tr += E.simular(MON[c], s, z)
        A = to_arrays(tr)
        for fi, f in enumerate(FILTROS):
            py = per_year(A, mask(A, f)) if A is not None else {y: (0, 0, 0, 0, 0, 0) for y in YEARS}
            rows.append((si, zi, fi, py))
    return rows


def label(si, zi, fi):
    s, z, f = SENALES[si], SALIDAS[zi], FILTROS[fi]
    return dict(modo=s.modo, gatillo=s.tf, k_imp=s.k_imp, lado=s.lado,
                stop="video 0,15 %" if z.stop_min is None else f"min {z.stop_min * 100:.1f} %", rr=z.rr,
                gestion=z.gestion, horas=z.horas, sesion=f["sesion"], noticias=f["noticias"], btc=f["btc"])


def pick(rows, train, solo_largos):
    best, bk = None, -1e9
    for si, zi, fi, py in rows:
        if solo_largos and SENALES[si].lado != "largo":
            continue
        c = comb(py, train)
        if c["n"] < MIN_N_TRAIN or c["t_dia"] is None or c["e"] <= 0:
            continue
        if c["t_dia"] > bk:
            best, bk = (si, zi, fi), c["t_dia"]
    return best


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hilos", type=int, default=os.cpu_count())
    a = ap.parse_args(argv)
    t0 = time.time()
    load_all()
    print(f"Datos cargados ({time.time() - t0:.0f} s). Rejilla: {len(SENALES)} señales x {len(SALIDAS)} salidas x "
          f"{len(FILTROS)} filtros = {len(SENALES) * len(SALIDAS) * len(FILTROS)} combinaciones", flush=True)
    rows = []
    with mp.get_context("fork").Pool(a.hilos) as pool:
        for k, r in enumerate(pool.imap_unordered(work, range(len(SENALES))), 1):
            rows += r
            print(f"  señales {k}/{len(SENALES)} ({time.time() - t0:.0f} s)", flush=True)
    os.makedirs(OUT, exist_ok=True)

    # rejilla.csv
    with open(os.path.join(OUT, "rejilla.csv"), "w", newline="") as f:
        w = None
        for si, zi, fi, py in sorted(rows, key=lambda r: r[:3]):
            row = label(si, zi, fi)
            for y in YEARS:
                c = comb(py, [y])
                row[f"n_{y}"] = c["n"]
                row[f"e_{y}"] = None if c["e"] is None else round(c["e"], 3)
            c = comb(py, YEARS)
            row.update(n_total=c["n"], e_total=None if c["e"] is None else round(c["e"], 3),
                       t_total=None if c["t"] is None else round(c["t"], 2),
                       t_dia_total=None if c["t_dia"] is None else round(c["t_dia"], 2))
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(row))
                w.writeheader()
            w.writerow(row)

    res = {"periodo": f"{iso(MON['BTCUSDT'].raw['1m']['T'][0])} a {iso(MON['BTCUSDT'].raw['1m']['T'][-1])} UTC",
           "monedas": COINS, "costo_ida_vuelta_pct": E.COST * 100, "combinaciones": len(rows)}
    # cuántas combinaciones ganan en 2026 (para ver el riesgo de elegir mirando el resultado)
    pos26 = [r for r in rows if comb(r[3], [2026])["n"] >= 30 and comb(r[3], [2026])["e"] > 0]
    res["combinaciones_con_e_positivo_en_2026_n30"] = len(pos26)
    allpos = [r for r in rows if all(comb(r[3], [y])["n"] >= 20 and comb(r[3], [y])["e"] > 0 for y in YEARS)]
    res["combinaciones_positivas_los_4_anios_n20"] = [dict(label(*r[:3]), **{str(y): comb(r[3], [y]) for y in YEARS})
                                                     for r in allpos[:20]]

    # walk-forward
    rng = np.random.default_rng(7)
    for nombre, solo in (("solo_largos", True), ("largos_o_cortos", False)):
        bloques, oos = [], []
        for y in FOLDS:
            train = [x for x in YEARS if x < y]
            b = pick(rows, train, solo)
            if b is None:
                bloques.append({"anio": y, "elegida": None})
                continue
            si, zi, fi = b
            tr = [t for t in trades_for(SENALES[si], SALIDAS[zi], FILTROS[fi]) if year_of(t.t_entrada) == y]
            oos += tr
            bloques.append({"anio": y, "elegida": label(si, zi, fi), "entrenamiento": comb(rows_py(rows, b), train),
                            "resultado": stats(tr), "con_reglas_del_video": stats(reglas_video(tr))})
        az = []
        for bl, y in zip(bloques, FOLDS):
            if bl["elegida"] is None:
                continue
            tr = [t for t in oos if year_of(t.t_entrada) == y]
            si, zi, fi = pick(rows, [x for x in YEARS if x < y], solo)
            for c in COINS:
                az += E.aleatorio(MON[c], SENALES[si].tf, SENALES[si].lado, [t for t in tr if t.moneda == c],
                                  SALIDAS[zi], rng)
        res[f"walk_forward_{nombre}"] = {"bloques": bloques, "total": stats(oos), "por_anio": by_year(oos),
                                          "azar_mismas_salidas": stats(az)}
        write_trades(oos, f"operaciones_wf_{nombre}.csv")
        print(f"WF {nombre}: {res[f'walk_forward_{nombre}']['total']}", flush=True)

    # lectura literal del video: A, B y C juntos, gatillo 1 min, stop 0,15 %, 1:1, gestión, Europa, noticias,
    # una posición a la vez y máximo 2 por día
    sv, zv, fv = VIDEO
    tv = []
    for modo in sv["modos"]:
        for lado in ("largo", "corto"):
            tv += trades_for(E.Senal(modo, sv["tf"], sv["k_imp"], lado), zv, fv)
    tv = reglas_video(tv)
    res["video_literal"] = {"total": stats(tv, riesgo=0.10), "por_anio": by_year(tv)}
    write_trades(tv, "operaciones_video.csv")
    print(f"Video literal: {res['video_literal']['total']}", flush=True)

    with open(os.path.join(OUT, "resumen.json"), "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(f"Listo en {time.time() - t0:.0f} s. Resultados en {OUT}")


def rows_py(rows, key):
    for si, zi, fi, py in rows:
        if (si, zi, fi) == key:
            return py


def write_trades(trades, name):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["moneda", "modo", "lado", "senal_utc", "entrada_utc", "salida_utc", "entrada", "stop", "objetivo",
                    "salida", "stop_pct", "ret_neto_pct", "r", "motivo"])
        for t in sorted(trades, key=lambda t: t.t_entrada):
            w.writerow([t.moneda, t.modo, t.lado, iso(t.t_senal), iso(t.t_entrada), iso(t.t_salida), t.entrada, t.stop,
                        t.objetivo, t.salida, round(t.stop_pct * 100, 3), round(t.ret * 100, 3), round(t.r_mult, 3),
                        t.motivo])


if __name__ == "__main__":
    main()
