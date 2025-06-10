# Bot de Trading para Hyperliquid con CCXT

Este documento explica cómo utilizar la versión del bot de trading que implementa operaciones de compra y venta utilizando la biblioteca CCXT para Hyperliquid.

## Cambios Implementados

Se han realizado los siguientes cambios en el bot:

1. **Nueva Conexión con CCXT**: Se ha creado un nuevo módulo `ccxt_connection.py` que implementa la conexión con Hyperliquid utilizando la biblioteca CCXT.

2. **Nuevo Gestor de Órdenes**: Se ha creado un nuevo módulo `ccxt_orders.py` que implementa la gestión de órdenes utilizando CCXT.

3. **Nuevo Punto de Entrada**: Se ha creado un nuevo archivo `ccxt_main.py` que utiliza los nuevos módulos de CCXT.

4. **Configuración Actualizada**: Se ha actualizado el archivo `config.json` para incluir opciones específicas de CCXT.

5. **Nuevas Funcionalidades**:
   - Configuración del porcentaje de capital a utilizar
   - Pausa del análisis técnico mientras hay posiciones abiertas
   - Implementación de trailing stop

## Requisitos

Para utilizar el bot con CCXT, necesitas instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

El archivo `config.json` incluye nuevas opciones:

```json
{
    "general": {
        "base_url": "https://api.hyperliquid.xyz",
        "ws_url": "wss://api.hyperliquid.xyz/ws",
        "testnet": false,
        "use_ccxt": true
    },
    "strategy": {
        "max_capital": 10000,
        "leverage": 5,
        "take_profit": 5.3,
        "stop_loss": 1.25,
        "trailing_stop_activation": 1.5,
        "trailing_stop_distance": 1.5,
        "timeframe": "5m",
        "capital_percentage": 100
    },
    "auth": {
        "account_address": "TU_DIRECCION_WALLET",
        "secret_key": "TU_CLAVE_PRIVADA"
    }
}
```

- `testnet`: Si se debe usar testnet en lugar de mainnet
- `use_ccxt`: Si se debe usar CCXT en lugar de la API REST directa
- `capital_percentage`: Porcentaje del capital disponible a utilizar (1-100)

## Uso

Para ejecutar el bot con CCXT:

```bash
python src/ccxt_main.py
```

## Funcionalidades Implementadas

### 1. Apertura y Cierre de Órdenes

El bot ahora utiliza CCXT para abrir y cerrar órdenes, lo que debería resolver los problemas anteriores con la API REST directa.

```python
# Ejemplo de apertura de orden
order_result = self.connection.place_market_order(
    asset=asset,
    is_buy=is_buy,
    sz=position_size
)

# Ejemplo de cierre de posición
close_result = self.connection.place_market_order(
    asset=asset,
    is_buy=close_is_buy,
    sz=size
)
```

### 2. Pausa del Análisis Técnico

El bot ahora puede pausar el análisis técnico mientras hay posiciones abiertas, lo que permite monitorear la posición sin abrir nuevas:

```python
# Pausar análisis
bot.pause_analysis()

# Reanudar análisis
bot.resume_analysis()
```

### 3. Trailing Stop

El trailing stop está implementado en el módulo de riesgo y se verifica en cada iteración del bucle de trading:

```python
# Verificar niveles de riesgo (stop loss, take profit, trailing stop)
should_close, reason = self.risk_manager.check_risk_levels(
    asset=asset,
    is_buy=is_buy,
    size=size,
    entry_price=entry_price,
    current_price=current_price
)
```

### 4. Configuración del Porcentaje de Capital

El bot ahora permite configurar el porcentaje del capital disponible a utilizar:

```python
# Configurar porcentaje de capital
bot.set_capital_percentage(50)  # Usar el 50% del capital disponible
```

## Solución de Problemas

Si encuentras problemas con el bot, verifica los siguientes puntos:

1. **Conexión a Hyperliquid**: Asegúrate de que las credenciales (dirección de wallet y clave privada) sean correctas.

2. **Fondos Suficientes**: Verifica que tengas fondos suficientes en tu cuenta de Hyperliquid.

3. **Logs**: Revisa los archivos de log en la carpeta `logs` para obtener más información sobre posibles errores.

4. **Versión de CCXT**: Asegúrate de tener instalada la versión más reciente de CCXT.

## Notas Adicionales

- El bot utiliza órdenes de mercado para asegurar la ejecución rápida de las operaciones.
- El trailing stop se activa cuando el precio alcanza el nivel de activación configurado.
- El porcentaje de capital se aplica al capital disponible después de restar el capital reservado para operaciones activas.

## Próximas Mejoras

- Implementación de más estrategias de trading
- Soporte para más pares de trading
- Interfaz web para monitoreo y control
- Notificaciones por correo electrónico o Telegram

