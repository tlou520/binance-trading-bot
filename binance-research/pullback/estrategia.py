"""Estrategia de retrocesos del video "150 dólares en una semana": dirección en 1 h, estructura en 5 min, gatillo en 1 min.

Reglas (todas con datos ya cerrados en el momento de decidir; la entrada es en la apertura de la vela siguiente):

1. Dirección en 1 h (vale mientras se cumple, o 3 horas en el caso B):
   A. Tendencia: cierre de 1 h al lado bueno de la EMA 50, EMA 50 a favor en las últimas 3 horas y los dos últimos
      mínimos de 1 h confirmados son crecientes (para cortos: máximos decrecientes).
   B. Reversión a la EMA 50: una vela de 1 h ataca muy rápido un soporte (caída de >= 3 ATR desde el máximo de las
      6 horas anteriores hasta un mínimo previo confirmado de los últimos 30 días), deja mecha inferior >= 40 % de la
      vela ("low test") y cierra por encima del soporte, con el precio aún >= 0,5 ATR por debajo de la EMA 50.
      El objetivo es la EMA 50 de 1 h.
   C. Rango: las últimas 24 horas caben en 2 a 6 ATR de 1 h y el precio está en el 30 % inferior del rango. El
      objetivo es la parte alta del rango menos el 15 % de su ancho.
2. Estructura en 5 min: en las últimas 2 horas hubo un impulso (máximo de la ventana a >= k_imp ATR de 5 min sobre el
   mínimo de las 2 horas anteriores, con al menos una vela de cuerpo >= 1 ATR) y luego un retroceso de entre el 30 % y
   el 70 % del impulso que no perdió el inicio del impulso. El precio aún está por debajo del máximo del impulso.
3. Gatillo (1 min o 5 min): el cierre supera el máximo de las 3 velas anteriores y la EMA 50 de esa temporalidad.
   Una sola entrada por impulso.
4. Stop: debajo del mínimo del retroceso (0,1 ATR de 5 min de margen), con una distancia mínima `stop_min` y una
   máxima del 2,5 % (si el stop queda más lejos, no se entra). Con `stop_min=None` se usa el stop fijo del video, 0,15 % bajo la entrada.
5. Objetivo: A = rr veces el riesgo; B = EMA 50 de 1 h; C = parte alta del rango. En B y C se exige que el objetivo
   esté a >= rr veces el riesgo.
6. Gestión (gestion=True): al avanzar 0,6 R el stop pasa a la entrada más los costos; si en 30 min el precio no avanzó
   0,3 R, se sale al cierre ("se atascó"). Siempre: salida al cierre a las `horas` horas (4 por defecto).
   Si una vela toca stop y objetivo a la vez se cuenta stop.

Los cortos se calculan con los precios en negativo (un corto es un largo sobre -precio), así las reglas son las mismas.
"""
import dataclasses

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv
from scipy.signal import lfilter

MIN = 60_000
HOUR = 60 * MIN
DAY = 24 * HOUR
COST = 0.0024            # comisión 0,1 % por lado + deslizamiento 0,02 % por lado
VIDEO_STOP = 0.0015


@dataclasses.dataclass(frozen=True)
class Senal:
    modo: str = "A"          # A tendencia, B reversión a la EMA 50, C rango
    tf: str = "1m"           # temporalidad del gatillo: 1m o 5m
    k_imp: float = 2.0       # tamaño mínimo del impulso de 5 min en ATR
    lado: str = "largo"      # largo o corto


@dataclasses.dataclass(frozen=True)
class Salida:
    stop_min: float = None   # None = stop fijo del video (0,15 %)
    rr: float = 1.0
    gestion: bool = False
    horas: int = 4           # duración máxima; al cumplirse se sale al cierre


@dataclasses.dataclass
class Trade:
    moneda: str
    modo: str
    lado: str
    t_senal: int
    t_entrada: int
    t_salida: int
    entrada: float
    stop: float
    objetivo: float
    salida: float
    stop_pct: float
    ret: float               # neto de costos, en fracción
    r_mult: float            # bruto, en múltiplos del riesgo
    motivo: str


# ---------------------------------------------------------------------------------------------------- utilidades
def ema(x: np.ndarray, n: int) -> np.ndarray:
    a = 2.0 / (n + 1)
    y, _ = lfilter([a], [1, a - 1], x, zi=[(1 - a) * x[0]])
    return y


