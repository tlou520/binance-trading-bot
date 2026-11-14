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
