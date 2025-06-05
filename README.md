# Bot de Trading Hyperliquid - Versión Completa v2

Bot de trading automatizado para Hyperliquid con estrategia optimizada para BTC, integración ccxt mejorada y compatibilidad total con todas las versiones del SDK de Hyperliquid.

## 🚀 Características Principales

- **Estrategia Optimizada para BTC**: Análisis técnico especializado con RSI y Bandas de Bollinger
- **Integración ccxt Mejorada**: Operaciones de trading más confiables usando ccxt
- **Compatibilidad Universal**: Funciona con todas las versiones del SDK de Hyperliquid
- **Gestión de Riesgos Avanzada**: Stop Loss, Take Profit y Trailing Stop automáticos
- **Arquitectura Híbrida**: API nativa para datos + ccxt para trading
- **Una Operación Simultánea**: Control estricto de capital según la estrategia

## 🔧 Novedades en Versión v2

### Correcciones de Compatibilidad
- ✅ **Problema skip_ws resuelto**: Compatible con todas las versiones del SDK
- ✅ **Inicialización robusta**: Manejo inteligente de diferentes versiones de API
- ✅ **Detección automática**: Se adapta a la versión del SDK instalada
- ✅ **Fallback inteligente**: Continúa funcionando aunque alguna API falle

### Arquitectura Híbrida Optimizada
- **API Nativa de Hyperliquid**: Para datos de mercado, precios y consultas
- **ccxt**: Para todas las operaciones de trading (más confiable)
- **Mejor de ambos mundos**: Datos precisos + trading robusto

## 📋 Requisitos

- Python 3.8+
- Cuenta en Hyperliquid con fondos
- Clave privada de la wallet
- Conexión a internet estable

## 🛠️ Instalación Rápida

### Opción A: Instalación Automática (Recomendada)

1. **Extraer el proyecto**:
```bash
# Extrae hyperliquid_bot_complete_v2.zip
cd hyperliquid_bot_complete_v2
```

2. **Configurar credenciales**:
```bash
# Edita config/config.json con tus credenciales
nano config/config.json
```

3. **Instalación automática**:
```bash
python setup_fix_v2.py
```

4. **Probar conexión**:
```bash
python test_connection_fixed_v2.py
```

5. **Ejecutar bot**:
```bash
python src/main.py
```

### Opción B: Instalación Manual

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Configurar credenciales** en `config/config.json`:
```json
{
  "auth": {
    "account_address": "TU_DIRECCION_WALLET",
    "secret_key": "TU_CLAVE_PRIVADA"
  }
}
```

3. **Ejecutar diagnóstico** (opcional):
```bash
python diagnose_hyperliquid.py
```

4. **Probar conexión**:
```bash
python test_connection_fixed_v2.py
```

## ⚙️ Configuración

### Archivo Principal (`config/config.json`)

```json
{
    "general": {
        "base_url": "https://api.hyperliquid.xyz",
        "ws_url": "wss://api.hyperliquid.xyz/ws"
    },
    "strategy": {
        "max_capital": 10000,
        "leverage": 5,
        "take_profit": 5.3,
        "stop_loss": 1.25,
        "trailing_stop_activation": 1.5,
        "trailing_stop_distance": 1.5,
        "timeframe": "5m"
    },
    "technical_analysis": {
        "rsi_period": 14,
        "rsi_lower_bound": 15,
        "rsi_upper_bound": 35,
        "rsi_upper_bound_short": 65,
        "rsi_overbought_short": 85,
        "bollinger_period": 20,
        "bollinger_std_dev": 2,
        "bb_width_min": 0.01,
        "bb_width_max": 0.08,
        "detailed_logs": true
    },
    "ccxt": {
        "enable_rate_limit": true,
        "default_slippage": 0.05,
        "default_type": "swap",
        "order_type": "market",
        "timeout": 30000
    },
    "auth": {
        "account_address": "YOUR_ACCOUNT_ADDRESS",
        "secret_key": "YOUR_SECRET_KEY"
    }
}
```

## 🧪 Scripts de Prueba

### Diagnóstico del Sistema
```bash
python diagnose_hyperliquid.py
```
Identifica tu versión del SDK y verifica compatibilidad.

### Prueba de Conexión v2
```bash
python test_connection_fixed_v2.py
```
Verifica que la conexión híbrida funcione correctamente.

### Prueba de ccxt
```bash
python test_ccxt_trader.py
```
Prueba específicamente el módulo de trading con ccxt.

### Prueba de Integración Completa
```bash
python test_integration.py
```
Valida todo el sistema integrado.

## 🚀 Ejecución

### Modo Principal
```bash
python src/main.py
```

### Modo de Prueba
```bash
python test_integration.py
```

## 📊 Estrategia de Trading

