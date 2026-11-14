"""Pruebas: nada usa velas futuras y la contabilidad cuadra. Se saltan si no están las velas de 1 min."""
import os
import unittest

import numpy as np
import pandas as pd

import estrategias as E

HAY = os.path.exists(os.path.join(E.DATA, "BTCUSDT_1m.npy"))


@unittest.skipUnless(HAY, "sin velas de 1 min")
class SinMirarElFuturo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cut = pd.Timestamp("2025-03-10 07:23")           # corte a mitad de hora y de día
        cls.full = E.prepare({s: E.load(s) for s in E.COINS})
        cls.part = E.prepare({s: E.load(s, cls.cut) for s in E.COINS})

    def test_indicadores_no_cambian_al_cortar_datos(self):
        cols = E.FEATS + ["mom28", "rk28", "dema50", "ema20", "atr_abs"]
        for s in ("BTC", "SOL"):
            b = self.part[s][cols]
            a = self.full[s][cols].loc[b.index]
            np.testing.assert_allclose(a.values, b.values, rtol=1e-9, equal_nan=True)

    def test_operaciones_no_cambian_al_cortar_datos(self):
        lim = self.cut - pd.Timedelta(days=15)
        for f in (lambda P: E.strat3(P), lambda P: E.strat2(P)[0]):
            a = [(t[0], t[1], t[2], round(t[3], 10)) for t in f(self.full) if t[2] < lim]
            b = [(t[0], t[1], t[2], round(t[3], 10)) for t in f(self.part) if t[2] < lim]
            self.assertEqual(a, b)
            self.assertGreater(len(a), 0)

    def test_objetivo_empieza_despues_de_la_decision(self):
        h = self.full["ETH"]
        i = 5000
        self.assertAlmostEqual(h.y24.iloc[i], h.o.iloc[i + 1 + E.HOLD_ML] / h.o.iloc[i + 1] - 1)

    def test_e3_stop_y_costo(self):
        for s, t0, t1, r in E.strat3(self.full):
            self.assertGreater(t1, t0)
            self.assertGreater(r, -0.08 - E.COST - 0.25)     # la pérdida la limita el stop (salvo hueco)


class Contabilidad(unittest.TestCase):
    def test_mensual(self):
        t = [("BTC", pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-05"), 0.06),
             ("ETH", pd.Timestamp("2024-01-30"), pd.Timestamp("2024-02-01"), -0.03)]
        m = E.monthly_from_trades(t)
        self.assertAlmostEqual(m.iloc[0], 0.01)
        self.assertAlmostEqual(m.iloc[1], -0.005)
        w = pd.Series([0.1, 0.1], index=pd.to_datetime(["2024-03-04", "2024-03-11"]))
        self.assertAlmostEqual(E.monthly_from_weekly(w).iloc[0], 0.21)


if __name__ == "__main__":
    unittest.main()
