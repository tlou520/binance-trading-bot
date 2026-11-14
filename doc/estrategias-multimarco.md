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

## Más meses positivos (sobre 4+6a)

Siete mejoras y nueve combinaciones, juzgadas de 2023 a 2026 (47 meses). Código: `meses.py`. Necesita además las
velas de ADA, LINK, AVAX, LTC, TRX y DOT desde 2020 en la misma carpeta (`descargar.py --monedas ADAUSDT ...`).

Un mes sin operaciones cuenta como no positivo. En la base, de los 27 meses no positivos, 12 son meses sin operar
(BTC bajo su media de 200 días) y 15 son meses con pérdida.

| Variante | 2023 | 2024 | 2025 | 2026 | Total | Meses positivos | En 2026 | Peor mes | Caída máxima |
|---|---|---|---|---|---|---|---|---|---|
| Base 4+6a | +19,5 % | +70,5 % | +11,3 % | +4,7 % | +137,6 % | 20/47 | 2/11 | −17,3 % | −22,6 % |
| 7. Percentil 90 | +48,5 % | +34,5 % | +7,6 % | −4,2 % | +105,9 % | 23/47 | 1/11 | −25,0 % | −30,4 % |
| 6a. Parar el mes en +3 % | +19,6 % | +1,6 % | +11,2 % | +2,1 % | +38,0 % | 21/47 | 2/11 | −19,7 % | −24,1 % |
| 6b. Parar el mes en −3 % | +20,3 % | +99,0 % | +11,3 % | +5,0 % | +179,8 % | 20/47 | 2/11 | −5,3 % | −8,3 % |
| 5a. BTC sobre EMA de 50 días | +18,5 % | +47,3 % | −0,8 % | +2,8 % | +77,8 % | 17/47 | 3/11 | −22,1 % | −29,9 % |
| 5b. Cada moneda sobre su EMA de 50 días | +5,1 % | +34,0 % | −0,7 % | +0,2 % | +40,1 % | 13/47 | 1/11 | −18,1 % | −28,8 % |
| 5c. Régimen mixto | +20,2 % | +67,0 % | +11,3 % | +1,5 % | +126,7 % | 22/47 | 3/11 | −17,3 % | −22,2 % |
| 4. Las 2 mejores del día | +20,0 % | +45,7 % | −22,2 % | +5,1 % | +42,9 % | 17/47 | 2/11 | −8,3 % | −22,2 % |
| 3. Doce monedas | +22,1 % | +34,1 % | +12,4 % | +4,6 % | +92,6 % | 18/47 | 2/11 | −20,3 % | −33,5 % |
| 2. Modelo propio para mercado bajista | +24,4 % | +88,1 % | +1,6 % | −21,9 % | +85,7 % | 23/47 | 4/11 | −17,3 % | −33,7 % |
| 1. Conjunto 6 h + 24 h + 72 h | +27,9 % | +62,7 % | +3,4 % | +1,9 % | +119,5 % | 21/47 | 2/11 | −13,8 % | −16,5 % |
| 1 (parte). Solo modelo de 72 h | +44,6 % | +87,1 % | +2,0 % | +6,9 % | +195,0 % | 20/47 | 1/11 | −19,3 % | −21,1 % |
| A. 24 h + 6b + 5c | +21,0 % | +75,9 % | +11,3 % | +1,7 % | +140,9 % | 21/47 | 3/11 | −6,0 % | −11,0 % |
| B. 72 h + 6b | +42,2 % | +96,5 % | +2,0 % | +6,9 % | +204,9 % | 19/47 | 1/11 | −7,8 % | −11,7 % |
| C. 72 h + 6b + 5c | +45,0 % | +95,7 % | +2,0 % | +8,8 % | +214,9 % | 22/47 | 4/11 | −7,8 % | −12,1 % |
| D. Mitad 24 h y mitad 72 h + 6b | +31,1 % | +99,5 % | +6,7 % | +6,0 % | +195,9 % | 20/47 | 2/11 | −6,4 % | −8,0 % |
| E. 24 h + percentil 90 + 6b | +49,6 % | +53,9 % | +9,9 % | +1,8 % | +157,6 % | 21/47 | 1/11 | −6,4 % | −17,8 % |
| F. 72 h + percentil 90 + 6b | +74,4 % | +111,5 % | +17,6 % | +10,5 % | +379,5 % | 25/47 | 1/11 | −10,3 % | −14,7 % |
| **G. 72 h + percentil 90 + 6b + 5c** | **+80,3 %** | **+112,3 %** | **+17,6 %** | **+7,7 %** | **+384,6 %** | **27/47** | 3/11 | −10,3 % | −14,4 % |
| H. Mitad 24 h y mitad 72 h, percentil 90 + 6b | +61,9 % | +81,9 % | +13,8 % | +6,1 % | +255,6 % | 23/47 | 1/11 | −8,1 % | −16,0 % |
| I. Como H, con 5c | +65,2 % | +80,0 % | +13,8 % | +2,5 % | +246,8 % | 23/47 | 1/11 | −9,0 % | −16,8 % |

### Ganadora: G

Modelo que predice 72 h (entrenado con historia desde 2020, un modelo por año), entrada sobre el percentil 90,
régimen mixto (BTC sobre su media de 200 días, o sobre su EMA de 50 días con la EMA subiendo) y parar el mes al
perder 3 % de la cuenta.

| Año | Operaciones | Acierto | Media neta | Ganancia | Meses positivos | Negativos | Sin operar | Entrar a cualquier hora |
|---|---|---|---|---|---|---|---|---|
| 2023 | 173 | 56,1 % | +2,180 % | +80,31 % | 9/12 | 2 | 1 | +0,530 % |
| 2024 | 243 | 57,2 % | +2,283 % | +112,30 % | 7/12 | 5 | 0 | +0,601 % |
| 2025 | 56 | 55,4 % | +1,780 % | +17,55 % | 8/12 | 2 | 2 | −0,304 % |
| 2026 | 56 | 41,1 % | +0,906 % | +7,69 % | 3/11 | 5 | 3 | −0,649 % |
| **Total** | **528** | **54,9 %** | **+2,050 %** | **+384,59 %** | **27/47** | **14** | **6** | |

Límites:

- 2026 sigue débil: 3 meses positivos de 11, y casi toda la ganancia del año viene de agosto (+14,7 %).
- G se armó después de ver los resultados de las piezas en estos mismos años. La ganancia real esperable es menor.
- Ninguna variante solo de compras ganó en la mayoría de los meses de 2026. Para ganar en meses bajistas haría falta
  vender en corto (futuros), que el bot no hace.

## Más meses positivos en 2026 (sobre G)

Diez mejoras y siete combinaciones, con datos hasta el 2026-11-13. Código: `meses2.py`. Los cortos se simulan con el
mismo costo que una compra (0,24 %) y en la práctica requieren futuros.

**Resultado: el máximo alcanzado es 5 meses positivos de 11 en 2026; no se llegó a 6 o 7.**

Ganancia de cada mes de 2026 (% de la cuenta):

| Variante | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G (base) | −1,75 | 0 | 0 | +0,33 | −1,59 | 0 | +0,43 | +14,72 | −0,56 | −1,03 | −3,12 | 3/11 |
| 10. Proteger el mes (+2 % / +1 %) | −1,75 | 0 | 0 | +0,33 | −1,59 | 0 | +0,43 | +14,72 | −0,56 | −1,03 | −3,12 | 3/11 |
| 9. Límite semanal −1,5 % | −1,75 | 0 | 0 | +0,33 | −1,59 | 0 | +0,43 | +14,72 | −0,56 | −1,03 | −3,12 | 3/11 |
| 8. Fuera de régimen, percentil 98 | −0,79 | −7,08 | 0 | +0,33 | −1,59 | +0,53 | +0,43 | +15,06 | −0,56 | −1,03 | −3,12 | 4/11 |
| 7. Stop 6 ATR y objetivo 12 ATR | −0,76 | 0 | 0 | +0,12 | −2,84 | 0 | −0,74 | +11,74 | −1,12 | −2,07 | −2,00 | 2/11 |
| 7b. Solo objetivo 12 ATR | −1,75 | 0 | 0 | +0,45 | −2,62 | 0 | +0,43 | +13,90 | −0,56 | −1,03 | −1,73 | 3/11 |
| 6. G + rebote tras capitulación | −1,90 | −9,90 | 0 | +0,33 | −1,59 | +3,13 | +0,43 | +14,72 | −0,56 | −1,03 | −3,12 | 4/11 |
| 5. Modelo de 7 días | 0 | 0 | 0 | −3,44 | −0,49 | 0 | −0,70 | +15,22 | −4,37 | −3,89 | 0 | 1/11 |
| 4. Reentreno mensual | −1,75 | 0 | 0 | −1,18 | −1,35 | 0 | −0,10 | +13,15 | +0,71 | −3,20 | +0,35 | 3/11 |
| 3. Promedio de 5 modelos | +0,29 | 0 | 0 | −1,25 | −2,16 | 0 | +0,43 | +13,82 | −1,71 | −1,59 | −3,75 | 3/11 |
| 2. G + cortos fuera de régimen | −2,32 | +4,62 | +0,26 | −1,15 | −1,59 | −4,40 | −0,81 | +14,72 | −0,56 | −1,03 | −3,12 | 3/11 |
| 1. Largo/corto neutral diario | −6,63 | −6,97 | −4,80 | −0,20 | −1,68 | −0,79 | +1,36 | −3,71 | −2,88 | −2,67 | −0,55 | 1/11 |
| **K1. Reentreno mensual + percentil 98 fuera de régimen** | −0,79 | −7,08 | +0,61 | −1,18 | −1,35 | −0,99 | +4,33 | +12,30 | +0,71 | −3,20 | +0,35 | **5/11** |
| K2. Reentreno mensual + rebote | −1,90 | −9,90 | 0 | −1,18 | −1,35 | +3,13 | −0,10 | +13,15 | +0,71 | −3,20 | +0,35 | 4/11 |
| K3. Reentreno mensual + objetivo 12 ATR | −1,75 | 0 | 0 | +0,07 | −2,86 | 0 | −0,10 | +14,94 | +0,71 | −3,20 | +0,53 | 4/11 |
| K4. Reentreno mensual + cortos (futuros) | −2,32 | +7,97 | −4,05 | −1,69 | −1,35 | −3,70 | −2,21 | +12,65 | +0,71 | −3,20 | +0,35 | 4/11 |
| K5. Reentreno mensual + cortos percentil 2 (futuros) | −1,71 | +4,71 | +4,41 | −1,18 | −1,35 | −3,98 | −0,10 | +13,15 | +0,71 | −3,20 | +0,35 | 5/11 |

