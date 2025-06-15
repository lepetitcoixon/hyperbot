"""
Módulo principal del bot de trading para Hyperliquid usando CCXT.
Implementa la estrategia optimizada para BTC con gestión de capital y una operación simultánea.
Comportamiento adaptativo: seguimiento de posiciones cuando están abiertas, análisis cuando no.
Versión 4: Detecta y hace seguimiento de TODAS las posiciones (automáticas y manuales).
Versión 4.1: Corrige la visualización de indicadores técnicos.
Versión 4.5: Añade log separado solo para errores.
"""

import logging
import time
import os
import sys
from datetime import datetime
import threading
import json
from typing import Dict, Any, List, Optional

# Configurar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importar módulos del bot
from src.config import Config
from src.ccxt_connection import CCXTHyperliquidConnection
from src.technical import TechnicalAnalysis
from src.ccxt_orders import CCXTOrderManager
from src.risk import RiskManager

# Configurar logging con archivo separado para errores
log_dir = os.path.join(parent_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

# Crear timestamp para los archivos de log
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Configurar el logger raíz
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Limpiar handlers existentes
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Formato de log
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler para log completo (todos los niveles)
complete_log_handler = logging.FileHandler(
    os.path.join(log_dir, f"ccxt_bot_complete_{timestamp}.log")
)
complete_log_handler.setLevel(logging.INFO)
complete_log_handler.setFormatter(log_format)

# Handler para log de errores únicamente (ERROR y CRITICAL)
error_log_handler = logging.FileHandler(
    os.path.join(log_dir, f"ccxt_bot_errors_{timestamp}.log")
)
error_log_handler.setLevel(logging.ERROR)
error_log_handler.setFormatter(log_format)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)

