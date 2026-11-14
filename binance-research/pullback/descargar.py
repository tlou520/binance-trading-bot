"""Descarga velas spot de 1 min desde el archivo público de Binance (data.binance.vision), sin API key.

Meses completos con los ZIP mensuales y el mes en curso con los ZIP diarios, así los datos llegan hasta ayer.
Cada moneda queda en un .npy con columnas [open_time_ms, open, high, low, close, volume, taker_buy_volume].
Desde 2025 Binance publica los tiempos de spot en microsegundos; aquí se pasan a milisegundos.

Uso:
    python descargar.py                                   # 6 monedas del video, 2023-01 a ayer
    python descargar.py --monedas BTCUSDT --desde 2025-01
    python descargar.py --salida E:/datos/k1m

Por defecto guarda en v3_research/tmp/k1m/ (ignorado por git). Los ZIP ya descargados se reutilizan.
"""
import argparse
import datetime as dt
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "v3_research", "tmp", "k1m")
BASE = "https://data.binance.vision/data/spot"
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT"]
TF = "1m"


def months(start: str, end: str):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def fetch(url: str, path: str, tries: int = 4) -> bool:
    """Descarga a `path` si no existe. Devuelve False si el archivo no existe en el servidor (404)."""
    if os.path.exists(path):
        return True
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                data = r.read()
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            err = e
        except Exception as e:  # red: reintentar con espera creciente
            err = e
        time.sleep(2 ** (k + 1))
    raise RuntimeError(f"no se pudo descargar {url}: {err}")


def parse(path: str) -> np.ndarray:
    with zipfile.ZipFile(path) as z, z.open(z.namelist()[0]) as f:
        first = f.readline()
        skip = 0 if first[:1].isdigit() else 1          # algunos archivos traen cabecera
    with zipfile.ZipFile(path) as z, z.open(z.namelist()[0]) as f:
        a = np.loadtxt(f, delimiter=",", usecols=(0, 1, 2, 3, 4, 5, 9), skiprows=skip, dtype=np.float64, ndmin=2)
    us = a[:, 0] > 1e14                                 # microsegundos -> milisegundos
    a[us, 0] = np.floor(a[us, 0] / 1000)
    return a


def main(argv=None):
    today = dt.datetime.now(dt.timezone.utc).date()
    ap = argparse.ArgumentParser()
    ap.add_argument("--monedas", nargs="*", default=COINS)
    ap.add_argument("--desde", default="2023-01")
    ap.add_argument("--hasta", default=(today - dt.timedelta(days=1)).isoformat(), help="último día (AAAA-MM-DD)")
    ap.add_argument("--salida", default=DEFAULT_OUT)
    ap.add_argument("--hilos", type=int, default=8)
    a = ap.parse_args(argv)
    last = dt.date.fromisoformat(a.hasta)
    # meses completos: hasta el mes anterior al de `last`, salvo que `last` sea fin de mes
    eom = (last + dt.timedelta(days=1)).day == 1
    full_end = last if eom else last.replace(day=1) - dt.timedelta(days=1)
    zdir, kdir = os.path.join(a.salida, "zip"), os.path.join(a.salida, "klines")
    os.makedirs(zdir, exist_ok=True)
    os.makedirs(kdir, exist_ok=True)
    jobs = []
    for s in a.monedas:
        for y, m in months(a.desde, full_end.strftime("%Y-%m")):
            jobs.append((s, f"{BASE}/monthly/klines/{s}/{TF}/{s}-{TF}-{y:04d}-{m:02d}.zip",
                         os.path.join(zdir, f"{s}-{TF}-{y:04d}-{m:02d}.zip")))
        if not eom:
            d = last.replace(day=1)
            while d <= last:
                jobs.append((s, f"{BASE}/daily/klines/{s}/{TF}/{s}-{TF}-{d.isoformat()}.zip",
                             os.path.join(zdir, f"{s}-{TF}-{d.isoformat()}.zip")))
                d += dt.timedelta(days=1)
    print(f"{len(a.monedas)} monedas, {a.desde} a {last}: {len(jobs)} archivos", flush=True)

    t0 = time.time()
    got = {s: [] for s in a.monedas}
    with ThreadPoolExecutor(a.hilos) as ex:
        for i, ((s, _, p), ok) in enumerate(zip(jobs, ex.map(lambda j: fetch(j[1], j[2]), jobs)), 1):
            if ok:
                got[s].append(p)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} ({time.time() - t0:.0f} s)", flush=True)
    for s, paths in got.items():
        if not paths:
            print(f"{s}: sin datos", flush=True)
            continue
        k = np.vstack([parse(p) for p in sorted(paths)])
        k = k[np.argsort(k[:, 0], kind="stable")]
        k = k[np.r_[True, np.diff(k[:, 0]) > 0]]
        np.save(os.path.join(kdir, f"{s}_{TF}.npy"), k)
        d0 = dt.datetime.fromtimestamp(k[0, 0] / 1000, dt.timezone.utc)
        d1 = dt.datetime.fromtimestamp(k[-1, 0] / 1000, dt.timezone.utc)
        print(f"{s}: {len(k)} velas de 1 min, {d0:%Y-%m-%d} a {d1:%Y-%m-%d %H:%M}", flush=True)
    print(f"Listo en {time.time() - t0:.0f} s. Carpeta: {kdir}")


if __name__ == "__main__":
    sys.exit(main())