Ganancia por año:

| Variante | 2023 | 2024 | 2025 | 2026 | Total | Meses positivos | Peor mes | Caída máxima |
|---|---|---|---|---|---|---|---|---|
| G (base) | +80,3 % | +112,3 % | +17,6 % | +6,6 % | +379,5 % | 27/47 | −10,3 % | −14,4 % |
| 10 | +71,9 % | +112,3 % | +12,8 % | +6,6 % | +338,7 % | 24/47 | −10,3 % | −14,4 % |
| 9 | +72,7 % | +103,8 % | +17,6 % | +6,6 % | +340,9 % | 27/47 | −9,7 % | −13,0 % |
| 8 | +86,0 % | +105,0 % | +17,6 % | +0,8 % | +351,9 % | 28/47 | −10,3 % | −17,4 % |
| 7 | +79,6 % | +86,2 % | +21,7 % | +1,6 % | +313,5 % | 23/47 | −6,0 % | −22,9 % |
| 7b | +81,9 % | +108,7 % | +19,4 % | +6,3 % | +381,8 % | 27/47 | −9,7 % | −13,2 % |
| 6 | +85,4 % | +118,0 % | +20,0 % | −1,1 % | +379,5 % | 30/47 | −10,3 % | −13,3 % |
| 5 | +47,6 % | +125,7 % | −0,9 % | +1,0 % | +233,5 % | 16/47 | −6,5 % | −11,9 % |
| 4 | +82,6 % | +107,2 % | +16,7 % | +5,9 % | +367,7 % | 28/47 | −6,1 % | −6,1 % |
| 3 | +72,0 % | +100,5 % | +13,0 % | +3,1 % | +301,6 % | 27/47 | −9,0 % | −16,1 % |
| 2 | +80,4 % | +107,6 % | +25,0 % | +3,4 % | +383,8 % | 28/47 | −10,3 % | −16,3 % |
| 1 | +30,5 % | +27,3 % | −17,8 % | −26,2 % | +0,8 % | 19/47 | −12,8 % | −39,3 % |
| **K1** | +82,0 % | +107,2 % | +18,7 % | +2,6 % | +359,5 % | 30/47 | −7,1 % | −10,7 % |
| K2 | +87,7 % | +129,6 % | +19,1 % | −1,7 % | +404,4 % | 31/47 | −9,9 % | −13,8 % |
| K3 | +94,2 % | +101,7 % | +12,8 % | +7,5 % | +374,8 % | 29/47 | −5,5 % | −8,9 % |
| K4 | +78,9 % | +57,8 % | +10,2 % | +1,9 % | +217,0 % | 27/47 | −10,7 % | −22,9 % |
| K5 | +82,4 % | +76,6 % | +0,5 % | +11,2 % | +260,1 % | 28/47 | −11,4 % | −19,0 % |

Lectura:

- **Se queda el reentreno mensual (4):** casi la misma ganancia que G con la caída máxima más baja (−6,1 %).
- **K1** es la que más meses positivos da en 2026 solo con compras (5/11), a cambio de un febrero de −7,08 % y menos
  ganancia en el año (+2,6 %).
- Los cortos ganan en febrero y marzo pero pierden en abril, junio y julio; no dan una mejora neta.
- Los controles de cuenta (10 y 9) y las salidas anticipadas (7) no cambian ningún mes de signo.
- Todas las combinaciones se eligieron viendo 2026; los 5/11 son un techo optimista, no una expectativa.

## Mejoras sobre la variante 4 con tres condiciones (2026)

Base: variante 4 (72 h, reentreno mensual, percentil 90, régimen mixto, parar el mes en −3 %): 3/11 meses positivos y
+5,92 % en 2026. Código: `meses3.py`. Una variante se acepta solo si cumple las tres en 2026: mejora más meses de los
que empeora (C1), tiene más meses positivos (C2) y gana más en el año (C3).

| Variante | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos | 2026 | Cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Base (4) | −1,75 | 0 | 0 | −1,18 | −1,35 | 0 | −0,10 | +13,15 | +0,71 | −3,20 | +0,35 | 3/11 | +5,92 % | |
| 7. Comisión con BNB (0,19 %) | −1,72 | 0 | 0 | −1,12 | −1,23 | 0 | −0,09 | +13,27 | +0,78 | −3,13 | +0,41 | 3/11 | +6,47 % | No (C2) |
| 6. Objetivo a 10 ATR | −1,75 | 0 | 0 | −0,22 | −2,81 | 0 | −0,10 | +16,32 | +0,83 | −3,20 | +0,42 | 3/11 | +8,51 % | No (C2) |
| 6. Objetivo a 12 ATR | −1,75 | 0 | 0 | +0,07 | −2,86 | 0 | −0,10 | +14,94 | +0,71 | −3,20 | +0,53 | 4/11 | +7,47 % | **Sí** |
| 6. Objetivo a 15 ATR | −1,75 | 0 | 0 | +0,57 | −3,08 | 0 | −0,10 | +18,10 | +0,71 | −3,20 | +0,75 | 4/11 | +10,98 % | **Sí** |
| 5a. Cierre de 1 h sobre EMA 20 | 0 | 0 | 0 | −0,77 | −2,24 | 0 | −0,72 | +12,05 | +0,83 | −3,19 | +2,74 | 3/11 | +8,23 % | No (C2) |
| 5b. BTC subió en 24 h | 0 | 0 | 0 | −1,18 | −2,10 | 0 | −0,72 | +11,96 | +0,65 | −2,43 | +2,74 | 3/11 | +8,49 % | No (C1, C2) |
| 5c. Última hora al alza | −0,18 | 0 | 0 | −1,28 | −1,95 | 0 | −0,72 | +15,01 | −0,17 | −3,64 | +2,46 | 2/11 | +8,73 % | No (C1, C2) |
| 4. Media posición bajo el percentil 95 | −0,87 | 0 | 0 | −0,66 | −1,63 | 0 | −0,05 | +7,35 | +0,16 | −1,85 | −0,59 | 2/11 | +1,56 % | No |
| 3a. Régimen débil: percentil 95 | +0,27 | 0 | 0 | −1,09 | −0,15 | 0 | 0 | +13,15 | +0,71 | −3,20 | +0,35 | 4/11 | +9,63 % | **Sí** |
| 3b. Régimen débil: percentil 98 | 0 | 0 | 0 | 0 | +1,27 | 0 | 0 | +13,15 | +0,71 | −3,20 | +0,35 | 4/11 | +12,11 % | **Sí** |
| 2a. Acuerdo con modelo de 24 h (> 0) | −1,75 | 0 | 0 | −1,18 | −0,83 | 0 | −0,10 | +13,56 | +0,29 | −2,94 | +1,55 | 3/11 | +7,98 % | No (C2) |
| 2b. Acuerdo con modelo de 24 h (> costo) | −1,86 | 0 | 0 | +0,37 | −1,48 | 0 | +0,62 | +15,82 | −1,19 | −3,44 | +1,71 | 4/11 | +9,74 % | No (C1) |
| 1. Variables de amplitud de mercado | +0,29 | 0 | 0 | +0,40 | −3,73 | 0 | +0,43 | +12,85 | −0,35 | −3,09 | −0,81 | 4/11 | +5,23 % | No (C1, C3) |

Combinaciones (120 probadas; 36 cumplen las tres). Opción fija por sugerencia: 1 amplitud, 2 acuerdo > 0, 3 percentil 95,
4 media posición, 5 BTC subió en 24 h, 6 objetivo a 12 ATR, 7 BNB.

| Combinación | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos | 2026 | 2023 | 2024 | 2025 | Meses + (47) | Caída máx. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2+3+6+7** | +0,28 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +14,31 | +0,36 | −2,88 | +1,52 | **5/11** | **+13,20 %** | +64,0 % | +118,4 % | +18,2 % | 31 | −5,4 % |
| 2+3+6 | +0,27 | 0 | 0 | +1,07 | −1,41 | 0 | 0 | +14,18 | +0,29 | −2,94 | +1,44 | 5/11 | +12,66 % | +61,7 % | +115,5 % | +17,2 % | 31 | −5,5 % |
| 3+6+7 | +0,28 | 0 | 0 | +1,13 | −1,70 | 0 | 0 | +15,08 | +0,78 | −3,13 | +0,58 | 5/11 | +12,65 % | +93,8 % | +104,0 % | +13,7 % | 30 | −8,7 % |
| 3+6 | +0,27 | 0 | 0 | +1,07 | −1,82 | 0 | 0 | +14,94 | +0,71 | −3,20 | +0,53 | 5/11 | +12,08 % | +90,9 % | +101,7 % | +12,7 % | 30 | −8,9 % |
| 2+3 | +0,27 | 0 | 0 | −1,09 | +0,26 | 0 | 0 | +13,56 | +0,29 | −2,94 | +1,55 | 5/11 | +11,63 % | +53,8 % | +104,9 % | +18,2 % | 29 | −5,5 % |
| Base (4) | −1,75 | 0 | 0 | −1,18 | −1,35 | 0 | −0,10 | +13,15 | +0,71 | −3,20 | +0,35 | 3/11 | +5,92 % | +82,6 % | +107,2 % | +16,7 % | 28 | −6,1 % |

**Se queda 2+3+6+7:** modelo de 72 h reentrenado cada mes; entrada sobre el percentil 90 (percentil 95 si BTC está
bajo su media de 200 días) y solo si el modelo de 24 h también predice subida; salida al llegar a +12 ATR o a las
72 h; comisión pagada con BNB; parar el mes en −3 %. Sin el descuento de BNB (2+3+6) sigue cumpliendo las tres.

