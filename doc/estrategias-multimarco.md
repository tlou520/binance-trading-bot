# Tres estrategias multi-marco (minuto, hora, día, mes)

Backtest con velas reales de 1 min de Binance spot (BTC, ETH, BNB, XRP, SOL, DOGE), del 2023-01-01 al 2026-11-12.
Solo largos, costo de 0,24 % por ida y vuelta. Código en `binance-research/multitf/`.

## Conclusión

**Ninguna se usa todavía.** Las tres pierden en 2026 y ninguna gana los tres años juzgados. La única con una ventaja
medible es E1 (aprendizaje automático): ganó en 2024 y 2025 y superó a "entrar a cualquier hora", pero en 2026 dejó de
acertar. Combinarlas no arregla el problema, porque las tres son compras y pierden juntas cuando el mercado cae.

## Reglas

| | E1 Aprendizaje automático | E2 Fuerza relativa | E3 Tendencia en cascada |
|---|---|---|---|
| Idea | Un modelo (LightGBM) predice la ganancia de las próximas 24 h | Comprar cada semana las monedas más fuertes | El día da la dirección, la hora da el retroceso y la entrada |
| Marcos | Minuto, hora, día, calendario y BTC (23 variables) | Día (28 días) y régimen de BTC (media de 200 días) | Día (EMA 50) y hora (EMA 20 y 50) |
| Entrada | Predicción sobre el costo y sobre el percentil 95 de la validación | Lunes 00:00 UTC: las 2 con mayor subida en 28 días, si subieron y BTC está sobre su media de 200 días | Tendencia diaria alcista, retroceso a la EMA 20 de 1 h y cierre sobre el máximo de las 3 horas previas |
| Salida | A las 24 h | Cuando deja de estar entre las 2 primeras | Stop bajo el retroceso (1,5 % a 8 %), objetivo 3R o 7 días |
| Capital | 1/6 por operación | 1/2 por moneda | 1/6 por operación |
| Ajuste | Se entrena solo con años anteriores al juzgado | Parámetros fijados de antemano | Parámetros fijados de antemano |

## Resultados

"Ganancia" es la de la cuenta completa en el año. E1 necesita un año de entrenamiento, por eso empieza en 2024.

### E1 Aprendizaje automático

| Año | Operaciones | Acierto | Media neta | Ganancia | Meses positivos | Entrar a cualquier hora |
|---|---|---|---|---|---|---|
| 2024 | 389 | 55,0 % | +0,733 % | +50,56 % | 8/12 | +0,075 % |
| 2025 | 266 | 55,6 % | +0,395 % | +18,70 % | 9/12 | −0,236 % |
| 2026 | 304 | 39,8 % | −0,551 % | −27,60 % | 4/11 | −0,325 % |
| **Total** | **959** | **50,4 %** | **+0,232 %** | **+29,37 %** | **21/35** | |

Correlación entre predicción y resultado real: +0,045 (2024), +0,070 (2025), −0,037 (2026).

### E2 Fuerza relativa semanal

| Año | Operaciones | Acierto | Media neta | Ganancia | Meses positivos |
|---|---|---|---|---|---|
| 2023 (desde julio) | 8 | 37,5 % | −1,974 % | +93,72 % | 3/12 |
| 2024 | 29 | 51,7 % | +17,419 % | +97,16 % | 5/12 |
| 2025 | 29 | 48,3 % | −0,178 % | −11,17 % | 5/12 |
| 2026 | 9 | 33,3 % | −3,455 % | −15,07 % | 1/11 |
| **Total** | **75** | **46,7 %** | **+6,041 %** | **+188,13 %** | **14/47** |

Las operaciones se cuentan en el año en que cierran; por eso 2023 muestra media negativa y ganancia positiva (las
compras ganadoras de 2023 cerraron en 2024). Gana menos que comprar y mantener BTC en 2024 (+121 %).

### E3 Tendencia en cascada

| Año | Operaciones | Acierto | Media neta | Ganancia | Meses positivos |
|---|---|---|---|---|---|
| 2023 | 311 | 32,8 % | +0,117 % | +3,46 % | 5/12 |
| 2024 | 313 | 33,2 % | +0,227 % | +7,12 % | 5/12 |
| 2025 | 231 | 29,0 % | −0,507 % | −19,19 % | 2/12 |
| 2026 | 179 | 26,3 % | −0,483 % | −13,91 % | 1/11 |
| **Total** | **1.034** | **30,9 %** | **−0,093 %** | **−22,89 %** | **13/47** |

### Combinadas (2024 a 2026)

- **Integrada:** la señal de E3, solo si la moneda está entre las 2 más fuertes (E2) y el modelo predice ganancia (E1).
- **Cartera 1/3:** un tercio del capital en cada estrategia, cada una por su cuenta.

