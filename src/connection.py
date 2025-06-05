"""
Módulo de conexión a Hyperliquid mainnet.
Gestiona la autenticación y comunicación con la API.
Versión actualizada compatible con hyperliquid.exchange.API (sin skip_ws)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import eth_account
from eth_account.signers.local import LocalAccount
from hyperliquid.exchange import API as HyperliquidAPI
from hyperliquid.api import API as HyperliquidInfoAPI
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
    """Clase para gestionar la conexión a Hyperliquid mainnet usando la API correcta."""
    
    def __init__(self, account_address: str, secret_key: str, base_url: Optional[str] = None, skip_ws: bool = False):
        """
        Inicializa la conexión a Hyperliquid.
        
        Args:
            account_address: Dirección de la cuenta principal
            secret_key: Clave privada para firmar transacciones
            base_url: URL base de la API (por defecto, mainnet)
            skip_ws: Si se debe omitir la conexión WebSocket (ignorado en esta versión)
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
        
        # Inicializar conexiones usando la API disponible (sin parámetros problemáticos)
        try:
            # Intentar diferentes formas de inicializar las APIs
            logger.info("Inicializando APIs de Hyperliquid...")
            
            # API para operaciones de exchange (trading) - inicialización simple
            try:
                self.exchange_api = HyperliquidAPI()
                logger.info("Exchange API inicializada correctamente")
            except Exception as e:
                logger.warning(f"Error inicializando Exchange API: {str(e)}")
                self.exchange_api = None
            
            # API para información (consultas) - inicialización simple
            try:
                self.info_api = HyperliquidInfoAPI()
                logger.info("Info API inicializada correctamente")
            except Exception as e:
                logger.warning(f"Error inicializando Info API: {str(e)}")
                self.info_api = None
            
            if self.exchange_api is None and self.info_api is None:
                raise Exception("No se pudo inicializar ninguna API")
            
            logger.info("APIs de Hyperliquid inicializadas")
            
        except Exception as e:
            logger.error(f"Error al inicializar APIs de Hyperliquid: {str(e)}")
            raise
        
        # Inicializar proveedor de datos OHLC reales
        try:
            self.data_provider = DataProvider(self.base_url)
        except Exception as e:
            logger.warning(f"Error inicializando data provider: {str(e)}")
            self.data_provider = None
        
        # Caché de metadatos de mercado
        self._market_metadata_cache = {}
        self._market_metadata_timestamp = 0
        
        logger.info(f"Conexión inicializada para la cuenta {self.account_address}")
        
        # Verificar conexión
        self.verify_connection()
    
    def verify_connection(self) -> None:
        """Verifica que la conexión sea válida y que la cuenta tenga fondos."""
        try:
            # Verificar fondos en cuenta perpetual usando la nueva API
            user_state = self.get_user_state()
            
            if not user_state:
                logger.warning("No se pudo obtener estado del usuario para verificación")
                return
            
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
            logger.warning("Continuando sin verificación completa de fondos")
    
    def get_user_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo del usuario.
        
        Returns:
            Estado del usuario con balances, posiciones y órdenes
        """
        try:
            if self.info_api is None:
                logger.error("Info API no disponible")
                return {}
            
            # Usar la API de información para obtener el estado del usuario
            user_state = self.info_api.user_state(self.account_address)
            return user_state
            
        except Exception as e:
            logger.error(f"Error al obtener estado del usuario: {str(e)}")
            return {}
    
    def get_market_data(self, asset: str) -> Dict[str, Any]:
        """
        Obtiene datos de mercado para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Datos de mercado del activo
        """
        try:
            if self.info_api is None:
                logger.error("Info API no disponible")
                return {}
            
            # Obtener información del mercado
            all_mids = self.info_api.all_mids()
            
            if asset in all_mids:
                mid_price = all_mids[asset]
                return {
                    "midPrice": mid_price,
                    "asset": asset
                }
            else:
                logger.error(f"Asset {asset} no encontrado en datos de mercado")
                return {}
                
        except Exception as e:
            logger.error(f"Error al obtener datos de mercado para {asset}: {str(e)}")
            return {}
    
    def get_candles(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos de velas para análisis técnico.
        
        Args:
            asset: Símbolo del activo
            interval: Intervalo de tiempo
            limit: Número de velas a obtener
            
        Returns:
            Lista de datos de velas
        """
        try:
            if self.data_provider is None:
                logger.error("Data provider no disponible")
                return []
            
            # Usar el proveedor de datos para obtener velas
            candles = self.data_provider.get_candles(asset, interval, limit)
            return candles
            
        except Exception as e:
            logger.error(f"Error al obtener velas para {asset}: {str(e)}")
            return []
    
    def place_order(self, asset: str, is_buy: bool, sz: float, limit_px: float, 
                   order_type: Dict[str, Any] = None, reduce_only: bool = False) -> Dict[str, Any]:
        """
        Coloca una orden en el mercado usando la API de exchange.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
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
        
        logger.info(f"Colocando orden: {asset}, {'compra' if is_buy else 'venta'}, {sz}, {limit_px}")
        
        try:
            if self.exchange_api is None:
                logger.error("Exchange API no disponible")
                return {"status": "error", "error": "Exchange API no disponible"}
            
            # Preparar la orden
            order_request = {
                "coin": asset,
                "is_buy": is_buy,
                "sz": sz,
                "limit_px": limit_px,
                "order_type": order_type,
                "reduce_only": reduce_only
            }
            
            # Usar la API de exchange para colocar la orden
            result = self.exchange_api.order(
                order_request,
                signature=self._sign_l1_action(order_request)
            )
            
            logger.info(f"Orden colocada exitosamente: {result}")
            return {"status": "ok", "response": result}
            
        except Exception as e:
            logger.error(f"Error al colocar orden: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def place_market_order(self, asset: str, is_buy: bool, sz: float) -> Dict[str, Any]:
        """
        Coloca una orden de mercado.
        
        Args:
            asset: Símbolo del activo
            is_buy: True para compra, False para venta
            sz: Tamaño de la orden
            
        Returns:
            Resultado de la orden
        """
        try:
            # Obtener precio actual para la orden de mercado
            market_data = self.get_market_data(asset)
            if not market_data:
                return {"status": "error", "error": "No se pudo obtener precio de mercado"}
            
            mid_price = float(market_data["midPrice"])
            
            # Ajustar precio para orden de mercado (con slippage)
            slippage = 0.01  # 1% de slippage
            if is_buy:
                market_price = mid_price * (1 + slippage)
            else:
                market_price = mid_price * (1 - slippage)
            
            # Colocar como orden límite con precio de mercado
            return self.place_order(
                asset=asset,
                is_buy=is_buy,
                sz=sz,
                limit_px=market_price,
                order_type={"limit": {"tif": "Ioc"}}  # Immediate or Cancel
            )
            
        except Exception as e:
            logger.error(f"Error al colocar orden de mercado: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def cancel_order(self, asset: str, order_id: str) -> Dict[str, Any]:
        """
        Cancela una orden existente.
        
        Args:
            asset: Símbolo del activo
            order_id: ID de la orden a cancelar
            
        Returns:
            Resultado de la cancelación
        """
        try:
            if self.exchange_api is None:
                logger.error("Exchange API no disponible")
                return {"status": "error", "error": "Exchange API no disponible"}
            
            cancel_request = {
                "coin": asset,
                "o": order_id
            }
            
            result = self.exchange_api.cancel(
                cancel_request,
                signature=self._sign_l1_action(cancel_request)
            )
            
            logger.info(f"Orden {order_id} cancelada exitosamente")
            return {"status": "ok", "response": result}
            
        except Exception as e:
            logger.error(f"Error al cancelar orden {order_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _sign_l1_action(self, action: Dict[str, Any]) -> str:
        """
        Firma una acción L1 para la API de exchange.
        
        Args:
            action: Acción a firmar
            
        Returns:
            Firma hexadecimal
        """
        try:
            # Implementar firma según la documentación de Hyperliquid
            # Esta es una implementación simplificada
            action_str = json.dumps(action, separators=(',', ':'))
            message_hash = eth_account.messages.encode_defunct(text=action_str)
            signed_message = self.account.sign_message(message_hash)
            return signed_message.signature.hex()
            
        except Exception as e:
            logger.error(f"Error al firmar acción: {str(e)}")
            raise
    
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las órdenes abiertas.
        
        Returns:
            Lista de órdenes abiertas
        """
        try:
            user_state = self.get_user_state()
            return user_state.get("openOrders", [])
            
        except Exception as e:
            logger.error(f"Error al obtener órdenes abiertas: {str(e)}")
            return []
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las posiciones abiertas.
        
        Returns:
            Lista de posiciones abiertas
        """
        try:
            user_state = self.get_user_state()
            return user_state.get("assetPositions", [])
            
        except Exception as e:
            logger.error(f"Error al obtener posiciones: {str(e)}")
            return []
    
    def validate_order_size(self, asset: str, size: float) -> Tuple[bool, float]:
        """
        Valida y ajusta el tamaño de una orden según los requisitos del mercado.
        
        Args:
            asset: Símbolo del activo
            size: Tamaño propuesto
            
        Returns:
            Tupla (es_válido, tamaño_ajustado)
        """
        try:
            # Obtener metadatos del mercado
            meta = self.get_market_metadata()
            
            if asset in meta:
                asset_meta = meta[asset]
                min_size = float(asset_meta.get("szDecimals", 0))
                
                if size < min_size:
                    logger.warning(f"Tamaño {size} menor que mínimo {min_size} para {asset}")
                    return False, min_size
                
                # Redondear al número correcto de decimales
                decimals = int(asset_meta.get("szDecimals", 6))
                adjusted_size = round(size, decimals)
                
                return True, adjusted_size
            else:
                logger.warning(f"No se encontraron metadatos para {asset}")
                return True, size
                
        except Exception as e:
            logger.error(f"Error al validar tamaño de orden: {str(e)}")
            return True, size
    
    def get_market_metadata(self) -> Dict[str, Any]:
        """
        Obtiene metadatos del mercado con caché.
        
        Returns:
            Metadatos del mercado
        """
        try:
            if self.info_api is None:
                logger.error("Info API no disponible")
                return {}
            
            current_time = time.time()
            
            # Usar caché si es reciente (5 minutos)
            if (current_time - self._market_metadata_timestamp) < 300 and self._market_metadata_cache:
                return self._market_metadata_cache
            
            # Obtener metadatos frescos
            meta = self.info_api.meta()
            
            # Procesar metadatos en formato utilizable
            processed_meta = {}
            if isinstance(meta, dict) and "universe" in meta:
                for asset_info in meta["universe"]:
                    if "name" in asset_info:
                        processed_meta[asset_info["name"]] = asset_info
            
            # Actualizar caché
            self._market_metadata_cache = processed_meta
            self._market_metadata_timestamp = current_time
            
            return processed_meta
            
        except Exception as e:
            logger.error(f"Error al obtener metadatos del mercado: {str(e)}")
            return self._market_metadata_cache or {}
    
    def transfer_spot_to_perp(self, amount: float) -> Dict[str, Any]:
        """
        Transfiere fondos de cuenta spot a perpetual.
        
        Args:
            amount: Cantidad a transferir
            
        Returns:
            Resultado de la transferencia
        """
        try:
            if self.exchange_api is None:
                logger.error("Exchange API no disponible")
                return {"status": "error", "error": "Exchange API no disponible"}
            
            transfer_request = {
                "destination": "perp",
                "amount": str(amount)
            }
            
            result = self.exchange_api.spot_transfer(
                transfer_request,
                signature=self._sign_l1_action(transfer_request)
            )
            
            logger.info(f"Transferencia de {amount} USDC de spot a perp exitosa")
            return {"status": "ok", "response": result}
            
        except Exception as e:
            logger.error(f"Error en transferencia spot a perp: {str(e)}")
            return {"status": "error", "error": str(e)}