Avisos: gana menos que la base en 2023 (+64,0 % frente a +82,6 %); agosto aporta casi toda la ganancia de 2026; y
se eligió entre 120 combinaciones viendo 2026, así que la ventaja real será menor.

## Ocho mejoras sobre 2+3+6+7 (septiembre a noviembre y 6/11)

Base: combinación 2+3+6+7 (5/11 y +13,20 % en 2026). Código: `meses4.py`. Condiciones en 2026: septiembre, octubre y
noviembre mejores que +0,36, −2,88 y +1,52 (C1); año positivo (C2); al menos 6 meses positivos (C3).

| Variante | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos | 2026 | Cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Base 2+3+6+7 | +0,28 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +14,31 | +0,36 | −2,88 | +1,52 | 5/11 | +13,20 % | |
| **8. Capital sin usar en Earn flexible (2 % anual)** | +0,45 | +0,15 | +0,17 | +1,28 | −1,18 | +0,16 | +0,17 | +14,45 | +0,50 | −2,73 | +1,57 | **9/11** | **+14,98 %** | **Sí** |
| 8b. Earn al 4 % anual | +0,61 | +0,30 | +0,33 | +1,42 | −1,04 | +0,32 | +0,33 | +14,58 | +0,64 | −2,59 | +1,61 | 9/11 | +16,74 % | Sí |
| 7. Parar el mes en −2 % | +0,28 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +14,31 | +0,36 | −2,51 | +1,40 | 5/11 | +13,50 % | No (C1, C3) |
| 6. Máximo 3 posiciones | +0,28 | 0 | 0 | +2,05 | −0,55 | 0 | 0 | +5,34 | +0,36 | −2,37 | +0,18 | 5/11 | +5,24 % | No (C1, C3) |
| 5. Pausa de 3 días tras pérdida | +0,28 | 0 | 0 | +1,13 | −1,95 | 0 | 0 | +13,99 | −0,47 | −2,88 | +1,52 | 4/11 | +11,23 % | No (C1, C3) |
| 4. Sin entrar con volatilidad alta de BTC | +0,28 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +14,56 | +0,33 | −2,88 | +2,68 | 5/11 | +14,71 % | No (C1, C3) |
| 3. Solo las 3 más fuertes a 28 días | 0 | 0 | 0 | +2,05 | −1,49 | 0 | 0 | +6,65 | +0,99 | −1,86 | +0,45 | 4/11 | +6,74 % | No (C1, C3) |
| 2. Stop a la entrada tras +6 ATR | +0,28 | 0 | 0 | +1,27 | −1,61 | 0 | 0 | +13,48 | +0,77 | −2,88 | +0,51 | 5/11 | +11,53 % | No (C1, C3) |
| 1. Cortos bajo el percentil 2 (futuros) | +0,35 | +4,98 | +4,47 | +1,13 | −1,31 | −3,93 | 0 | +14,31 | +0,36 | −2,88 | +1,52 | 7/11 | +19,35 % | No (C1) |

Combinaciones (247 probadas; 10 cumplen las tres, 4 de ellas sin futuros; todas las que cumplen sin futuros incluyen
la 8):

| Combinación | Sep | Oct | Nov | Positivos | 2026 | 2023 | 2024 | 2025 | Meses + (47) | Caída máx. |
|---|---|---|---|---|---|---|---|---|---|---|
| **8 sola** | +0,50 | −2,73 | +1,57 | 9/11 | +14,98 % | +66,4 % | +121,6 % | +20,2 % | 37 | −5,3 % |
| 4+7+8 | +0,47 | −2,35 | +2,73 | 9/11 | +16,98 % | +40,5 % | +92,1 % | +4,3 % | 34 | −11,9 % |
| 4+8 | +0,47 | −2,73 | +2,73 | 9/11 | +16,53 % | +40,6 % | +106,2 % | +4,3 % | 35 | −11,9 % |
| 2+4+7+8 | +0,88 | −2,35 | +1,73 | 9/11 | +16,11 % | +38,1 % | +75,3 % | +3,1 % | 34 | −11,9 % |
| 1+8 (futuros) | +0,50 | −2,73 | +1,57 | 8/11 | +21,06 % | +66,3 % | +89,3 % | +3,8 % | 32 | −16,5 % |
| Base | +0,36 | −2,88 | +1,52 | 5/11 | +13,20 % | +64,0 % | +118,4 % | +18,2 % | 31 | −5,4 % |

**Se queda la 8 sola.** Es la única que cumple las tres sin empeorar ningún año. Las combinaciones con la 4 ganan algo
más en 2026 pero pierden mucho en 2023 y 2025.

Avisos: la 8 no es operativa de trading sino interés sobre el USDT sin usar; el 2 % anual es un supuesto que hay que
comprobar en Binance Earn. Sin la 8, ninguna mejora de trading en spot cumple las tres condiciones: octubre sigue
entre −2,9 % y −1,1 % en todas.

## Diez mejoras solo de trading sobre 2+3+6+7

La mejora 8 de la ronda anterior (Earn flexible) queda descartada: el proyecto es de trading y no se cuentan
intereses. Código: `meses5.py` (`--combos` para las combinaciones). Condiciones en 2026: septiembre, octubre y
noviembre mejores que +0,36, −2,88 y +1,52 (C1) y año positivo (C2). Tener 6 meses positivos ya no es obligatorio.

| Variante | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos | 2026 | Cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Base 2+3+6+7 | +0,28 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +14,31 | +0,36 | −2,88 | +1,52 | 5/11 | +13,20 % | |
| 10. No entrar en fin de semana | +0,28 | 0 | 0 | +1,19 | −1,69 | 0 | 0 | +13,73 | +0,76 | −2,88 | +1,52 | 5/11 | +12,70 % | No |
| 9. No entrar cerca de noticias | +0,28 | 0 | 0 | −0,26 | −0,02 | 0 | 0 | +14,31 | +0,36 | −2,54 | +1,79 | 4/11 | +13,80 % | No |
| 8. BTC subió en 24 h | 0 | 0 | 0 | +1,37 | −1,50 | 0 | 0 | +13,25 | +0,47 | −2,39 | +2,68 | 4/11 | +13,86 % | **Sí** |
| 7. Modelo predice subida de BTC | 0 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +16,69 | −0,54 | −3,18 | +1,66 | 3/11 | +14,02 % | No |
| 6. Renovar sin costo | +0,28 | 0 | 0 | +1,13 | −1,28 | 0 | 0 | +14,31 | +0,42 | −2,88 | +1,52 | 5/11 | +13,31 % | No |
| 5. Orden límite a 0,5 ATR | 0 | 0 | 0 | +0,62 | −1,43 | 0 | 0 | +15,11 | +0,08 | −2,53 | +2,03 | 4/11 | +13,62 % | No |
| 5b. Orden límite a 0,25 ATR | +0,32 | 0 | 0 | +0,19 | −1,68 | 0 | 0 | +14,23 | +0,78 | −2,31 | +1,77 | 5/11 | +13,10 % | **Sí** |
| 4. Compras fuera de régimen (percentil 98) | +1,25 | −7,03 | +0,62 | +1,13 | −1,31 | −0,96 | +4,47 | +20,18 | +0,36 | −2,88 | +1,52 | 7/11 | +16,31 % | No |
| 3. Salir si el modelo de 24 h predice caída | +0,08 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +7,55 | −0,67 | −3,27 | −1,52 | 3/11 | +1,64 % | No |
| 2. Umbral propio por moneda | −2,63 | 0 | 0 | +0,78 | −2,12 | 0 | 0 | +12,52 | −0,79 | −3,22 | +0,66 | 3/11 | +4,46 % | No |
| 1. Más peso a lo reciente (12 meses) | −0,90 | 0 | 0 | 0 | −2,03 | 0 | 0 | +12,42 | −3,48 | −5,62 | −2,90 | 1/11 | −3,45 % | No |

Combinaciones de 4, 5, 6, 8, 9 y 10 (88 probadas; 68 cumplen C1 y C2). Las más equilibradas:

| Combinación | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos | 2026 | 2023 | 2024 | 2025 | Meses + (47) | Caída máx. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **4+5b+6+9** | +1,34 | −6,71 | 0 | +0,19 | −0,65 | −0,92 | +4,67 | +18,66 | +0,81 | −2,01 | +1,99 | 6/11 | +16,65 % | +65,7 % | +103,1 % | +22,7 % | 34 | −8,0 % |
| 4+5b+9 | +1,34 | −6,71 | 0 | +0,19 | −0,65 | −0,92 | +4,67 | +18,66 | +0,78 | −2,01 | +1,99 | 6/11 | +16,61 % | +65,0 % | +102,0 % | +22,6 % | 34 | −8,0 % |
| 4+5b | +1,34 | −6,71 | 0 | +0,19 | −1,65 | −0,92 | +4,67 | +18,66 | +0,78 | −2,31 | +1,77 | 6/11 | +14,84 % | +62,6 % | +107,6 % | +20,5 % | 34 | −8,9 % |
| 4+5b+6+10 | +0,32 | +6,75 | 0 | −0,38 | −2,18 | −0,60 | +4,67 | +17,99 | +1,20 | −2,31 | +1,77 | 6/11 | +28,90 % | +58,6 % | +71,9 % | +16,6 % | 29 | −5,6 % |
| 4+5+6+8+9+10 | 0 | 0 | 0 | 0 | −0,65 | −0,56 | 0 | +19,75 | +0,47 | −1,53 | +2,92 | 3/11 | +20,45 % | +20,3 % | +47,8 % | +2,4 % | 19 | −7,0 % |
| 5b sola | +0,32 | 0 | 0 | +0,19 | −1,68 | 0 | 0 | +14,23 | +0,78 | −2,31 | +1,77 | 5/11 | +13,10 % | +63,8 % | +107,6 % | +18,7 % | 33 | −5,3 % |
| Base | +0,28 | 0 | 0 | +1,13 | −1,31 | 0 | 0 | +14,31 | +0,36 | −2,88 | +1,52 | 5/11 | +13,20 % | +64,0 % | +118,4 % | +18,2 % | 31 | −5,4 % |

