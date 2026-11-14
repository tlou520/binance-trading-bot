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
