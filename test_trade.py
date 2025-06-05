"""
Script de prueba para abrir y cerrar una operación en Hyperliquid.
Este script abre una posición de prueba de 20 USDC y la cierra automáticamente después de un tiempo definido.
"""

import os
import sys
import time
import json
import logging
import argparse
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("test_trade")

# Añadir directorio padre al path para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importar módulos del bot
from src.connection import HyperliquidConnection
from src.config import Config

class TestTrader:
    """Clase para probar operaciones en Hyperliquid."""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa el trader de prueba.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        logger.info("Inicializando trader de prueba")
        
        # Buscar el archivo config.json en varias ubicaciones posibles
        if config_path is None:
            possible_paths = [
                # Ruta relativa al script actual
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.json"),
                # Ruta relativa al directorio padre
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json"),
                # Directorio actual
                os.path.join(os.getcwd(), "config", "config.json"),
                # Directorio actual + hyperliquid_bot
                os.path.join(os.getcwd(), "hyperliquid_bot", "config", "config.json"),
                # Directorio actual + hyperliquid_bot_final
                os.path.join(os.getcwd(), "hyperliquid_bot_final", "config", "config.json"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    logger.info(f"Usando archivo de configuración: {config_path}")
                    break
            
            if config_path is None:
                logger.error("No se pudo encontrar el archivo config.json")
                logger.error("Por favor, asegúrese de que el archivo config.json existe en alguna de estas ubicaciones:")
                for path in possible_paths:
                    logger.error(f"  - {path}")
                raise FileNotFoundError("No se pudo encontrar el archivo config.json")
        
        # Cargar configuración
        self.config = self._load_config(config_path)
        logger.info("Configuración cargada")
        
        # Inicializar conexión
        self.connection = HyperliquidConnection(
            account_address=self.config["auth"]["account_address"],
            secret_key=self.config["auth"]["secret_key"],
            base_url=self.config["general"]["base_url"]
        )
        logger.info("Conexión a Hyperliquid inicializada")
        
        # Parámetros de trading
        self.asset = "BTC"
        self.leverage = self.config["strategy"]["leverage"]
        self.test_amount_usdc = 20.0  # Monto fijo de 20 USDC para la prueba
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Carga la configuración desde un archivo JSON.
        
        Args:
            config_path: Ruta al archivo de configuración
            
        Returns:
            Diccionario con la configuración
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Error al cargar la configuración: {str(e)}")
            raise
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de la cuenta.
        
        Returns:
            Diccionario con el resumen de la cuenta
        """
        try:
            user_state = self.connection.get_user_state()
            
            # Registrar la estructura completa para depuración
            logger.debug(f"Estructura completa de user_state: {json.dumps(user_state, indent=2)}")
            
            # Obtener valor de la cuenta perpetual de diferentes maneras posibles
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            wallet_value = float(margin_summary.get("walletValue", 0))
            
            # Verificar si hay posiciones abiertas
            positions = user_state.get("assetPositions", [])
            active_positions = len([p for p in positions if float(p.get("position", {}).get("szi", 0)) != 0])
            
            # Verificar balances individuales de activos
            asset_balances = {}
            for asset_position in positions:
                position = asset_position.get("position", {})
                coin = position.get("coin", "")
                size = float(position.get("szi", 0))
                if size != 0:
                    asset_balances[coin] = size
            
            if asset_balances:
                logger.info(f"Balances de activos: {asset_balances}")
            
            return {
                "total_capital": account_value,
                "available_capital": wallet_value,
                "active_positions": active_positions
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen de cuenta: {str(e)}")
            return {
                "total_capital": 0,
                "available_capital": 0,
                "active_positions": 0
            }
    
    def check_and_transfer_funds(self, amount: float = 25.0) -> bool:
        """
        Verifica si hay fondos suficientes en la cuenta perpetual y transfiere desde spot si es necesario.
        
        Args:
            amount: Cantidad mínima requerida en USDC
            
        Returns:
            True si hay fondos suficientes o la transferencia fue exitosa, False en caso contrario
        """
        try:
            # Obtener estado de la cuenta
            user_state = self.connection.get_user_state()
            
            # Registrar la estructura completa para depuración
            logger.info(f"Verificando fondos en la cuenta...")
            
            # Verificar fondos en cuenta perpetual de múltiples maneras
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            wallet_value = float(margin_summary.get("walletValue", 0))
            
            # Verificar si hay posiciones abiertas
            positions = user_state.get("assetPositions", [])
            has_positions = False
            for position in positions:
                pos_data = position.get("position", {})
                size = float(pos_data.get("szi", 0))
                if size != 0:
                    has_positions = True
                    break
            
            # Verificar si hay órdenes abiertas
            open_orders = user_state.get("openOrders", [])
            has_orders = len(open_orders) > 0
            
            # Verificar si hay fondos en la cuenta de perpetuales
            has_funds = account_value > 0 or wallet_value > 0 or has_positions or has_orders
            
            if has_funds:
                logger.info(f"Fondos suficientes en cuenta perpetual: ${account_value:.2f}, Wallet: ${wallet_value:.2f}")
                if has_positions:
                    logger.info(f"Posiciones abiertas encontradas")
                if has_orders:
                    logger.info(f"Órdenes abiertas encontradas: {len(open_orders)}")
                return True
            
            # Si no se detectaron fondos en perpetual, verificar fondos en cuenta spot
            cross_margin_summary = user_state.get("crossMarginSummary", {})
            spot_balance = cross_margin_summary.get("spotBalance", {})
            usdc_balance = float(spot_balance.get("USDC", 0))
            
            if usdc_balance < amount:
                logger.error(f"Fondos insuficientes en cuenta spot: ${usdc_balance:.2f}. Se requieren al menos ${amount:.2f} USDC.")
                logger.error("Por favor, deposite fondos en su cuenta de Hyperliquid antes de continuar.")
                return False
            
            # Transferir fondos de spot a perpetual
            logger.info(f"Transfiriendo ${amount:.2f} USDC de spot a perpetual...")
            result = self.connection.transfer_spot_to_perp(amount)
            
            if result.get("status") == "error":
                logger.error(f"Error al transferir fondos: {result.get('message')}")
                return False
            
            logger.info(f"Transferencia exitosa: {result}")
            
            # Verificar nuevamente los fondos después de la transferencia
            time.sleep(2)  # Esperar a que se actualice el estado
            user_state = self.connection.get_user_state()
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            
            if account_value >= amount:
                logger.info(f"Fondos verificados en cuenta perpetual después de transferencia: ${account_value:.2f}")
                return True
            else:
                logger.warning(f"Fondos en cuenta perpetual después de transferencia: ${account_value:.2f}. Puede que la transferencia aún esté procesándose.")
                return True  # Continuar de todos modos, ya que la transferencia podría estar en proceso
            
        except Exception as e:
            logger.error(f"Error al verificar o transferir fondos: {str(e)}")
            return False
    
    def get_current_price(self) -> float:
        """
        Obtiene el precio actual del activo usando datos OHLC.
        
        Returns:
            Precio actual del activo
        """
        try:
            # Obtener velas recientes
            candles = self.connection.get_candles(self.asset, interval="5m", limit=1)
            
            if not candles or len(candles) == 0:
                logger.error("No se pudieron obtener datos de velas")
                return 0
            
            # Usar el precio de cierre de la última vela
            last_candle = candles[-1]
            price = float(last_candle.get("close", 0))
            
            if price == 0:
                logger.error("Precio obtenido es 0, usando valor predeterminado")
                return 50000.0  # Valor predeterminado para BTC
            
            logger.info(f"Precio actual de {self.asset}: {price}")
            return price
        except Exception as e:
            logger.error(f"Error al obtener precio actual: {str(e)}")
            return 50000.0  # Valor predeterminado para BTC
    
    def calculate_position_size(self, price: float) -> float:
        """
        Calcula el tamaño de la posición para que sea equivalente a 20 USDC.
        
        Args:
            price: Precio actual del activo
            
        Returns:
            Tamaño de la posición en BTC
        """
        if price <= 0:
            logger.error("Precio inválido para calcular tamaño de posición")
            return 0.001  # Valor mínimo por defecto
        
        # Calcular tamaño para que sea equivalente a 20 USDC
        # Fórmula: tamaño = (monto_usdc * apalancamiento) / precio
        size = (self.test_amount_usdc * self.leverage) / price
        
        # Redondear a 6 decimales para evitar errores de precisión
        size = round(size, 6)
        
        # Obtener tamaño mínimo para el activo
        min_size = self.connection.get_min_order_size(self.asset)
        
        # Asegurar que el tamaño sea al menos el mínimo requerido
        if size < min_size:
            logger.warning(f"Tamaño calculado ({size}) es menor que el mínimo requerido ({min_size}). Ajustando al mínimo.")
            size = min_size
        
        logger.info(f"Tamaño de posición calculado: {size} {self.asset} (equivalente a {self.test_amount_usdc} USDC con apalancamiento {self.leverage}x)")
        return size
    
    def open_test_position(self, is_long: bool = True) -> Dict[str, Any]:
        """
        Abre una posición de prueba usando orden a mercado.
        
        Args:
            is_long: True para posición larga, False para corta
            
        Returns:
            Respuesta de la API con el resultado de la orden
        """
        try:
            # Obtener precio actual (solo para información)
            mark_px = self.get_current_price()
            
            if mark_px == 0:
                logger.error("No se pudo obtener el precio actual")
                return {"status": "error", "message": "No se pudo obtener el precio actual"}
            
            # Calcular tamaño de la posición basado en el precio actual
            position_size = self.calculate_position_size(mark_px)
            
            # Colocar orden a mercado
            logger.info(f"Abriendo posición {'LONG' if is_long else 'SHORT'} de prueba en {self.asset} con orden a mercado")
            logger.info(f"Precio actual (referencia): {mark_px}, Tamaño: {position_size}")
            logger.info(f"Valor de la posición: {position_size * mark_px} USD, Con apalancamiento {self.leverage}x: {position_size * mark_px * self.leverage} USD")
            
            # Usar directamente orden a mercado para evitar problemas de validación de precio
            result = self.connection.place_market_order(
                asset=self.asset,
                is_buy=is_long,
                sz=position_size
            )
            
            logger.info(f"Resultado de la orden: {result}")
            
            # Verificar si hay errores en la respuesta
            if result.get("status") == "error":
                logger.error(f"Error al abrir posición: {result.get('message')}")
                return result
            
            response_data = result.get("response", {}).get("data", {})
            statuses = response_data.get("statuses", [])
            
            for status in statuses:
                error = status.get("error")
                if error:
                    logger.error(f"Error al abrir posición: {error}")
                    return {"status": "error", "message": error}
            
            return result
        except Exception as e:
            logger.error(f"Error al abrir posición de prueba: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def close_test_position(self) -> Dict[str, Any]:
        """
        Cierra todas las posiciones abiertas.
        
        Returns:
            Respuesta de la API con el resultado de la orden
        """
        try:
            # Obtener posiciones abiertas
            positions = self.connection.get_positions()
            
            for position in positions:
                asset = position.get("coin")
                size = float(position.get("szi", 0))
                
                if asset == self.asset and size != 0:
                    # Determinar si es long o short
                    is_long = size > 0
                    
                    # Cerrar posición (invertir dirección)
                    logger.info(f"Cerrando posición {'LONG' if is_long else 'SHORT'} en {asset}")
                    logger.info(f"Tamaño de la posición: {abs(size)}")
                    
                    result = self.connection.place_market_order(
                        asset=asset,
                        is_buy=not is_long,  # Invertir dirección
                        sz=abs(size),  # Usar tamaño absoluto
                        reduce_only=True  # Asegurar que solo cierre la posición
                    )
                    
                    logger.info(f"Resultado del cierre: {result}")
                    return result
            
            logger.warning(f"No se encontraron posiciones abiertas para {self.asset}")
            return {"status": "warning", "message": f"No se encontraron posiciones abiertas para {self.asset}"}
        except Exception as e:
            logger.error(f"Error al cerrar posición de prueba: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def run_test(self, position_type: str = "long", hold_time: int = 30) -> None:
        """
        Ejecuta una prueba completa: abre una posición, espera y la cierra.
        
        Args:
            position_type: Tipo de posición ("long" o "short")
            hold_time: Tiempo en segundos para mantener la posición abierta
        """
        try:
            # Mostrar resumen de cuenta inicial
            account_summary = self.get_account_summary()
            logger.info(f"Resumen de cuenta inicial: Capital total=${account_summary['total_capital']:.2f}, "
                       f"Disponible=${account_summary['available_capital']:.2f}, "
                       f"Posiciones activas={account_summary['active_positions']}")
            
            # Verificar y transferir fondos si es necesario
            if not self.check_and_transfer_funds(25.0):
                logger.error("No hay fondos suficientes para realizar la prueba. Por favor, deposite fondos en su cuenta de Hyperliquid.")
                logger.error("IMPORTANTE: Debe tener fondos en su cuenta spot y transferirlos a perpetual antes de operar.")
                return
            
            # Determinar tipo de posición
            is_long = position_type.lower() == "long"
            
            # Abrir posición
            open_result = self.open_test_position(is_long)
            
            if open_result.get("status") == "error":
                logger.error(f"Error al abrir posición: {open_result.get('message')}")
                return
            
            logger.info(f"Posición {'LONG' if is_long else 'SHORT'} abierta correctamente")
            logger.info(f"Esperando {hold_time} segundos antes de cerrar la posición...")
            
            # Esperar el tiempo especificado
            time.sleep(hold_time)
            
            # Cerrar posición
            close_result = self.close_test_position()
            
            if close_result.get("status") == "error":
                logger.error(f"Error al cerrar posición: {close_result.get('message')}")
                logger.error("La posición podría seguir abierta. Verifique manualmente en la interfaz web.")
                return
            
            logger.info("Prueba completada con éxito. La posición ha sido abierta y cerrada correctamente.")
            
            # Mostrar resumen de cuenta final
            account_summary = self.get_account_summary()
            logger.info(f"Resumen de cuenta final: Capital total=${account_summary['total_capital']:.2f}, "
                       f"Disponible=${account_summary['available_capital']:.2f}, "
                       f"Posiciones activas={account_summary['active_positions']}")
            
        except Exception as e:
            logger.error(f"Error durante la prueba: {str(e)}")

def main():
    """Función principal para ejecutar la prueba."""
    parser = argparse.ArgumentParser(description="Script de prueba para abrir y cerrar operaciones en Hyperliquid")
    parser.add_argument("--position", choices=["long", "short"], default="long", help="Tipo de posición a abrir (long o short)")
    parser.add_argument("--hold-time", type=int, default=30, help="Tiempo en segundos para mantener la posición abierta")
    parser.add_argument("--transfer", type=float, help="Transferir la cantidad especificada de USDC de spot a perpetual")
    parser.add_argument("--debug", action="store_true", help="Activar modo debug con información detallada")
    parser.add_argument("--config", type=str, help="Ruta al archivo de configuración")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Modo debug activado")
    
    try:
        # Inicializar trader de prueba
        trader = TestTrader(config_path=args.config)
        
        # Si se solicitó transferencia de fondos
        if args.transfer:
            if trader.check_and_transfer_funds(args.transfer):
                logger.info(f"Fondos transferidos correctamente: {args.transfer} USDC")
            else:
                logger.error("Error al transferir fondos. Abortando prueba.")
                return
        else:
            # Ejecutar prueba completa
            trader.run_test(position_type=args.position, hold_time=args.hold_time)
    
    except Exception as e:
        logger.error(f"Error al ejecutar la prueba: {str(e)}")

if __name__ == "__main__":
    main()