**Se propone 4+5b+6+9:** sobre la base, comprar fuera de régimen solo sobre el percentil 98, entrar con orden límite
0,25 ATR por debajo de la apertura (hasta 6 h), no pagar costo al renovar una posición y no entrar cerca de FOMC o
empleo de EE. UU. Cumple C1 y C2, llega a 6/11 y mantiene 2023 a 2025 cerca de la base. A cambio, febrero pasa a
−6,71 % y la caída máxima sube de −5,4 % a −8,0 %.

Octubre sigue negativo en todas las variantes (la mejor, −1,53 %, lo logra dejando casi de operar). Las combinaciones
se eligieron viendo 2026; la ventaja real será menor.

## Versión final: ajustes a 4+5b+6+9 con cinco condiciones

Código: `meses6.py`. Resumen con gráficos: [`resumen-ilustrado.md`](resumen-ilustrado.md). La combinación 4+5b+6+9
mejoraba septiembre a noviembre, pero dejaba febrero en −6,71 %, bajaba 2024 y subía la caída máxima. Condiciones,
todas frente a la combinación 2+3+6+7: septiembre, octubre y noviembre de 2026 mejores (C1); 2026 positivo (C2);
febrero no negativo (C3); 2024 no baja (C4); la caída máxima no sube (C5).

| Variante | Feb | Sep | Oct | Nov | Positivos | 2026 | 2024 | Caída máx. | Falla |
|---|---|---|---|---|---|---|---|---|---|
| Base de las condiciones (2+3+6+7) | 0 | +0,36 | −2,88 | +1,52 | 5/11 | +13,20 % | +118,4 % | −5,45 % | |
| Punto de partida (4+5b+6+9) | −6,71 | +0,81 | −2,01 | +1,99 | 6/11 | +16,65 % | +103,1 % | −8,00 % | C3, C4, C5 |
| 7. Quitar las compras fuera de régimen | 0 | +0,81 | −2,01 | +1,99 | 5/11 | +14,88 % | +103,1 % | −5,27 % | C4 |
| 6. Fuera de régimen solo si BTC subió en 7 días | 0 | +0,81 | −2,01 | +1,99 | 5/11 | +19,56 % | +103,1 % | −5,27 % | C4 |
| 5. Fuera de régimen solo si BTC subió en 24 h | 0 | +0,81 | −2,01 | +1,99 | 5/11 | +18,45 % | +103,1 % | −5,27 % | C4 |
| 4. Fuera de régimen si el modelo de 24 h supera el costo | −6,71 | +0,81 | −2,01 | +1,99 | 6/11 | +16,78 % | +103,1 % | −8,00 % | C3, C4, C5 |
| 3. Fuera de régimen con media posición | −3,36 | +0,81 | −2,01 | +1,99 | 6/11 | +15,89 % | +103,1 % | −5,27 % | C3, C4 |
| 2. Fuera de régimen: una sola pérdida por mes | −6,71 | +0,81 | −2,01 | +1,99 | 5/11 | +7,08 % | +103,1 % | −8,00 % | C3, C4, C5 |
| 1. Orden límite, o a mercado si no se llena | −6,71 | +0,81 | −2,50 | +1,99 | 6/11 | +18,28 % | +111,9 % | −7,81 % | C3, C4, C5 |

Ninguna cumple sola: la orden límite (5b) es la que baja 2024, porque deja sin entrar operaciones ganadoras. De las
83 combinaciones de las piezas, 3 cumplen las cinco condiciones, todas con entrada a mercado:

| Combinación | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Positivos | 2026 | 2023 | 2024 | 2025 | Meses + (47) | Caída máx. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Fuera de régimen si BTC subió en 24 h + renovar sin costo + sin noticias** | +0,28 | +0,65 | 0 | −0,26 | −0,02 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 | 5/11 | +19,64 % | +69,9 % | +124,3 % | +20,5 % | 31 | −5,45 % |
| Fuera de régimen si BTC subió en 7 días + renovar sin costo + sin noticias | +0,28 | 0 | 0 | −0,26 | −0,02 | 0 | 0 | +20,42 | +0,42 | −2,54 | +1,79 | 4/11 | +19,96 % | +69,1 % | +124,3 % | +20,5 % | 30 | −5,45 % |
| Sin compras fuera de régimen + renovar sin costo + sin noticias | +0,28 | 0 | 0 | −0,26 | −0,02 | 0 | 0 | +14,31 | +0,42 | −2,54 | +1,79 | 4/11 | +13,87 % | +69,0 % | +124,3 % | +20,5 % | 30 | −5,45 % |

**Versión final:** la primera. Es la 2+3+6+7 más tres reglas: comprar fuera de régimen solo sobre el percentil 98 y
si BTC subió en las últimas 24 h, mantener la posición sin pagar otra comisión si la señal sigue a las 72 h, y no
entrar cerca de FOMC o empleo de EE. UU. Total 2023-2026: +449,4 %.

Avisos: la mejora de septiembre a noviembre es pequeña (+0,06, +0,34 y +0,27 puntos); la subida del año viene de
agosto (+20,42 %); abril pasa de +1,13 % a −0,26 % por el filtro de noticias; y las reglas se eligieron viendo 2026.

## De 5 a 7 meses positivos en 2026 sin empeorar nada

Código: `meses7.py`. Punto de partida: la versión anterior (fuera de régimen si BTC subió en 24 h, renovar sin costo
y sin noticias). Condiciones, todas frente a ella: 2023, 2024, 2025 y 2026 no ganan menos (K1 a K4); la caída máxima
no sube (K5); los meses positivos de 47 no bajan (K6); septiembre, octubre y noviembre de 2026 no empeoran (K7);
febrero de 2026 no es negativo (K8). Meta: al menos 7 meses positivos de 11 en 2026.

Régimen débil: el régimen mixto está activo pero BTC está bajo su media de 200 días.

| Variante | 2023 | 2024 | 2025 | 2026 | Total | Caída máx. | Meses + (47) | Meses + 2026 | Falla |
|---|---|---|---|---|---|---|---|---|---|
| Punto de partida | +69,86 | +124,31 | +20,53 | +19,64 | +449,4 | −5,45 | 31 | 5 | |
| 1a. Objetivo de venta a 8 ATR | +50,17 | +90,84 | +18,49 | +24,57 | +323,0 | −5,45 | 30 | 6 | K1 K2 K3 K6 K7 |
| 1b. Objetivo de venta a 16 ATR | +67,36 | +91,22 | +20,64 | +20,92 | +366,9 | −5,45 | 31 | 6 | K1 K2 |
| 1c. Duración máxima de 48 h | +50,14 | +124,40 | +21,36 | +10,49 | +351,8 | −7,96 | 31 | 5 | K1 K4 K5 K7 |
| 2a. Tras perder en una moneda, 48 h sin volver a ella | +63,16 | +105,46 | +10,97 | +17,57 | +337,4 | −7,38 | 30 | 4 | K1 a K7 |
| 2b. Tras dos pérdidas seguidas, 48 h sin comprar | +64,90 | +105,30 | +14,99 | +15,58 | +349,9 | −5,63 | 28 | 4 | K1 a K7 |
| 3a. Proteger el mes: tras +0,5 %, parar si baja a +0,1 % | +69,86 | +114,72 | +16,10 | +17,68 | +398,4 | −5,45 | 29 | 5 | K2 K3 K4 K6 |
| 3b. Proteger el mes: tras +1 %, parar si baja a +0,3 % | +69,86 | +114,72 | +16,10 | +20,74 | +411,3 | −5,45 | 29 | 5 | K2 K3 K6 |
| 3c. Proteger el mes: tras +2 %, parar si baja a +1 % | +66,89 | +114,72 | +11,33 | +19,64 | +377,3 | −6,97 | 29 | 5 | K1 K2 K3 K5 K6 |
| 4a. Régimen débil: exigir percentil 98 | +67,76 | +124,31 | +20,53 | +20,91 | +448,4 | −5,45 | 31 | 5 | K1 |
| 4b. Régimen débil: exigir que BTC subió en 24 h | +69,82 | +124,31 | +20,53 | +18,09 | +442,2 | −5,45 | 30 | 4 | K1 K4 K6 |
| 4c. Régimen débil: media posición | +64,85 | +124,31 | +20,53 | +19,64 | +433,2 | −5,45 | 31 | 5 | K1 |
| 4x. Régimen débil: objetivo de venta a 8 ATR | +66,09 | +124,31 | +20,53 | +20,18 | +439,7 | −5,45 | 32 | 6 | K1 |
| 5a. Máximo 3 posiciones abiertas, siempre | +59,92 | +58,31 | +19,70 | +8,76 | +229,6 | −4,20 | 32 | 7 | K1 K2 K3 K4 K7 |
| 5b. Máximo 4 posiciones abiertas, siempre | +62,89 | +97,51 | +23,28 | +9,55 | +334,5 | −4,59 | 33 | 7 | K1 K2 K4 K7 |
| **5c. Máximo 3 posiciones abiertas al entrar en régimen débil** | +69,86 | +124,31 | +20,53 | +21,44 | +457,7 | −5,45 | 33 | **7** | **ninguna** |
| 5d. Máximo 4 posiciones abiertas al entrar en régimen débil | +69,86 | +124,31 | +20,53 | +20,70 | +454,3 | −5,45 | 33 | 7 | ninguna |
| 6a. Stop en el punto de equilibrio tras ganar 3 ATR | +64,35 | +129,96 | +12,71 | +16,62 | +396,8 | −5,45 | 33 | 5 | K1 K3 K4 K7 |
| 6b. Stop en el punto de equilibrio tras ganar 5 ATR | +59,00 | +127,93 | +17,13 | +18,49 | +402,9 | −5,45 | 31 | 5 | K1 K3 K4 K7 |
| 7. El modelo de 7 días también predice subida | +39,70 | +129,64 | +21,16 | +16,20 | +351,6 | −3,76 | 27 | 4 | K1 K4 K6 K7 |
| 8a. Segundo modelo de 24 h fuera de régimen | +80,62 | +138,28 | +23,73 | +3,16 | +449,4 | −9,33 | 32 | 4 | K4 K5 K8 |
| 8b. Segundo modelo de 24 h fuera de régimen, si BTC subió en 24 h | +78,09 | +124,31 | +20,53 | +7,70 | +418,6 | −6,11 | 30 | 5 | K4 K5 K6 K8 |

