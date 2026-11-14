# Estrategia de retrocesos del video "150 dólares en una semana"

Backtest de la estrategia de *scalping* del video con velas reales de 1 min de Binance spot, del 2023-01-01 al
2026-11-12. Código en `binance-research/pullback/`.

## Conclusión

**No se usa.** Ninguna de las 12.288 combinaciones probadas gana de forma estable después de costos:

- La lectura literal del video (stop de 0,15 %, objetivo 1:1) pierde en el 99,7 % de las operaciones. La comisión de
  ida y vuelta (0,24 %) es mayor que la distancia al objetivo, así que hasta los aciertos pierden dinero.
- Con stops más amplios y objetivos más lejanos, la ganancia **antes de costos** queda cerca de cero (la mejor, +0,12 %
  por operación) y no alcanza a pagar el 0,24 %.
- Ninguna combinación tiene ganancia neta positiva los 4 años. En 2026 solo el 1,7 % gana, y esas mismas pierden en
  otros años: 2026 favoreció los cortos y en 2024 fueron las que más perdieron.
- Elegidas sin mirar el año juzgado (walk-forward), las combinaciones pierden en 2024, 2025 y 2026, y lo hacen peor
  que entradas al azar con las mismas salidas.

## Reglas implementadas

Todo lo programable de la transcripción (ver el inventario de 26 elementos en la conversación). Las decisiones usan
solo velas ya cerradas y la entrada es en la apertura de la vela siguiente.

| Bloque | Regla |
|---|---|
| Monedas | BTC, ETH, BNB, XRP, SOL y DOGE |
| Dirección en 1 h | **A. Tendencia:** cierre al lado bueno de la EMA 50, EMA 50 a favor en 3 horas y mínimos crecientes. **B. Reversión:** ataque rápido (>= 3 ATR) a un mínimo previo de los últimos 30 días, mecha de rechazo >= 40 % ("*low test*") y precio bajo la EMA 50; objetivo en la EMA 50. **C. Rango:** 24 horas dentro de 2 a 6 ATR y precio en el 30 % inferior; objetivo en la parte alta |
| Estructura en 5 min | Impulso de >= 2 o 3 ATR con una vela de cuerpo >= 1 ATR, luego retroceso del 30 % al 70 % que no pierde el inicio del impulso |
| Gatillo | En 1 min (o 5 min): cierre sobre el máximo de las 3 velas anteriores y sobre la EMA 50. Una entrada por impulso |
| Stop | Bajo el mínimo del retroceso, con distancia mínima de 0,6 %, 1,2 % o 2 %; o el 0,15 % fijo del video |
| Objetivo | 1, 1,5, 2 o 3 veces el riesgo (en B y C, el nivel, si está a esa distancia o más) |
| Gestión | Opcional: stop a la entrada al avanzar 0,6 R y salida si en 30 min no avanzó 0,3 R. Salida a las 4 o 24 horas |
| Filtros | Horario europeo (6 a 16 UTC), sin operar de 30 min antes a 60 min después de FOMC y empleo de EE. UU., BTC a favor para altcoins |
| Reglas del video | Una posición a la vez entre todas las monedas, máximo 2 por día, no operar más tras ganar 2 R en el día |
| Costos | 0,24 % por ida y vuelta (comisión 0,1 % por lado más deslizamiento) |

No se programó lo que el video no define o no tiene datos: patrones mayores (cuñas) y libro de órdenes. El calendario
del CPI no se pudo descargar (bls.gov bloquea el acceso); el filtro usa FOMC y empleo.

## Resultados

### Lectura literal del video

A, B y C juntos, gatillo en 1 min, stop 0,15 %, 1:1, gestión, horario europeo, filtro de noticias y reglas del video.

| Año | Operaciones | Acierto | Ganancia media neta |
|---|---|---|---|
| 2023 | 728 | 0,4 % | −0,231 % |
| 2024 | 732 | 0,3 % | −0,242 % |
| 2025 | 729 | 0,1 % | −0,240 % |
| 2026 | 632 | 0,3 % | −0,241 % |
| **Total** | **2.821** | **0,3 %** | **−0,238 %** |

Con el riesgo del video (10 % por operación), 100 USDT quedan en 0,12 USDT.

### Walk-forward (solo largos, lo que el bot puede operar en spot)

La combinación de cada año se elige con el mejor t por día en los años anteriores (mínimo 60 operaciones).

| Año juzgado | Combinación elegida | Operaciones | Acierto | Ganancia media | t por día | 100 USDT al 1 % |
|---|---|---|---|---|---|---|
| 2024 | C, gatillo 1 min, stop 2 %, 3R, gestión, 4 h, filtro de noticias | 156 | 22,4 % | −0,416 % | −2,47 | 72,07 |
| 2025 | C, gatillo 5 min, stop 0,6 %, 3R, 24 h, horario europeo, BTC a favor | 53 | 18,9 % | −0,262 % | −1,14 | 87,34 |
| 2026 | B, gatillo 5 min, stop 1,2 %, 1R, 24 h, BTC a favor | 18 | 22,2 % | −0,675 % | −2,66 | 90,29 |
| **Total** | | **227** | **21,6 %** | **−0,401 %** | **−3,37** | **56,83** |

Entradas al azar con las mismas salidas: −0,059 % por operación. La estrategia pierde más que el azar. Permitiendo
también cortos, el total es casi igual (220 operaciones, −0,383 %).

### Lo que pasa si se elige mirando 2026

Las combinaciones con mejor resultado en 2026 son cortos de los modos B y C con stop de 2 % y objetivo 2R
(+1,0 % a +1,1 % por operación, unas 30 operaciones). En 2024 esas mismas perdieron entre −0,4 % y −0,8 % por
operación. Elegir así es ajustar al pasado: no dice nada del futuro.

## Cómo reproducirlo

Ver `binance-research/pullback/README.md`.