### Condiciones de Entrada LONG
- RSI entre 15-35 (sobreventa)
- Precio cerca del límite inferior de las Bandas de Bollinger
- Ancho de Bandas entre 1%-8% (volatilidad adecuada)

### Condiciones de Entrada SHORT
- RSI entre 65-85 (sobrecompra)
- Precio cerca del límite superior de las Bandas de Bollinger
- Ancho de Bandas entre 1%-8% (volatilidad adecuada)

### Gestión de Riesgos
- **Stop Loss**: 1.25% (configurable)
- **Take Profit**: 5.3% (configurable)
- **Trailing Stop**: Activación en 1.5%, distancia 1.5%
- **Leverage**: 5x (configurable)
- **Capital Máximo**: $10,000 por operación

## 📁 Estructura del Proyecto

```
hyperliquid_bot_complete_v2/
├── src/
│   ├── main.py              # Módulo principal
│   ├── config.py            # Gestión de configuración
│   ├── connection.py        # Conexión híbrida v2 (ACTUALIZADO)
│   ├── ccxt_trader.py       # Trading con ccxt
│   ├── orders.py            # Gestión de órdenes con ccxt
│   ├── technical.py         # Análisis técnico
│   ├── risk.py              # Gestión de riesgos
│   ├── utils.py             # Utilidades
│   └── data_provider.py     # Proveedor de datos OHLC
├── config/
│   └── config.json          # Configuración principal
├── logs/                    # Logs del bot
├── data/                    # Datos temporales
├── diagnose_hyperliquid.py  # Diagnóstico del SDK
├── test_connection_fixed_v2.py  # Prueba de conexión v2
├── setup_fix_v2.py         # Instalación automática v2
├── test_ccxt_trader.py     # Prueba de ccxt
├── test_integration.py     # Prueba de integración
├── test_error_handling.py  # Prueba de errores
├── requirements.txt        # Dependencias
├── README.md              # Este archivo
├── MIGRATION_GUIDE.md     # Guía de migración
└── CHANGELOG.md           # Registro de cambios
```

## 🔄 Arquitectura Híbrida v2

### Flujo de Datos
1. **Datos de Mercado** → API nativa de Hyperliquid
2. **Análisis Técnico** → Procesamiento local
3. **Señales de Trading** → Generación de órdenes
4. **Ejecución de Órdenes** → ccxt (más confiable)
5. **Gestión de Riesgos** → Monitoreo continuo

### Ventajas
- ✅ **Datos precisos**: API nativa para información de mercado
- ✅ **Trading robusto**: ccxt para operaciones confiables
- ✅ **Compatibilidad total**: Funciona con cualquier versión del SDK
- ✅ **Fallback inteligente**: Continúa funcionando aunque falle una parte

## 🐛 Solución de Problemas

### Error de Importación
```bash
# Ejecutar diagnóstico
python diagnose_hyperliquid.py

# Reinstalar SDK si es necesario
pip uninstall hyperliquid
pip install hyperliquid-python-sdk
```

### Error de Conexión
```bash
# Probar conexión específica
python test_connection_fixed_v2.py

# Verificar credenciales en config.json
```

### Error de ccxt
```bash
# Probar ccxt específicamente
python test_ccxt_trader.py

# Reinstalar ccxt si es necesario
pip install --upgrade ccxt
```

## ⚠️ Consideraciones Importantes

### Seguridad
- **Nunca compartir** la clave privada
- Usar cantidades pequeñas para pruebas iniciales
- Monitorear las operaciones de cerca

### Recomendaciones
- Empezar con capital pequeño ($100-500)
- Probar en horarios de baja volatilidad
- Revisar logs regularmente
- Ajustar parámetros según resultados

## 📞 Soporte

### Diagnóstico Automático
1. Ejecutar `python diagnose_hyperliquid.py`
2. Ejecutar `python test_connection_fixed_v2.py`
3. Revisar logs en la carpeta `logs/`

### Problemas Comunes
- **Error skip_ws**: Resuelto en v2
- **API no disponible**: Usa arquitectura híbrida
- **Credenciales incorrectas**: Verificar config.json
- **Fondos insuficientes**: Verificar balance en Hyperliquid

## 🎯 Ventajas de la Versión Completa v2

- ✅ **Todo incluido**: Bot completo + correcciones + pruebas
- ✅ **Compatibilidad universal**: Funciona con cualquier versión del SDK
- ✅ **Instalación automática**: Script de configuración incluido
- ✅ **Diagnóstico integrado**: Herramientas de troubleshooting
- ✅ **Documentación completa**: Guías y ejemplos incluidos
- ✅ **Arquitectura robusta**: Híbrida para máxima confiabilidad

---

**⚡ Bot de Trading Hyperliquid - Versión Completa v2 con ccxt y Compatibilidad Universal**

