"""Gráficos del resumen ilustrado (doc/resumen-ilustrado.md). Uso: python graficos.py (después de meses6.py y meses9.py).

Comparan la estrategia vigente (2d+3e+11b de meses9) con la versión final anterior (7e de meses8, la base de
meses9). Las versiones más viejas aparecen solo como «Otras»."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
IMG = os.path.join(os.path.dirname(os.path.dirname(HERE)), "doc", "img")
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
GREY = "#b9b7b0"
N_NEW, N_FIN, N_OLD, N_BTC = "2d+3e+11b (vigente)", "Versión final (base)", "Otras", "Comprar y mantener BTC"
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e6e5e0"
MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 11,
                     "axes.titlelocation": "left"})


def pct(v, d=1):
    return f"{v:+.{d}f} %".replace(".", ",").replace("-", "−")


def load():
    m = pd.read_csv(os.path.join(OUT, "meses6_mensual.csv"), index_col=0)
    m9 = pd.read_csv(os.path.join(OUT, "meses9_mensual.csv"), index_col=0)
    m["final"], m["nueva"] = m9["base"], m9["2d+3e+11b"]    # base de meses9 = 7e de meses8; vigente = 2d+3e+11b
    import estrategias as E
    from mejoras import DATA20
    h = E.load("BTC", None, "2022-12-01", DATA20)          # comprar y mantener BTC, desde la apertura de 2023
    c = h.c.groupby(h.index.to_period("M")).last()
    btc = c.pct_change().dropna()
    btc.index = btc.index.astype(str)
    d = pd.DataFrame({"nueva": m["nueva"], "final": m["final"], "otras": m["base"], "btc": btc.reindex(m.index).fillna(0.0)})
    return d[d.index >= "2023-01"]


def evolucion():
    # etapa: (ganancia 2026 %, meses positivos 2026, caída máxima %) tomados de doc/estrategias-multimarco.md
    st = [("Otras · etapa 1", -27.6, 4, -31.1), ("Otras · etapa 2", 4.7, 2, -22.6), ("Otras · etapa 3", 6.6, 3, -14.4),
          ("Otras · etapa 4", 5.9, 3, -6.1), ("Otras · etapa 5", 13.2, 5, -5.4), ("Otras · etapa 6", 19.6, 5, -5.4),
          ("Otras · etapa 7", 21.4, 7, -5.4), ("Versión final (base)\netapa 8", 22.1, 7, -3.5),
          ("2d+3e+11b (vigente)\netapa 9", 26.2, 7, -3.5)]
    fig, ax = plt.subplots(1, 3, figsize=(12, 5.2), sharey=True)
    y = np.arange(len(st))[::-1]
    for a, (k, title, fmt) in zip(ax, ((1, "Ganancia de 2026", lambda v: pct(v)),
                                       (2, "Meses positivos de 2026 (de 11)", lambda v: str(v)),
                                       (3, "Caída máxima", lambda v: pct(v)))):
        v = [s[k] for s in st]
        col = [BLUE if i == len(st) - 1 else ORANGE if i == len(st) - 2 else GREY for i in range(len(st))]
        a.barh(y, v, height=0.62, color=col)
        a.axvline(0, color=MUTED, lw=0.8)
        span = max(abs(min(v)), abs(max(v)))
        for yi, vi in zip(y, v):
            a.text(vi + (0.03 * span if vi >= 0 else -0.03 * span), yi, fmt(vi), va="center",
                   ha="left" if vi >= 0 else "right", color=INK, fontsize=9.5)
        a.set_title(title)
        a.set_xlim(min(0, min(v)) - 0.45 * span, max(0, max(v)) + 0.32 * span)
        a.set_xticks([])
        a.spines["bottom"].set_visible(False)
        a.spines["left"].set_visible(False)
        a.tick_params(length=0)
    ax[0].set_yticks(y, [s[0] for s in st], color=INK2)
    ax[0].tick_params(axis="y", pad=14)
    fig.suptitle("De las versiones anteriores a la estrategia vigente", x=0.01, ha="left", fontweight="bold", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(IMG, "mt-evolucion.png"), dpi=160)


def meses_2026(d):
    m = 100 * d.loc[d.index >= "2026-01", ["final", "nueva"]]
    x = np.arange(len(m))
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    w = 0.42
    ax.bar(x - w / 2 - 0.01, m.final, w, color=ORANGE, label=N_FIN)
    ax.bar(x + w / 2 + 0.01, m.nueva, w, color=BLUE, label=N_NEW)
    ax.axhline(0, color=MUTED, lw=0.8)
    for xi, (a, b) in enumerate(zip(m.final, m.nueva)):
        for dx, v in ((-w / 2, a), (w / 2, b)):
            if abs(v) > 0.005:
                ax.text(xi + dx, v + (0.5 if v >= 0 else -0.5), f"{v:+.2f}".replace(".", ",").replace("-", "−"),
                        ha="center", va="bottom" if v >= 0 else "top", fontsize=7, color=INK2)
    ax.set_xticks(x, MES[:len(m)], color=INK2)
    ax.set_ylabel("Ganancia del mes (% de la cuenta)")
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_ylim(m.values.min() - 2.5, m.values.max() + 3)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("2026 mes a mes: versión final (base) y 2d+3e+11b")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "mt-meses-2026.png"), dpi=160)


def mapa(d):
    g = (100 * d.nueva).to_frame("v")
    g["a"], g["m"] = [int(i[:4]) for i in g.index], [int(i[5:7]) for i in g.index]
    t = g.pivot(index="a", columns="m", values="v").reindex(columns=range(1, 13))
    cmap = LinearSegmentedColormap.from_list("div", [RED, "#f0efec", BLUE])
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.imshow(t.values, cmap=cmap, vmin=-12, vmax=12, aspect="auto")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            v = t.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, "0" if abs(v) < 0.005 else f"{v:+.{2 if abs(v) < 0.05 else 1}f}".replace(".", ",").replace("-", "−"),
                        ha="center", va="center", fontsize=9, color="#ffffff" if abs(v) > 7 else INK)
    ax.set_xticks(range(12), MES, color=INK2)
    ax.set_yticks(range(len(t)), t.index, color=INK2)
    ax.set_xticks(np.arange(-0.5, 12), minor=True)
    ax.set_yticks(np.arange(-0.5, len(t)), minor=True)
    ax.grid(which="minor", color=SURF, lw=2)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("2d+3e+11b: ganancia de cada mes (% de la cuenta). Azul gana, rojo pierde, 0 es un mes sin operar")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "mt-mapa-meses.png"), dpi=160)


def capital(d):
    eq = 100 * (1 + d).cumprod()
    x = pd.PeriodIndex(eq.index, freq="M").to_timestamp(how="end")
    fig, ax = plt.subplots(figsize=(11, 4.6))
    for k, c, n in (("btc", AQUA, N_BTC), ("otras", GREY, N_OLD), ("final", ORANGE, N_FIN), ("nueva", BLUE, N_NEW)):
        ax.plot(x, eq[k], color=c, lw=2, label=n)
        ax.text(x[-1] + pd.Timedelta(days=12), eq[k].iloc[-1] * {"nueva": 1.16, "final": 0.99, "otras": 1.04, "btc": 0.9}.get(k, 1.0),
                f"{n}: {eq[k].iloc[-1]:,.0f} USDT".replace(",", "."), va="center", fontsize=9, color=INK2)
    ax.set_yscale("log")
    ax.set_yticks([100, 200, 300, 500, 700], ["100", "200", "300", "500", "700"])
    ax.minorticks_off()
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_xlim(x[0], x[-1] + pd.Timedelta(days=400))
    ax.set_xticks(pd.to_datetime([f"{a}-01-01" for a in (2023, 2024, 2025, 2026)]), ["2023", "2024", "2025", "2026"])
    ax.set_ylabel("Capital (USDT, escala logarítmica)")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("100 USDT desde enero de 2023 (backtest, después de costos)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "mt-capital.png"), dpi=160)
    dd = 100 * (eq / eq.cummax() - 1)
    fig, ax = plt.subplots(figsize=(11, 3.4))
    for k, c, n in (("btc", AQUA, N_BTC), ("otras", GREY, N_OLD), ("final", ORANGE, N_FIN), ("nueva", BLUE, N_NEW)):
        ax.plot(x, dd[k], color=c, lw=2, label=n)
        ax.text(x[-1] + pd.Timedelta(days=12), dd[k].iloc[-1] + {"nueva": 5.0, "final": 0.5, "otras": -4.0}.get(k, 0.0),
                f"{n}: peor {pct(dd[k].min())}", va="center", fontsize=9, color=INK2)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_xlim(x[0], x[-1] + pd.Timedelta(days=400))
    ax.set_xticks(pd.to_datetime([f"{a}-01-01" for a in (2023, 2024, 2025, 2026)]), ["2023", "2024", "2025", "2026"])
    ax.set_ylabel("Caída desde el máximo (%)")
    ax.set_title("Caída desde el máximo anterior, medida a fin de mes")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "mt-caida.png"), dpi=160)


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    d = load()
    evolucion()
    meses_2026(d)
    mapa(d)
    capital(d)
    yr = lambda c: {a: round(100 * ((1 + d[c][[i.startswith(str(a)) for i in d.index]]).prod() - 1), 2) for a in (2023, 2024, 2025, 2026)}
    dd = (1 + d).cumprod()
    print("caída máxima:", (100 * (dd / dd.cummax() - 1).min()).round(2).to_dict())
    for c in d.columns:
        print(c, yr(c), "total", round(100 * ((1 + d[c]).prod() - 1), 1), "meses positivos", int((d[c] > 0).sum()), "de", len(d))