def atr(d: dict, n: int = 14) -> np.ndarray:
    pc = np.r_[d["C"][0], d["C"][:-1]]
    tr = np.maximum(d["H"] - d["L"], np.maximum(abs(d["H"] - pc), abs(d["L"] - pc)))
    a = 1.0 / n                                   # media de Wilder
    y, _ = lfilter([a], [1, a - 1], tr, zi=[(1 - a) * tr[0]])
    return y


def resample(d: dict, ms: int) -> dict:
    k = d["T"] // ms * ms
    s = np.r_[0, np.flatnonzero(np.diff(k)) + 1]
    e = np.r_[s[1:] - 1, len(k) - 1]
    return {"T": k[s], "O": d["O"][s], "H": np.maximum.reduceat(d["H"], s), "L": np.minimum.reduceat(d["L"], s),
            "C": d["C"][e]}


def neg(d: dict) -> dict:
    """Vista para cortos: precios en negativo, con máximo y mínimo intercambiados."""
    return {"T": d["T"], "O": -d["O"], "H": -d["L"], "L": -d["H"], "C": -d["C"]}


def last_closed(T_open: np.ndarray, ms: int, t: np.ndarray) -> np.ndarray:
    """Índice de la última vela (de duración ms) ya cerrada en el instante t; -1 si ninguna."""
    return np.searchsorted(T_open + ms, t, "right") - 1


def roll(x: np.ndarray, w: int, f, fill) -> np.ndarray:
    """f sobre la ventana [i-w+1, i]; las primeras w-1 posiciones usan `fill` como relleno."""
    p = np.r_[np.full(w - 1, fill), x]
    return f(swv(p, w), axis=1)


def pivot_lows(L: np.ndarray, n: int) -> np.ndarray:
    w = swv(np.r_[np.full(n, np.inf), L, np.full(n, np.inf)], 2 * n + 1)
    return np.flatnonzero(L == w.min(axis=1))


