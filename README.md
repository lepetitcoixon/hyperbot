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

1. **technical.py**: Implementa los indicadores técnicos y la lógica de señales.
2. **orders.py**: Gestiona las órdenes, posiciones y capital.
3. **config.json**: Configuración de parámetros de la estrategia.
4. **api_server.py**: Provee una API FastAPI para controlar el bot y exponer datos.
5. **ccxt_main.py**: Contiene la clase principal del bot y su lógica, ahora controlada por `api_server.py`.
6. **Archivos de Interfaz de Usuario (en `src/` y `src/components/`):** Implementan el dashboard de gestión web.

## Ejecución de la Interfaz Web de Gestión

La interfaz web proporciona una forma interactiva de iniciar, detener, monitorear el bot y gestionar su configuración.

### Prerrequisitos

*   **Backend (Python):**
    *   Python 3.8 o superior.
    *   Pip (manejador de paquetes de Python).
    *   Instalar dependencias: `pip install -r requirements.txt` en el directorio raíz del proyecto.
*   **Frontend (Node.js):**
    *   Node.js (se recomienda la última versión LTS).
    *   npm (viene con Node.js) o Yarn.
    *   Instalar dependencias: `npm install` (o `yarn install`) en el directorio raíz del proyecto (donde se encuentra `package.json`).

### 1. Ejecutar el Servidor API del Backend

El servidor API maneja la lógica del bot y la comunicación con el exchange.

*   **Comando:**
    ```bash
    # Desde el directorio raíz del proyecto:
    python src/api_server.py
    ```
    (Nota: Este script ejecuta directamente el servidor API Uvicorn. Gracias a las modificaciones internas en el script (`sys.path` y el bloque `if __name__ == "__main__":`), ahora es la forma recomendada y más simple de iniciar el backend).
*   **URL por defecto:** El servidor API estará disponible en `http://localhost:8000`.

### 2. Ejecutar la Aplicación Frontend (React)

La interfaz de usuario se ejecuta como una aplicación React separada.

*   **Comando:**
    ```bash
    npm run dev
    ```
    o si usas Yarn:
    ```bash
    yarn dev
    ```
    (Estos comandos se ejecutan desde el directorio raíz del proyecto).
*   **URL por defecto:** La interfaz web estará accesible en `http://localhost:5173` (o el puerto que Vite indique si el 5173 está ocupado).

### 3. Acceder a la Aplicación

Una vez que ambos servidores (backend y frontend) estén en ejecución:
1.  Abre tu navegador web.
2.  Dirígete a la URL del frontend: `http://localhost:5173`.
3.  Desde aquí podrás interactuar con el bot.

**Nota:** La interfaz web es ahora la forma recomendada para gestionar el bot, ya que la lógica del bot (originalmente en `src/ccxt_main.py`) ha sido refactorizada para ser controlada por el servidor API.

## Monitoreo

El bot, cuando es gestionado a través de la interfaz web, proporciona información detallada en:
- La sección "Logs" de la interfaz web.
- Los archivos de log en la carpeta `logs/`.
- El panel ("Dashboard") con resúmenes de cuenta y posiciones.

La información incluye:
- Análisis de mercado y señales generadas (en logs detallados).
- Órdenes ejecutadas con detalles de precio y tamaño.
- Posiciones cerradas con PnL y razón de cierre.
- Resumen de cuenta con capital total, disponible y reservado.

## Consideraciones Importantes

- La estrategia está optimizada para operar exclusivamente en BTC (configurable a través de la interfaz, aunque la lógica principal del bot está diseñada para BTC).
- El bot gestiona automáticamente el capital según la configuración.
- Las ganancias y el manejo del capital se reflejan en el balance de la cuenta.
- El número de operaciones simultáneas es configurable (por defecto 1, según la estrategia original).
- **Gestión centralizada:** Se recomienda usar la interfaz web para iniciar/detener el bot y modificar la configuración para evitar conflictos si se intentara ejecutar también la versión CLI de forma independiente.