2026 mes a mes (%):

| Variante | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Punto de partida | +0,28 | +0,65 | 0 | −0,26 | −0,02 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 1a | +0,28 | +0,65 | 0 | −0,87 | +1,98 | −0,56 | 0 | +22,26 | +1,84 | −2,54 | +1,16 |
| 1b | +0,28 | +0,65 | 0 | −1,04 | +0,84 | −0,91 | 0 | +20,94 | +0,42 | −2,54 | +2,36 |
| 1c | +0,27 | +1,04 | 0 | −0,25 | +1,19 | −0,23 | 0 | +16,63 | +0,88 | −2,24 | −5,85 |
| 2a | +0,28 | +0,65 | 0 | −0,26 | −0,60 | −0,91 | 0 | +20,10 | −0,47 | −2,54 | +1,79 |
| 2b | +0,28 | +0,65 | 0 | −0,26 | −1,66 | −0,91 | 0 | +20,42 | −1,37 | −2,54 | +1,79 |
| 3a | +0,28 | +0,65 | 0 | −0,26 | −1,66 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 3b | +0,28 | +0,65 | 0 | −0,26 | −0,02 | 0 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 3c | +0,28 | +0,65 | 0 | −0,26 | −0,02 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 4a | 0 | +0,65 | 0 | 0 | +1,06 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 4b | 0 | +0,65 | 0 | −0,19 | −1,12 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 4c | +0,14 | +0,65 | 0 | −0,13 | −0,01 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 4x | +0,28 | +0,65 | 0 | −0,87 | +1,05 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 5a | +0,28 | +0,65 | 0 | +0,65 | +0,56 | −0,91 | 0 | +9,28 | +0,42 | −2,54 | +0,45 |
| 5b | +0,28 | +0,65 | 0 | +0,26 | +0,34 | −0,91 | 0 | +9,80 | +0,42 | −2,54 | +1,32 |
| **5c** | +0,28 | +0,65 | 0 | **+0,65** | **+0,56** | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 5d | +0,28 | +0,65 | 0 | +0,26 | +0,34 | −0,91 | 0 | +20,42 | +0,42 | −2,54 | +1,79 |
| 6a | 0 | +0,65 | 0 | +1,77 | −1,83 | −0,56 | 0 | +17,45 | +0,89 | −2,53 | +0,98 |
| 6b | 0 | +0,65 | 0 | +1,24 | −1,24 | −0,56 | 0 | +19,58 | +0,82 | −2,54 | +0,76 |
| 7 | +0,28 | +0,65 | 0 | −0,26 | −0,02 | −0,91 | 0 | +20,42 | +0,53 | −3,15 | −0,63 |
| 8a | −0,60 | −3,78 | +0,39 | −0,26 | −0,02 | −5,30 | 0 | +14,21 | +0,42 | −2,54 | +1,79 |
| 8b | +0,28 | −3,44 | +0,64 | −0,26 | −0,02 | −2,58 | 0 | +14,21 | +0,42 | −2,54 | +1,79 |

Combinaciones: 15.360 probadas.

| Meses positivos en 2026 | Combinaciones | De ellas, no empeoran nada |
|---|---|---|
| 2 | 229 | 0 |
| 3 | 2.061 | 0 |
| 4 | 5.501 | 0 |
| 5 | 5.579 | 1 (el punto de partida) |
| 6 | 1.790 | 0 |
| 7 | 200 | 2 (5c y 5d) |
| 8 o más | 0 | 0 |

Las que llegan a 7 meses y menos condiciones rompen:

| Combinación | 2023 | 2024 | 2025 | 2026 | Total | Caída máx. | Meses + (47) | Abr | May | Falla |
|---|---|---|---|---|---|---|---|---|---|---|
| **5c** | +69,86 | +124,31 | +20,53 | +21,44 | +457,7 | −5,45 | 33 | +0,65 | +0,56 | ninguna |
| 5d | +69,86 | +124,31 | +20,53 | +20,70 | +454,3 | −5,45 | 33 | +0,26 | +0,34 | ninguna |
| 5c+4x | +66,09 | +124,31 | +20,53 | +20,74 | +442,2 | −5,45 | 33 | +0,04 | +0,59 | K1 |
| 5c+4c | +64,85 | +124,31 | +20,53 | +20,54 | +437,2 | −5,45 | 33 | +0,33 | +0,28 | K1 |
| 5d+4c | +64,85 | +124,31 | +20,53 | +20,17 | +435,6 | −5,45 | 33 | +0,13 | +0,17 | K1 |
| 8b+5c | +78,09 | +124,31 | +20,53 | +9,33 | +426,4 | −4,70 | 32 | +0,65 | +0,56 | K4 K8 |
| 5c+3b | +69,86 | +114,72 | +16,10 | +21,44 | +414,3 | −5,45 | 31 | +0,65 | +0,56 | K2 K3 |

**Versión final:** 5c sola. Con régimen débil no se abre una compra nueva si ya hay 3 posiciones abiertas; con
régimen fuerte no hay tope. Ninguna combinación la mejora: sumarle cualquier otra pieza rompe alguna condición.
Ninguna de las 15.360 llega a 8 meses: marzo y julio no tienen operaciones, y junio y octubre siguen negativos.

Avisos:

- Entre 2023 y 2026 el tope quita solo 5 compras, todas de abril y mayo de 2026 y todas perdedoras (−2,37 %, −2,27 %,
  −0,87 %, −1,33 % y −2,17 %). Por eso 2023, 2024 y 2025 no cambian.
- En 2022, que no entra en las tablas, el tope de 3 habría quitado 7 compras que en conjunto ganaban: ese año pasa de
  +4,4 % a +1,5 %. Con tope de 4 (5d) 2022 sube a +5,1 %.
- Abril y mayo quedan positivos por poco (+0,65 % y +0,56 %).
- La regla se eligió viendo 2026.

## Subir septiembre, octubre y noviembre de 2026 sin empeorar nada

Código: `meses8.py`. Punto de partida: la versión final (5c de `meses7.py`). Condiciones, todas frente a ella: 2023,
2024, 2025 y 2026 no ganan menos (K1 a K4); la caída máxima no sube (K5); los meses positivos de 47 no bajan de 33
(K6); los de 2026 no bajan de 7 (K7); febrero de 2026 no es negativo (K8); ni septiembre, ni octubre, ni noviembre
empeoran (K9). Meta: que la suma de septiembre a noviembre suba (hoy −0,38 %).

Doce sugerencias y, en una segunda y tercera ronda, versiones más finas de las que más ayudaron (12, 7, 3 y 1):

