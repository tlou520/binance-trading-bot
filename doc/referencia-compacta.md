# Referencia compacta del proyecto

Este documento reúne en un solo archivo el contenido de nueve documentos anteriores, condensado:

| Documento anterior | Sección aquí |
|---|---|
| `introduccion-al-trading.md` | [1](#1-conceptos-básicos-de-trading) |
| `matematica-del-bot.md` | [2](#2-matemática-del-bot) |
| `agente-rl-y-esperanza-positiva.md` | [3](#3-agente-rl-y-esperanza-positiva) |
| `estrategia-v3-hacia-el-80.md` | [4](#4-estrategia-v3) |
| `resultados-v3-2026-10-24.md` | [5](#5-resultados-de-la-v3-al-2026-10-24) |
| `estrategia-extremos.md` | [6](#6-estrategia-de-extremos-video-de-youtube) |
| `estrategia-pullback.md` | [7](#7-estrategia-de-retrocesos-video-150-dólares-en-una-semana) |
| `plan-analogos.md` y `resultados-analogos.md` | [8](#8-predicción-por-análogos) |

Los documentos completos siguen disponibles en el historial de git (el commit anterior a esta compactación). Se conservan los números de sección (`§14`, `sección 2.10`, etc.) para que las referencias desde el código sigan apuntando al lugar correcto. Los documentos que **no** se tocaron son [`resumen-ilustrado.md`](resumen-ilustrado.md) y [`estrategias-multimarco.md`](estrategias-multimarco.md).

**Índice**

1. [Conceptos básicos de trading](#1-conceptos-básicos-de-trading)
2. [Matemática del bot](#2-matemática-del-bot)
3. [Agente RL y esperanza positiva](#3-agente-rl-y-esperanza-positiva)
4. [Estrategia v3](#4-estrategia-v3)
5. [Resultados de la v3 al 2026-10-24](#5-resultados-de-la-v3-al-2026-10-24)
6. [Estrategia de extremos (video de YouTube)](#6-estrategia-de-extremos-video-de-youtube)
7. [Estrategia de retrocesos (video "150 dólares en una semana")](#7-estrategia-de-retrocesos-video-150-dólares-en-una-semana)
8. [Predicción por análogos](#8-predicción-por-análogos)

---

## 1. Conceptos básicos de trading

**Trading** es comprar y vender un activo para ganar con la diferencia de precio. Un inversor compra para mantener años; un trader busca movimientos más cortos y sale rápido cuando se equivoca.

**Mercados y pares.** En Binance todo se negocia en pares (`BTCUSDT`: se entrega USDT para recibir BTC). El bot opera `BTCUSDT`, `ETHUSDT`, `SOLUSDT` y `DOGEUSDT` en **spot**, solo en largo: compra para vender más caro. Los futuros permiten apostar a la baja y apalancarse; el bot no los usa.

**Libro de órdenes.** El precio es el último acuerdo entre comprador y vendedor. *Bid* es la mejor oferta de compra, *ask* la mejor de venta y el *spread* es la distancia entre ambos. Una orden grande se ejecuta contra varios niveles y paga un **deslizamiento** (precio medio peor que el mejor visible).

**Tipos de orden.** *Market* (ejecución inmediata, precio incierto), *limit* (precio fijo, puede no ejecutarse), *stop loss* (vende si el precio cae a X), *take profit* (vende si sube a Y) y *OCO* (TP y SL a la vez; al ejecutarse uno se cancela el otro). Quien deja una orden esperando en el libro es *maker*; quien la ejecuta contra el libro es *taker*. Comisión estándar de Binance spot: ~0.1 % por operación.

> **En este bot:** Node.js coloca órdenes *limit* al precio actual. El TP y el SL no se envían a Binance: el bot los vigila y vende cuando el precio los cruza.

**Velas.** Cada vela resume un periodo con OHLC (apertura, máximo, mínimo, cierre) y volumen. Una vela de 1 h agrupa cuatro de 15 min: open de la primera, close de la última, high y low extremos, volumen sumado. Una ventana de 20 velas no significa lo mismo en 15 min (5 horas) que en 1 min (20 minutos).

**Estados del mercado.** Tendencia (máximos y mínimos crecientes o decrecientes) o rango (rebote entre soporte y resistencia). Las estrategias de rango son reversión a la media (`MeanReversion`, `VWAP`); las de tendencia, seguimiento (`TrendFollowing`, `VolatilitySqueeze`). El bot elige una estrategia por moneda y la usa siempre, sin detectar el estado.

**Volatilidad.** Desviación estándar de los retornos. Tiende a venir en racimos. Las criptomonedas son mucho más volátiles que las acciones.

**Long, short y apalancamiento.** Un *short* gana si el precio baja (vende algo prestado y lo recompra). Con apalancamiento $L$ el margen es $1/L$ de la posición, así que la caída que liquida es aproximadamente $100\,\% / L$ (10x: ~10 %). El apalancamiento no cambia cuánto gana o pierde una posición en dólares; cambia cuánto dinero propio se inmoviliza.

**Gestión del riesgo.** $R$ es la pérdida si toca el stop loss; los resultados se miden en múltiplos de $R$. Tamaño de la posición para arriesgar un porcentaje fijo del capital:

$$
\text{Cantidad} = \frac{\text{Capital} \times \%\text{ riesgo}}{\text{Entrada} - \text{Stop}}
$$

Las pérdidas pesan más que las ganancias: perder el 50 % exige ganar el 100 % para volver al punto de partida.

**Esperanza matemática.** Con tasa de acierto $p$, ganancia $bR$ y pérdida $R$:

$$
E = p\,(bR) - (1-p)\,R,
\qquad
E = 0 \iff p^{*} = \frac{1}{1+b}
$$

Con costos $c$ (en las mismas unidades que $R$), la tasa mínima sube a $p^{*} = \dfrac{1 + c/R}{1 + b}$.

Ganar en promedio no garantiza ganar en cada tramo. Con la ventaja $\hat E$ y la desviación $\sigma$ por operación, después de $N$ operaciones la ventaja crece como $N\hat E$ y el ruido como $\sigma\sqrt N$. Para que la ventaja supere al doble del ruido (aprox. 95 % de confianza):

$$
N \ge \left(\frac{2\sigma}{\hat E}\right)^2
$$

Ejemplo: con $\hat E = 0.26R$ y $\sigma = 1.48R$, hacen falta unas 130 operaciones; para $\hat E = 0.10R$ en sentido contrario, unas 756.

**Costos.** Comisión (~0.1 % por lado), spread (se compra en el ask y se vende en el bid) y deslizamiento. Con el costo de ida y vuelta (0.24 %), una operación que busca un 0.5 % pierde el 40 % de la ganancia esperada en costos.

**Psicología.** Los errores típicos son no usar stop loss, moverlo para no perder, la venganza tras una pérdida, el FOMO, el sobreapalancamiento y el sobreajuste al pasado. El antídoto del bot son reglas definidas antes de entrar y validación con datos no vistos.

---

## 2. Matemática del bot

**Notación.** $P_t$ cierre de la vela $t$; $V_t$ volumen; $n$ ventana (`window`); $k$ multiplicador de desviaciones (`std_dev_multiplier`); $\mu_t$ media móvil; $\sigma_t$ desviación móvil; $TP$, $SL$ objetivo y corte; $R$ distancia entre entrada y stop.

### Parte 1 · Bloques básicos

**§1 Media móvil simple.** Solo usa el **cierre** de cada vela, que es el precio de la última operación del periodo.

$$
\mu_t = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}
$$

En vivo el bot solo usa velas cerradas (desde el 2026-10-18); el precio provisional de una vela abierta sirve solo para vigilar TP y SL. Mientras no haya $n$ cierres, la estrategia devuelve `HOLD`.

**§2 Desviación estándar muestral (Bessel).**

$$
\sigma_t = \sqrt{\frac{1}{n-1}\sum_{i=0}^{n-1}\left(P_{t-i}-\mu_t\right)^2}
$$

**§3 Bandas de Bollinger.** $U_t = \mu_t + k\sigma_t$, $L_t = \mu_t - k\sigma_t$. El optimizador prueba $k$ entre 0.8 y 3.2. Las colas de las criptomonedas son gordas: el "95 %" de la normal es solo una referencia.

### Parte 2 · Las estrategias

**§4 Riesgo/beneficio.** Cada estrategia define $R$ (hasta el SL) y $bR$ (hasta el TP): $b = 1$ en reversión, $b = 2$ en tendencia, $b = 2.5$ en squeeze. Con $b = 2$ hace falta acertar más del 33.3 %.

**§5 Reversión a la media (`MeanReversionStrategy`).**
- Compra si $P_t < L_t$.
- $TP = \mu_t$, $R = TP - P_t$, $SL = P_t - R$ ($b = 1$).
- Se descarta si $R < 0.005\,P_t$ (el riesgo mínimo del 0.5 %).

**§6 Ruptura / seguimiento de tendencia (`RollingVolatilityStrategy`, en `ml_results.json` aparece como `TrendFollowing`).**
- Compra si $P_t > U_t$.
- $SL = \mu_t$, $R = P_t - \mu_t$, $TP = P_t + 2R$.
- No tiene filtro de riesgo mínimo.

**§7 Reversión al VWAP (`VWAPReversionStrategy`).**

$$
VWAP_t = \frac{\sum_{i=0}^{n-1} P_{t-i}V_{t-i}}{\sum_{i=0}^{n-1} V_{t-i}},
\qquad
L_t = VWAP_t - k\sigma_t,
\qquad
\text{BUY si } P_t < L_t
$$

El TP es el VWAP y el SL, la misma simetría que en §5. Desde el 2026-10-18 usa el volumen real. Antes, el motor en vivo pasaba $V = 1$, así que VWAP era igual a la media simple y ambas estrategias daban resultados idénticos.

**§8 Compresión de volatilidad (`VolatilitySqueezeStrategy`).**

$$
BW_t = \frac{U_t - L_t}{\mu_t} = \frac{2k\sigma_t}{\mu_t}
$$

- Se arma si $BW_t < \theta = 0.05$ (el optimizador nunca cambia $\theta$).
- Compra si está armada y $P_t > U_t$; luego se desarma.
- $SL = \mu_t$, $TP = P_t + 2.5R$; mismo filtro de $R \ge 0.5\,\%$.

**§9 Arbitraje estadístico por z-score (`StatisticalArbitrageStrategy`).** No está conectada: hoy no opera.

$$
S_t = \frac{P^{B}_t}{P^{A}_t},
\qquad
z_t = \frac{S_t - \mu_S}{\sigma_S},
\qquad
\text{BUY } B \text{ si } z_t < -2
$$

$SL = 0.99\,P^B_t$, $TP = 1.02\,P^B_t$. Solo compra una pata, no hace la cobertura corta, así que no es un arbitraje completo.

**§9 bis Compra de capitulación (`CapitulationStrategy`).** Es la única idea con evidencia para un bot solo largo en spot: comprar la sobrerreacción tras una caída extrema con volumen climático.

$$
D_t = \frac{P_t}{P_{t-4}} - 1,
\qquad
\text{BUY si } D_t < -k\,\sigma_t\sqrt{4}\ \text{ y }\ v_t \ge 2\,\bar v_t
$$

Salida con la geometría X5 de la v3 (§4, 2.10) sin la barrera de 96 h: $s_d = \sigma_t\sqrt{N_d}$, $TP = P_t(1 + 0.7s_d)$, $SL = P_t(1 - 1.75s_d)$. La relación $b = 0.4$ deja el acierto del azar en ≈ 71 %. Solo hay ventaja si supera ese nivel después de costos. El optimizador elige $n$ y $k$; las constantes son fijas.

### Parte 3 · Ejecución y gestión del dinero

**§10 Tamaño de la posición.** Presupuesto fijo de 15 USDT por operación.
- Versión anterior: $q = \lfloor 15/P \cdot 10^d \rfloor / 10^d$, con $d = 5$ en BTC y $3$ en el resto.
- Versión vigente (2026-10-19): orden a mercado **por importe** (`quoteOrderQty` = 15 USDT). Binance calcula la cantidad redondeando al `stepSize`. Si el par no admite compra por importe, $q = 15/P$ redondeado con `floorToStep`.
- Riesgo real: $q\,(P_{entrada} - SL)$.

*Estados del ledger.* Antes de enviar la orden se escribe una fila `PENDING` con su `client_order_id`. Si se confirma, pasa a `OPEN`; si Binance la rechaza o no se ejecutó, `CANCELLED`. Si no llega respuesta, o Binance dice que la orden no existe (`-1007`), es una **compra dudosa**: sigue `PENDING`, la moneda no abre otra compra y se consulta de nuevo a los 5 s, y tras cada "no existe", a los 10, 30 y 90 s. Al arrancar, cada `PENDING` se consulta una vez; no retrasa el WebSocket.

**§11 PnL en vivo.** Cierre si $P_t \ge TP$ o $P_t \le SL$.

$$
PnL = \text{USDT recibidos} + q_{res}\,P_{salida} - \text{USDT pagados} - \text{comisiones}
$$

- Las comisiones en la moneda comprada ya vienen descontadas de la cantidad vendida; no se restan dos veces. Las cobradas en USDT o BNB sí se restan.
- $q_{res}$ es el residuo que no se puede vender por estar bajo el `stepSize`. Se valora al precio medio de venta, no como pérdida.
- La venta puede completarse en varios tramos; el PnL los suma. Una venta "dudosa" no se reenvía hasta confirmarla (10, 30 y 90 s).
- Si la posición entera queda por debajo del mínimo de Binance (polvo), se cierra en el ledger sin venta y sin PnL.
- Rechazos `-1013`, `NOTIONAL` o `LOT_SIZE`: se da por polvo solo si, valorada al precio medio, no llega al mínimo con un 1 % de margen. Si es vendible, se reintenta con espera creciente (5, 10, 20, 40 y 60 s).
- Al arrancar, cada posición del ledger se verifica en Binance. Si no responde, la posición no se toca.

### Parte 4 · Backtesting y optimización

**Datos.** Velas de 15 min desde 2023-01-01 hasta el día anterior a cada ejecución (132 763 velas por moneda en la ejecución del 2026-10-19).

| Periodo | Uso | Velas |
|---|---|---|
| Desarrollo (walk-forward) | 38 pliegues: entrenar 6 meses, probar el siguiente, de 2023-07 a 2026-08 | 128 539 |
| Validación final | 2026-09-01 a 2026-10-14. No elige nada; solo puede vetar | 4 224 |
| Parámetros en vivo | Los 6 meses más recientes (2026-04-15 a 2026-10-14) | 17 568 |
| XGBoost (§18) | Último mes completo, 80/20 | ≈ 2 870 |

En vivo no se usa la historia descargada: `pre_seed_engine` pide las últimas velas cerradas (mínimo 100).

*Por qué importa.* Hasta el 2026-10-18 el optimizador veía un solo mes (septiembre de 2026). Las estrategias elegidas ganaban todas en ese mes; del 1 al 14 de octubre tres de las cuatro monedas perdieron.

**§12 Simulador de capital.** Desde el 2026-10-18 hace lo mismo que el bot en vivo: 15 USDT por operación, barreras con el máximo y mínimo de cada vela, comisiones incluidas.

$$
q = \frac{15}{P_e},
\qquad
P_s = \begin{cases} SL & \text{si } L_t \le SL \\ TP & \text{si } H_t \ge TP \end{cases},
\qquad
PnL = q(P_s - P_e) - q(P_e + P_s)\,c,
\qquad c = 0.12\,\%
$$

- Si la vela abre ya más allá de una barrera, sale a la apertura.
- Si una vela toca las dos barreras, cuenta el SL (supuesto conservador).
- Las barreras se vigilan desde la vela siguiente a la entrada.
- La ventana de la estrategia nunca se congela, aunque haya posición abierta.
- Capital inicial: 1 000 USDT.

*Paridad.* Con 13 056 velas por moneda, el simulador y el bot en vivo reproducido sin conexión abrieron y cerraron las mismas operaciones en las mismas velas. `ml_evaluator.py` usa la versión rápida (`fast_backtest.py`) solo después de comprobar que da exactamente las mismas operaciones que `simulate_live`.

**§13 Métricas.**

$$
WR = \frac{W}{W+L}\cdot 100,
\qquad
PF = \frac{G^{+}}{G^{-}},
\qquad
EP = \frac{PnL}{W+L},
\qquad
MDD = \max_j \frac{\text{Pico}_j - C_j}{\text{Pico}_j}
$$

$$
\text{Score} = PnL - 10\cdot MDD_{\%},
\qquad \text{solo si } W+L > 5
$$

**§14 Búsqueda en rejilla y selección.**
- Rejilla: $n \in \{8, 12, \dots, 96\}$ (23 valores) y $k \in \{0.8, 1.0, \dots, 3.2\}$ (13 valores): 299 parejas por estrategia.
- Se elige la **meseta**, no el pico: $\bar S(n,k)$ es el promedio del score en la celda y sus vecinas ($n \pm 4$, $k \pm 0.2$), con al menos 30 operaciones en el entrenamiento.
- Ejemplo: en ETHUSDT con `MeanReversion`, el pico $(40, 2.8)$ tenía $S = -1.02$, pero sus vecinas promediaban $-3.67$; la meseta $(84, 3.2)$ ganó con $\bar S = -2.30$. Elegir la zona no garantiza ganar; evita apostar por un pico que sus vecinas no confirman.
- Si el PnL de entrenamiento de la pareja elegida no es positivo, ese mes no se opera.
- Cada mes de prueba se simula aparte, como lo viviría el bot: estrategia nueva precargada con $\max(n+20, 100)$ velas. Hay una sola posición por moneda: si la operación del mes anterior sigue abierta, el mes no abre otra hasta la vela siguiente a su salida. Cada operación se sigue hasta su salida real.

**Criterio de paso (walk-forward).** Por moneda y estrategia, el OOS debe cumplir:
1. al menos 30 operaciones;
2. PnL neto > 0;
3. al menos la mitad de los meses con operaciones en positivo;
4. $p < 0.05/16 = 0.003125$, con $t$ por día (las operaciones del mismo día no son independientes):

$$
t = \frac{\bar d}{s_d/\sqrt{D}},
\qquad p = P(T_{D-1} \ge t)
$$

**Veto.** Una estrategia que pasa el walk-forward y pierde dinero en la validación final queda `rechazada`. Una estrategia es `validada` si pasa, no la veta la validación final y tiene parámetros rentables en los 6 meses recientes. Si una moneda tiene varias validadas, se queda la de mayor $t$.

**Resultado de la ejecución del 2026-10-19.** Las 16 parejas (4 monedas × 4 estrategias) ganan dentro de muestra; fuera de muestra, 12 de 16 pierden. El mejor $p$ es 0.30. Con 3 meses de entrenamiento el mejor $p$ es 0.268; con 12, 0.457. **Ninguna estrategia pasa.** El bot en modo normal no carga ninguna estrategia; las cuatro monedas quedan en pausa.

*Modo experimental.* `ALLOW_UNVALIDATED_STRATEGIES=1` (desactivado por defecto) carga la mejor pareja OOS con parámetros rentables recientes, marcada como **NO VALIDADA**: `VolatilitySqueeze` (96, 2.0) en BTC, `VWAP` (84, 2.6) en ETH, `VolatilitySqueeze` (64, 3.2) en SOL y `TrendFollowing` (12, 2.8) en DOGE. Con `BINANCE_MARKET=mainnet` se ignora. Lo esperable en ese modo es perder dinero.

> **Nota de consistencia.** La tabla de ventanas de §22 del original listaba `TrendFollowing` (56, 3.0) para SOL. Esa pareja no coincide con esta lista; antes de usarla, revisar `ml_results.json`.

**§14.1 Filtros de entrada (desde el 2026-10-22).** Se aplican igual en el evaluador y en vivo; se configuran en `config.py` (`None` desactiva cada uno):
- **Riesgo mínimo del 1.5 %:** $P_t - SL \ge 0.015\,P_t$.
- **Co-señal:** la misma regla dio BUY en otra moneda del roster en las últimas 48 velas. La vela actual no cuenta.
- **Interruptor de momentum:** el mes se opera solo si la suma de los 12 meses anteriores del PnL en sombra es positiva.
- **Velas de 1 h** (`KLINE_INTERVAL`): con 15 min la esperanza era −0.15 % por operación; con 1 h, −0.03 %.
- En testnet, `TESTNET_IGNORE_MOMENTUM=1` hace que el interruptor no bloquee, para juntar resultados. En mainnet siempre se respeta.
- Cada BUY, abierto o bloqueado, se guarda en `orders/signals.csv` con su motivo.

### Parte 5 · Machine learning

**§15 Etiqueta.** $y_t = 1$ si $P_{t+12}/P_t - 1 > 1\,\%$ (3 horas con velas de 15 min).

**§16 Variables.**
- Retorno $r_t = P_t/P_{t-1} - 1$.
- Volatilidad de los últimos $m \in \{10, 20\}$ retornos.
- Distancia a la SMA de 20: $d_t = (P_t - SMA_{20})/SMA_{20}$.
- RSI de 14 con medias simples (Cutler): $RS = G/L$, $RSI = 100 - 100/(1+RS)$. Puede diferir un poco del RSI de Wilder que muestran las plataformas.
- Cambio de volumen $V_t/V_{t-1} - 1$.

**§17 XGBoost.** 100 árboles, profundidad máxima 4, tasa $\eta = 0.05$, salida logística:

$$
\hat p = \frac{1}{1+e^{-F_M(x)}},
\qquad
F_M(x) = \sum_{m=1}^{M}\eta\, f_m(x)
$$

Pérdida: log loss más $\Omega(f) = \gamma T + \tfrac12\lambda\sum w_j^2$. En cada nodo, $g_i = \hat p_i - y_i$, $h_i = \hat p_i(1-\hat p_i)$, peso de hoja $w^{*} = -\sum g/(\sum h + \lambda)$, y ganancia al partir:

$$
\text{Ganancia} = \tfrac12\left[\tfrac{G_I^2}{H_I+\lambda} + \tfrac{G_D^2}{H_D+\lambda} - \tfrac{(G_I+G_D)^2}{H_I+H_D+\lambda}\right] - \gamma
$$

**§18 Validación 80/20 y accuracy.** La accuracy es engañosa con clases desbalanceadas: en septiembre de 2026 fue 96.7 %, 92.1 %, 84.8 % y 83.0 % en BTC, ETH, SOL y DOGE, casi lo mismo que decir siempre "0" (solo entre 3 % y 17 % de las velas eran 1). Además, el modelo **no se guarda ni se usa en vivo**: `predict_signal_quality` no se llama desde ningún lado. Hoy XGBoost no filtra operaciones.

**§19 HMM (en desarrollo).** Retorno logarítmico $\ell_t = \ln(P_t/P_{t-1})$, ya implementado. El HMM gaussiano (transiciones $A_{ij}$, emisiones $\mathcal N(\mu_j, \sigma_j^2)$, Baum–Welch y Viterbi) está pendiente; `predict_regime` devuelve 0 siempre.

**§20 Gestor RL (en desarrollo).** Estado: $u_t = (P_t - P_{entrada})/P_{entrada}$ y velas en la operación. Acciones previstas: mantener, cerrar, mover el stop. Trailing de ejemplo: $SL = 0.99\,P_t$. PPO previsto con recorte $\epsilon$:

$$
L^{CLIP}(\theta) = \mathbb E_t\big[\min(\rho_t\hat A_t,\ \text{clip}(\rho_t, 1-\epsilon, 1+\epsilon)\hat A_t)\big]
$$

Hoy siempre devuelve `HOLD_POSITION`. Ver también §3 de este documento, que concluye que las salidas aprendidas no tienen nada que aprender con los datos actuales.

**§21 Volatilidad histórica.** $\bar\sigma = \text{std}(r_1, \dots, r_N)\cdot 100$. Con $\bar\sigma = 0.35\,\%$ por vela de 15 min, el movimiento típico en 3 horas es $0.35\sqrt{12} \approx 1.2\,\%$, así que un objetivo de 1 % en 3 horas es realista.

### Parte 6 · Cinco sugerencias para encontrar un margen

**Idea de fondo.** No hace falta adivinar el mercado; hace falta una ventaja **en promedio** que supere los costos. Los patrones reales son débiles (aciertos del 52–58 %, no del 80 %), cambian con el tiempo y se debilitan cuando muchos los explotan. Por eso el orden es: primero medir si el patrón existe, después operarlo solo si el margen supera los costos.

1. **Razón de varianzas (medir si el precio oscila o persiste).**

$$
VR(q) = \frac{\text{Var}(r_t + \dots + r_{t-q+1})}{q\,\text{Var}(r_t)}
$$

$VR < 1$: oscila, terreno de reversión. $VR > 1$: persiste, terreno de tendencia. $VR \approx 1$: ruido. Prueba de Lo-MacKinlay con $|z| > 2$. Idea: medirla en ventana móvil para elegir la estrategia según el estado.

2. **Ornstein–Uhlenbeck (rango).** Regresión $X_t - X_{t-1} = a + \beta X_{t-1} + \varepsilon_t$, con $\kappa = -\ln(1+\beta)$, $\mu = -a/\beta$, $t_{1/2} = \ln 2/\kappa$ y $\sigma_{eq} = \sigma_\varepsilon/\sqrt{1-(1+\beta)^2}$. Compra en $\mu - k\sigma_{eq}$, vende en $\mu$, y cierra si pasan unas $3\,t_{1/2}$ sin volver. Si $\beta$ no es significativo, no hay rango que operar.

3. **Seguimiento con stop dinámico (tendencia).** Dirección $s_t = \text{signo}(\ln(P_t/P_{t-L}))$. ATR con el rango verdadero $\max(H-L, |H-C_{prev}|, |L-C_{prev}|)$. Chandelier: $SL_t = \max_{\text{desde entrada}}(H) - m\cdot ATR_t$, con $m \in [2, 3]$. Sin TP fijo: una tendencia fuerte puede dar $5R$ o $10R$.

4. **Patrones por hora UTC.** $t_h = \bar r_h/(s_h/\sqrt{N_h})$. Como se prueban 24 horas, se exige $|t_h| > 3$ (Bonferroni). Uso más robusto: ajustar bandas y stops a la volatilidad típica de cada hora.

5. **Triple barrera + meta-labeling.** La etiqueta no es "sube 1 %", sino "¿toca primero el TP o el SL?". Operar solo si $\hat p_i > p^{*} = \dfrac{1 + c/R_i}{1+b}$. Validación walk-forward con hueco igual al tiempo máximo de la operación.

*Cómo encajan:* el margen no viene de una fórmula mágica; viene de sumar ventajas pequeñas y no regalar dinero en costos ni en malas mediciones. Antes de implementar cualquiera, hay que arreglar el backtest (pagar el $b$ real, usar máximos y mínimos, descontar comisiones y validar con datos no vistos).

### Parte 7 · Volatilidad del momento y ajuste a ella

El bot expresa sus decisiones en unidades de $\sigma_t$: entrada, TP y SL se miden en sigmas, no en dólares.

**§22 Medir.** La ventana cubre $n \times \Delta t$. Desde el 2026-10-18, $\Delta t = 15$ min en backtest y en vivo, con velas cerradas de `kline_15m`. Antes, en vivo eran ~6 s por foto: $n = 20$ cubría 2 minutos en vivo y 5 horas en el backtest.

*Ventanas con los parámetros del modo experimental:*

| Moneda | Estrategia | $n$ | $k$ | Ventana |
|---|---|---|---|---|
| BTCUSDT | VolatilitySqueeze | 96 | 2.0 | 24 h |
| ETHUSDT | VWAP | 84 | 2.6 | 21 h |
| SOLUSDT | VolatilitySqueeze (§14) | 64 | 3.2 | 16 h |
| DOGEUSDT | TrendFollowing | 12 | 2.8 | 3 h |

*Corrección del 2026-10-18:* el motor en vivo recibía fotos de `kline_1m` y la ventana se congelaba con posición abierta. Una reproducción sin conexión de 13 056 velas dio ahora las mismas señales que el backtest.

**§23 Z-score.** $z_t = (P_t - \mu_t)/\sigma_t$. La reversión compra si $z_t < -k$ y la ruptura, si $z_t > k$. El mismo movimiento de 350 USDT puede ser extremo ($z = -5.8$) en un mercado tranquilo y normal ($z = -0.9$) en uno agitado.

**§24 TP y SL proporcionales a σ.** En reversión, $R = |z_t|\sigma_t > k\sigma_t$; en ruptura, $R = z_t\sigma_t > k\sigma_t$. Por eso la distancia de riesgo crece sola con la volatilidad. El filtro del 0.5 % equivale a exigir $\sigma_t \ge 0.005\,P_t/|z_t|$.
- La ruptura (`TrendFollowing`) no tiene ese filtro: puede operar con volatilidad tan baja que los costos (0.24 %) se coman la ganancia.
- El squeeze es la única que mira el nivel de volatilidad: se arma si $2k\sigma_t/\mu_t < 5\,\%$.

**§25 Lo que aún no se ajusta a la volatilidad.**
1. **Tamaño fijo.** 15 USDT por operación: el riesgo en dólares crece con $R$. Alternativa: $q = \text{Riesgo fijo}/R$.
2. **Medición lenta.** Con una ventana simple, $\sigma_t$ tarda hasta $n$ muestras en reflejar un cambio. Alternativa: EWMA, $\sigma_t^2 = \lambda\sigma_{t-1}^2 + (1-\lambda)r_t^2$, con $\lambda \approx 0.94$ (o 0.80 para reaccionar antes).
3. **Mide precios, no retornos.** Una tendencia limpia infla $\sigma$ aunque no haya temblor. Medir retornos evita ese sesgo.
4. **La ventana ve menos de la mitad del movimiento.** Con $n$ precios, $\sigma_{ventana}^2 \approx \sigma_{paso}^2 (n+1)/6$, mientras el precio se mueve $\sigma_{paso}\sqrt n$. La proporción tiende a $1/\sqrt6 \approx 41\,\%$ para cualquier $n$, así que las bandas con $k = 2$ no cubren el "95 %" de la normal.
5. **Escala de tiempo.** Corregido el 2026-10-18: en vivo solo entra el cierre de cada vela de 15 min, con $O_T$, $H_T$, $L_T$, $C_T$ construidos sobre todos los precios del intervalo.

### Parte 8 · El recorrido completo

Las secciones van por tema; este resumen ordena las fórmulas por momento de uso.

**Fase A · Antes de operar** (`ml_evaluator.py`, unos 2 minutos; deja `ml_results.json`):

| Paso | Qué | Dónde (archivo) |
|---|---|---|
| A1 | Cargar velas de 15 min y separar desarrollo, validación final y 6 meses recientes | `download_data.py`, `load_history`, `build_periods` |
| A2 | Simular toda la historia por pareja $(n,k)$ | `FastSymbol.simulate` (paridad con `simulate_live`) |
| A3 | Medir cada pareja con sus 6 meses de entrenamiento: $S = PnL - 10\,MDD_\%$ | `PairEvaluator.select` |
| A4 | Elegir la meseta $\arg\max \bar S$ y simular el mes siguiente | `run_folds` |
| A5 | Validar el OOS con $t$ y $p < 0.003125$; validación final solo veta | `decide` |
| A6 | Elegir parámetros en vivo con los 6 meses recientes; cargar solo validadas | `load_best_strategies` |

XGBoost también se entrena aquí, pero ni A3–A6 ni la fase B usan su predicción.

**Fase B · En vivo** (en cada vela cerrada; el TP/SL se vigila con cada precio):

| Paso | Qué | Dónde (archivo) |
|---|---|---|
| B1 | Cierra una vela de 15 min (`k.x`) | `handleMarketData` |
| B2–B4 | Ventana, $\mu_t$, $\sigma_t$ | `price_history`, `series.mean/std` |
| B5 | Bandas y $z_t$ | cada estrategia |
| B6 | Señal; si no hay, `HOLD` | `evaluate` |
| B7–B8 | $R$, TP, SL; filtro $R \ge 0.5\,\%$ | `evaluate` |
| B9 | Fila `PENDING`, compra por importe de 15 USDT; `OPEN` o `CANCELLED` | `openPosition`, `marketBuy` |
| B10 | Vigilar TP y SL | `manageExistingPosition` |
| B11 | Venta a mercado y PnL neto | `closePosition`, `finishClose`, `netPnl` |
| B12 | Registro en `trades.csv` y aviso por Telegram; al reiniciar se reconcilian `PENDING` y posiciones | `server.py`, `ledger.py`, `syncStateFromLedger` |

---

## 3. Agente RL y esperanza positiva

Experimentos con datos locales (velas de 15 min, 2023-01 a 2026-10-14) sobre las cuatro estrategias del modo experimental. Costo de 0.12 % por lado (0.10 % comisión y 0.02 % deslizamiento).

**Notación.** $E$ = PnL neto medio por operación. $R$ = riesgo inicial. WR = fracción con PnL neto > 0. $b$ = TP/SL en múltiplos de $R$. $c_R$ = costo de ida y vuelta en $R$. IC = correlación entre una variable y el resultado futuro.

### 1. Respuesta corta

- **El agente no puede crear ventaja donde no la hay.** Después de entrar, el precio se comporta casi como una martingala; cualquier regla de salida deja la misma esperanza bruta (cero). Subir el WR sin información nueva es geometría.
- **"Fabricar" WR es trivial y no sirve.** Un *lock-in* con ganancia $+mR$ da WR $= 1/(1+m)$. Los stops a equilibrio y las barreras de tiempo subieron el WR y **bajaron** la $E$.
- **Lo que sí sube la $E$ hoy es barato y no es RL:** pagar comisiones con BNB (+0.05 % por operación) y dejar de operar lo que no tiene ventaja (solo SOL Squeeze tiene $E$ claramente positiva).
- **Las salidas aprendidas no mejoran nada** con el estado observable: ninguna variable predice el PnL restante ($|\rho| < 0.045$ dentro de muestra).
- **Si se construye el agente:** decide al cierre de vela, recompensa = PnL neto en $R$, algoritmo supervisado *offline*, PPO solo como ajuste fino. Se acepta solo si gana en $E$ con prueba pareada y corrección de Bonferroni. "Rechazado" es un resultado válido.
- **El WR alto con ganancia exige ventaja en la entrada**, no en la salida. La v3 llega a ≈ 73–79 % fuera de muestra porque gana entre +9 y +17 puntos sobre el azar en la entrada.

### 2. Por qué subir el win rate no basta

**Teorema de parada opcional.** Si el precio es martingala después de la entrada, para cualquier regla de salida acotada $\tau$:

$$
\mathbb E[X_\tau] = 0 \;\Rightarrow\; E_{neta} = -c_R,
\qquad
p^{*} = \frac{1+c_R}{1+b}
$$

El WR fuera de muestra actual es el del azar: MeanReversion 49.9 % (azar 50 %), TrendFollowing 33.2 % (33.3 %), VolatilitySqueeze 29.9 % (28.6 %).

*Monte Carlo (60 000 trayectorias, $R = 2\,\%$):* en las ocho políticas simuladas el WR va del 30 al 66 % y la $E$ queda siempre en ≈ $-c_R$.

*Datos reales (2023-01 a 2026-08, 1 569 operaciones base):*

| Salida | WR | $E$ %/op | PnL USDT |
|---|---|---|---|
| **Base TP/SL** | 40.4 % | **+0.025** | +5.96 |
| Equilibrio tras +0.5 $R$ | 55.1 % | −0.078 | −24.92 |
| Equilibrio tras +1.5 $R$ | 44.7 % | −0.002 | −0.53 |
| Barrera de tiempo 16 velas | 41.0 % | −0.160 | −58.52 |
| *Trailing* 1 % + TP | 32.4 % | −0.186 | −64.90 |
| Chandelier 4·ATR + TP | 34.5 % | −0.139 | −45.32 |
| Azar dentro de la ventana | 42.1 % | +0.034 | +11.10 |
| Oráculo dentro de la ventana | 67.3 % | +1.292 | +390.24 |

Ninguna regla simple supera a la base. La salida actual no demuestra habilidad (su $E$ no se distingue de cero, $t = 0.29$).

**Cuándo una salida sube WR y $E$ a la vez.** Solo con deriva condicional predecible: $\Delta E \approx 0.4\,\rho\,\sigma_{rem}$. Para cubrir 0.12 $R$ de costos hace falta $\rho \approx 0.3$; un buen IC intradía en cripto está entre 0.02 y 0.05.

### 3. Prácticas de profesionales que sí dan esperanza

La ventaja de los profesionales está en **operar solo lo que tiene esperanza medida, no destruirla con costos y sobreajuste, y dejar de operar cuando deja de pagar**. La gestión del riesgo no convierte una $E$ negativa en positiva; con $E \le 0$, la fracción óptima de Kelly es $f^* = 0$.

| # | Práctica | Efecto | Estado en el bot |
|---|---|---|---|
| 1 | Operar solo setups con $E$ fuera de muestra, corregida por pruebas múltiples (límite inferior bootstrap > 0, DSR > 0) | E | ✅ walk-forward · ❌ DSR/PBO |
| 2 | Interruptor por $E$ móvil: apagar si $E + 1.0\,SE < 0$; reactivar desde sombra | E | ❌ |
| 3 | Ejecutar barato: BNB, TP con LIMIT/OCO, no entrar si el objetivo < 2–3× el costo | E | ✅ costos en backtest · ❌ BNB, maker |
| 4 | Filtro de régimen de mayor marco (TSMOM de BTC) como variable, no como regla dura | E | 🟡 HMM solo en investigación |
| 5 | Comprar la sobrerreacción tras caídas extremas con capitulación taker | E (encaje natural para spot) | ❌ |
| 6 | Flujo taker como timing; `imb = 2·taker_buy/volumen − 1` | E pequeña | ❌ |
| 7 | Meta-etiquetado: filtrar la señal, no reemplazarla | WR y E | ❌ |
| 8 | Salida coherente con la fuente de ventaja: stop en rupturas, TP en la media en reversión; nunca *trailing* en reversión | E | 🟡 SL/TP fijos |
| 9 | Liquidez y eventos: sin rupturas en fin de semana o con volumen < 0.7; sin entradas cerca de CPI/FOMC | R | ❌ |
| 10 | Tamaño por riesgo y volatilidad (≤ ¼ Kelly) | R | ❌ (15 USDT fijos) |
| 11 | Cortacircuitos de cartera: sin entradas tras −3 $R$ en el día o −6 $R$ en la semana | R | ❌ |
| 12 | No escalar ni promediar a la baja | Evita perder E | ✅ no se hace |
| 13 | Diario estadístico: R-múltiplos, MAE/MFE, $E$ por celda, señales omitidas | E indirecta | 🟡 sin $R$ ni MAE/MFE |

**Mitos (no automatizar):** el 80 % de WR como objetivo, Fibonacci, *smart money* sin cuantificar, el 1:2 fijo por sí mismo, la estacionalidad horaria como señal y las tomas parciales en tendencia.

### 4. Lo que dicen los datos del bot

*Desarrollo = 2023-01 a 2026-08 (1 569 operaciones). RES = 2026-09-01 a 10-14 (48 operaciones, solo comprueba el signo).*

| Medida | Efecto en $E$ | Veredicto |
|---|---|---|
| **Comisiones con BNB** | +0.05 %/op; PnL +5.96 → +17.75 USDT | **Hacer ya** |
| TP con orden LIMIT (maker) | +0.009 %/op | Valor de ejecución, no de costo |
| Maker en las dos patas | Sigue negativa | No hacerlo: la entrada LIMIT sufre selección adversa |
| Costo cero (cota) | BTC +0.111 %, ETH +0.040 % | BTC y ETH no tienen ventaja bruta: el problema no es el costo |
| Solo SOL Squeeze | SOL +0.887 %/op (257 ops); BTC −0.129, ETH −0.200, DOGE −0.019 | La única ventaja real del conjunto |
| Selección por *momentum* 12 meses | +0.244 %/op; MDD 27.6 → 10.0 | Prometedora, **no demostrada** (no pasa Bonferroni) |
| Nocional ∝ $E$ de 12 meses | +0.364 % por USDT; PnL/MDD 2.42 frente a 0.22 | Regla base que el RL de tamaño debe batir |
| Riesgo fijo por operación | PnL −26.67 USDT | **Descartar** |
| Filtro riesgo ≥ 1.5 % | +0.157 %/op | Hipótesis: no monótona y RES no la confirma |
| Geometría TP/SL (72 variantes) | SOL: meseta positiva con TP 2–4 $R$; ETH y DOGE pierden | Mantener la actual; el problema de ETH y DOGE es la entrada |
| Quitar el TP y seguir la media | SOL +1.27 → −0.10 %/op en 2026 | Empeora las tendencias |
| Día de la semana | Lunes y martes negativos (Spearman +0.71) | Única variable de calendario algo estable |
| Hora UTC y volatilidad relativa | Se invierte en 2026 (Spearman −0.80) | No usar como filtro fijo |
| Co-señal entre monedas (12 h) | ΔE +0.26 pp en 2026 | Candidata a hipótesis prerregistrada |
| Filtro LightGBM (20 % superior) | +1.28 % dentro → −0.21 % fuera | **Sobreajuste** (AUC 0.714 → 0.577) |
| *Bandit* con exploración | −0.149 % y −0.260 % | Explorar cuesta datos sin aportar |
| Variables de estado para la salida (22) | Pearson OOS −0.16 a −0.19 | Ninguna predice el PnL restante |
| Prototipo de parada óptima | 2026: −0.43 USDT (t = −0.20) y +0.45 (t = +0.30) | Empata con la base |

**Tamaño de muestra.** Para detectar $\Delta E = 0.02\,R$ en prueba pareada hacen falta 6 107 operaciones con α = 0.05 y 12 631 con α = 0.003125. Una mejora realista de salida no es demostrable con los datos actuales.

### 5. Diseño del agente recomendado

**Qué decide.** La entrada (tomar u omitir, y tamaño 0/0.5/1/2×) puede subir $E$; la salida solo si hay deriva predecible (hoy no la hay); la geometría TP/SL no se da como acción.

**Estado (en $R$ y en $\sigma$).** $u_t = (P_t - P_e)/R_0$, MFE, MAE, distancias a TP y SL en $\sigma$, velas transcurridas, costo en $R$, $E$ reciente del par, día de la semana, retornos propios y de BTC, régimen, flujo taker, PnL del día y riesgo abierto. Ninguna variable entra sin IC > 0.1 fuera de muestra.

**Reglas duras fuera del agente:** límites de pérdida diaria y semanal, tope de riesgo abierto, interruptor por $E$ móvil, nocional mínimo y máximo.

**Acciones de salida v1:** `HOLD`, `CLOSE`, `SL_BE`, `SL_TRAIL_1σ`, `SL_TRAIL_2σ`. El stop solo sube; sin DCA, martingala ni *grid*. Barrera de tiempo de 384 velas.

**Recompensa:** PnL neto en $R$ con $\gamma = 1$. Prohibido premiar conteos (aciertos, "no tocar el SL"): el agente maximizaría el WR por geometría. Línea base pareada: $r = PnL_{agente} - PnL_{fijo}$ sobre la misma entrada.

**Costos de entrenamiento:** los actuales o algo peores, nunca costo cero (con costo cero aprende a cortar pronto).

**Algoritmo:** mejora de política en un paso, $A(s,a) = \hat E[G \mid s, a, \text{luego } \pi^0] - \hat E[G \mid s, \pi^0]$, y después *fitted-Q* con LightGBM (variante Longstaff–Schwartz). PPO solo como ajuste fino, con al menos 5 semillas.

**Criterio de aceptación:**
1. Walk-forward del bot (38 pliegues, 6 meses de entrenamiento y 1 de prueba, embargo de $H$), hiperparámetros congelados de antemano.
2. Prueba pareada de $\Delta E > 0$ con $t$ de una cola y Bonferroni $\alpha = 0.05/16 = 0.003125$.
3. Antifabricación: si $\Delta WR > 0$ y $\Delta E \le 0$, se rechaza. Si $FWR = \Delta WR_{azar}/\Delta WR_{señal} > 0.5$, la subida del WR es geometría.
4. Cola: peor operación ≥ −(1 $R$ + costo), CVaR 5 % y drawdown no peores que la base.
5. Consistencia: $\Delta E > 0$ en ≥ 60 % de los pliegues; PBO < 0.2.
6. Filtro de entradas evaluado señal a señal y contra azar simulado en secuencia.
7. Veto final en 2026-09-01 a 10-14 (ΔE ≥ 0 y PnL ≥ 0), luego sombra en testnet (≥ 2 semanas o 50 posiciones).
8. Reportar siempre WR, $E$, factor de beneficio, ganancia y pérdida medias, CVaR 5 % y asimetría.

### 6. Plan por fases

| Fase | Qué | Impacto en $E$ | Condición para seguir |
|---|---|---|---|
| 0 | Comisiones con BNB y alerta de saldo | +0.05 %/op, demostrado | — |
| 1 | Operar solo lo que tiene ventaja (tabla de $E$ por estrategia × moneda con IC) | Evita −0.13 a −0.20 %/op | Revisión mensual |
| 2 | Diario de señales con resultado en sombra, R-múltiplos y MAE/MFE | Indirecto: crea el *dataset* | — |
| 3 | Interruptor por $E$ móvil y cortacircuitos (−3 $R$ día, −6 $R$ semana, riesgo abierto ≤ 2 $R$) | Protege, no crea | — |
| 4 | Reglas base de cartera en sombra | +0.36 %/USDT en desarrollo, sin significancia | Pasar Bonferroni en walk-forward |
| 5 | Filtro de entradas (*meta-labeling* en `StrategyEngine.get_signal`) | ΔE ≈ +0.2 pp esperado, no demostrado | Prueba señal a señal y contra azar |
| 6 | Señal base nueva: capitulación con sobrerreacción, o ENS13 + X5 de la v3 (§4) | Única vía a WR alto **con** $E > 0$ | Walk-forward con Bonferroni |
| 7 | TP con LIMIT u OCO | +0.009 %/op; mejora la ejecución | — |
| 8 | Agente de salida | Hoy ≈ 0 | Solo si una variable nueva da IC > 0.1 OOS y ΔE con $t > 2$ |
| 9 | PPO como ajuste fino | Desconocido | Solo si la fase 8 es significativa |

Las fases 0–4 no necesitan RL y son las que más esperanza protegen o añaden por esfuerzo. El agente de salida va al final porque los datos actuales no le dan nada que aprender.

### 7. Fuentes clave

Harvey, Liu y Zhu (RFS 2016); Bailey y López de Prado (*Deflated Sharpe Ratio*); Novy-Marx y Velikov (costos de anomalías); Barber, Lee, Liu y Odean (*day traders* de Taiwán); Kaminski y Lo (cuándo ayudan los stops); Bailey et al. (*Probability of Backtest Overfitting*); Grossman y Zhou (exposición con restricción de drawdown); Moreira y Muir (volatilidad objetivo); Moskowitz, Ooi y Pedersen (*Time Series Momentum*); Liu y Tsyvinski (criptomonedas); López de Prado, *Advances in Financial Machine Learning* (caps. 3, 4 y 7). Los enlaces completos están en el historial del documento original.

---

## 4. Estrategia v3

> **La estrategia a implementar es la v3:** un ensamble de 13 modelos (ENS13) que compra **velas de capitulación** usando datos de futuros, y que solo opera cuando **otra de 4 monedas ancla también dio señal en las últimas 12 horas** (un pánico de mercado, no una caída aislada). Sale con TP a $+0.7\,s_d$, SL a $-1.75\,s_d$ y cierre forzado a las **96 h**.

- **WR esperado fuera de muestra:** ≈ 73–79 %, con E de +0.6 a +1.2 % por operación. El 87.8 % de diseño es una **cota optimista**: la v2 marcó 81 % en diseño y 69 % en monedas nuevas.
- **Techo realista:** ≈ 75–78 %. Un 80 % por operación demostrado es improbable (15–25 %). La meta alcanzable es ≈ 80 % de meses ganadores.
- **Lo demostrado fuera de muestra:** una ventaja **relativa** sobre el azar, +9 a +17 puntos de WR y ≈ +1.1 % de E en 14 monedas nunca vistas. La co-señal y la barrera de 96 h **no** están validadas fuera de muestra.
- **Bloqueo práctico:** el modelo necesita datos de futuros cada 5 min de `fapi.binance.com`, bloqueada desde la ubicación del usuario (HTTP 451). Ver §7.6.
- **Siguiente paso:** infraestructura honesta (§7), canal sombra de 18 monedas, estrés 2022 y prueba prospectiva desde 2026-10-01 (§8). Dinero real en cero hasta aprobar.

*Convenciones.* **Diseño** = 2023-01-01 a 2025-06-30. **Holdout** = 2025-07-01 a 2026-09-30 (gastado). **Prospectivo** = desde 2026-10-01 (único periodo que puede validar). $c$ = 0.24 % ida y vuelta (0.30 % de estrés; 0.19 % con BNB y TP límite). **WR** = fracción con retorno neto > 0. **Episodio** = grupo de días con operaciones separados por ≤ 2 días; es la unidad real de muestra. Las cifras de diseño suman **12 666** configuraciones registradas en `trials_log.csv`.

### 1. Por qué llegar al 80 % es difícil

**1.1 Sin ventaja, el WR lo pone la geometría.** Con deriva favorable $\nu$ (en $s_d$ por día):

$$
P(\text{TP primero}) = \frac{1}{1+b}\ \text{ con } \nu = 0,
\qquad
P_\nu(\text{TP primero}) = \frac{1-e^{2\nu m}}{e^{-2\nu a}-e^{2\nu m}}
$$

Con la salida X5 ($a = 0.7$, $m = 1.75$): WR 71.4 % con $\nu = 0$; 75 % con $\nu = 0.07$; **80 % con $\nu = 0.19$** (≈ +0.8 % por día mientras dura la operación). Esa deriva aparece en los rebotes tras una capitulación. En diseño, las operaciones con co-señal tienen $\nu \approx 0.43$; el azar con la misma co-señal, ≈ 0.18.

**1.2 WR mínimo con costos.** $p^{*} = \dfrac{1 + c/R}{1+b}$. Con $b = 0.5$, $c = 0.24\,\%$, $R = 2\,\%$: $p^{*} = 74.7\,\%$. El ATR mediano de 15 min es 0.27 % en BTC, 0.35 % en ETH, 0.60 % en SOL y 0.53 % en DOGE: **los costos equivalen a casi un ATR de BTC**. Regla práctica: $R \ge 8$–$10\,c$. Para X5, $p^{*}$ teórico = 73.7 %, empírico ≈ 65 %, porque las salidas por tiempo suben el $b$ efectivo a ≈ 0.53.

**1.3 Descomposición.** $p = p_{azar}(a, m, H, \text{régimen}) + \Delta_{modelo} + \Delta_{compuerta}$. Con X5, el azar da 61.7 % en diseño; el modelo añade de +9.4 pt (v2) a +16.9 pt (v1) fuera de muestra; la compuerta, +2.1 a +4.5 pt en diseño. Para el 80 % harían falta ≈ +20 pt fuera de muestra: nunca se ha replicado algo así.

**1.4 Cuánto vale un punto de WR.** $E = (\bar W + \bar L)(p - p^*_{emp})$. Con v2 en 8 monedas nuevas, 1 pt = 0.075 % de E.

**1.5 Por qué X5 y no una geometría de WR más alto.** $E_{bruta} \approx \mu\,\mathbb E[\tau]$, con $\mathbb E[\tau] \approx a\cdot m$ días. Ninguna geometría fija domina a X5: bajar el TP sube el WR y baja la E. La única mejora que sube las dos es alargar la barrera de tiempo (E7).

**1.6 Selectividad y tamaño de muestra.** Operaciones independientes para que el límite inferior de Wilson al 95 % supere el objetivo: para afirmar ≥ 70 % con WR real de 80 %, hacen falta 81; para ≥ 75 % con 80 %, 289. Multiplicar por el efecto de diseño DEFF (1.0–1.2 con 4 monedas; probablemente 2–3 con 18). **La unidad real es el episodio.** Para la esperanza: $n_{min} = \big((z_{1-\alpha} + z_{0.8})\sigma/\mu\big)^2 \cdot DEFF$. Un +1 pt real es invisible en diseño.

**1.7 La meta honesta son los meses ganadores.** $P(\text{mes} > 0) \approx \Phi\big(\mu n_m / (\sigma\sqrt{n_m\,DEFF})\big)$. Con $\mu = 1\,\%$, $n_m = 15$, DEFF 1.5: ≈ 77 % de meses ganadores.

### 2. La estrategia v3 paso a paso

**2.1 Resumen.**

| Paso | Regla |
|---|---|
| Datos | Velas spot de 15 min + *metrics*, *funding*, prima y velas de futuros, con alineación sin fuga |
| Variables | 74, normalizadas por la volatilidad propia, sin identificar la moneda |
| Modelo | ENS13: 6 LightGBM + 6 MLP + 1 CNN, Platt por miembro, media de probabilidades |
| Señal | $\hat p \ge \theta = 0.7142683625605063$ |
| Compuerta | Otra ancla (BTC, ETH, SOL, DOGE) con $\hat p \ge \theta$ en las últimas 48 velas |
| Entrada | Al cierre de la vela de señal; una posición por moneda; máximo 3 abiertas |
| Salida | TP límite a $+0.7\,s_d$, SL a $-1.75\,s_d$, cierre a mercado a las 384 velas |
| Riesgo | 0.5 % del capital por operación; ≤ 1.5 % por episodio; pausas |
| Universo | 18 pares USDT |

**2.2 Datos.** `data.binance.vision` (≈ 90 MB para 4 monedas y 2.5 años). Velas spot de 15 min (`spot/monthly/klines`), *metrics* de 5 min (OI, ratios de top traders y globales, ratio taker), *funding* de 8 h, prima de 15 min y velas de futuros. Historial mínimo: ≥ 35 días antes del inicio. **Antes de descargar, apagar la VPN.**

**2.3 Alineación sin fuga.** El campo `create_time` de los *metrics* cambió de significado el 2024-03-04: antes marcaba el final del intervalo, después el inicio. Regla vigente: usar el registro con marca $T$ en la vela $i$ si $T \le t_i + 5$ min (la teórica segura es ≤ 10 min). *Funding*: `calc_time` ≤ $t_i$ + 15 min. Rellenar **solo hacia adelante** (*metrics* hasta 30 min; prima y velas de futuros, 2 velas; *funding*, 40). En vivo, si falta un dato más de 30 min, esa vela no opera. Control: el taker de futuros correlaciona 0.84 con el desequilibrio spot; desplazado 15 min, cae a 0.12–0.16.

**2.4 Volatilidad diaria.** $s_d = \text{std}(\ln(c_t/c_{t-1}),\ 672\ \text{velas})\cdot\sqrt{96}$. Ejemplo: 0.44 % en 15 min da $s_d = 4.31\,\%$.

**2.5 Variables.** 74 variables causales normalizadas por la volatilidad propia: retornos $\text{ret}_k = \ln(c_t/c_{t-k})/(\sigma_{15}\sqrt k)$ para $k \in \{1, 4, 16, 48, 96, 288, 672\}$, cambios de OI, imbalances taker, z-scores de 672 velas, funding, prima, basis, ratios de cuentas y posiciones de top traders, RSI14, rango, volumen relativo, hora y día (senos y cosenos), entre otras. Lo que el modelo aprende a comprar: rango de +2.3 desviaciones, volumen de +1.4, caída en la última hora y OI bajo frente al volumen. La lista exacta está en `nn/nn_common.py`.

**2.6 Etiqueta (geometría G3, solo para entrenar).** $TP = c(1+0.75s_d)$, $SL = c(1-1.5s_d)$, $H = 192$ velas, $y = \mathbb 1[\text{retorno neto} > 0]$. Purga de las últimas $H+1$ velas antes de cada corte. La salida operativa es X5 (§2.10), no G3.

**2.7 Ensamble ENS13 y calibración.** 6 LightGBM (50 iteraciones, 15 hojas, `min_data_in_leaf` 1 000, lr 0.03), 6 MLP (74 → 128 → 64 → 1, GELU, *dropout* 0.3, AdamW) y 1 CNN 1D dilatada. Platt por miembro: $\hat p_k = 1/(1+e^{-(A_k s_k + B_k)})$; $\hat p$ = media de los 13. Entrenamiento hasta 2025-03; validación desde 2025-04-01. Coeficientes y *hashes* de los 20 archivos en `spec_nn_v2.json`; se cargan de ahí, nunca a mano. AUC de validación entre 0.54 y 0.62.

**2.8 Umbral.** $\theta = \arg\max \bar E_{val}$ sujeto a WR ≥ 0.75, ≥ 150 velas y ≥ 15 días. Resultado congelado: $\theta = 0.7142683625605063$ (cuantil 0.98: opera el 2 % superior). En validación: WR 98.7 %, E 2.18 %, 676 velas. **No se relaja $\theta$:** todo cambio de calibración o de umbral perdió entre 8 y 13 pt en diseño. Advertencia: fuera de muestra puede haber menos de 31 operaciones por moneda y año.

**2.9 Co-señal.** $A_{i,t} = \sum_{j \in \mathcal A, j \ne i}\mathbb 1[\max_{t-W<s\le t}\mathbb 1(\hat p_{j,s}\ge\theta)=1]$, con $\mathcal A$ = {BTC, ETH, SOL, DOGE} y $W = 48$ velas (12 h; la ventana incluye la vela actual). Se compra $i$ si $\hat p_{i,t} \ge \theta$ y $A_{i,t} \ge 1$. En diseño, las señales con co-señal ganaron 85.5 % (+1.90 %) y las aisladas, 75.9 % (+0.88 %). Usar $A \ge 1$, no $A \ge 2$ (con $A \ge 2$ la ventaja sobre el azar condicionado desaparece).

**2.10 Salida X5 con barrera de 96 h.** $TP = c(1+0.7s_d)$, $SL = c(1-1.75s_d)$, $H = 384$ velas. Ejemplo: entrada 100, $s_d = 4.31\,\%$ → TP 103.02 (límite), SL 92.46, cierre forzado a las 96 h. Empate TP/SL en la misma vela = SL. Hueco bajo el SL = salida a la apertura. Por qué 96 h: entre 72 y 96 h, las operaciones resueltas terminan en 18 TP frente a 2 SL.

**2.11 Riesgo y tamaño.** $\text{nocional} = \text{riesgo}/R$. Con 0.5 % de riesgo y $R = 7.5\,\%$, el nocional es 6.7 % del capital (67 USDT sobre 1 000). Máximo 3 posiciones (riesgo por episodio ≤ 1.5 %). Pausa si la pérdida acumulada supera 10 R o hay 3 episodios negativos seguidos. Freno general: caída ≥ 10 % desde el máximo, pérdida del día ≥ 5 %, CUSUM y fallos operativos. **No usar Kelly con la E de diseño:** arruinaba entre el 31 y el 55 % de los años simulados.

**2.12 Costos.** Pagar con BNB (0.075 % por lado) y salir del TP con orden límite baja $c$ de 0.24 % a ≈ 0.19 %: +0.05 % de E y 0 de WR. Hay que mantener saldo en BNB.

**2.13 Higiene de eventos.** Excluir la moneda desde un aviso de deslistado o etiqueta de monitoreo; durante ±14–30 días de un desbloqueo grande de tokens; si se listó hace poco. Los choques con noticia siguen la tendencia; los choques sin noticia revierten.

**2.14 La v3 vela a vela.**
1. Al cerrar cada vela de 15 min, comprobar que las 18 monedas y BTCUSDT tienen la vela cerrada y los futuros alineados.
2. Calcular las 74 variables y $\hat p$ con ENS13.
3. Actualizar el registro de señales de las 4 anclas (últimas 48 velas).
4. Para cada moneda con $\hat p \ge \theta$: exigir $A \ge 1$, higiene, sin posición, cupo (< 3) y sin pausa.
5. Comprar a mercado en menos de 60 s; recalcular TP y SL sobre el precio real de llenado; colocar la OCO; guardar `time_stop_ts`.
6. Vigilar la OCO; a las 384 velas, cancelar y vender a mercado.
7. Registrar todo y actualizar los interruptores.

### 3. Qué resultados esperar

**3.1 Historial de versiones.**

| Versión | Diseño | Holdout o monedas nuevas | Lectura |
|---|---|---|---|
| Bot actual, 4 monedas | 6 854 op, 42.5 %, −0.238 % | 1 569 op, **7.1 %**, −0.374 % | Sin ventaja |
| C1, ridge + MR20 | 467 op, 72.4 %, +0.541 % | 148 op, **60.1 %**, −0.498 % | Rechazado |
| v1, ENS6, G3 | 132 op, 72.0 %, +0.93 % | 383 op, **68.7 %**, +0.41 %; ΔWR +16.9 | Rechazado |
| v2, ENS13, X5 | 188 op, **81.4 %**, +1.41 % | 621 op, **69.4 %**, +0.32 %; ΔWR +9.4 | Rechazado: **el 81 % era selección** |
| v2 + co-señal | 131 op, 85.5 %, +1.90 % | — | Inflado |
| **v3** | 131 op, **87.8 %**, +2.02 % (+2.07 % con BNB), $t_{día}$ 5.90 | — | **Cota optimista** |
| **v3 esperada** | — | **WR ≈ 73–79 %, E +0.6 a +1.2 %**, 250–400 op/año, 70–85 % de meses ganadores | Estimación |

En la v2 sobre monedas nuevas, el límite inferior del WR corregido por correlación entre operaciones del mismo día baja a **63.4 %**.

**3.2 Demostrado y no demostrado.**
- **Demostrado:** el modelo elige entradas mejores que el azar en 14 monedas nunca vistas (+9 a +17 pt, ≈ +1.1 % de E).
- **No demostrado:** la E absoluta. El holdout fue bajista: el azar perdía −0.73 % por operación.
- **Concentración:** en la v2, los 10 días más activos reúnen 168 de 621 operaciones con E +1.18 %; el resto tiene E ≈ 0.
- **Descriptivo P1 (2026-10-22)** sobre las 4 monedas originales en 2025-07 a 2026-09 (periodo ya gastado): 169 op, WR 75.7 %, E +0.17 % ($t_{día}$ 0.37). La barrera de 384 velas sube WR y E frente a 288; la compuerta no mejoró en ese periodo.
- **Envejecimiento:** la v2 dio 78 % (2025-T3), 71 % (T4), 63 % (2026-T1), 60 % (T2) y 78 % (T3).

**La información manda, no la arquitectura** (E en walk-forward): LightGBM +0.04 % solo con velas y +0.71 % con futuros; MLP +0.20 % → +0.83 %; CNN +0.19 % → +0.37 %.

**3.3 Robustez de la co-señal.** Aporte +4.1 pt y +0.49 % en diseño; +3 a +6 pt y +0.3 a +0.6 % esperados fuera de muestra, con −30 % de operaciones. Positiva en los 6 pliegues. Episodios: 24, con 83 % positivos; sin los 5 mayores, E +2.20 %. Sobre el azar condicionado, +12.0 pt y +1.19 % ($t = 2.76$), aunque parte del efecto es "el día era bueno". *Bootstrap* por día: ΔE +1.04 % [+0.15, +1.97]; por episodio es más estricto. Gradiente por vela ($W = 4$ h): $A = 0$ → 66.4 %; $A = 1$ → 79.3 %; $A \ge 2$ → 88.5 %.

**E7 (barrera de 96 h):** +2.3 pt / +0.12 % en ENS13, P = 0.04. Versión honesta (barrera elegida con pliegues anteriores): +1.5 pt / +0.07 %. Esperado fuera de muestra: +1 a +1.5 pt y 0 a +0.1 % de E. Riesgo: con deriva negativa podría costar E.

**Cuidado con las cifras de diseño:** la co-señal y la v3 usan el umbral de cada pliegue, no el $\theta$ congelado. Lo que se lee con confianza es la **diferencia** que añade cada capa, no el nivel absoluto.

**3.4 Correcciones de cifras.**
- **Error en `nn_report.summarize`** (corregido el 2026-10-18): reordenaba las monedas con un índice sobre el vector ya ordenado. 145 de las 188 operaciones de diseño de la v2 quedaban asociadas a la moneda equivocada. Las cifras agregadas no cambian; por moneda sí. Tabla vigente: azar de diseño v2 61.7 % / −0.426 %; ΔWR/ΔE +19.7 pt / +1.83 %; BTC 80.9 % / +0.74 %; ETH 87.1 % / +1.67 %; SOL 80.0 % / +1.30 %; DOGE 80.0 % / +1.94 %.
- **Azar corregido en monedas nuevas:** v1 51.7 % (antes 54.4 %), v2 60.0 % (antes 61.7 %). ΔWR/ΔE corregidos: v1 +17.0 pt / +1.08 %; v2 +9.4 pt / +1.00 %; secundaria v1 +6.6 pt / +0.39 %. Los veredictos no cambian.
- **Tabla de versiones vieja → vigente:** alineación $T \le t+10$ → $T \le t+5$ min; ENS6 → ENS13; reentrenamiento cada trimestre → **prohibido** durante la prueba; *bootstrap* por día → por episodio; pruebas para el DSR 12 268 → **12 666**.

**3.5 Lo que no es confirmación.** "17/18 meses" (v2 sin compuerta, meses con E > 0) y "15/15 meses activos" (v3) son métricas distintas.

### 4. Piezas opcionales y con reserva

**4.1 D1, veto por DVOL bajo (brazo S3).** No comprar si $z_{30}(t) = (\text{DVOL}_{h} - \overline{\text{DVOL}}_{720})/\sigma_{720} < -1$, con DVOL de Deribit para BTC usado en todas las monedas. Si el precio cae sin que las opciones paguen miedo, la caída se parece a la de un vendedor informado.

| Ensamble | ΔWR / ΔE sobre la v3 | Vetadas: n, WR, E |
|---|---|---|
| ENS13 (contaminado) | +3.3 / +0.33 % | 14, 64 %, −0.50 % |
| ENS12U | +2.1 / +0.20 | 54, 69 %, −0.13 % |
| ENS6 | +2.7 / +0.26 | 11, 55 %, −1.32 % |

A favor: P por episodio 0.01–0.05. En contra: el azar condicionado explica entre 63 y 129 % del efecto; descansa en 5–7 episodios. **Si se confirma:** +0.5 a +2 pt y +0.05 a +0.2 % de E, con 35–45 % de probabilidad de efecto nulo. Solo se confirma con episodios nuevos. **Grabar el DVOL desde ya.**

**4.2 ENS12U, pesos de unicidad (brazo S2).** $u_i = \frac{1}{|T_i|}\sum_{t\in T_i} 1/c_t$, donde $c_t$ cuenta las etiquetas activas en la vela $t$ sumando las 4 monedas. Reduce la brecha validación-prueba, pero no sube el WR (76.5 % frente a 79.1 %). Lo vuelve más creíble.

**4.3 S4, palanca de preferencias (no es una mejora).** Desde las 36 h, bajar el TP a +0.6 %: 90.2 % de WR y −0.16 % de E frente a la v3. Compra WR con E; es *post hoc*.

**4.4 Hipótesis abiertas (grabar, no adoptar).**

| Hipótesis | ΔWR / ΔE | Problema |
|---|---|---|
| G_BE: la co-señal viene de BTC o ETH | +2.4 / +0.26 | 3/6 pliegues |
| F_rank1: la moneda que inicia el episodio | +4.3 / +0.22 | −63 % de operaciones |
| Episodio ≥ 3 días después del anterior | +2.8 / +0.38 | n = 60 |
| BTC > SMA30 | +4.7 / +0.34 | No se replica; habría apagado el bot en el holdout |
| Liquidaciones exactas | No probado | Datos limitados |
| Tipo de choque (titulares con LLM) | No probado | GDELT dio HTTP 429 |

Una variable entra al modelo solo si, con ≥ 150 señales prospectivas, muestra gradiente monotónico con P ≤ 0.10.

### 5. Lo que no funciona: no repetir

Cifras de diseño salvo que se indique. Referencia: v2 81.4 % y +1.41 %; con co-señal, 85.5 % y +1.90 %.

| Pieza | Número clave | Por qué falla |
|---|---|---|
| Estrategias actuales (MR, TF, Squeeze, VWAP) | WR = geometría; E −0.20 a −0.27 % | Sin información |
| Optimizar con 1 mes y 1 196 configuraciones | PBO hasta 0.51 | Elige ruido |
| 41 filtros univariados | RSI +7.8 → −3.0 pt; volumen +2.9 → −5.4 | Se invierten |
| Meta-etiquetado logístico | AUC 0.52–0.55 | Sin ventaja |
| C1, ridge + MR20 | 72.4 → 60.1 % | Selección |
| TP corto ($b \approx 0.3$), G4 | WR 70–80 %, E −0.17 a −0.31 % | El azar logra lo mismo |
| LSTM, Transformer, CNN más grande | Parada en épocas 1–3 | Sobreajuste |
| Entrada *maker* escalonada | E +0.61 a +1.22 % | Selección adversa |
| Toma parcial + stop a equilibrio | 90.4 % "contable" (azar 79.5 %), −0.6 % de E | WR fabricado |
| SL ancho, salida a 24 h | +1.27 / +1.25 / +0.55 % | Peores que X5 |
| ACI (umbral adaptativo) | 72.5–78.2 % | Persigue ruido |
| Abstención por desacuerdo | 78.9 % / 80.5 % | Las de más desacuerdo son mejores (84.1 %) |
| $\theta$ más bajo en pánico | 70–72 %, E +0.08 a +0.35 % | Añade beta del día |
| Cobertura con corto en BTC | 78.7 % / +0.95 % (media) | Pierde en los rebotes |
| *Grid* spot, DCA, martingala | 98.7–99.9 % de ciclos con pérdida latente | Ruina |
| Geometría elegida en walk-forward | +0.0 pt / −0.09 % | Ninguna domina a X5 |
| $\theta$ re-elegido con la compuerta | −8.0 a −8.4 pt | No relajar $\theta$ |
| H3, TP por estado | 93.9 %, −1.01 % | Toma parcial disfrazada |
| H8 calibración beta; H9 Platt mensual | −11.7 a −12.7 pt | Platt frágil en la cola |
| LLM como decisor, modelos fundacionales | WR 41 % frente a 50 % | Solo vale un LLM como clasificador de titulares |
| *Carry*, *market making*, *Dual Investment*, arbitraje | — | Bloqueado, E < 0 o venta de cola |

**Lecciones:** (1) lo que espera o recorta después de la señal pierde los mejores rebotes; (2) lo que sube el WR sin información nueva lo paga con E o lo esconde en la cola; (3) toda calibración o cambio de $\theta$ pierde 8–13 pt.


### 6. Trampas del WR fabricado

| Trampa | Cómo se ve |
|---|---|
| Geometría | TP corto y SL largo: el azar ya acierta $1/(1+b)$ |
| Pérdidas que no se cierran | Martingala, DCA, *grid*, "mantener hasta que dé ganancia" |
| Contar mal | TP parcial como ganancia; salidas "en cero" como ganadas |
| Costos irreales | Comisión cero o límite llenado al tocar el precio |
| Selección | Miles de variantes y se publica la mejor (v2: 81 → 69 %) |
| Fugas del futuro | `create_time` desde 2024-03-04; velas abiertas |
| Ventanas y rankings | "Últimos 90 días" alcistas; sobrevivientes |
| Productos de "rendimiento" | APR "garantizado" que es una prima de opción vendida |

**Antes de creer cualquier WR, exigir:** (a) E neta con $t$ agrupado por día; (b) WR del azar con la misma geometría; (c) pérdida máxima y drawdown con posiciones a mercado; (d) número de configuraciones probadas; (e) resultados posteriores al congelamiento. Si la mejora viene de cambiar la salida, la E también debe subir.

### 7. Especificación para implementar

**7.1 Estado del código.**

| Pieza | Hoy | Falta |
|---|---|---|
| `ws-client.ts` | Corregido 2026-10-18: `@kline_15m`, solo velas cerradas, TP/SL con cada precio, sin doble SELL | Sincronizar varias monedas por `open_time` |
| `rest-client.ts` | Redondeo por `stepSize`/`tickSize` hacia abajo | SL con `ceil`; `MARKET` con `FULL`; OCO |
| `quantitative_strategies/` | Bollinger. 2026-10-19: las cuatro quedaron `rechazada` en las 4 monedas | — |
| `strategy_engine.py`, `optimize.py` | Paridad verificada; `ml_evaluator.py` marca `validada` o `rechazada` | Estados `prospectiva` y `paridad`; `strategy_registry.json` |
| `server.py` | Precarga velas cerradas del mismo mercado que el WebSocket | Mensaje `bars` multi-moneda; precarga ≥ 35 días |
| `src/risk/`, OCO, `nn_strategy/` | **No existen** | Crear (§7.3 y §7.4) |

**7.2 Infraestructura obligatoria.**

| # | Requisito |
|---|---|
| S1 | Datos en vivo = datos del backtest: velas cerradas, ventana que no se congela, entrada en < 60 s (una vela de retraso le costó a C1 ≈ 30 % de E) |
| S2 | Redondeo por filtros de Binance |
| S3 | Backtest honesto (`harness.py` con 46 pruebas) |
| S4 | Protocolo: Wilson, $t$ por día, ΔE frente al azar, DSR ≥ 0.95, PBO ≤ 0.2, Holm |
| S5 | Gestión de riesgo: topes e interruptores |
| S6 | Ejecución verificable: MARKET + OCO + `time_stop_ts` persistente + prueba de paridad |
| S7 | Motor en `HOLD`; dinero real en cero |

Redondeo: $TP' = \lfloor TP/\text{tick}\rfloor\,\text{tick}$, $SL' = \lceil SL/\text{tick}\rceil\,\text{tick}$, $q' = \lfloor q/\text{step}\rfloor\,\text{step}$, válida si $TP' \ge P + \text{tick}$ y $SL' \le P - \text{tick}$. Ejemplo: DOGE a 0.09000 con TP 0.09150; con `round(x, 2)` el TP quedaba en 0.09 (igual a la entrada).

**Topes:** nocional por operación ≤ 10 %, total ≤ 40 %, cola total ≤ 6 %. Detener con caída ≥ 10 %, pérdida del día ≥ 5 %, racha ≥ 8, CUSUM desde 30 operaciones, revisión a las 150 operaciones con $t_{día} < 1$, o fallos operativos (deslizamiento > 0.10 % por lado en 50 operaciones; datos con más de 2 velas de atraso).

**Paridad (S6), al menos 2 semanas o 50 operaciones:** velas idénticas al REST; señales con Jaccard = 1; deslizamiento ≤ 0.02 % por lado; ≥ 95 % de salidas coincidentes. **La testnet solo valida infraestructura**, nunca la calidad de la señal.

**7.3 Módulos Python propuestos.** `nn_strategy/features.py` (74 variables con $T \le t_i + 5$ min), `nn_strategy/model.py` (verifica SHA-256 al arrancar), `nn_strategy/gate.py` (búfer de 48 velas), `nn_strategy/exits.py` (TP, SL, `time_stop_ts`), `nn_strategy/hygiene.py`, `feeds/futures_shadow.py` (archivos diarios), `feeds/dvol.py`, `strategy_registry.json` (`rechazada`, `paridad`, `prospectiva`, `validada`), `shadow/run_daily.py` (simula brazos sin órdenes) y `backtest/`. `strategy_engine.py` solo devuelve señales de estrategias validadas.

**7.4 Cambios en Node propuestos.**
1. `ws-client.ts`: `@kline_15m`, ignorar `k.x === false`, acumular por `open_time`.
2. `rest-client.ts`: `placeMarketOrder` (`MARKET`, `FULL`, precio medio = `cummulativeQuoteQty / executedQty`), `placeSellOco` en `/api/v3/orderList/oco`, `getOrderList` y `cancelOrderList`.
3. `src/risk/sizing.ts`: nocional = 0.5 % / $R$, máximo 3 posiciones.
4. `src/risk/kill-switches.ts`: pausas de la v3, guardadas en `orders/risk_state.json`.
5. Barrera persistente: `time_stop_ts = open_time + (384 + 1)·900 000` ms.
6. Registro en `orders/trades.csv` con `strategy_id`, `spec_hash`, precios de llenado, `oco_order_list_id`, `time_stop_ts`, motivo de salida, PnL neto y marcadores.

**7.5 Lista de control anti-fuga.**
- [ ] Solo velas cerradas; decisión en $t_i + 15$ min; *metrics* con $T \le t_i + 5$ min.
- [ ] Estandarización con estadísticos del entrenamiento; purga de $H+1$ velas.
- [ ] Co-señal con velas cerradas; DVOL con horas cerradas.
- [ ] Tras cualquier cambio en variables: auditoría de los 16 cortes y prueba de alineación.
- [ ] Ninguna decisión con datos del holdout 2025-07 a 2026-09.

**7.6 El bloqueo de fapi y sus tres salidas.** El modelo necesita cada 5 min OI, ratios, *funding* y prima de `fapi.binance.com`, que responde **HTTP 451** desde la ubicación del usuario.
1. **Sombra diferida:** archivos diarios de `data.binance.vision` (1 día de retraso). Bastan para la prueba prospectiva.
2. **Fuente sustituta en vivo** (Coinalyze, OKX *rubik*), con prueba de equivalencia. Si no es equivalente, reentrenar con esa fuente.
3. **Servidor en una jurisdicción permitida**, cumpliendo los términos de Binance.

Sin una de las tres, nada se opera en vivo. D1 no depende de Binance.

**7.7 Monitoreo.** Frecuencia de señales fuera de ×0.5–×2 de lo esperado; WR real frente a $\hat p$ medio con más de 10 pt de diferencia; deriva de variables clave; pasar a `HOLD` si, con ≥ 30 operaciones, E < 0 con $t < -2$ o el WR cae por debajo del 55 %.

**7.8 Pruebas de aceptación.** Arnés 46/46; sombra que reproduce bit a bit 3 días de control (2025-06); redondeo sin $TP' \le P$ ni $SL' \ge P$; tamaño con casos sintéticos; paridad en testnet y *hashes* al arrancar.

### 8. Hoja de ruta y pre-registro

**8.1 Fases.** Cada paso que descarga de Binance requiere la VPN apagada.

| Fase | Prioridad | Plazo | Qué | Criterio |
|---|---|---|---|---|
| 0 | P0 | 1–3 días | Corregir `summarize`, reemitir tablas, firmar pre-registro con *hash* | Si el azar corregido mueve ΔWR más de 2 pt, se anota |
| 1 | P0 | Semanas 1–2 | Canal sombra diario de 18 monedas + DVOL | Reproduce 3 días de control; faltan ≤ 5 % |
| 2 | P1 | Semanas 2–6 | Holdout fresco de 20 monedas (2023-01 a 2025-06) | Solo confirma reglas dentro del episodio |
| 3 | P1 | Semanas 3–6 | Estrés 2022 (LUNA, FTX) | Pérdida por episodio ≤ 3 R |
| 4 | P2 | Desde ya | Grabar hacia adelante: DVOL, USDT-USD de Coinbase, L4, Hyperliquid, anuncios, titulares | Entra con ≥ 150 señales y gradiente monotónico con P ≤ 0.10 |
| 5 | P2 | Mes 1 | ENS12U reentrenado hasta 2026-09-30 y congelado | Brazo S2 |
| 6 | P0 | Meses 1–15 | Prospectiva con revisión mensual | Aprobar, futilidad o seguir |
| 7 | P3 | Solo si aprueba | Operación real pequeña con BNB y topes | 3 meses con deslizamiento ≤ 0.1 % por lado |

Las reglas de episodio (co-señal, D1) solo se confirman con el estrés 2022 o la prospectiva. Las reglas dentro del episodio (E7, H5) se confirman con cualquiera de las tres.

**8.2 Pre-registro y brazos** (redactado el 2026-10-15; especificación congelada `spec_nn_v2.json`; X5 con 384 velas; universo de 18; $T \le t_i + 5$ min):

| Brazo | Regla | Papel |
|---|---|---|
| **P1** | v2 + $A_4 \ge 1$ ($W$ = 12 h) + 384 velas | Primario |
| C0 | v2 sin compuerta | Control |
| S1 | v2 + $A_{18} \ge 3$ | Secundario |
| S2 | ENS12U + $A_4 \ge 1$ | Secundario |
| S3 | v3 + D1 | Secundario; regla de episodio |
| S4 | v3 + TP a +0.6 % desde las 36 h | Opcional |
| Azar | Misma moneda, mes y geometría | Referencia |

Periodo: desde 2026-10-01 hasta 400 operaciones de P1 o 2027-12-31, lo que llegue primero (12–18 meses esperados). Con WR 76 % hacen falta ≈ 225 operaciones independientes; ≈ 400–450 con DEFF ≈ 2.

**8.3 Criterios de aprobación de P1** (con $c = 0.24\,\%$ salvo indicación):
1. E > 0 con $t$ por día ≥ 1.645, y E > 0 también con $c = 0.30\,\%$.
2. Límite inferior de Wilson ≥ 0.70 ("aprueba 70") o ≥ 0.75 ("aprueba 75"). **El 80 % solo se declara con límite inferior ≥ 0.80.**
3. ΔE frente al azar > 0 con $t \ge 1.645$, y ΔWR > 0.
4. E(P1) − E(C0 con $A_4 = 0$) > 0, con P ≤ 0.10 por *bootstrap* (por días; reportar también por episodio, más estricto).
5. ≥ 60 % de los episodios en positivo.
6. Hashes intactos.

**Criterio de S3:** con ≥ 150 señales de P1, las vetadas por D1 deben tener menos WR, con P ≤ 0.10 y ≥ 5 episodios vetados.

**8.4 Vigilancia mensual con e-procesos.** Mirar cada mes y parar cuando "se ve bien" infla los falsos positivos. Un e-proceso permite mirar cuando se quiera:

$$
M_n = \prod_{i=1}^{n}\big(1 + \lambda_i(X_i - p_0)\big),
\qquad \text{rechazar } H_0: p \le p_0 \text{ si } M_n \ge 20
$$

con $X_i = 1$ si la operación ganó, $p_0 = 0.70$, $\lambda_i \in [0, 1.43]$ elegido solo con datos anteriores y $20 = 1/\alpha$. Con WR real de 78 %, $\ln M$ crece ≈ +0.014 por operación y llega a $\ln 20$ en ≈ 210 operaciones. **Futilidad:** con ≥ 200 operaciones, si el límite superior de Wilson es < 0.70 o la E queda entera bajo 0, se declara "no aprobado".

**8.5 Prohibiciones y dinero real.** Durante la prueba no se cambian $\theta$, la geometría (incluida la barrera de 384), el corte de D1, el universo ni $W$; no se reentrena la v2; no se usa el holdout. No hacer: *grid*, DCA, martingala, toma parcial, recalibrar $\theta$, LLM como decisor, entradas *maker*. **Dinero real:** $w = 0$ hasta aprobar; después, empezar con $w = 0.05$ y nunca más de ¼ de Kelly calculado con la E en su cota inferior.

**8.6 Dónde está todo.** La carpeta de datos y modelos está en `binance-research/data/research/` (ignorada por git). Clave: `output/constructor/spec_nn_v2.json` (especificación congelada), `nn/models_v2/` (20 archivos, 796 KB), `nn/nn_common.py` (variables), `scripts/harness.py` (arnés), `output/validador/trials_log.csv` (12 666 configuraciones), `output/verificador/` (preregistros y auditorías). Los datos auxiliares (Deribit DVOL, Bitfinex, Coinbase, etc.) están en `E:/tmp/r2_data/`.

---

## 5. Resultados de la v3 al 2026-10-24

Todo con el modelo congelado (`spec_nn_v2.json`), salida X5 con 384 velas, 15 USDT por operación y costo de 0.24 % ida y vuelta, salvo indicación. Salidas en `binance-research/v3_research/output/`.

**Respuesta corta.**
- **Lo único que gana dinero fuera de muestra es la v3, y gana poco:** C0 en 19 monedas nunca usadas dio E +0.41 % por operación y +95 USDT en 15 meses (≈ +6 USDT/mes con 15 USDT por operación). **No es significativo** ($t$ por día 1.08, p = 0.14) y solo 8 de 15 meses fueron positivos.
- **En mercado bajista pierde:** en 2022, S1 en 18 monedas perdió −44.49 USDT, aunque siguió ganándole al azar por +6 pt de WR.
- **Un PnL positivo todos los meses no está al alcance:** en todos los periodos hay entre un tercio y la mitad de meses negativos.
- **Descartado con datos nuevos:** las 5 estrategias de Bollinger (pierden en 10–11 de cada 13 monedas) y el filtro "BTC > media de 30 días" (mejoraba 2025–26 pero empeoró 2022).

**Tablas.**

| Periodo (C0, 19 monedas) | Op. | WR | E | PnL | Monedas + | Meses + | p |
|---|---|---|---|---|---|---|---|
| 2023-03 a 2025-06 (entrenamiento, otras monedas) | 3041 | 76.7 % | +0.85 % | +386 | 19/19 | 25/28 | < 0.001 |
| **2025-07 a 2026-09 (nuevo)** | 1548 | 72.5 % | **+0.41 %** | **+95** | 14/19 | 8/15 | 0.14 |

La primera fila está inflada: el modelo aprendió ese comportamiento. La que cuenta es la segunda.

**Universo de 18 del pre-registro (S1):**

| Periodo | Op. | WR | E | PnL | Monedas + | Meses + | Peor mes | Caída máx. |
|---|---|---|---|---|---|---|---|---|
| 2022 (estrés) | 1129 | 67.1 % | −0.26 % | −44.49 | 6/18 | 5/12 | −34.2 | 102.0 |
| 2025-07 a 2026-09 (gastado) | 1051 | 72.1 % | +0.22 % | +34.13 | 14/18 | 10/15 | −28.7 | 71.5 |
| 2026-10-01 a 10-23 (prospectivo) | 33 | 72.7 % | +0.20 % | +0.99 | 8/15 | — | — | — |

**Costos.** Con BNB y TP como orden límite (0.17 %), la E sube ≈ +0.065 puntos por operación en todos los brazos.

**Riesgo y tamaño.** Con 18–19 monedas puede haber hasta 19 posiciones abiertas (≈ 285 USDT con 15 USDT cada una). Caídas máximas de 70 a 102 USDT: entre el 25 % y el 36 % de ese capital. Con 30 USDT por operación, la expectativa del periodo nuevo sería ≈ +12 USDT/mes, con meses de −70 USDT. **Recomendación:** dinero real en cero hasta que el canal sombra acumule 150–200 operaciones de S1 posteriores al 2026-10-01 y la E siga positiva con $t$ por día ≥ 1.645.

**Coinalyze (la v3 en vivo).** Coincide casi perfecto con Binance en OI, ratio global, flujo taker, velas del perpetuo y funding (correlación ≥ 0.999). No tiene los ratios de top traders ni la prima. La prueba de equivalencia del modelo **no es concluyente**: no hubo señales en los 5 días que cubre Coinalyze. `v3_live.py` genera señales en vivo sin enviar órdenes.

**Pendiente.** (1) Acumular operaciones prospectivas (tarea semanal de `scripts/programar_tareas_v3.ps1`, con una diaria para el canal sombra y otra cada 15 min para las señales). (2) Que la equivalencia de Coinalyze dé "equivalente" con al menos 5 señales. (3) Solo entonces, órdenes de la v3 en testnet.

**Actualización (2026-10-24): reglas de cartera y umbral.** Probadas en monedas nuevas, eligiendo con el periodo de diseño y validando en 2025-07 a 2026-09 y 2022.

*Descartado:* tope de posiciones abiertas (reduce el PnL más que la caída); interruptor mensual por PnL previo (inestable); más co-señal (mejora poco); tamaño según la confianza (la prueba sobreestima el efecto).

*Sí se sostiene: subir el umbral del modelo de 0.7143 a 0.745.* La E sube de forma monótona con $p$ en los tres periodos y la caída máxima se reduce a la mitad:

| S1 (A18 ≥ 3), 19 monedas nuevas | θ = 0.7143 | **θ = 0.745** |
|---|---|---|
| Diseño 2023-03 a 2025-06: E / PnL / caída | +0.97 % / +408 / 63 | +1.67 % / +296 / 30 |
| **Nuevo 2025-07 a 2026-09: E / PnL / caída / meses +** | +0.45 % / +95 / 93 / 8 de 15 | **+1.10 % / +100 / 41 / 11 de 15** |
| Estrés 2022: E / PnL / caída | −0.27 % / −46 / 102 | −0.10 % / −9 / 77 |

**Confirmación pre-registrada en 13 monedas distintas** (preregistro escrito antes de descargar datos): E +0.86 % → **+1.57 %**, caída 78 → 35 USDT.

**Lo que no resuelve.** El resultado depende de pocos días de pánico: sin los 10 mejores días, el periodo nuevo queda en −34 USDT (S1H). La mediana mensual de S1H es +2 USDT. En 2022 sigue sin ganar. Con 15 USDT por operación: ≈ +3 a +7 USDT al mes, con hasta 13–19 posiciones abiertas.

**Registro.** S1H (S1 con $p \ge 0.745$) queda como brazo exploratorio en `run_daily.py` y `v3_live.py`, fijado para la prueba prospectiva.

**Qué tan reciente es la evidencia.** Los periodos terminan en 2026-09 porque los datos completos de futuros llegan hasta ahí. Octubre se reconstruyó con prima de perpetuo (equivalente, Jaccard 0.92). El umbral 0.745 se eligió mirando esos meses; solo la confirmación en 13 monedas y octubre son independientes.

**Por trimestre (S1 con θ = 0.7143 frente a S1H con θ = 0.745):**

| Trimestre | S1: WR / E / PnL | S1H: WR / E / PnL |
|---|---|---|
| 2025-T3 | 83 % / +1.40 % / +41 | 91 % / +2.15 % / +17 |
| 2025-T4 | 71 % / +1.37 % / +69 | 76 % / +3.38 % / +82 |
| **2026-T1** | 66 % / −0.39 % / −19 | 68 % / −0.23 % / −5 |
| **2026-T2** | 60 % / −0.86 % / −31 | 57 % / −0.78 % / −12 |
| 2026-T3 | 82 % / +0.73 % / +35 | 82 % / +0.91 % / +19 |

El modelo se desgastó en la primera mitad de 2026 y se recuperó en el tercer trimestre. S1H pierde menos en los malos trimestres, pero también pierde. Eso apoya reentrenar con datos recientes como brazo aparte (S2).

**1 a 23 de octubre de 2026** (posterior a todo lo mirado; el umbral ya estaba fijado):

| Monedas | θ | Op. | WR | E | PnL |
|---|---|---|---|---|---|
| 19 nuevas | 0.7143 | 45 | 68.9 % | −0.14 % | −0.9 |
| 19 nuevas | **0.745** | 20 | 80.0 % | **+0.95 %** | **+2.8** |
| 13 nuevas | 0.7143 | 31 | 77.4 % | +0.80 % | +3.7 |
| 13 nuevas | **0.745** | 11 | 81.8 % | **+0.77 %** | **+1.3** |

Son muy pocas operaciones para concluir, pero S1H es positivo en los dos conjuntos.

---

## 6. Estrategia de extremos (video de YouTube)

*Implementación y backtest del 2026-11-02. Código en `binance-research/extremos/`. Proyecto aparte: no toca las estrategias del bot.*

**Reglas.**
- **Diario (UTC, cierre del día), las tres condiciones:**
  - *Extremo:* soporte con al menos `toques` mínimos locales (pivote de 3 días) dentro de ±0.5 ATR en el último año; el mínimo de hoy entra en esa zona y el cierre no queda más de 0.5 ATR por debajo; el mínimo de hoy está en el 25 % inferior del rango de 90 días.
  - *Llega estirado:* en los últimos 5 días hubo un tramo de 5 velas con $z \le -\theta$, donde $z = (\ln C_t - \ln C_{t-5})/(\sigma_d\sqrt5)$.
  - *Frena y gira:* cuerpos de las últimas 3 velas < 60 % de los de las 3 anteriores; mecha inferior media ≥ 30 % de la vela; cierre de hoy por encima de $O_{t-1}$, $O_{t-2}$ y $C_{t-3}$.
- **1 h, durante 3 días:** mínimo de la caída; ruptura con un cierre sobre el último máximo local; Fibonacci del impulso; toque de $P_{0.618} + 0.25\,ATR_{1h}$ con $|EMA_{50} - P_{0.618}| \le c\cdot ATR_{1h}$. Se descarta si antes toca el 0.75.
- **Gatillo en 5 min,** hasta 6 h después del toque: primer cierre sobre la diagonal de los dos últimos máximos decrecientes y/o la EMA 20. Se compra a ese cierre.
- **Salida:** stop en 0.75; objetivo en el máximo del impulso o 1.6 R; 7 días sin tocar → cierre. Costo 0.24 %. Una operación por moneda.
- **Datos:** velas de 5 min de 23 monedas, 2021-10 a 2026-10. Diseño hasta 2024-12; validación desde 2025-01.
- **Criterio:** E > 0 en validación, $t \ge 2$, al menos 100 operaciones y además $t \ge 2$ contando cada día de señal una vez.

**Rejilla:** 64 combinaciones (toques {2, 3}; θ {1.5, 2}; condición 3 sí/no; $c$ {1, 2}; gatillo {EMA 20, diagonal + EMA 20}; objetivo {máximo, 1.6 R}).

**Respuesta corta: no pasa el criterio.**
- Al pie de la letra casi no opera: 1 operación en diseño y 1 en validación.
- La mejor combinación de diseño pierde en validación: −0.33 % por operación con 51 operaciones.
- Lo único con algo de señal es el filtro diario solo (comprar al día siguiente y vender a 3 días): diseño +0.69 % (58 op., $t$ 0.9); validación +2.21 % (27 op., $t$ 1.94). Comprar todos los días perdió −0.57 % en el mismo periodo.

**Walk-forward (elegir con todo el pasado).** Completa: 41 operaciones fuera de muestra, +1.78 %, $t$ 1.75. Solo diario: 75 operaciones, +2.24 %, $t$ 3.20 pero $t$ **por día 0.68**. Las 75 operaciones salen de 32 días; un día (2024-04-18) aporta 14 operaciones que ganaron +6.4 % cada una (rebote de todo el mercado). Contando cada día una vez, la ganancia baja a +0.78 %. 2026 es negativo en las dos familias.

**Dónde se pierden las señales (versión al pie de la letra):** de 26 311 días-moneda en diseño, 7 087 pasan la condición de extremo, 1 047 llegan estirados, 76 frenan y giran, 25 no tocan el 0.618 en 3 días, 38 tocan pero la EMA 50 queda lejos, 11 tocan el 0.75 antes. El paso más restrictivo es la confluencia con la EMA 50: después de una caída fuerte la media queda muy arriba.

**Recomendación:** no llevarla al bot. La señal diaria gana en promedio, pero casi todo viene de unos pocos rebotes de mercado que dan señal en muchas monedas a la vez. Si se sigue, tratar la señal como evento de mercado y juntar más años de datos.

**Cómo reproducir:** `cd binance-research/extremos`, `python descargar_5m.py`, `python -m unittest test_estrategia`, `python backtest.py` y `python backtest.py --walk-forward` (≈ 3 min de descarga y 3 min por backtest).

---

## 7. Estrategia de retrocesos (video "150 dólares en una semana")

*Backtest con velas reales de 1 min de Binance spot, 2023-01-01 a 2026-11-12. Código en `binance-research/pullback/`.*

**Conclusión: no se usa.** Ninguna de las 12 288 combinaciones probadas gana de forma estable después de costos.
- La lectura literal (stop de 0.15 %, objetivo 1:1) pierde en el 99.7 % de las operaciones: la comisión de ida y vuelta (0.24 %) es mayor que la distancia al objetivo.
- Con stops más amplios, la ganancia **antes de costos** queda cerca de cero (la mejor, +0.12 % por operación) y no alcanza a pagar el 0.24 %.
- Ninguna combinación es positiva los 4 años. En 2026 solo el 1.7 % gana, y esas mismas pierden en otros años.
- Elegidas sin mirar el año juzgado (walk-forward), pierden en 2024, 2025 y 2026, y peor que entradas al azar con las mismas salidas.

**Reglas implementadas.** Monedas BTC, ETH, BNB, XRP, SOL y DOGE. Dirección en 1 h (tendencia, reversión o rango). Estructura de impulso y retroceso en 5 min. Gatillo en 1 o 5 min al cerrar sobre el máximo de las 3 velas anteriores y sobre la EMA 50. Stop bajo el mínimo del retroceso (distancia mínima 0.6, 1.2 o 2 %) o el 0.15 % del video. Objetivo 1, 1.5, 2 o 3 R. Filtros: horario europeo, sin operar alrededor de FOMC y empleo, BTC a favor para altcoins. Reglas del video: una posición a la vez, máximo 2 por día. Costo 0.24 %. No se programó lo que el video no define (cuñas, libro de órdenes). El calendario de CPI no se pudo descargar.

**Walk-forward (solo largos).** 2024: −0.42 %; 2025: −0.26 %; 2026: −0.68 % (muestras de 18 a 156 operaciones). Total: 227 operaciones, −0.40 % por operación, $t$ por día −3.37. Entradas al azar con las mismas salidas: −0.06 %. La estrategia pierde más que el azar.

**Trampa de elegir mirando 2026.** Las mejores combinaciones de 2026 son cortos con stop de 2 % y objetivo 2R (+1.0 a +1.1 % por operación, ≈ 30 operaciones). En 2024 esas mismas perdieron entre −0.4 % y −0.8 %. Elegir así es ajustar al pasado.

---

## 8. Predicción por análogos

*Plan y resultados. Código en `binance-research/analogos/`. Proyecto aparte: no usa ni modifica las estrategias del bot.*

**Idea.** Buscar en el pasado los momentos más parecidos al actual y usar lo que pasó después para predecir. Cada sugerencia se mide con el mismo marco y solo se adopta si mejora **en validación**, después de comisiones.

**Marco común.**
- Velas de 1 h de BTC, ETH, SOL y DOGE (2021-10 a 2026-10). Biblioteca de vecinos con 24 h de margen.
- Predicción $\hat y_t = \sum w_i y_{s_i}/\sum w_i$ y consenso $\pi_t = \#\{y_{s_i}>0\}/k$. Compra si $\hat y > c = 0.24\,\%$ y $\pi \ge q$; venta a las $h$ velas; 15 USDT por operación.
- **Reglas sin fuga:** vecinos solo con $s \le t - 24$; cada variable con información publicada hasta $t$; estandarización con datos anteriores a $t$; un vecino por episodio.
- **Periodos fijos:** diseño 2023-01 a 2024-12 (aquí se eligen parámetros); validación 2025-01 a 2026-10 (se mira una vez).
- **Criterio:** E neta > 0 en validación, $t \ge 2$ y al menos 100 operaciones.

**Sugerencias.**
1. **k-NN sobre la forma del precio:** ventana z-normalizada de $L$ velas; distancia euclidiana; rejilla de $L$, $k$, $h$, $q$ y tamaño de biblioteca.
2. **DTW (alineamiento temporal):** banda de Sakoe–Chiba $r$; LB_Keogh como cota inferior; horizonte escalado por la pendiente del camino.
3. **Estado del mercado (forma + contexto):** 10 variables (retornos de 6 y 24 h, curvatura, volatilidad relativa, volumen relativo, compras agresivas, posición en el rango de 7 días, tendencia de BTC, funding, cambio del interés abierto); pesos aprendidos; PCA opcional.
4. **Patrones como palabras (SAX):** palabras de $n$ velas con niveles de retorno estandarizado; estimador de probabilidad con Wilson; corrección de Bonferroni.
5. **Todas las monedas y acuerdo de 4 h:** biblioteca conjunta; 1 h como señal y 4 h como filtro.

**Resultados (elegidos solo con diseño; medidos en validación).**

| Sugerencia | E diseño | E validación | n validación | $t$ | IC validación | ¿Pasa? |
|---|---|---|---|---|---|---|
| 1 · k-NN forma | +0.37 % | **−0.14 %** | 970 | −1.28 | +0.011 | No |
| 2 · DTW | +0.29 % | **−0.30 %** | 836 | −2.41 | −0.022 | No |
| 3 · Estado del mercado | +1.60 % | **−0.39 %** | 138 | −0.96 | +0.028 | No |
| 4 · Palabras | +0.63 % | **−0.17 %** | 603 | −1.38 | +0.005 | No |
| 5 · Todas las monedas | +0.42 % | **−0.59 %** | 118 | −1.75 | −0.022 | No |
| Referencia: comprar siempre | +0.08 % | −0.27 % | — | — | — | — |

**Lectura.**
- **Ninguna pasa el criterio.** Todas ganan en diseño, donde se eligen parámetros, y pierden o quedan en cero en validación. El IC de validación está entre −0.02 y +0.03.
- **Control con fuga de futuro:** +1.21 % en validación. Confirma que la prueba detecta la trampa.
- **Estado del mercado:** el camino de mejoras en validación fue forma −0.24 %; + contexto +0.02 %; + estandarizar −0.08 %; + pesos aprendidos **+0.12 %** ($t$ 0.53); + PCA −0.39 %. PCA fue la mejor en diseño (+1.60 %) y la peor en validación: el ejemplo más claro de sobreajuste.
- **DTW:** ninguna banda mejora a la euclidiana. La pendiente media del camino quedó en 0.99–1.00: casi no hay patrones "más lentos o más rápidos" que aprovechar.
- **Palabras:** Bonferroni reduce las operaciones de diseño de 403 a 125, sin cambiar el resultado.
- **Todas las monedas:** 1 moneda −0.59 %; 4 monedas −0.45 %; 23 monedas −0.21 % (solo 8 % de los vecinos son de la misma moneda). El filtro de 4 h empeora en todos los casos.

**Qué significa.**
1. El precio pasado, solo o con este contexto, no predice las 12–24 h siguientes lo bastante para pagar 0.24 % de comisión.
2. Elegir mirando los datos infla siempre el resultado: las 5 sugerencias ganaban entre +0.29 % y +1.60 % en diseño.
3. El marco de prueba funciona y se puede reutilizar.
4. **Recomendación:** no llevar ninguna regla al bot. Lo único con algo de señal es el contexto de la sugerencia 3 con pesos aprendidos (+0.12 %, $t = 0.53$), que requeriría información nueva (liquidaciones, flujo de órdenes) y validación en monedas y meses no mirados.

**Cómo reproducir:** `cd binance-research/analogos`, `python -m unittest test_common test_s2`, `python run_all.py` (≈ 60 min en 4 núcleos; datos desde `ANALOGOS_DATA_DIRS` si están en otra carpeta).

---

## 9. Mapa de referencias antiguas

Si un comentario o README cita un archivo antiguo, esta es la equivalencia:

| Cita antigua | Ahora |
|---|---|
| `doc/matematica-del-bot.md` (§n) | `doc/referencia-compacta.md` §2 (mismos números de sección) |
| `doc/agente-rl-y-esperanza-positiva.md` (sección/sugerencia) | `doc/referencia-compacta.md` §3 |
| `doc/estrategia-v3-hacia-el-80.md` (sección) | `doc/referencia-compacta.md` §4 |
| `doc/resultados-v3-2026-10-24.md` | `doc/referencia-compacta.md` §5 |
| `doc/estrategia-extremos.md` | §6 |
| `doc/estrategia-pullback.md` | §7 |
| `doc/plan-analogos.md`, `doc/resultados-analogos.md` | §8 |
| `doc/introduccion-al-trading.md` | §1 |
| `matematica-aplicativa.md`, `modelos-complejos-y-datos.md`, `estrategias-extra-hacia-el-80.md` | Ya estaban sustituidos por `estrategia-v3-hacia-el-80.md` (ahora §4) |

**Actualizado en este commit:** las referencias del código y del README a los archivos anteriores apuntan ya a `referencia-compacta.md`.
