"""
Módulo de conexión a Hyperliquid mainnet.
Gestiona la autenticación y comunicación con la API.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import eth_account
from eth_account.signers.local import LocalAccount
import requests
import time
import json
import os
import sys
import binascii

# Importar el proveedor de datos para obtener datos OHLC reales
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_provider import DataProvider

logger = logging.getLogger("connection")

class HyperliquidConnection:
    """Clase para gestionar la conexión a Hyperliquid mainnet."""
    
    def __init__(self, account_address: str, secret_key: str, base_url: Optional[str] = None, skip_ws: bool = False):
        """
        Inicializa la conexión a Hyperliquid.
        
        Args:
            account_address: Dirección de la cuenta principal
            secret_key: Clave privada para firmar transacciones
            base_url: URL base de la API (por defecto, mainnet)
            skip_ws: Si se debe omitir la conexión WebSocket
        """
        self.account_address = account_address
        self.secret_key = secret_key
        self.base_url = base_url or "https://api.hyperliquid.xyz"
        self.skip_ws = skip_ws
        
        # Validar formato de la clave secreta
        if not secret_key or not isinstance(secret_key, str):
            raise ValueError("La clave secreta no puede estar vacía")
        
        # Verificar que la clave secreta tenga formato hexadecimal
        if not secret_key.startswith("0x"):
            logger.warning("La clave secreta no comienza con '0x', añadiendo prefijo")
            secret_key = "0x" + secret_key
        
        # Verificar que solo contenga caracteres hexadecimales
        try:
            # Eliminar el prefijo '0x' para la validación
            hex_part = secret_key[2:] if secret_key.startswith("0x") else secret_key
            int(hex_part, 16)  # Intentar convertir a entero en base 16
        except ValueError:
            raise ValueError("La clave secreta contiene caracteres no hexadecimales")
        
        # Inicializar cuenta
        try:
            self.account: LocalAccount = eth_account.Account.from_key(secret_key)
        except binascii.Error as e:
            raise ValueError(f"Error al procesar la clave secreta: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error al inicializar la cuenta: {str(e)}")
        
        # Validar que la cuenta coincida con la dirección proporcionada o usar la dirección de la cuenta
        if account_address and account_address != self.account.address:
            logger.info(f"Usando dirección de cuenta proporcionada: {account_address}")
            logger.info(f"Dirección de la cuenta de firma: {self.account.address}")
        else:
            self.account_address = self.account.address
            logger.info(f"Usando dirección de cuenta derivada de la clave: {self.account_address}")
        
        # Inicializar proveedor de datos OHLC reales
        self.data_provider = DataProvider(self.base_url)
        
        # Caché de metadatos de mercado
        self._market_metadata_cache = {}
        self._market_metadata_timestamp = 0
        
        logger.info(f"Conexión inicializada para la cuenta {self.account_address}")
        
        # Verificar conexión
        self.verify_connection()
    
    def verify_connection(self) -> None:
        """Verifica que la conexión sea válida y que la cuenta tenga fondos."""
        try:
            # Verificar fondos en cuenta perpetual usando la API REST directamente
            user_state = self.get_user_state()
            
            # Registrar la estructura completa para depuración
            logger.debug(f"Estructura completa de user_state: {json.dumps(user_state, indent=2)}")
            
            # Obtener valor de la cuenta perpetual de diferentes maneras posibles
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            wallet_value = float(margin_summary.get("walletValue", 0))
            
            # Verificar si hay posiciones abiertas
            positions = user_state.get("assetPositions", [])
            has_positions = len(positions) > 0
            
            # Verificar si hay órdenes abiertas
            open_orders = user_state.get("openOrders", [])
            has_orders = len(open_orders) > 0
            
            # Verificar balances individuales de activos
            asset_balances = {}
            for asset_position in positions:
                position = asset_position.get("position", {})
                coin = position.get("coin", "")
                size = float(position.get("szi", 0))
                if size != 0:
                    asset_balances[coin] = size
            
            # Verificar si hay fondos en la cuenta de perpetuales
            has_funds = account_value > 0 or wallet_value > 0 or has_positions or has_orders or len(asset_balances) > 0
            
            if has_funds:
                logger.info(f"Conexión verificada. Valor de la cuenta perpetual: {account_value}, Wallet: {wallet_value}")
                if has_positions:
                    logger.info(f"Posiciones abiertas: {len(positions)}")
                if has_orders:
                    logger.info(f"Órdenes abiertas: {len(open_orders)}")
                if asset_balances:
                    logger.info(f"Balances de activos: {asset_balances}")
            else:
                # Intentar verificar fondos en la cuenta spot
                cross_margin_summary = user_state.get("crossMarginSummary", {})
                spot_balance = cross_margin_summary.get("spotBalance", {})
                usdc_balance = float(spot_balance.get("USDC", 0))
                
                if usdc_balance > 0:
                    logger.info(f"No hay fondos en cuenta perpetual, pero hay {usdc_balance} USDC en cuenta spot.")
                    logger.warning(
                        f"La cuenta {self.account_address} no tiene fondos en perpetual, pero tiene fondos en spot. "
                        f"Use la función transfer_spot_to_perp para transferir fondos."
                    )
                else:
                    logger.warning(
                        f"La cuenta {self.account_address} podría no tener fondos suficientes en perpetual ni en spot. "
                        f"Verificar manualmente en la interfaz web."
                    )
        except Exception as e:
            logger.error(f"Error al verificar la conexión: {str(e)}")
            # No lanzar excepción para permitir que el bot continúe funcionando
    
    def get_user_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del usuario.
        
        Returns:
            Diccionario con el estado del usuario
        """
        try:
            # Implementar llamada directa a la API REST
            url = f"{self.base_url}/info"
            payload = {"type": "clearinghouseState", "user": self.account_address}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error al obtener estado del usuario: {str(e)}")
            return {}
    
    def get_market_data(self, asset: str) -> Dict[str, Any]:
        """
        Obtiene datos de mercado para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "ETH")
            
        Returns:
            Diccionario con datos de mercado
        """
        try:
            # Obtener metadatos del mercado directamente usando la API REST
            url = f"{self.base_url}/info"
            payload = {"type": "meta"}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Buscar el activo específico en la respuesta
            universe = data.get("universe", [])
            for market in universe:
                if market.get("name") == asset:
                    logger.info(f"Datos de mercado obtenidos para {asset}")
                    return market
            
            logger.warning(f"No se encontraron datos de mercado para {asset}")
            return {}
        except Exception as e:
            logger.error(f"Error al obtener datos de mercado para {asset}: {str(e)}")
            return {}
    
    def get_market_metadata(self, asset: str = None) -> Dict[str, Any]:
        """
        Obtiene metadatos del mercado, incluyendo tamaños mínimos de orden.
        
        Args:
            asset: Símbolo del activo específico (opcional)
            
        Returns:
            Diccionario con metadatos del mercado o del activo específico
        """
        # Verificar si la caché es válida (menos de 1 hora)
        current_time = time.time()
        if current_time - self._market_metadata_timestamp > 3600 or not self._market_metadata_cache:
            try:
                # Obtener metadatos del mercado directamente usando la API REST
                url = f"{self.base_url}/info"
                payload = {"type": "meta"}
                headers = {"Content-Type": "application/json"}
                
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Procesar y almacenar en caché
                universe = data.get("universe", [])
                
                # Crear un diccionario indexado por nombre de activo
                asset_metadata = {}
                for asset_data in universe:
                    name = asset_data.get("name", "")
                    if name:
                        asset_metadata[name] = asset_data
                
                self._market_metadata_cache = {
                    "meta": data,
                    "assets": asset_metadata
                }
                self._market_metadata_timestamp = current_time
                
                logger.info(f"Metadatos de mercado actualizados. {len(asset_metadata)} activos disponibles.")
                
                # Registrar los metadatos para depuración
                logger.debug(f"Metadatos de mercado: {json.dumps(self._market_metadata_cache, indent=2)}")
                
            except Exception as e:
                logger.error(f"Error al obtener metadatos del mercado: {str(e)}")
                if not self._market_metadata_cache:
                    return {"meta": {}, "assets": {}}
        
        # Si se solicita un activo específico
        if asset:
            asset_data = self._market_metadata_cache.get("assets", {}).get(asset, {})
            if not asset_data:
                logger.warning(f"No se encontraron metadatos para el activo {asset}")
            return asset_data
        
        return self._market_metadata_cache
    
    def get_min_order_size(self, asset: str) -> float:
        """
        Obtiene el tamaño mínimo de orden para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Tamaño mínimo de orden
        """
        try:
            # Obtener decimales para el tamaño de orden directamente
            sz_decimals = self.data_provider.get_sz_decimals(asset)
            
            if sz_decimals > 0:
                min_size = 10 ** -sz_decimals
                logger.info(f"Tamaño mínimo de orden para {asset}: {min_size} (basado en {sz_decimals} decimales)")
                return min_size
            
            # Intentar obtener de los metadatos del mercado
            asset_data = self.get_market_metadata(asset)
            
            # Método 1: Buscar en szDecimals
            sz_decimals = asset_data.get("szDecimals")
            if sz_decimals:
                try:
                    sz_decimals = int(sz_decimals)
                    if sz_decimals > 0:
                        min_size = 10 ** -sz_decimals
                        logger.info(f"Tamaño mínimo de orden para {asset}: {min_size} (basado en {sz_decimals} decimales)")
                        return min_size
                except (ValueError, TypeError):
                    pass
            
            # Método 2: Buscar en stepSz
            step_sz = asset_data.get("stepSz")
            if step_sz:
                try:
                    step_sz_float = float(step_sz)
                    if step_sz_float > 0:
                        logger.info(f"Tamaño mínimo de orden para {asset}: {step_sz_float} (basado en stepSz)")
                        return step_sz_float
                except (ValueError, TypeError):
                    pass
            
            # Si no se encontró, usar valores predeterminados
            default_min_sizes = {
                "BTC": 0.001,  # 1 miliBTC
                "ETH": 0.01,   # 10 miliETH
                "SOL": 0.1,    # 0.1 SOL
            }
            min_size = default_min_sizes.get(asset, 0.01)
            logger.warning(f"No se pudo determinar el tamaño mínimo para {asset}. Usando valor predeterminado: {min_size}")
            return min_size
            
        except Exception as e:
            logger.error(f"Error al obtener tamaño mínimo para {asset}: {str(e)}")
            # Valores predeterminados seguros
            default_min_sizes = {
                "BTC": 0.001,  # 1 miliBTC
                "ETH": 0.01,   # 10 miliETH
                "SOL": 0.1,    # 0.1 SOL
            }
            return default_min_sizes.get(asset, 0.01)
    
    def validate_order_size(self, asset: str, size: float) -> Tuple[bool, float]:
        """
        Valida si el tamaño de una orden es válido y lo ajusta si es necesario.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            size: Tamaño de la orden a validar
            
        Returns:
            Tupla (es_válido, tamaño_ajustado)
        """
        min_size = self.get_min_order_size(asset)
        
        # Normalizar el tamaño para que sea un múltiplo del step size
        normalized_size = self.data_provider.normalize_size(asset, size)
        
        if abs(normalized_size) < min_size:
            logger.warning(f"Tamaño de orden {size} para {asset} es menor que el mínimo {min_size}. Ajustando al mínimo.")
            # Mantener el signo original (para posiciones cortas)
            adjusted_size = min_size if normalized_size >= 0 else -min_size
            # Normalizar nuevamente para asegurar que sea un múltiplo exacto
            adjusted_size = self.data_provider.normalize_size(asset, adjusted_size)
            return False, adjusted_size
        
        if normalized_size != size:
            logger.info(f"Tamaño de orden ajustado de {size} a {normalized_size} para cumplir con el step size")
            return False, normalized_size
        
        return True, size
    
    def get_candles(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC combinando datos históricos de Binance con el precio actual de Hyperliquid.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        logger.info(f"Obteniendo datos OHLC para {asset} (intervalo: {interval}, límite: {limit})")
        
        # Usar el método combinado del proveedor de datos
        candles = self.data_provider.get_combined_candles(asset, interval, limit)
        
        if not candles:
            logger.error(f"No se pudieron obtener datos OHLC para {asset}")
            return []
        
        logger.info(f"Obtenidos {len(candles)} datos OHLC para {asset}")
        return candles
    
    def place_order(self, asset: str, is_buy: bool, sz: float, limit_px: float, 
                   order_type: Dict[str, Any] = None, reduce_only: bool = False) -> Dict[str, Any]:
        """
        Coloca una orden en el mercado.
        
        Args:
            asset: Símbolo del activo (ej. "ETH")
            is_buy: True para compra, False para venta
            sz: Tamaño de la orden
            limit_px: Precio límite
            order_type: Tipo de orden (por defecto, límite GTC)
            reduce_only: Si la orden solo debe reducir posiciones existentes
            
        Returns:
            Respuesta de la API con el resultado de la orden
        """
        if order_type is None:
            order_type = {"limit": {"tif": "Gtc"}}
        
        # Validar y ajustar el tamaño de la orden
        is_valid, adjusted_sz = self.validate_order_size(asset, sz)
        if not is_valid:
            logger.warning(f"Tamaño de orden ajustado de {sz} a {adjusted_sz} para cumplir con el mínimo requerido")
            sz = adjusted_sz
        
        logger.info(f"Colocando orden: {asset}, {'compra' if is_buy else 'venta'}, {sz}, {limit_px}")
        
        try:
            # Usar la API REST directamente
            url = f"{self.base_url}/exchange"
            
            # Preparar la firma
            timestamp = int(time.time() * 1000)
            nonce = timestamp
            
            # Construir el payload
            action = {
                "type": "order",
                "asset": asset,
                "isBuy": is_buy,
                "sz": str(sz),
                "limitPx": str(limit_px),
                "orderType": order_type,
                "reduceOnly": reduce_only
            }
            
            payload = {
                "action": action,
                "nonce": nonce,
                "signature": self._sign_action(action, nonce)
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verificar si hay errores en la respuesta
            if result.get("status") == "ok":
                response_data = result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])
                
                for status in statuses:
                    error = status.get("error")
                    if error:
                        logger.error(f"Error en la orden: {error}")
                        return {"status": "error", "error": error}
                
                logger.info(f"Orden colocada exitosamente: {response_data}")
                return {"status": "ok", "response": response_data}
            else:
                error = result.get("error", "Error desconocido")
                logger.error(f"Error al colocar la orden: {error}")
                return {"status": "error", "error": error}
        except Exception as e:
            logger.error(f"Error al colocar la orden: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _sign_action(self, action: Dict[str, Any], nonce: int) -> str:
        """
        Firma una acción para la API de Hyperliquid.
        
        Args:
            action: Acción a firmar
            nonce: Número único para evitar repetición
            
        Returns:
            Firma en formato hexadecimal
        """
        # Implementar la firma según la documentación de Hyperliquid
        message = json.dumps({"action": action, "nonce": nonce})
        message_hash = eth_account.messages.encode_defunct(text=message)
        signed_message = self.account.sign_message(message_hash)
        return signed_message.signature.hex()
    
    def transfer_spot_to_perp(self, amount: float) -> Dict[str, Any]:
        """
        Transfiere fondos de la cuenta spot a la cuenta perpetual.
        
        Args:
            amount: Cantidad a transferir en USDC
            
        Returns:
            Resultado de la transferencia
        """
        try:
            logger.info(f"Transfiriendo {amount} USDC de spot a perpetual")
            
            # Usar la API REST directamente
            url = f"{self.base_url}/exchange"
            
            # Preparar la firma
            timestamp = int(time.time() * 1000)
            nonce = timestamp
            
            # Construir el payload
            action = {
                "type": "transferSpotMargin",
                "amount": str(amount)
            }
            
            payload = {
                "action": action,
                "nonce": nonce,
                "signature": self._sign_action(action, nonce)
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "ok":
                logger.info(f"Transferencia exitosa: {amount} USDC")
                return {"status": "ok", "response": result.get("response")}
            else:
                error = result.get("error", "Error desconocido")
                logger.error(f"Error en la transferencia: {error}")
                return {"status": "error", "error": error}
        except Exception as e:
            logger.error(f"Error al transferir fondos: {str(e)}")
            return {"status": "error", "error": str(e)}