# ---------------------------------------------------------------------------------------------------- por moneda
class Moneda:
    """Velas de 1 min de una moneda y todo lo derivado (5 min, 1 h, indicadores), por lado."""

    def __init__(self, simbolo: str, d1: dict, btc: "Moneda" = None):
        self.simbolo = simbolo
        self.raw = {"1m": d1, "5m": resample(d1, 5 * MIN), "1h": resample(d1, HOUR)}
        self.btc = btc
        self._c = {}

    def vista(self, tf: str, lado: str) -> dict:
        k = ("v", tf, lado)
        if k not in self._c:
            d = self.raw[tf] if lado == "largo" else neg(self.raw[tf])
            self._c[k] = dict(d, e50=ema(d["C"], 50), atr=atr(d))
        return self._c[k]

    # ------------------------------------------------------------------ 1 h
    def dir_1h(self, modo: str, lado: str):
        """(ok[h], objetivo[h]) para cada vela de 1 h cerrada h."""
        k = ("d", modo, lado)
        if k in self._c:
            return self._c[k]
        h = self.vista("1h", lado)
        n = len(h["C"])
        O, H, L, C, e, a = h["O"], h["H"], h["L"], h["C"], h["e50"], h["atr"]
        tgt = np.full(n, np.nan)
        if modo == "A":
            piv = pivot_lows(L, 3)
            cnt = np.searchsorted(piv + 3, np.arange(n), "right")
            p1 = piv[np.maximum(cnt - 1, 0)]
            p0 = piv[np.maximum(cnt - 2, 0)]
            hl = (cnt >= 2) & (L[p1] > L[p0])
            ok = (C > e) & (e > np.r_[np.full(3, np.inf), e[:-3]]) & hl
        elif modo == "B":
            piv = pivot_lows(L, 3)
            rng = np.maximum(H - L, 1e-12)
            wick = (np.minimum(O, C) - L) / rng
            prev_hi = roll(np.r_[-np.inf, H[:-1]], 6, np.max, -np.inf)
            cand = np.flatnonzero((wick >= 0.4) & (prev_hi - L >= 3 * a) & (C <= e - 0.5 * a))
            ev = np.zeros(n, bool)
            for i in cand:
                tol = 0.5 * a[i]
                pv = piv[(piv + 3 <= i - 6) & (piv >= i - 720)]
                if len(pv) and np.any((abs(L[pv] - L[i]) <= tol) & (C[i] >= L[pv] - tol)):
                    ev[i] = True
            ok = ev | np.r_[False, ev[:-1]] | np.r_[False, False, ev[:-2]]
            tgt = e.copy()
        elif modo == "C":
            hi = roll(H, 24, np.max, np.nan)
            lo = roll(L, 24, np.min, np.nan)
            wd = hi - lo
            ok = (wd >= 2 * a) & (wd <= 6 * a) & ((C - lo) / np.maximum(wd, 1e-12) <= 0.3)
            tgt = hi - 0.15 * wd
        else:
            raise ValueError(modo)
        self._c[k] = (np.nan_to_num(ok, nan=0).astype(bool), tgt)
        return self._c[k]

    # ------------------------------------------------------------------ 5 min
    def estructura_5m(self, k_imp: float, lado: str):
        k = ("e", k_imp, lado)
        if k in self._c:
            return self._c[k]
        m = self.vista("5m", lado)
        O, H, L, C, a = m["O"], m["H"], m["L"], m["C"], m["atr"]
        n, W, Lb = len(C), 24, 24
        idx = np.arange(n)
        wh = swv(np.r_[np.full(W - 1, -np.inf), H], W)
        am = wh.argmax(axis=1)
        ih = idx - (W - 1) + am                                   # índice del máximo del impulso
        wl = swv(np.r_[np.full(W - 1, np.inf), L], W)
        pos = np.arange(W)[None, :]
        pl = np.where(pos > am[:, None], wl, np.inf).min(axis=1)  # mínimo del retroceso (después del máximo)
        ihc = np.maximum(ih, 0)
        leg_lo = roll(L, Lb + 1, np.min, np.inf)[ihc]
        body = roll(C - O, Lb + 1, np.max, -np.inf)[ihc]
        hi = H[ihc]
        imp = hi - leg_lo
        depth = (hi - pl) / np.maximum(imp, 1e-12)
        ok = ((ih >= Lb) & (idx - ih >= 1) & (imp >= k_imp * a) & (body >= a) & (depth >= 0.3) & (depth <= 0.7)
              & (C < hi))
        self._c[k] = (ok, ihc, pl, hi)
        return self._c[k]

    # ------------------------------------------------------------------ señales
    def senales(self, s: Senal):
        """Candidatos: índice j de la vela de gatillo y datos de la estructura. Sin filtros ni salidas."""
        k = ("s", s)
        if k in self._c:
            return self._c[k]
        x = self.vista(s.tf, s.lado)
        bms = MIN if s.tf == "1m" else 5 * MIN
        tclose = x["T"] + bms
        k5 = last_closed(self.raw["5m"]["T"], 5 * MIN, tclose)
        h1 = last_closed(self.raw["1h"]["T"], HOUR, tclose)
        ok5, ih5, pl5, hi5 = self.estructura_5m(s.k_imp, s.lado)
        okh, tgth = self.dir_1h(s.modo, s.lado)
        k5c, h1c = np.maximum(k5, 0), np.maximum(h1, 0)
        prev3 = roll(np.r_[-np.inf, x["H"][:-1]], 3, np.max, -np.inf)
        cond = ((k5 >= 0) & (h1 >= 0) & ok5[k5c] & okh[h1c] & (x["C"] > prev3) & (x["C"] > x["e50"])
                & (x["C"] < hi5[k5c]))
        cond[-1] = False
        j = np.flatnonzero(cond)
        key = ih5[k5c[j]]
        _, first = np.unique(key, return_index=True)            # una entrada por impulso
        j = np.sort(j[first])
        low3 = roll(x["L"], 4, np.min, np.inf)[j]
        a5 = self.vista("5m", s.lado)["atr"][k5c[j]]
        stop = np.minimum(pl5[k5c[j]], low3) - 0.1 * a5
        out = dict(j=j, stop=stop, tgt=tgth[h1c[j]], t=x["T"][j + 1], hi5=hi5[k5c[j]])
        self._c[k] = out
        return out