| Variante | 2023 | 2024 | 2025 | 2026 | Total | Caída máx. | Meses + (47) | Meses + 2026 | Sep | Oct | Nov | Sep a nov | Falla |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Punto de partida | +69,86 | +124,31 | +20,53 | +21,44 | +457,70 | −5,45 | 33 | 7 | +0,42 | −2,54 | +1,79 | −0,38 |  |
| 1. No entrar en fin de semana | +76,66 | +79,29 | +15,68 | +21,89 | +346,60 | −5,45 | 30 | 7 | +0,82 | −2,54 | +1,79 | +0,02 | K2 K3 K6 |
| 2b. Máximo 4 posiciones si BTC cae en 7 días | +65,98 | +115,77 | +24,01 | +20,89 | +436,80 | −5,45 | 32 | 7 | +0,42 | −2,54 | +1,32 | −0,84 | K1 K2 K4 K6 K9 |
| 2a. Máximo 3 posiciones si BTC cae en 7 días | +65,27 | +111,37 | +19,85 | +19,85 | +401,80 | −5,45 | 31 | 7 | +0,42 | −2,54 | +0,45 | −1,69 | K1 K2 K3 K4 K6 K9 |
| 3b. Parar la semana al perder 1,5 % | +66,94 | +83,46 | +18,19 | +21,44 | +339,60 | −5,45 | 31 | 7 | +0,42 | −2,54 | +1,79 | −0,38 | K1 K2 K3 K6 |
| 3a. Parar el mes al perder 2 % | +69,86 | +114,72 | +20,30 | +21,76 | +434,30 | −5,45 | 32 | 7 | +0,42 | −2,16 | +1,66 | −0,12 | K2 K3 K6 K9 |
| 4. Percentil 95 cuando BTC cae en 7 días | +65,24 | +139,30 | +19,55 | +17,24 | +454,30 | −5,45 | 30 | 5 | −0,36 | −2,62 | −0,87 | −3,81 | K1 K3 K4 K6 K7 K9 |
| 5c. La moneda está sobre su EMA de 50 días | +46,31 | +118,16 | +9,25 | +17,55 | +309,90 | −3,57 | 24 | 4 | +0,42 | −2,16 | 0 | −1,75 | K1 K2 K3 K4 K6 K7 K9 |
| 5b. La moneda está en la mitad más fuerte (7 días) | +60,07 | +95,88 | +17,74 | +16,29 | +329,30 | −4,47 | 26 | 3 | −0,48 | −2,42 | +1,57 | −1,36 | K1 K2 K3 K4 K6 K7 K9 |
| 5a. La moneda subió en 7 días | +48,71 | +92,62 | +1,19 | +19,09 | +245,10 | −6,97 | 22 | 3 | −0,08 | −1,67 | +0,98 | −0,79 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 6c. Régimen fuerte: BTC sobre su EMA de 50 horas | +34,49 | +101,15 | +11,58 | +21,27 | +266,00 | −5,73 | 26 | 6 | −0,57 | −2,02 | +2,68 | +0,03 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 6b. Régimen fuerte: BTC subió en 7 días | +46,76 | +81,77 | +3,97 | +18,47 | +228,60 | −6,81 | 25 | 5 | −0,36 | −2,46 | 0 | −2,81 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 6a. Régimen fuerte: BTC subió en 24 h | +30,57 | +103,08 | +7,92 | +22,17 | +249,60 | −6,84 | 28 | 7 | +0,53 | −2,05 | +2,68 | +1,11 | K1 K2 K3 K5 K6 |
| 7. Salir cuando el régimen se apaga | +74,22 | +125,18 | +19,30 | +21,75 | +469,80 | −3,48 | 32 | 6 | +0,42 | −2,54 | +2,37 | +0,19 | K3 K6 K7 |
| 8b. Stop de catástrofe a 8 ATR | +59,95 | +121,65 | +13,48 | +18,30 | +376,00 | −7,35 | 31 | 6 | +0,44 | −2,14 | −1,04 | −2,73 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 8a. Stop de catástrofe a 6 ATR | +61,20 | +113,08 | +4,63 | +15,40 | +314,70 | −8,30 | 28 | 5 | +0,53 | −2,30 | −1,72 | −3,47 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 9. Menos tamaño cuando el ATR está sobre su mediana de 30 días | +44,13 | +76,21 | +11,56 | +11,01 | +214,50 | −4,21 | 33 | 7 | +0,50 | −2,58 | +2,17 | +0,03 | K1 K2 K3 K4 K9 |
| 10b. Percentil 95 si las últimas 10 operaciones pierden en promedio | +65,20 | +100,33 | −7,76 | +11,56 | +240,60 | −9,06 | 21 | 5 | −0,86 | −0,49 | −0,89 | −2,22 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 10a. Percentil 95 si las últimas 6 operaciones pierden en promedio | +58,09 | +91,48 | −7,76 | +12,13 | +213,10 | −9,06 | 22 | 5 | −0,35 | −0,49 | −0,89 | −1,72 | K1 K2 K3 K4 K5 K6 K7 K9 |
| 11. Acuerdo con el modelo de peso reciente | +56,60 | +160,54 | +27,42 | +16,76 | +507,00 | −5,45 | 30 | 5 | −0,61 | −2,84 | +0,17 | −3,27 | K1 K4 K6 K7 K9 |
| 12. Acuerdo con el modelo de amplitud de mercado | +79,72 | +111,81 | +20,53 | +21,90 | +459,30 | −3,68 | 32 | 7 | +0,81 | −2,54 | +1,79 | +0,01 | K2 K6 |
| 12b. Modelo de amplitud: basta con que prediga subida | +80,11 | +111,81 | +20,53 | +21,44 | +458,40 | −3,68 | 32 | 7 | +0,42 | −2,54 | +1,79 | −0,38 | K2 K6 |
| 12c. Modelo de amplitud solo si BTC cae en 7 días | +71,76 | +123,76 | +20,53 | +21,22 | +461,50 | −5,45 | 33 | 7 | +0,24 | −2,54 | +1,79 | −0,56 | K2 K4 K9 |
| 12d. Modelo de amplitud solo en régimen fuerte | +79,42 | +111,81 | +20,53 | +21,90 | +458,40 | −3,68 | 32 | 7 | +0,81 | −2,54 | +1,79 | +0,01 | K2 K6 |
| 12e. Modelo de amplitud solo fuera del régimen fuerte | +70,15 | +124,31 | +20,53 | +21,44 | +458,60 | −5,45 | 33 | 7 | +0,42 | −2,54 | +1,79 | −0,38 | ninguna |
| 7b. Salir al apagarse el régimen, solo compras hechas en régimen fuerte | +74,11 | +125,18 | +19,30 | +22,14 | +471,30 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 | +0,19 | K3 |
| 7c. Salir al apagarse el régimen solo si la posición va perdiendo | +77,07 | +125,18 | +19,84 | +21,75 | +481,80 | −3,48 | 32 | 6 | +0,42 | −2,54 | +2,37 | +0,19 | K3 K6 K7 |
| 7d. Como 7b, y solo si la posición va perdiendo | +77,48 | +125,18 | +19,84 | +22,14 | +485,00 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 | +0,19 | K3 |
| 7e. Salir si BTC pierde su media de 200 días y la posición va perdiendo (compras en régimen fuerte) | +77,48 | +127,43 | +19,84 | +22,14 | +490,80 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 | +0,19 | K3 |
| 3c. Parar el mes al perder 2,5 % | +69,86 | +124,31 | +20,30 | +21,29 | +456,00 | −5,45 | 33 | 7 | +0,42 | −2,54 | +1,66 | −0,51 | K3 K4 K9 |
| 1b. Sin fin de semana solo si BTC cae en 7 días | +65,63 | +100,72 | +16,14 | +22,36 | +372,40 | −7,05 | 30 | 7 | +0,82 | −2,54 | +1,79 | +0,02 | K1 K2 K3 K5 K6 |

Combinaciones: 93.612 probadas. Solo 2 no empeoran nada (el punto de partida y la 12e, que no cambia septiembre a
noviembre). **Ninguna cumple todas las condiciones y además sube los tres meses.** 24.680 suben la suma de los tres
meses, pero rompen al menos una condición.

Las que menos rompen:

| Combinación | 2023 | 2024 | 2025 | 2026 | Total | Caída máx. | Meses + (47) | Meses + 2026 | Sep | Oct | Nov | Falla |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Punto de partida | +69,86 | +124,31 | +20,53 | +21,44 | +457,7 | −5,45 | 33 | 7 | +0,42 | −2,54 | +1,79 | |
| **7e** | +77,48 | +127,43 | +19,84 | +22,14 | +490,8 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 | K3 |
| 7d | +77,48 | +125,18 | +19,84 | +22,14 | +485,0 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 | K3 |
| 7b | +74,11 | +125,18 | +19,30 | +22,14 | +471,3 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 | K3 |
| 12+7b+3a | +76,78 | +112,64 | +19,06 | +22,93 | +450,2 | −3,68 | 33 | 7 | +0,81 | −2,16 | +2,25 | K2 K3 |
| 12 | +79,72 | +111,81 | +20,53 | +21,90 | +459,3 | −3,68 | 32 | 7 | +0,81 | −2,54 | +1,79 | K2 K6 |

La más cercana es la 7e: si BTC cierra bajo su media de 200 días y la posición va perdiendo, se vende en la apertura
siguiente (solo compras hechas en régimen fuerte). Cambia 18 operaciones entre 2023 y 2026 y 14 salen mejor; las que
salen peor son dos de marzo de 2025 (DOGE de +4,94 % a −1,65 % y SOL de +7,03 % a −2,37 %) y dos de octubre de 2025.
Por eso 2025 baja de +20,53 % a +19,84 % (0,69 puntos) y falla K3. Ninguna variante de esa regla (umbral de pérdida,
confirmación con el modelo de 24 h o con BTC, stop mensual) recupera 2025.

Septiembre y octubre no mejoran con ninguna regla que respete las condiciones: sus pérdidas vienen de compras en
régimen fuerte que el modelo dio por buenas, y los filtros que las quitan también quitan ganadoras de 2023 y 2024.

**Decisión:** se acepta la 7e como versión final, con 2025 0,69 puntos más bajo. Total +490,8 %, caída máxima
−3,48 %, 33 meses positivos de 47 y 7 de 11 en 2026.


## Subir octubre y noviembre de 2026 sin empeorar nada

Código: `meses9.py`. Punto de partida: la versión final (7e de `meses8.py`). Condiciones, todas frente a ella: 2023,
2024, 2025 y 2026 no ganan menos (K1 a K4); la caída máxima no sube (K5); los meses positivos de 47 no bajan de 33
(K6); los de 2026 no bajan de 7 (K7); ningún mes de 2026 que hoy es positivo pasa a negativo (K8); ni octubre ni
noviembre empeoran (K9). Meta: subir octubre (hoy −2,54 %) y noviembre (hoy +2,37 %, hasta el día 13); lo ideal es
octubre positivo.

Las pérdidas de octubre son cinco compras en régimen fuerte, con BTC entre 13 % y 21 % sobre su media de 200 días:

| Compra | Moneda | Resultado | Mejor momento | Peor momento |
|---|---|---|---|---|
| 2 oct 15:00 | SOL | −1,14 % | +1,36 % | −2,93 % |
| 5 oct 00:00 | BNB | −3,08 % | +1,83 % | −4,63 % |
| 5 oct 00:00 | ETH | −5,79 % | +0,41 % | −6,93 % |
| 7 oct 02:00 | XRP | −4,75 % | +0,12 % | −10,65 % |
| 13 oct 14:00 | XRP | −2,26 % | +1,77 % | −5,78 % |

Ninguna llegó a ir ganando de forma apreciable, así que las salidas (objetivo, punto de equilibrio, cortes) no las
arreglan: solo sirve no comprarlas. La pérdida de noviembre es una compra de BTC del día 10 (−2,59 %), hecha con BTC
a 3 % de su media de 200 días y cayendo.

### Diez sugerencias, de menor a mayor complejidad

| # | Sugerencia | Qué cambia |
|---|---|---|
| 1 | Margen en el modelo de 24 h | Debe predecir una subida mayor que un mínimo, no solo mayor que cero |
| 2 | Margen sobre el percentil | La predicción de 72 h debe superar el umbral por un porcentaje |
| 3 | Freno por caída de BTC | Sin compras dentro de régimen si BTC cayó más de x % en 24 h |
| 4 | Filtro de volatilidad | Sin compras si el ATR de la moneda está lejos de su mediana de 30 días |
| 5 | Persistencia de la señal | La señal debe llevar 2 o 3 horas seguidas activa |
| 6 | Corte por tiempo | A las 24 o 48 h, vender si la compra pierde más de 4 o 6 ATR |
| 7 | Salida por señal | Vender una compra que va perdiendo si el modelo pasa a predecir caída |
| 8 | No sumar a pérdidas | Sin compras nuevas si las posiciones abiertas pierden en promedio más de x % |
| 9 | Reentreno quincenal | Modelos nuevos el día 1 y el día 16 |
| 10 | Segundo modelo | Un clasificador predice si la operación termina ganando con las salidas reales |