# Añadir handlers al logger raíz
root_logger.addHandler(complete_log_handler)
root_logger.addHandler(error_log_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("ccxt_main")

# Log de inicio con información de archivos
logger.info("=" * 60)
logger.info("🚀 INICIANDO BOT DE TRADING CCXT HYPERLIQUID")
logger.info("=" * 60)
logger.info(f"📁 Log completo: ccxt_bot_complete_{timestamp}.log")
logger.info(f"❌ Log de errores: ccxt_bot_errors_{timestamp}.log")
logger.info("=" * 60)

class CCXTHyperliquidBot:
    """Clase principal del bot de trading para Hyperliquid con CCXT y estrategia optimizada para BTC."""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa el bot de trading con CCXT.
        
        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        # Inicializar configuración
        if config_path is None:
            config_path = os.path.join(parent_dir, "config", "config.json")
        
        self.config = Config(config_path)
        logger.info("Configuración cargada")
        
        # Obtener configuraciones
        self.general_config = self.config.get_general_config()
        self.strategy_config = self.config.get_strategy_config()
        self.ta_config = self.config.get_technical_analysis_config()
        self.auth_config = self.config.get_auth_config()
        
        # Inicializar componentes
        self.technical_analyzer = TechnicalAnalysis(self.ta_config)
        logger.info("Analizador técnico inicializado con estrategia optimizada para BTC")
        
        # Inicializar conexión CCXT
        self.connection = CCXTHyperliquidConnection(
            wallet_address=self.auth_config["account_address"],
            private_key=self.auth_config["secret_key"],
            testnet=self.general_config.get("testnet", False)
        )
        logger.info("Conexión CCXT a Hyperliquid inicializada")
        
        # Inicializar gestor de riesgos
        self.risk_manager = RiskManager(self.config)
        logger.info("Gestor de riesgos inicializado")
        
        # Inicializar gestor de órdenes CCXT
        capital_percentage = self.strategy_config.get("capital_percentage", 100)
        self.order_manager = CCXTOrderManager(
            connection=self.connection,
            technical_analyzer=self.technical_analyzer,
            risk_manager=self.risk_manager,
            capital_percentage=capital_percentage
        )
        logger.info(f"Gestor de órdenes CCXT inicializado con {capital_percentage}% del capital")
        
        # Flags de control
        self.running = False
        self.thread = None
        
        # Configuración de intervalos
        self.position_check_interval = 30  # 30 segundos para seguimiento de posiciones
        self.analysis_interval = 30  # 30 segundos para análisis técnico
        
        logger.info("Bot CCXT inicializado correctamente con estrategia optimizada para BTC")
        logger.info(f"Intervalos configurados: Seguimiento de posiciones={self.position_check_interval}s, Análisis técnico={self.analysis_interval}s")
        logger.info("🔍 NUEVO: Detecta y hace seguimiento de TODAS las posiciones (automáticas y manuales)")
        logger.info("📝 NUEVO: Log separado para errores únicamente")
    
    def get_current_btc_price(self) -> float:
        """
        Obtiene el precio actual de BTC.
        
        Returns:
            Precio actual de BTC o 0 si hay error
        """
        try:
            market_data = self.connection.get_market_data("BTC")
            if market_data:
                return float(market_data.get("midPrice", 0))
            return 0.0
        except Exception as e:
            logger.error(f"Error al obtener precio actual de BTC: {str(e)}")
            return 0.0
    
    def get_real_positions_from_account(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las posiciones reales abiertas en la cuenta usando CCXT.
        
        Returns:
            Lista de posiciones abiertas
        """
        try:
            # Obtener posiciones usando CCXT
            positions = self.connection.exchange.fetch_positions()
            
            # Filtrar solo posiciones abiertas (con tamaño > 0)
            open_positions = []
            for position in positions:
                if position and position.get('contracts', 0) != 0:
                    # Convertir al formato esperado por el bot
                    symbol = position.get('symbol', '')
                    asset = symbol.split('/')[0] if '/' in symbol else symbol
                    
                    # Determinar si es long o short
                    contracts = float(position.get('contracts', 0))
                    is_buy = contracts > 0
                    size = abs(contracts)
                    
                    # Obtener precio de entrada
                    entry_price = float(position.get('entryPrice', 0))
                    
                    # Calcular capital usado (aproximado)
                    capital_used = size * entry_price
                    
                    open_positions.append({
                        'asset': asset,
                        'symbol': symbol,
                        'is_buy': is_buy,
                        'size': size,
                        'entry_price': entry_price,
                        'capital_used': capital_used,
                        'unrealized_pnl': float(position.get('unrealizedPnl', 0)),
                        'percentage': float(position.get('percentage', 0)),
                        'contracts': contracts,
                        'side': position.get('side', 'long' if is_buy else 'short'),
                        'raw_position': position  # Guardar datos originales
                    })
            
            return open_positions
            
        except Exception as e:
            logger.error(f"Error al obtener posiciones reales de la cuenta: {str(e)}")
            return []
    
    def monitor_all_positions(self, asset: str) -> None:
        """
        Monitorea TODAS las posiciones activas (automáticas y manuales) y muestra información detallada de P/L.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
        """
        try:
            # Obtener precio actual de BTC
            current_btc_price = self.get_current_btc_price()
            
            # Verificar posiciones del bot para take profit, stop loss y trailing stop
            self.order_manager.check_positions()
            
            # Obtener TODAS las posiciones reales de la cuenta
            real_positions = self.get_real_positions_from_account()
            
            if real_positions:
                logger.info("=== SEGUIMIENTO DE TODAS LAS POSICIONES ===")
                logger.info(f"💰 Precio actual BTC: ${current_btc_price:.2f}")
                logger.info(f"📊 Total posiciones detectadas: {len(real_positions)}")
                logger.info("-" * 50)
                
                for i, position in enumerate(real_positions, 1):
                    asset_name = position["asset"]
                    is_buy = position["is_buy"]
                    size = position["size"]
                    entry_price = position["entry_price"]
                    capital_used = position["capital_used"]
                    unrealized_pnl = position["unrealized_pnl"]
                    pnl_percentage = position["percentage"]
                    
                    # Usar el precio actual ya obtenido para BTC
                    if asset_name == "BTC":
                        current_price = current_btc_price
                    else:
                        # Para otros activos, obtener precio específico
                        market_data = self.connection.get_market_data(asset_name)
                        current_price = float(market_data.get("midPrice", 0)) if market_data else 0
                    
                    if current_price <= 0:
                        logger.warning(f"Precio actual no válido para {asset_name}")
                        continue
                    
                    # Calcular cambio de precio desde entrada
                    price_change = current_price - entry_price
                    price_change_pct = ((current_price / entry_price) - 1) * 100
                    
                    # Determinar el estado de la posición
                    pnl_status = "GANANCIA" if unrealized_pnl >= 0 else "PÉRDIDA"
                    price_direction = "📈" if price_change >= 0 else "📉"
                    position_type = "🤖 BOT" if any(pos["asset"] == asset_name for pos in self.order_manager.active_positions.values()) else "👤 MANUAL"
                    
                    logger.info(f"Posición #{i}: {asset_name} {'LONG' if is_buy else 'SHORT'} {position_type}")
                    logger.info(f"  Tamaño: {size} {asset_name}")
                    logger.info(f"  Precio entrada: ${entry_price:.2f}")
                    logger.info(f"  Precio actual: ${current_price:.2f} {price_direction} ${price_change:+.2f} ({price_change_pct:+.2f}%)")
                    logger.info(f"  Capital usado: ${capital_used:.2f}")
                    logger.info(f"  P/L: ${unrealized_pnl:.2f} ({pnl_percentage:+.2f}%) - {pnl_status}")
                    
                    # Mostrar información adicional para posiciones del bot
                    bot_position = None
                    for pos_key, pos_data in self.order_manager.active_positions.items():
                        if pos_data["asset"] == asset_name:
                            bot_position = pos_data
                            break
                    
                    if bot_position:
                        # Calcular tiempo transcurrido
                        entry_time = bot_position["entry_time"]
                        time_elapsed = datetime.now() - entry_time
                        hours, remainder = divmod(time_elapsed.total_seconds(), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                        
                        # Obtener niveles de riesgo
                        risk_levels = bot_position.get("risk_levels", {})
                        stop_loss = risk_levels.get("stop_loss", {}).get("stop_level", "N/A")
                        take_profit = risk_levels.get("take_profit", {}).get("take_profit_level", "N/A")
                        trailing_activation = risk_levels.get("trailing_stop", {}).get("activation_level", "N/A")
                        
                        logger.info(f"  Tiempo abierta: {time_str}")
                        logger.info(f"  Stop Loss: ${stop_loss}")
                        logger.info(f"  Take Profit: ${take_profit}")
                        logger.info(f"  Trailing Stop: ${trailing_activation}")
                    else:
                        logger.info(f"  ⚠️ Posición manual - Sin gestión automática de riesgo")
                    
                    logger.info("-" * 50)
                
                # Mostrar resumen de cuenta
                account_summary = self.order_manager.get_account_summary()
                logger.info(f"Capital total: ${account_summary['total_capital']:.2f} | "
                           f"Disponible: ${account_summary['available_capital']:.2f} | "
                           f"Reservado: ${account_summary['reserved_capital']:.2f}")
                logger.info("=" * 50)
            else:
                logger.info("📊 No hay posiciones abiertas en la cuenta")
            
        except Exception as e:
            logger.error(f"Error al monitorear todas las posiciones: {str(e)}", exc_info=True)
    
    def get_indicator_status(self, analysis: Dict[str, Any]) -> str:
        """
        Obtiene el estado de los indicadores técnicos con iconos.
        CORREGIDO: Ahora lee correctamente la estructura del análisis técnico.
        
        Args:
            analysis: Resultado del análisis técnico
            
        Returns:
            String con el estado de los indicadores
        """
        try:
            # Los datos están directamente en el nivel superior del análisis
            rsi_value = analysis.get("rsi", 0)
            bb_width = analysis.get("bb_width", 0)
            last_price = analysis.get("last_price", 0)
            bollinger_upper = analysis.get("bollinger_upper", 0)
            bollinger_lower = analysis.get("bollinger_lower", 0)
            bollinger_ma = analysis.get("bollinger_ma", 0)
            
            # Obtener configuración de parámetros del analizador técnico
            rsi_lower_bound = self.ta_config.get("rsi_lower_bound", 15)
            rsi_upper_bound = self.ta_config.get("rsi_upper_bound", 35)
            rsi_upper_bound_short = self.ta_config.get("rsi_upper_bound_short", 65)
            rsi_overbought_short = self.ta_config.get("rsi_overbought_short", 85)
            bb_width_min = self.ta_config.get("bb_width_min", 0.01)
            bb_width_max = self.ta_config.get("bb_width_max", 0.08)
            
            # RSI - Verificar si está en rango para LONG o SHORT
            if (rsi_lower_bound <= rsi_value <= rsi_upper_bound) or (rsi_upper_bound_short <= rsi_value <= rsi_overbought_short):
                rsi_status = f"✅ RSI({rsi_value:.1f})"
            else:
                rsi_status = f"❌ RSI({rsi_value:.1f})"
            
            # Bandas de Bollinger - Verificar posición del precio
            bb_position = "middle"
            bb_signal_active = False
            
            if last_price >= bollinger_upper:
                bb_position = "upper"
                bb_signal_active = True
            elif last_price <= bollinger_lower:
                bb_position = "lower"
                bb_signal_active = True
            else:
                # Calcular distancia relativa a las bandas
                if bollinger_upper > bollinger_lower:
                    distance_to_upper = abs(last_price - bollinger_upper) / (bollinger_upper - bollinger_lower)
                    distance_to_lower = abs(last_price - bollinger_lower) / (bollinger_upper - bollinger_lower)
                    
                    if distance_to_upper < 0.1:  # Muy cerca de banda superior
                        bb_position = "near_upper"
                        bb_signal_active = True
                    elif distance_to_lower < 0.1:  # Muy cerca de banda inferior
                        bb_position = "near_lower"
                        bb_signal_active = True
            
            if bb_signal_active:
                bb_status = f"✅ BB({bb_position})"
            else:
                bb_status = f"❌ BB({bb_position})"
            
            # BB Width - Verificar si está en rango válido
            if bb_width_min <= bb_width <= bb_width_max:
                bb_width_status = f"✅ BBW({bb_width:.3f})"
            else:
                bb_width_status = f"❌ BBW({bb_width:.3f})"
            
            return f"{rsi_status} | {bb_status} | {bb_width_status}"
            
        except Exception as e:
            logger.error(f"Error al obtener estado de indicadores: {str(e)}")
            return "❌ RSI(N/A) | ❌ BB(N/A) | ❌ BBW(N/A)"
    
    def search_for_signals(self, asset: str) -> None:
        """
        Busca señales de trading cuando no hay posiciones activas.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
        """
        try:
            # Obtener precio actual de BTC
            current_btc_price = self.get_current_btc_price()
            
            logger.info("=== BÚSQUEDA DE SEÑALES DE TRADING ===")
            logger.info(f"💰 Precio actual BTC: ${current_btc_price:.2f}")
            
            # Analizar mercado
            logger.info(f"Analizando {asset} para señales de entrada...")
            analysis = self.order_manager.analyze_market(asset)
            
            # Obtener estado de indicadores
            indicators_status = self.get_indicator_status(analysis)
            logger.info(f"Indicadores: {indicators_status}")
            
            # Verificar si hay señal
            signal = analysis.get("signals", {}).get("overall")
            if signal in ["buy", "sell"]:
                logger.info(f"🎯 SEÑAL DETECTADA para {asset}: {signal.upper()}")
                logger.info(f"Razón: {analysis.get('signals', {}).get('reason', 'No especificada')}")
                
                # Ejecutar señal
                result = self.order_manager.execute_signal(
                    asset=asset,
                    signal=signal
                )
                
                if result.get("status") == "ok":
                    logger.info(f"✅ ORDEN EJECUTADA EXITOSAMENTE:")
                    logger.info(f"  Asset: {result.get('asset')}")
                    logger.info(f"  Tipo: {'LONG' if result.get('is_buy') else 'SHORT'}")
                    logger.info(f"  Tamaño: {result.get('size')}")
                    logger.info(f"  Precio: ${result.get('price'):.2f}")
                    logger.info(f"  Capital usado: ${result.get('capital_used'):.2f}")
                    logger.info("🔄 Cambiando a modo seguimiento de posición...")
                elif result.get("status") == "skipped":
                    logger.info(f"⏭️ Orden omitida: {result.get('message')}")
                else:
                    logger.error(f"❌ Error al ejecutar señal: {result}")
            else:
                logger.info(f"📊 No hay señal clara para {asset}. Continuando análisis...")
                if analysis.get("signals", {}).get("reason"):
                    logger.info(f"Condiciones actuales: {analysis.get('signals', {}).get('reason')}")
            
            # Mostrar resumen de cuenta
            account_summary = self.order_manager.get_account_summary()
            logger.info(f"Capital disponible para trading: ${account_summary['available_capital']:.2f}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Error al buscar señales: {str(e)}", exc_info=True)
    
    def run_trading_loop(self):
        """Ejecuta el bucle principal de trading con comportamiento adaptativo."""
        logger.info("🚀 Iniciando bucle de trading adaptativo con CCXT")
        logger.info("📋 Comportamiento:")
        logger.info(f"  • Con posiciones abiertas: Seguimiento cada {self.position_check_interval} segundos")
        logger.info(f"  • Sin posiciones: Análisis técnico cada {self.analysis_interval} segundos")
        logger.info("🔍 NUEVO: Detecta posiciones automáticas Y manuales")
        logger.info("🔧 CORREGIDO: Visualización correcta de indicadores técnicos")
        logger.info("📝 NUEVO: Log separado para errores únicamente")
        
        # Configurar el par de trading (BTC)
        asset = "BTC"
        
        while self.running:
            try:
                # Obtener TODAS las posiciones reales de la cuenta (no solo las del bot)
                real_positions = self.get_real_positions_from_account()
                has_active_positions = len(real_positions) > 0
                
                if has_active_positions:
                    # MODO: SEGUIMIENTO DE POSICIONES (TODAS)
                    logger.info(f"🔍 MODO: Seguimiento de todas las posiciones ({len(real_positions)} posición(es))")
                    self.monitor_all_positions(asset)
                    
                    # Esperar intervalo de seguimiento de posiciones (30 segundos)
                    time.sleep(self.position_check_interval)
                    
                else:
                    # MODO: BÚSQUEDA DE SEÑALES
                    logger.info("🔎 MODO: Búsqueda de señales de trading")
                    self.search_for_signals(asset)
                    
                    # Esperar intervalo de análisis técnico (30 segundos)
                    time.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"❌ Error en bucle de trading: {str(e)}", exc_info=True)
                time.sleep(30)  # Esperar antes de reintentar
    
    def start(self):
        """Inicia la ejecución del bot."""
        if self.running:
            logger.warning("⚠️ El bot ya está en ejecución")
            return
        
        logger.info("🎬 Iniciando bot de trading CCXT con estrategia optimizada para BTC")
        logger.info("🔍 Detectará y hará seguimiento de TODAS las posiciones (automáticas y manuales)")
        logger.info("📝 Log de errores guardado por separado para debugging")
        
        # Marcar como en ejecución
        self.running = True
        
        # Crear e iniciar hilo principal
        self.thread = threading.Thread(
            target=self.run_trading_loop,
            name="TradingLoop"
        )
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("✅ Bot CCXT iniciado correctamente")
    
    def stop(self):
        """Detiene la ejecución del bot."""
        if not self.running:
            logger.warning("⚠️ El bot no está en ejecución")
            return
        
        logger.info("🛑 Deteniendo bot de trading CCXT")
        
        # Marcar como detenido
        self.running = False
        
        # Esperar a que el hilo termine
        if self.thread:
            self.thread.join(timeout=5.0)
            logger.info("🔌 Hilo de trading detenido")
        
        self.thread = None
        logger.info("✅ Bot CCXT detenido correctamente")
    
    def set_capital_percentage(self, percentage: int):
        """
        Configura el porcentaje de capital a utilizar.
        
        Args:
            percentage: Porcentaje de capital a utilizar (1-100)
        """
        result = self.order_manager.set_capital_percentage(percentage)
        if result.get("status") == "ok":
            logger.info(f"💰 Porcentaje de capital configurado: {percentage}%")
        else:
            logger.error(f"❌ Error al configurar porcentaje de capital: {result.get('message')}")
    
    def set_position_check_interval(self, seconds: int):
        """
        Configura el intervalo de verificación de posiciones.
        
        Args:
            seconds: Intervalo en segundos (mínimo 10)
        """
        if seconds < 10:
            logger.warning("⚠️ El intervalo mínimo es 10 segundos")
            seconds = 10
        
        self.position_check_interval = seconds
        logger.info(f"⏱️ Intervalo de seguimiento de posiciones configurado: {seconds} segundos")
    
    def set_analysis_interval(self, seconds: int):
        """
        Configura el intervalo de análisis técnico.
        
        Args:
            seconds: Intervalo en segundos (mínimo 10)
        """
        if seconds < 10:
            logger.warning("⚠️ El intervalo mínimo es 10 segundos")
            seconds = 10
        
        self.analysis_interval = seconds
        logger.info(f"⏱️ Intervalo de análisis técnico configurado: {seconds} segundos")

# def main():
#     """Función principal para ejecutar el bot."""
#     try:
#         # Crear e iniciar el bot
#         bot = CCXTHyperliquidBot()
#         bot.start()
        
#         # Mantener el programa en ejecución
#         try:
#             while True:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             logger.info("⌨️ Interrupción de teclado detectada")
#         finally:
#             bot.stop()
    
#     except Exception as e:
#         logger.error(f"❌ Error al iniciar el bot: {str(e)}", exc_info=True)

# if __name__ == "__main__":
#     main()