def salida(x: dict, a: int, ent: float, stop: float, tp: float, z: Salida, bms: int):
    """Recorre las velas desde la de entrada `a`. Devuelve (índice de salida relativo, precio, motivo)."""
    O, H, L, C = x["O"], x["H"], x["L"], x["C"]
    b = min(a + z.horas * HOUR // bms, len(C))
    ns = 30 * MIN // bms
    dist = ent - stop
    Hw, Lw = H[a:b], L[a:b]
    hs, ht = Lw <= stop, Hw >= tp
    iS = int(hs.argmax()) if hs.any() else len(Hw)
    iT = int(ht.argmax()) if ht.any() else len(Hw)
    sp = stop
    if z.gestion:
        hb = Hw >= ent + 0.6 * dist
        ib = int(hb.argmax()) if hb.any() else len(Hw)
        if ib < min(iS, iT) and ib + 1 < len(Hw):
            be = ent + COST * abs(ent)
            h2 = Lw[ib + 1:] <= be
            if h2.any():
                i2 = ib + 1 + int(h2.argmax())
                if i2 < iS:
                    iS, sp = i2, be
    if min(iS, iT) >= len(Hw):
        xi, px, motivo = len(Hw) - 1, C[b - 1], "tiempo"
    elif iS <= iT:                                   # stop y objetivo en la misma vela: se cuenta stop
        xi, px, motivo = iS, min(O[a + iS], sp), ("stop" if sp == stop else "equilibrio")
    else:
        xi, px, motivo = iT, max(O[a + iT], tp), "objetivo"
    if z.gestion and xi >= ns and Hw[:ns].max() < ent + 0.3 * dist:
        xi, px, motivo = ns - 1, C[a + ns - 1], "atasco"
    return xi, px, motivo


def _trade(mon, modo, lado, x, j, a, xi, ent, stop, tp, px, motivo, bms):
    sgn = 1 if lado == "largo" else -1
    dist = ent - stop
    return Trade(mon.simbolo, modo, lado, int(x["T"][j]), int(x["T"][a]), int(x["T"][a + xi] + bms), sgn * ent,
                 sgn * stop, sgn * tp, sgn * px, dist / abs(ent), (px - ent) / abs(ent) - COST, (px - ent) / dist,
                 motivo)


def simular(mon: Moneda, s: Senal, z: Salida) -> list:
    """Simula cada candidato por su cuenta; en una misma moneda no se abre otra mientras hay una abierta."""
    c = mon.senales(s)
    x = mon.vista(s.tf, s.lado)
    bms = MIN if s.tf == "1m" else 5 * MIN
    out, busy = [], -1
    for j, st, tg in zip(c["j"], c["stop"], c["tgt"]):
        a = j + 1
        if a <= busy:
            continue
        ent = x["O"][a]
        stop = ent - VIDEO_STOP * abs(ent) if z.stop_min is None else min(st, ent - z.stop_min * abs(ent))
        dist = ent - stop
        if dist <= 0 or dist / abs(ent) > 0.025:
            continue
        if s.modo == "A":
            tp = ent + z.rr * dist
        else:
            tp = tg
            if not np.isfinite(tp) or tp - ent < z.rr * dist:
                continue
        xi, px, motivo = salida(x, a, ent, stop, tp, z, bms)
        busy = a + xi
        out.append(_trade(mon, s.modo, s.lado, x, j, a, xi, ent, stop, tp, px, motivo, bms))
    return out


def aleatorio(mon: Moneda, tf: str, lado: str, trades: list, z: Salida, rng: np.random.Generator) -> list:
    """Referencia: por cada operación real, una entrada en un minuto al azar del mismo mes, con el mismo stop en %
    y objetivo a rr veces el riesgo. Mide qué parte del resultado se debe solo a las reglas de salida."""
    x = mon.vista(tf, lado)
    bms = MIN if tf == "1m" else 5 * MIN
    T = x["T"]
    out = []
    for t in trades:
        m0 = (t.t_entrada // (30 * DAY)) * 30 * DAY
        lo, hi = np.searchsorted(T, m0), np.searchsorted(T, m0 + 30 * DAY) - 1
        if hi - lo < 10:
            continue
        a = int(rng.integers(lo + 1, hi))
        ent = x["O"][a]
        stop = ent - t.stop_pct * abs(ent)
        tp = ent + max(z.rr, abs(t.objetivo - t.entrada) / max(abs(t.entrada - t.stop), 1e-12)) * (ent - stop)
        xi, px, motivo = salida(x, a, ent, stop, tp, z, bms)
        out.append(_trade(mon, "azar", lado, x, a - 1, a, xi, ent, stop, tp, px, motivo, bms))
    return out
