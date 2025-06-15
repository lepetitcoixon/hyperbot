"""
Módulo principal del bot de trading para Hyperliquid.
Implementa la estrategia optimizada para BTC con gestión de capital y una operación simultánea.
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
from src.connection import HyperliquidConnection
from src.technical import TechnicalAnalysis
from src.orders import OrderManager
from src.risk import RiskManager

# Configurar logging
log_dir = os.path.join(parent_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("main")

class HyperliquidBot:
    """Clase principal del bot de trading para Hyperliquid con estrategia optimizada para BTC."""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa el bot de trading.
        
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
        
        # Inicializar conexión
        self.connection = HyperliquidConnection(
            account_address=self.auth_config["account_address"],
            secret_key=self.auth_config["secret_key"],
            base_url=self.general_config["base_url"],
            skip_ws=True
        )
        logger.info("Conexión a Hyperliquid inicializada")
        
        # Inicializar gestor de riesgos
        self.risk_manager = RiskManager(self.config)
        logger.info("Gestor de riesgos inicializado")
        
        # Inicializar gestor de órdenes
        self.order_manager = OrderManager(
            connection=self.connection,
            technical_analyzer=self.technical_analyzer,
            risk_manager=self.risk_manager
        )
        logger.info("Gestor de órdenes inicializado")
        
        # Flags de control
        self.running = False
        self.thread = None
        
        logger.info("Bot inicializado correctamente con estrategia optimizada para BTC")
    
    def run_trading_loop(self):
        """Ejecuta el bucle principal de trading."""
        logger.info("Iniciando bucle de trading")
        
        # Configurar el par de trading (BTC)
        asset = "BTC"
        
        while self.running:
            try:
                # Analizar mercado
                logger.info(f"Analizando {asset}")
                analysis = self.order_manager.analyze_market(asset)
                
                # Verificar si hay señal
                signal = analysis.get("signals", {}).get("overall")
                if signal in ["buy", "sell"]:
                    logger.info(f"Señal detectada para {asset}: {signal}")
                    
                    # Ejecutar señal
                    result = self.order_manager.execute_signal(
                        asset=asset,
                        signal=signal
                    )
                    
                    if result.get("status") == "ok":
                        logger.info(f"Orden ejecutada: {result}")
                    elif result.get("status") == "skipped":
                        logger.info(f"Orden omitida: {result.get('message')}")
                    else:
                        logger.error(f"Error al ejecutar señal: {result}")
                else:
                    logger.info(f"No hay señal clara para {asset}")
                
                # Verificar posiciones abiertas para take profit y stop loss
                self.order_manager.check_positions()
                
                # Obtener resumen de la cuenta
                account_summary = self.order_manager.get_account_summary()
                logger.info(f"Resumen de cuenta: Capital total=${account_summary['total_capital']:.2f}, "
                           f"Disponible=${account_summary['available_capital']:.2f}, "
                           f"Excedente=${account_summary['excess_capital']:.2f}, "
                           f"Posiciones activas={account_summary['active_positions']}")
                
                # Esperar antes de la siguiente iteración (timeframe de 5 minutos)
                time.sleep(60)  # Verificar cada minuto
                
            except Exception as e:
                logger.error(f"Error en bucle de trading: {str(e)}", exc_info=True)
                time.sleep(60)  # Esperar antes de reintentar
    
    def start(self):
        """Inicia la ejecución del bot."""
        if self.running:
            logger.warning("El bot ya está en ejecución")
            return
        
        logger.info("Iniciando bot de trading con estrategia optimizada para BTC")
        
        # Marcar como en ejecución
        self.running = True
        
        # Crear e iniciar hilo principal
        self.thread = threading.Thread(
            target=self.run_trading_loop,
            name="TradingLoop"
        )
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Bot iniciado correctamente")
    
    def stop(self):
        """Detiene la ejecución del bot."""
        if not self.running:
            logger.warning("El bot no está en ejecución")
            return
        
        logger.info("Deteniendo bot de trading")
        
        # Marcar como detenido
        self.running = False
        
        # Esperar a que el hilo termine
        if self.thread:
            self.thread.join(timeout=5.0)
            logger.info("Hilo de trading detenido")
        
        self.thread = None
        logger.info("Bot detenido correctamente")

def main():
    """Función principal para ejecutar el bot."""
    try:
        # Crear e iniciar el bot
        bot = HyperliquidBot()
        bot.start()
        
        # Mantener el programa en ejecución
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupción de teclado detectada")
        finally:
            bot.stop()
    
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