| Estrategia | 2024 | 2025 | 2026 | Total | Meses positivos | Peor mes | Caída máxima |
|---|---|---|---|---|---|---|---|
| E1 | +50,56 % | +18,70 % | −27,60 % | +29,37 % | 21/35 | −20,14 % | −31,06 % |
| E2 | +97,16 % | −11,17 % | −15,07 % | +48,74 % | 11/35 | −21,02 % | −39,89 % |
| E3 | +7,12 % | −19,19 % | −13,91 % | −25,47 % | 8/35 | −11,01 % | −32,81 % |
| Integrada (E3 con filtros de E2 y E1) | +1,59 % | −11,65 % | −7,61 % | −17,08 % | 9/35 | −4,77 % | −18,38 % |
| Cartera 1/3 | +58,94 % | −2,33 % | −17,85 % | +27,52 % | 17/35 | −13,11 % | −23,04 % |
| Comprar y mantener BTC | +121,31 % | −6,33 % | −18,47 % | +69,00 % | 19/35 | −20,43 % | −49,36 % |
| Comprar y mantener las 6 | +179,80 % | −17,73 % | −32,17 % | +56,15 % | 18/35 | −27,85 % | −59,08 % |

## Qué queda por probar

- E1 es la base más prometedora. Falta ver por qué falla en 2026: reentrenar cada mes en vez de cada año y exigir que
  el modelo haya acertado en los últimos meses antes de operar.
- Las tres son solo compras. En mercado bajista (2025 y 2026) lo mejor que pueden hacer es no operar.

## Cómo reproducirlo

```
cd binance-research/multitf
python -m unittest test_estrategias
python backtest.py
```

Necesita las velas de 1 min de `binance-research/pullback/descargar.py` y los paquetes `pandas` y `lightgbm`. Tarda
unos 10 segundos. Salidas en `output/`: `resumen.json`, `mensual.csv` y `operaciones_*.csv`.

## Mejoras de E1 (para corregir 2026)

Seis mejoras probadas por separado sobre la misma base, más tres combinaciones. Código: `mejoras.py`. Necesita las
velas desde 2020: `python ../pullback/descargar.py --desde 2020-01 --salida ../v3_research/tmp/k1m_2020`.

Ganancia de la cuenta por año:

| Variante | 2024 | 2025 | 2026 | Total | Meses positivos | Caída máxima |
|---|---|---|---|---|---|---|
| Base | +50,56 % | +18,70 % | −27,60 % | +29,37 % | 21/35 | −31,06 % |
| 6a. Filtro de régimen (BTC sobre media de 200 días) | +22,38 % | +6,93 % | +0,02 % | +30,88 % | 13/35 | −18,35 % |
| 6b. Percentil 98 | +28,39 % | +36,52 % | −23,07 % | +34,86 % | 18/35 | −25,31 % |
| 6. Régimen + percentil 98 | +11,82 % | +18,69 % | −0,64 % | +31,87 % | 12/35 | −13,96 % |
| 5. Interruptor (últimas 30 operaciones) | +39,20 % | −3,00 % | −9,30 % | +22,46 % | 12/35 | −18,90 % |
| 4. Historia desde 2020 | +71,44 % | +11,97 % | −9,62 % | +73,49 % | 15/35 | −21,74 % |
| 3. Reentreno mensual (24 meses) | +54,86 % | +14,95 % | −12,03 % | +56,60 % | 22/35 | −19,28 % |
| 2. Objetivo antes que stop (modelo nuevo) | +9,12 % | −8,02 % | −45,12 % | −44,92 % | 15/35 | −50,69 % |
| 2b. Modelo base con stop y objetivo | +24,41 % | −3,18 % | −42,14 % | −30,30 % | 13/35 | −49,22 % |
| 1. Segundo modelo (solo filtra 2025 y 2026) | +50,56 % | +22,97 % | −27,87 % | +33,54 % | 20/35 | −28,29 % |
| 3+4. Historia y reentreno mensual | +39,73 % | +24,26 % | −12,03 % | +52,74 % | 21/35 | −19,28 % |
| 3+4+6a | +35,49 % | +7,99 % | −5,66 % | +38,03 % | 14/35 | −18,71 % |
| **4+6a. Historia desde 2020 y filtro de régimen** | **+70,51 %** | **+11,32 %** | **+4,74 %** | **+98,83 %** | 12/35 | −22,62 % |

Con historia desde 2020 también se pueden juzgar 2022 y 2023:

| Variante | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| 4. Historia desde 2020 | −13,88 % | +24,16 % | +71,44 % | +11,97 % | −9,62 % |
| 3+4 | −8,40 % | +49,48 % | +39,73 % | +24,26 % | −12,03 % |
| 4+6a | 0 % (no opera) | +19,51 % | +70,51 % | +11,32 % | +4,74 % |

Lectura:

- **Se quedan:** más historia (4) y filtro de régimen (6a). El reentreno mensual (3) mejora 2026 pero no lo vuelve
  positivo; queda como alternativa.
- **Se descartan:** stop y objetivo (2), que empeora todo; segundo modelo (1), que casi no cambia nada; interruptor
  (5), que quita más ganancias de 2025 que pérdidas de 2026; percentil 98 solo (6b), que no arregla 2026.
- **Cuidado:** 4+6a se eligió después de ver 2026, y su 2026 son 59 operaciones con 2 meses positivos de 11. No es
  prueba de que funcione; hay que validarla con datos nuevos (en papel) antes de usar dinero.
