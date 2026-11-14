# Estrategia de retrocesos (video "150 dólares en una semana")

Backtest de la estrategia de *scalping* del video: dirección en 1 h, estructura de impulso y retroceso en 5 min y
gatillo en 1 min, con velas reales de Binance spot. Proyecto aparte: no usa ni modifica las estrategias del bot.
Explicación y resultados: [`doc/referencia-compacta.md`](../../doc/referencia-compacta.md).

| Archivo | Qué hace |
|---|---|
| `descargar.py` | Descarga velas de 1 min de `data.binance.vision` (sin API key): ZIP mensuales y, para el mes en curso, diarios |
| `noticias.csv` | Calendario de noticias: FOMC (fechas oficiales de federalreserve.gov) y empleo de EE. UU. (primer viernes del mes, 8:30 de Nueva York; aproximado) |
| `estrategia.py` | Las reglas: dirección en 1 h (A tendencia, B reversión a la EMA 50, C rango), estructura en 5 min, gatillo, stop, objetivo y gestión |
| `backtest.py` | Rejilla de 12.288 combinaciones, walk-forward por años, lectura literal del video y entradas al azar |
| `test_estrategia.py` | Pruebas: agregación de velas, EMA, velas cerradas, stop antes que objetivo, lados y que nada use velas futuras |

## Cómo correrlo en local

Desde esta carpeta, con el `.venv` del proyecto activado (necesita `numpy` y `scipy`):

```
cd binance-research/pullback
python descargar.py
python -m unittest test_estrategia
python backtest.py
```

- `descargar.py` baja unos 350 ZIP (6 monedas, 2023-01 a ayer) y deja unos 670 MB de `.npy` en
  `v3_research/tmp/k1m/klines/`. Para guardarlo en el disco E: `python descargar.py --salida E:/datos/k1m` y luego
  `set PULLBACK_DATA_DIR=E:/datos/k1m/klines` antes de las pruebas y el backtest. Si la descarga falla con la VPN
  activa, desactívala solo para este paso.
- `backtest.py` tarda 1 a 2 minutos con 4 núcleos y necesita unos 6 GB de RAM (`--hilos 2` usa menos).

## Salidas (`output/`)

- `resumen.json`: walk-forward (combinación elegida por año, resultado, entradas al azar), lectura literal del video
  y cuántas combinaciones ganan en 2026.
- `rejilla.csv`: todas las combinaciones con n y ganancia media por año.
- `operaciones_wf_*.csv`, `operaciones_video.csv`: cada operación con entrada, stop, objetivo, salida y resultado.