Resultados por separado. Las variantes 2d, 2e, 3d, 3e y 3f son una segunda ronda (versiones más finas de la 2 y la
3) y la 11 salió de una tercera ronda de búsqueda de reglas, descrita más abajo. En negrita, las que no rompen nada:

| Variante | 2023 | 2024 | 2025 | 2026 | Total | Caída máx. | Meses + (47) | Meses + 2026 | Sep | Oct | Nov | Falla |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Punto de partida (versión final) | +77,48 | +127,43 | +19,84 | +22,14 | +490,8 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 |  |
| 1a. El modelo de 24 h predice más de +0,02 % | +76,64 | +119,82 | +19,84 | +22,11 | +468,2 | −3,48 | 33 | 7 | +0,42 | −2,53 | +2,37 | K1 K2 K4 |
| 1b. El modelo de 24 h predice más de +0,05 % | +77,37 | +121,11 | +19,96 | +21,24 | +470,4 | −3,48 | 32 | 6 | −0,58 | −2,53 | +2,37 | K1 K2 K4 K6 K7 K8 |
| 1c. El modelo de 24 h predice más de +0,10 % | +80,98 | +106,58 | +15,89 | +20,42 | +421,7 | −3,61 | 32 | 6 | −0,58 | −3,05 | +2,25 | K2 K3 K4 K5 K6 K7 K8 K9 |
| 2a. Predicción 3 % sobre el umbral | +78,38 | +138,93 | +18,46 | +21,61 | +514,0 | −3,48 | 33 | 7 | +0,82 | −2,53 | +2,37 | K3 K4 |
| 2b. Predicción 5 % sobre el umbral | +80,26 | +141,53 | +20,49 | +21,77 | +538,8 | −3,48 | 33 | 7 | +0,82 | −2,53 | +2,50 | K4 |
| 2c. Predicción 10 % sobre el umbral | +78,99 | +123,19 | +25,64 | +19,04 | +497,5 | −3,91 | 30 | 6 | +0,82 | −3,05 | +2,38 | K2 K4 K5 K6 K7 K9 |
| **2d. Predicción 5 % sobre el umbral, solo en régimen fuerte** | +79,17 | +141,53 | +20,49 | +22,79 | +540,2 | −3,48 | 33 | 7 | +0,82 | −2,53 | +2,50 | ninguna |
| **2e. Predicción 6 % sobre el umbral, solo en régimen fuerte** | +81,93 | +139,10 | +20,32 | +22,79 | +542,6 | −3,48 | 33 | 7 | +0,82 | −2,53 | +2,50 | ninguna |
| 3a. Sin compras en régimen si BTC cayó más de 2 % en 24 h | +57,57 | +121,96 | −2,99 | +22,16 | +314,5 | −8,93 | 27 | 6 | +0,42 | −2,54 | +2,68 | K1 K2 K3 K5 K6 K7 |
| 3b. Sin compras en régimen si BTC cayó más de 3 % en 24 h | +58,94 | +126,82 | +8,62 | +22,05 | +378,0 | −8,93 | 28 | 6 | +0,42 | −2,54 | +2,59 | K1 K2 K3 K4 K5 K6 K7 |
| 3c. Sin compras en régimen si BTC cayó más de 4 % en 24 h | +68,81 | +126,28 | +2,34 | +21,80 | +376,1 | −13,12 | 29 | 6 | +0,42 | −2,54 | +2,37 | K1 K2 K3 K4 K5 K6 K7 |
| 3d. Régimen fuerte: sin compras si BTC está a menos de 3 % de su media de 200 días y cayó en 24 h | +77,12 | +128,39 | +20,17 | +22,65 | +496,3 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,80 | K1 |
| **3e. Régimen fuerte: sin compras si BTC está a menos de 3 % de su media y cayó más de 2 % en 24 h** | +77,48 | +128,39 | +19,98 | +22,65 | +496,5 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,80 | ninguna |
| **3f. Régimen fuerte: sin compras si BTC está a menos de 5 % de su media y cayó más de 2 % en 24 h** | +77,48 | +128,39 | +23,43 | +22,65 | +513,7 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,80 | ninguna |
| 4a. Sin compras si el ATR está bajo 0,6 veces su mediana de 30 días | +84,24 | +122,63 | +19,43 | +20,82 | +491,9 | −4,95 | 32 | 6 | +0,82 | −3,33 | +2,25 | K2 K3 K4 K5 K6 K7 K8 K9 |
| 4b. Sin compras si el ATR está bajo 0,75 veces su mediana de 30 días | +82,80 | +144,44 | +15,55 | +21,94 | +529,6 | −4,04 | 33 | 7 | +0,82 | −3,29 | +2,52 | K3 K4 K5 K9 |
| 4c. Sin compras si el ATR está sobre 1,5 veces su mediana de 30 días | +46,16 | +65,74 | +7,23 | +0,31 | +160,6 | −5,19 | 23 | 4 | +1,24 | −2,54 | +2,68 | K1 K2 K3 K4 K5 K6 K7 K8 |
| 5a. Señal activa 2 horas seguidas | +65,52 | +104,69 | +24,87 | +12,68 | +376,7 | −4,94 | 27 | 4 | −1,37 | −3,04 | +2,98 | K1 K2 K4 K5 K6 K7 K8 K9 |
| 5b. Señal activa 3 horas seguidas | +31,83 | +97,32 | +24,42 | +13,08 | +266,0 | −4,98 | 24 | 4 | −1,84 | −3,20 | +2,90 | K1 K2 K4 K5 K6 K7 K8 K9 |
| 6a. A las 24 h, vender si pierde más de 4 ATR | +78,03 | +134,98 | +21,60 | +19,21 | +506,4 | −3,48 | 34 | 7 | +0,42 | −2,38 | +0,46 | K4 K9 |
| 6b. A las 24 h, vender si pierde más de 6 ATR | +78,30 | +133,90 | +23,99 | +21,20 | +526,7 | −3,48 | 33 | 7 | +0,42 | −2,54 | +1,58 | K4 K9 |
| 6c. A las 48 h, vender si pierde más de 4 ATR | +71,23 | +115,20 | +16,04 | +19,99 | +413,1 | −5,54 | 32 | 7 | +0,43 | −3,16 | +1,74 | K1 K2 K3 K4 K5 K6 K9 |
| 6d. A las 48 h, vender si pierde más de 6 ATR | +73,29 | +118,26 | +19,43 | +21,97 | +450,9 | −4,14 | 32 | 7 | +0,50 | −2,75 | +2,37 | K1 K2 K3 K4 K5 K6 K9 |
| 7a. Vender si va perdiendo y la predicción cae al 10 % más bajo | +67,76 | +132,44 | +23,59 | +21,14 | +483,8 | −3,54 | 33 | 7 | +0,42 | −3,24 | +2,25 | K1 K4 K5 K9 |
| 7b. Vender si va perdiendo y la predicción cae al 5 % más bajo | +70,96 | +128,24 | +25,08 | +22,14 | +496,1 | −3,40 | 33 | 7 | +0,42 | −2,54 | +2,37 | K1 |
| 7c. Vender si va perdiendo y los modelos de 72 h y 24 h predicen caída | +52,42 | +127,72 | +20,66 | +13,96 | +377,3 | −5,14 | 28 | 4 | −0,83 | −2,45 | −1,94 | K1 K4 K5 K6 K7 K8 K9 |
| 8a. Sin compras nuevas si las abiertas pierden más de 1 % en promedio | +65,21 | +131,30 | +10,90 | +20,05 | +408,8 | −3,63 | 30 | 5 | −0,47 | −1,75 | +2,37 | K1 K3 K4 K5 K6 K7 K8 |
| 8b. Sin compras nuevas si las abiertas pierden más de 2 % en promedio | +64,52 | +113,30 | +7,97 | +20,05 | +354,8 | −8,84 | 29 | 5 | −0,47 | −1,75 | +2,37 | K1 K2 K3 K4 K5 K6 K7 K8 |
| 8c. Sin compras nuevas si las abiertas pierden más de 3 % en promedio | +65,92 | +110,06 | +8,12 | +22,14 | +360,2 | −8,84 | 30 | 7 | +0,42 | −2,54 | +2,37 | K1 K2 K3 K5 K6 |
| 9. Reentreno quincenal (días 1 y 16) | +80,21 | +92,16 | +18,36 | +11,03 | +355,1 | −9,86 | 30 | 7 | −2,35 | −2,71 | +1,16 | K2 K3 K4 K5 K6 K8 K9 |
| 10a. Segundo modelo: probabilidad de ganar mayor que 50 % | +28,51 | +109,77 | +28,04 | +24,84 | +330,9 | −3,77 | 28 | 6 | +1,08 | −1,37 | +2,68 | K1 K2 K5 K6 K7 |
| 10b. Segundo modelo: probabilidad de ganar mayor que 55 % | +31,15 | +111,24 | +32,20 | +23,29 | +351,6 | −3,67 | 30 | 6 | +0,79 | −1,48 | +1,52 | K1 K2 K5 K6 K7 K9 |
| 10c. Segundo modelo: probabilidad de ganar sobre su percentil 90 | +23,86 | +87,70 | +31,84 | +20,74 | +270,1 | −3,78 | 29 | 5 | 0 | 0 | +1,10 | K1 K2 K4 K5 K6 K7 K9 |
| 11a. Régimen fuerte: sin compras si la dispersión es menor que 2 % y BTC está más de 10 % sobre su media | +77,84 | +127,43 | +19,84 | +24,63 | +504,1 | −3,48 | 33 | 7 | +0,42 | −0,43 | +2,25 | K9 |
| 11b. Régimen fuerte: sin compras si la dispersión es menor que 2,5 % y BTC está más de 10 % sobre su media | +78,73 | +127,43 | +20,48 | +25,53 | +514,8 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,25 | K9 |
| 11c. Régimen fuerte: sin compras si la dispersión es menor que 3 % y BTC está más de 10 % sobre su media | +77,36 | +127,33 | +19,78 | +25,53 | +506,2 | −3,50 | 33 | 7 | +0,82 | −0,11 | +2,25 | K1 K2 K3 K5 K9 |
| **11d. Régimen fuerte: sin compras si la dispersión es menor que 2,5 % y BTC está más de 12,5 % sobre su media** | +78,73 | +127,43 | +20,48 | +25,19 | +513,1 | −3,48 | 33 | 7 | +0,42 | −0,11 | +2,37 | ninguna |

