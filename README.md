# Estrategia de Trading BTC Optimizada - Documentación

## Descripción General

Este documento describe la implementación de la estrategia optimizada para trading de BTC en Hyperliquid. La estrategia se basa en indicadores técnicos específicos (RSI y Bandas de Bollinger) con reglas claras para entradas y salidas, y una gestión de capital conservadora.

## Parámetros Principales

- **Capital máximo operativo:** $10,000 USD (excedente guardado como ganancias)
- **Apalancamiento:** 5x (fijo)
- **Asignación de capital:** 100% del capital disponible (hasta el máximo de $10,000)
- **Take Profit:** 5.5% (basado en precio)
- **Stop Loss:** 1.25% (basado en precio)
- **Timeframe:** Velas de 5 minutos

## Condiciones de Entrada

### LONG (Compra)
- RSI entre 30-35
- Precio toca o cruza la banda inferior de Bollinger
- Filtro de volatilidad: BB Width entre 0.01-0.08

### SHORT (Venta)
- RSI entre 65-70
- Precio toca o cruza la banda superior de Bollinger
- Filtro de volatilidad: BB Width entre 0.01-0.08

## Cálculo de Indicadores

- **RSI:** Período de 14
- **Bandas de Bollinger:** SMA 20 períodos, 2 desviaciones estándar
- **BB Width:** (Banda Superior - Banda Inferior) / Media

## Reglas de Gestión

- Máximo 1 operación simultánea
- Si el capital supera los $10,000, operar solo con $10,000 y guardar el excedente
- Cierre automático de posiciones al alcanzar Take Profit o Stop Loss

## Archivos Modificados

1. **technical.py**: Implementa los indicadores técnicos y la lógica de señales
2. **orders.py**: Gestiona las órdenes, posiciones y capital
3. **main.py**: Coordina la ejecución del bot y el bucle de trading
4. **config.json**: Configuración de parámetros de la estrategia

## Uso del Bot

1. Actualiza los valores de `account_address` y `secret_key` en `config.json`
2. Ejecuta el bot con el comando: `python src/main.py`
3. El bot analizará el mercado de BTC cada minuto y ejecutará operaciones según las condiciones de la estrategia
4. Los logs se guardarán en la carpeta `logs` para seguimiento

## Monitoreo

El bot proporciona información detallada en los logs sobre:
- Análisis de mercado y señales generadas
- Órdenes ejecutadas con detalles de precio y tamaño
- Posiciones cerradas con PnL y razón de cierre
- Resumen de cuenta con capital total, disponible y excedente

## Consideraciones Importantes

- La estrategia está optimizada para operar exclusivamente en BTC
- El bot gestiona automáticamente el capital, asegurando que no se supere el máximo operativo
- Las ganancias que excedan el capital máximo se guardan como excedente
- Solo se permite una operación activa a la vez
