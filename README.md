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

1. Actualiza los valores de `account_address` y `secret_key` en `config/config.json` (la ruta ha cambiado).
2. Ejecuta el bot con el comando: `python src/main.py` (Ten en cuenta que `main.py` ahora podría estar refactorizado o ser el punto de entrada para `ccxt_main.py` si se mantiene la ejecución CLI directa).
3. El bot (si se ejecuta directamente) analizará el mercado de BTC y ejecutará operaciones según las condiciones de la estrategia.
4. Los logs se guardarán en la carpeta `logs` para seguimiento.

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
    python src/api_server.py
    ```
    (Nota: Este script inicia un servidor Uvicorn. Alternativamente, puedes ejecutar `uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload` desde el directorio raíz).
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

**Nota:** La interfaz web es ahora la forma recomendada para gestionar el bot, ya que `src/main.py` o `src/ccxt_main.py` han sido refactorizados para ser controlados por el servidor API.

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