### Combinaciones

Se probaron 215.808 combinaciones: todas las de las diez sugerencias sin la 5 ni la 9 (que empeoran casi todo), con
las variantes de la segunda ronda, y las de la 11 con las que quedaron más cerca.

| Resultado | Combinaciones |
|---|---|
| No empeoran nada (K1 a K9) | 99 |
| Además suben octubre y noviembre | 95 |
| Dejan octubre en positivo | 0 |

Las 99 que no empeoran nada usan solo las reglas 1a, 2b, 2d, 2e, 3d, 3e, 3f y 11. Las que más suben:

| Combinación | 2023 | 2024 | 2025 | 2026 | Total | Caída máx. | Meses + (47) | Meses + 2026 | Sep | Oct | Nov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Versión final | +77,48 | +127,43 | +19,84 | +22,14 | +490,8 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,37 |
| 2d+3f+11d | +81,24 | +142,56 | +22,92 | +26,38 | +582,9 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,93 |
| 2e+3f+11d | +82,26 | +140,12 | +23,32 | +26,38 | +582,0 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,93 |
| 2d+3e+11d | +81,24 | +142,56 | +21,35 | +26,38 | +574,2 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,93 |
| 2d+3f+11b | +81,24 | +142,56 | +22,92 | +26,23 | +582,1 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,81 |
| **2d+3e+11b** | +81,24 | +142,56 | +21,35 | +26,23 | +573,4 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,81 |
| 2d+3e+11c | +79,72 | +142,44 | +20,64 | +26,23 | +563,5 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,81 |
| 3e+11b | +78,73 | +128,39 | +20,62 | +26,06 | +520,7 | −3,48 | 33 | 7 | +0,82 | −0,11 | +2,68 |
| 2d+3e | +79,17 | +142,56 | +20,69 | +23,30 | +546,7 | −3,48 | 33 | 7 | +0,82 | −2,53 | +2,93 |
| 2e+3f | +81,93 | +140,12 | +22,65 | +23,30 | +560,6 | −3,48 | 33 | 7 | +0,82 | −2,53 | +2,93 |
| 3e | +77,48 | +128,39 | +19,98 | +22,65 | +496,5 | −3,48 | 33 | 7 | +0,42 | −2,54 | +2,80 |
| 11d | +78,73 | +127,43 | +20,48 | +25,19 | +513,1 | −3,48 | 33 | 7 | +0,42 | −0,11 | +2,37 |

Sin la 11, octubre no se mueve (de −2,54 % a −2,53 %): las 22 combinaciones de las diez sugerencias que cumplen
todo solo suben noviembre y septiembre.

### Lo que cumple todo

Tres reglas de entrada, todas para el régimen fuerte, cumplen las condiciones y se suman entre sí:

| Regla | Qué hace | Operaciones que cambia (2023 a 2026) |
|---|---|---|
| **2d. Margen de 5 %** | La predicción debe superar el percentil 90 por un 5 % | Quita 61 y añade 45 (muchas solo se retrasan una hora) |
| **3e. Freno cerca de la media** | Sin compras si BTC está a menos de 3 % sobre su media de 200 días y cayó más de 2 % en 24 h | Quita 6: cinco perdedoras y una ganadora |
| **11b. Monedas moviéndose igual** | Sin compras si la desviación estándar de las subidas de 7 días de las seis monedas es menor que 2,5 % y BTC está más de 10 % sobre su media de 200 días | Quita 11 y añade 4 |

| Medida | Versión final | 2d+3e | 3e+11b | **2d+3e+11b** |
|---|---|---|---|---|
| 2023 | +77,48 % | +79,17 % | +78,73 % | **+81,24 %** |
| 2024 | +127,43 % | +142,56 % | +128,39 % | **+142,56 %** |
| 2025 | +19,84 % | +20,69 % | +20,62 % | **+21,35 %** |
| 2026 | +22,14 % | +23,30 % | +26,06 % | **+26,23 %** |
| Total | +490,8 % | +546,7 % | +520,7 % | **+573,4 %** |
| Caída máxima | −3,48 % | −3,48 % | −3,48 % | **−3,48 %** |
| Meses positivos de 47 | 33 | 33 | 33 | **33** |
| Meses positivos de 2026 | 7 | 7 | 7 | **7** |
| Septiembre de 2026 | +0,42 % | +0,82 % | +0,82 % | **+0,82 %** |
| Octubre de 2026 | −2,54 % | −2,53 % | −0,11 % | **−0,11 %** |
| Noviembre de 2026 | +2,37 % | +2,93 % | +2,68 % | **+2,81 %** |
| 2022 (fuera de las tablas) | +1,54 % | +1,54 % | +1,54 % | +1,54 % |

Operaciones que quita la 3e (con la 2d ya puesta). Las cinco perdedoras son las mismas que la salida de
protección ya vendía con pérdida: la 3e es esa misma idea aplicada a la entrada.

| Compra | Moneda | Resultado que tenía |
|---|---|---|
| 30 sep 2024 | DOGE | −2,67 % |
| 13 mar 2025 | ETH | +4,36 % |
| 28 mar 2025 | BNB | −1,12 % |
| 28 mar 2025 | ETH | −0,37 % |
| 3 nov 2025 | DOGE | −3,74 % |
| 10 nov 2026 | BTC | −2,59 % |

Operaciones que cambia la 11b (con la 2d y la 3e ya puestas):

| Compra | Moneda | Antes | Después |
|---|---|---|---|
| 29 ene 2023 | XRP | −2,14 % | Entra el 30 ene: +3,63 % |
| 30 ene 2023 | SOL | −1,91 % | Entra 8 h después: −0,95 % |
| 1 may 2023 | XRP | −0,30 % | No se compra |
| 8 may 2023 | XRP | −2,51 % | Entra 2 h después: −2,70 % |
| 8 ene 2025 | SOL | −3,57 % | No se compra |
| 28 sep 2026 | DOGE | +1,79 % | Entra el 29 sep: +1,62 % |
| 2 oct 2026 | SOL | −1,14 % | No se compra |
| 5 oct 2026 | BNB | −3,03 % | No se compra |
| 5 oct 2026 | ETH | −5,82 % | No se compra |
| 7 oct 2026 | XRP | −4,75 % | No se compra |
| 29 oct 2026 | XRP | +0,74 % | No se compra |

Octubre queda en −0,11 %: una compra de DOGE (+1,62 %) y la de XRP del 13 de octubre (−2,26 %), que ninguna regla
quita sin romper otra condición.

Sensibilidad (sobre 2d+3e; «sí» es que cumple K1 a K9):

| Regla | Valores que cumplen | Valores que no cumplen |
|---|---|---|
| 2d, margen | 5 % y 6 % | 1 % a 4 % (2025 baja a +18,2 %), 7 % (octubre −2,63 %), 8 % o más |
| 3e, distancia a la media y caída de BTC | 3 % con caída de 0 a 3 %; 5 % con caída de 2 o 3 % | 5 % con caída de 0 o 1 % (2025 baja), 8 % o más |
| 11b, dispersión y distancia de BTC a su media | Dispersión de 1,5 % a 3,5 % con BTC de 10 % a 15 % sobre la media | Dispersión de 4 %, 5 % y 6 % (con 4,5 % sí cumple); BTC a 5 % sobre la media |

### Lo que no funcionó

- **Octubre positivo:** ninguna combinación de las diez lo logra. En la búsqueda de reglas, un solo par de 131.995
  lo deja en +0,05 % sin romper nada (moneda menos de 8,5 % por encima de BTC en 30 días y más de 52,4 % de volumen
  comprador en 24 h); es un punto aislado, sin vecinos que cumplan, y no se propone.
- **Salidas (6 y 7) y no sumar a pérdidas (8):** bajan noviembre o los años anteriores. Las compras del 2 de
  noviembre iban perdiendo cerca de 2 % a las 24 h y terminaron ganando.
- **Reentreno quincenal (9):** peor en casi todo; 2024 baja de +127 % a +92 %.
- **Segundo modelo (10):** es lo que más sube octubre entre las diez (−1,37 % con 10a; sin operaciones con 10c),
  pero 2023 cae de +77 % a +24 %–+31 %.
- **Más de 100 variantes sueltas:** salidas por caída de BTC o de las monedas en 4 h, 24 h o 7 días, filtros de
  sobreextensión, tope de posiciones en régimen fuerte, duración de 60 a 120 h, objetivo de 10 a 14 ATR y
  renovación más flexible. Todas rompen al menos una condición.

### Avisos

- **La 11b salió de una búsqueda de 132.599 reglas** (604 condiciones sobre 28 variables y 131.995 pares). Con tantas
  pruebas, alguna regla cumple por azar. A su favor: no es un punto aislado (cumple toda una zona de umbrales) y
  también quita perdedoras de 2023 y 2025. En contra: cambia 15 operaciones y 6 son de septiembre y octubre de 2026,
  justo los meses que se querían mejorar.
- **La 2d es un ajuste fino:** cumple con 5 % y 6 %, y falla con 4 % y con 7 %. Su ganancia (+50 puntos de total)
  viene de 2024 y es la menos fiable de las tres.
- **La 3e se apoya en 6 operaciones** y la más simple de explicar: es la salida de protección aplicada a la entrada.
- **2022 no cambia** con ninguna de las tres (casi no hubo régimen fuerte): no hay un año fuera de muestra que las
  confirme.
- Octubre no llega a positivo: queda en −0,11 %.

**Decisión:** se adopta la 2d+3e+11b como estrategia vigente (etapa 9). Total +573,4 %, caída máxima −3,48 %, 33
meses positivos de 47 y 7 de 11 en 2026. Octubre de 2026 queda en −0,11 % y noviembre en +2,81 %. La versión final
anterior (7e) queda como base de comparación.
