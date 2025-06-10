# Bot Adaptativo - Seguimiento de Posiciones y Búsqueda de Señales

## Cambios Implementados

He modificado el comportamiento del bot para que sea completamente adaptativo según el estado de las posiciones:

### 🔄 **Comportamiento Adaptativo**

#### **Con Posiciones Abiertas:**
- ✅ **No busca nuevas señales** (evita sobreoperación)
- ✅ **Seguimiento cada 30 segundos** de las posiciones activas
- ✅ **Gestión automática de TP, SL y Trailing Stop**
- ✅ **Información detallada de P/L en $ y %**
- ✅ **Tiempo transcurrido desde la apertura**
- ✅ **Niveles de riesgo configurados**

#### **Sin Posiciones Abiertas:**
- ✅ **Análisis técnico normal cada 60 segundos**
- ✅ **Búsqueda activa de señales de entrada**
- ✅ **Información del capital disponible**

### 📊 **Información Mostrada en Logs**

#### **Modo Seguimiento de Posiciones:**
```
=== SEGUIMIENTO DE POSICIONES ACTIVAS ===
Posición: BTC LONG
  Tamaño: 0.001 BTC
  Precio entrada: $95,234.50
  Precio actual: $96,150.25
  Capital usado: $95.23
  Tiempo abierta: 00:15:30
  P/L: $0.92 (+4.81%) - GANANCIA
  Stop Loss: $94,280.12
  Take Profit: $97,500.00
  Trailing Stop: $96,000.00
==================================================
Capital total: $222.09 | Disponible: $126.86 | Reservado: $95.23
```

#### **Modo Búsqueda de Señales:**
```
=== BÚSQUEDA DE SEÑALES DE TRADING ===
Analizando BTC para señales de entrada...
🎯 SEÑAL DETECTADA para BTC: BUY
Razón: RSI oversold + MACD bullish crossover
✅ ORDEN EJECUTADA EXITOSAMENTE:
  Asset: BTC
  Tipo: LONG
  Tamaño: 0.001
  Precio: $95,234.50
  Capital usado: $95.23
🔄 Cambiando a modo seguimiento de posición...
```

### ⚙️ **Configuración de Intervalos**

- **Seguimiento de posiciones**: 30 segundos (configurable)
- **Análisis técnico**: 60 segundos (configurable)
- **Mínimo permitido**: 10 segundos para posiciones, 30 segundos para análisis

### 🎯 **Ventajas del Nuevo Comportamiento**

1. **Eficiencia Mejorada**: No desperdicia recursos analizando cuando hay posiciones abiertas
2. **Seguimiento Detallado**: Información completa del rendimiento de las posiciones
3. **Gestión de Riesgo Activa**: Monitoreo constante de TP, SL y Trailing Stop
4. **Información Clara**: Logs organizados y fáciles de interpretar
5. **Flexibilidad**: Intervalos configurables según necesidades

### 📁 **Archivos Modificados**

- `ccxt_main_adaptive.py` - Nueva versión del bot con comportamiento adaptativo
- Mantiene compatibilidad total con todos los demás módulos

### 🚀 **Cómo Usar**

1. **Reemplazar el archivo principal**:
   ```bash
   cp src/ccxt_main_adaptive.py src/ccxt_main.py
   ```

2. **Ejecutar el bot**:
   ```bash
   python src/ccxt_main.py
   ```

3. **Configurar intervalos** (opcional):
   ```python
   bot.set_position_check_interval(30)  # 30 segundos
   bot.set_analysis_interval(60)        # 60 segundos
   ```

### 📈 **Flujo de Operación**

```
Inicio del Bot
     ↓
¿Hay posiciones abiertas?
     ↓                    ↓
   SÍ                    NO
     ↓                    ↓
Modo Seguimiento    Modo Análisis
(cada 30s)          (cada 60s)
     ↓                    ↓
• Mostrar P/L        • Buscar señales
• Gestionar TP/SL    • Ejecutar órdenes
• Trailing Stop      • Mostrar capital
     ↓                    ↓
Esperar 30s         Esperar 60s
     ↓                    ↓
     ←←←←←←←←←←←←←←←←←←←←←←
```

### 🔧 **Funciones Adicionales**

- `set_position_check_interval(seconds)` - Configura intervalo de seguimiento
- `set_analysis_interval(seconds)` - Configura intervalo de análisis
- `set_capital_percentage(percentage)` - Configura % de capital a usar

El bot ahora es mucho más inteligente y eficiente, proporcionando información detallada cuando es necesaria y optimizando recursos cuando no hay posiciones activas.

