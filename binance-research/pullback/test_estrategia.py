"""Pruebas de la estrategia de retrocesos. Las de datos reales se saltan si no se descargaron las velas de 1 min."""
import os
import unittest

import numpy as np

import estrategia as E

DATA = os.environ.get("PULLBACK_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                        "v3_research", "tmp", "k1m", "klines"))


def synth(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + abs(rng.normal(0, 0.0005, n)))
    l = np.minimum(o, c) * (1 - abs(rng.normal(0, 0.0005, n)))
    t = np.arange(n, dtype=np.int64) * E.MIN + 1_700_000_000_000 // E.HOUR * E.HOUR
    return {"T": t, "O": o, "H": h, "L": l, "C": c}


def load(sym, end_ms=None):
    a = np.load(os.path.join(DATA, f"{sym}_1m.npy"))
    if end_ms is not None:
        a = a[a[:, 0] < end_ms]
    return {"T": a[:, 0].astype(np.int64), "O": a[:, 1], "H": a[:, 2], "L": a[:, 3], "C": a[:, 4]}


class Basicas(unittest.TestCase):
    def test_resample(self):
        d = synth(600)
        m = E.resample(d, 5 * E.MIN)
        self.assertEqual(len(m["T"]), 120)
        self.assertEqual(m["O"][3], d["O"][15])
        self.assertEqual(m["C"][3], d["C"][19])
        self.assertEqual(m["H"][3], d["H"][15:20].max())
        self.assertEqual(m["L"][3], d["L"][15:20].min())

    def test_ema(self):
        x = np.arange(1.0, 60.0)
        y = E.ema(x, 9)
        a, ref = 2 / 10, [x[0]]
        for v in x[1:]:
            ref.append(a * v + (1 - a) * ref[-1])
        np.testing.assert_allclose(y, ref)

    def test_last_closed(self):
        T = np.array([0, 300_000, 600_000])
        # una vela de 5 min que abre en 300000 cierra en 600000
        self.assertEqual(list(E.last_closed(T, 300_000, np.array([299_999, 300_000, 599_999, 600_000]))), [-1, 0, 0, 1])

    def test_salida_stop_primero(self):
        x = {"O": np.array([100, 100.0]), "H": np.array([102, 100.0]), "L": np.array([98, 100.0]),
             "C": np.array([100, 100.0])}
        xi, px, motivo = E.salida(x, 0, 100.0, 99.0, 101.0, E.Salida(0.01, 1.0, False, 4), E.MIN)
        self.assertEqual((xi, px, motivo), (0, 99.0, "stop"))       # toca ambos en la misma vela: stop

    def test_corto_simetrico(self):
        d = synth(20000, 3)
        m = E.Moneda("X", d)
        z = E.Salida(0.004, 1.5, True, 4)
        largos = E.simular(m, E.Senal("A", "1m", 2.0, "largo"), z)
        cortos = E.simular(m, E.Senal("A", "1m", 2.0, "corto"), z)
        # stop y objetivo del lado correcto en cada caso
        for t in cortos:
            self.assertGreater(t.stop, t.entrada)
            self.assertLess(t.objetivo, t.entrada)
        for t in largos:
            self.assertLess(t.stop, t.entrada)
            self.assertGreater(t.objetivo, t.entrada)
        self.assertTrue(len(largos) + len(cortos) > 0)


@unittest.skipUnless(os.path.exists(os.path.join(DATA, "ETHUSDT_1m.npy")), "sin velas de 1 min")
class SinMirarElFuturo(unittest.TestCase):
    def test_senales_no_cambian_al_cortar_datos(self):
        full = load("ETHUSDT")
        cut = int(full["T"][len(full["T"]) - 200_000])           # cortar ~140 días antes del final
        part = {k: v[full["T"] < cut] for k, v in full.items()}
        for modo in "ABC":
            for tf in ("1m", "5m"):
                for lado in ("largo", "corto"):
                    s = E.Senal(modo, tf, 2.0, lado)
                    a = E.Moneda("ETH", full).senales(s)
                    b = E.Moneda("ETH", part).senales(s)
                    # comparar solo señales cuya entrada queda claramente antes del corte
                    lim = cut - 2 * E.DAY
                    ka, kb = a["t"] < lim, b["t"] < lim
                    np.testing.assert_array_equal(a["t"][ka], b["t"][kb], err_msg=f"{modo} {tf} {lado}")
                    np.testing.assert_allclose(a["stop"][ka], b["stop"][kb])

    def test_operaciones_no_cambian_al_cortar_datos(self):
        full = load("SOLUSDT")
        cut = int(full["T"][len(full["T"]) - 300_000])
        part = {k: v[full["T"] < cut] for k, v in full.items()}
        for s, z in [(E.Senal("A", "1m", 2.0, "largo"), E.Salida(0.012, 2.0, True, 24)),
                     (E.Senal("B", "5m", 2.0, "corto"), E.Salida(0.006, 1.0, False, 4))]:
            a = [t for t in E.simular(E.Moneda("SOL", full), s, z) if t.t_salida < cut - E.DAY]
            b = [t for t in E.simular(E.Moneda("SOL", part), s, z) if t.t_salida < cut - E.DAY]
            self.assertEqual([(t.t_entrada, t.t_salida, round(t.ret, 12)) for t in a],
                             [(t.t_entrada, t.t_salida, round(t.ret, 12)) for t in b])


if __name__ == "__main__":
    unittest.main()
