"""
Módulo de conexión a Hyperliquid utilizando la biblioteca CCXT.
Gestiona la autenticación y comunicación con la API de Hyperliquid a través de CCXT.
"""

import logging
import time
import ccxt
from typing import Dict, Any, Optional, List, Tuple
import json

logger = logging.getLogger("ccxt_connection")

class CCXTHyperliquidConnection:
    """Clase para gestionar la conexión a Hyperliquid utilizando CCXT."""
    
    def __init__(self, wallet_address: str, private_key: str, testnet: bool = False):
        """
        Inicializa la conexión a Hyperliquid utilizando CCXT.
        
        Args:
            wallet_address: Dirección de la wallet
            private_key: Clave privada para firmar transacciones
            testnet: Si se debe usar testnet en lugar de mainnet
        """
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.testnet = testnet
        
        # Inicializar el exchange de CCXT
        self.exchange = ccxt.hyperliquid({
            'walletAddress': wallet_address,
            'privateKey': private_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'defaultSlippage': 0.05  # 5% de slippage máximo
            }
        })
        
        # Configurar testnet si es necesario
        if testnet:
            self.exchange.set_sandbox_mode(True)
        
        # Símbolo para BTC
        self.btc_symbol = 'BTC/USDC:USDC'
        
        logger.info(f"Conexión CCXT inicializada para la cuenta {wallet_address}")
        
        # Verificar conexión
        self.verify_connection()
    
    def verify_connection(self) -> None:
        """Verifica que la conexión sea válida y que la cuenta tenga fondos."""
        try:
            # Obtener balance
            balance = self.exchange.fetch_balance()
            
            # Registrar la estructura completa para depuración
            logger.debug(f"Estructura completa de balance: {json.dumps(balance, indent=2)}")
            
            # Verificar si hay fondos en la cuenta
            total_balance = balance.get('total', {})
            usdc_balance = total_balance.get('USDC', 0)
            
            if usdc_balance > 0:
                logger.info(f"Conexión verificada. Balance USDC: {usdc_balance}")
            else:
                logger.warning(f"La cuenta {self.wallet_address} podría no tener fondos suficientes.")
                
        except Exception as e:
            logger.error(f"Error al verificar la conexión: {str(e)}")
            # No lanzar excepción para permitir que el bot continúe funcionando
    
    def get_market_price(self, symbol: str = None) -> float:
        """
        Obtiene el precio actual de mercado para un símbolo.
        
        Args:
            symbol: Símbolo del par de trading (por defecto, BTC/USDC:USDC)
            
        Returns:
            Precio actual de mercado
        """
        if symbol is None:
            symbol = self.btc_symbol
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.info(f"Precio de mercado para {symbol}: {price}")
            return price
        except Exception as e:
            logger.error(f"Error al obtener precio de mercado para {symbol}: {str(e)}")
            return 0.0
    
    def get_user_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del usuario.
        
        Returns:
            Diccionario con el estado del usuario
        """
        try:
            # Obtener balance
            balance = self.exchange.fetch_balance()
            
            # Obtener posiciones abiertas
            positions = self.exchange.fetch_positions()
            
            # Obtener órdenes abiertas
            open_orders = self.exchange.fetch_open_orders()
            
            # Construir un estado similar al de la API original de Hyperliquid
            user_state = {
                "balance": balance,
                "positions": positions,
                "openOrders": open_orders,
                "marginSummary": {
                    "accountValue": balance.get('total', {}).get('USDC', 0),
                    "walletValue": balance.get('free', {}).get('USDC', 0)
                }
            }
            
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
            Diccionario con datos de mercado
        """
        symbol = f"{asset}/USDC:USDC"
        
        try:
            # Obtener ticker
            ticker = self.exchange.fetch_ticker(symbol)
            
            # Construir datos de mercado similares a la API original
            market_data = {
                "name": asset,
                "midPrice": ticker['last'],
                "markPrice": ticker['last'],
                "indexPrice": ticker['last'],
                "lastTradedPrice": ticker['last'],
                "bid": ticker['bid'],
                "ask": ticker['ask'],
                "volume24h": ticker['quoteVolume'],
                "openInterest": ticker.get('info', {}).get('openInterest', 0)
            }
            
            logger.info(f"Datos de mercado obtenidos para {asset}")
            return market_data
        except Exception as e:
            logger.error(f"Error al obtener datos de mercado para {asset}: {str(e)}")
            return {}
    
    def get_candles(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        symbol = f"{asset}/USDC:USDC"
        
        # Mapear el intervalo al formato de CCXT
        timeframe_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        
        timeframe = timeframe_map.get(interval, "5m")
        
        try:
            # Obtener velas OHLC
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convertir al formato esperado por el bot
            candles = []
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                candles.append({
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })
            
            logger.info(f"Obtenidas {len(candles)} velas para {asset} (intervalo: {interval})")
            return candles
        except Exception as e:
            logger.error(f"Error al obtener velas para {asset}: {str(e)}")
            return []
    
    def calculate_order_size(self, usd_amount: float, price: float) -> float:
        """
        Calcula el tamaño de la orden en base al monto en USD y el precio.
        
        Args:
            usd_amount: Monto en USD a utilizar
            price: Precio actual del activo
            
        Returns:
            Tamaño de la orden
        """
        if price <= 0:
            return 0.0
        
        # Calcular tamaño y redondear a 6 decimales
        size = round(usd_amount / price, 6)
        return size
    
    def place_market_order(self, asset: str, is_buy: bool, sz: float) -> Dict[str, Any]:
        """
        Coloca una orden de mercado.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            is_buy: True para compra, False para venta
            sz: Tamaño de la orden
            
        Returns:
            Resultado de la operación
        """
        symbol = f"{asset}/USDC:USDC"
        side = "buy" if is_buy else "sell"
        
        try:
            # Obtener precio actual para el cálculo del slippage
            price = self.get_market_price(symbol)
            if price <= 0:
                return {"status": "error", "error": "No se pudo obtener un precio válido para la orden"}
            
            logger.info(f"Precio de mercado para {symbol}: {price}")
            
            # Validar y ajustar tamaño de orden
            is_valid, adjusted_size = self.validate_order_size(asset, sz)
            if not is_valid:
                logger.warning(f"Tamaño de orden ajustado de {sz} a {adjusted_size}")
                sz = adjusted_size
            
            # Parámetros adicionales para la orden
            params = {}
            
            # CORREGIDO: Colocar orden de mercado con el precio explícito para el cálculo del slippage
            order = self.exchange.create_order(symbol, 'market', side, abs(sz), price=price, params=params)
            
            logger.info(f"Orden de mercado colocada: {side} {abs(sz)} {asset} a ~${price:.2f}")
            
            return {
                "status": "ok",
                "response": {
                    "data": {
                        "statuses": [
                            {
                                "filled": {
                                    "oid": order.get("id", ""),
                                    "price": str(price),
                                    "sz": sz
                                }
                            }
                        ]
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error al colocar orden de mercado: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def place_order(self, asset: str, is_buy: bool, sz: float, limit_px: float, order_type: Dict[str, Any] = None, reduce_only: bool = False) -> Dict[str, Any]:
        """
        Coloca una orden límite.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            is_buy: True para compra, False para venta
            sz: Tamaño de la orden
            limit_px: Precio límite
            order_type: Tipo de orden (no utilizado en CCXT)
            reduce_only: Si la orden es solo para reducir posición
            
        Returns:
            Resultado de la operación
        """
        symbol = f"{asset}/USDC:USDC"
        side = "buy" if is_buy else "sell"
        
        try:
            # Parámetros adicionales
            params = {
                'reduceOnly': reduce_only
            }
            
            # Colocar orden límite
            order = self.exchange.create_order(symbol, 'limit', side, sz, limit_px, params)
            
            logger.info(f"Orden límite colocada: {asset}, {'compra' if is_buy else 'venta'}, {sz}, precio: {limit_px}")
            
            return {
                "status": "ok",
                "response": {
                    "data": {
                        "statuses": [
                            {
                                "resting": {
                                    "oid": order['id'],
                                    "price": limit_px,
                                    "sz": sz
                                }
                            }
                        ]
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error al colocar orden límite: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def cancel_order(self, asset: str, order_id: str) -> Dict[str, Any]:
        """
        Cancela una orden activa.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            order_id: ID de la orden
            
        Returns:
            Resultado de la cancelación
        """
        symbol = f"{asset}/USDC:USDC"
        
        try:
            # Cancelar orden
            result = self.exchange.cancel_order(order_id, symbol)
            
            logger.info(f"Orden {order_id} cancelada exitosamente")
            
            return {"status": "ok", "response": result}
        except Exception as e:
            logger.error(f"Error al cancelar orden {order_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_order_status(self, asset: str, order_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una orden.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            order_id: ID de la orden
            
        Returns:
            Estado de la orden
        """
        symbol = f"{asset}/USDC:USDC"
        
        try:
            # Obtener estado de la orden
            order = self.exchange.fetch_order(order_id, symbol)
            
            # Convertir al formato esperado por el bot
            status = {}
            
            if order['status'] == 'closed':
                status["filled"] = {
                    "price": order['price'],
                    "sz": order['amount']
                }
            elif order['status'] == 'canceled':
                status["cancelled"] = True
            else:
                status["resting"] = {
                    "oid": order['id'],
                    "price": order['price'],
                    "sz": order['amount']
                }
            
            return status
        except Exception as e:
            logger.error(f"Error al obtener estado de orden {order_id}: {str(e)}")
            return {}
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de la cuenta.
        
        Returns:
            Diccionario con resumen de la cuenta
        """
        try:
            # Obtener balance
            balance = self.exchange.fetch_balance()
            
            # Obtener valores relevantes
            total_usdc = balance.get('total', {}).get('USDC', 0)
            free_usdc = balance.get('free', {}).get('USDC', 0)
            used_usdc = balance.get('used', {}).get('USDC', 0)
            
            # Obtener posiciones abiertas
            positions = self.exchange.fetch_positions()
            
            return {
                "total_capital": total_usdc,
                "available_capital": free_usdc,
                "used_capital": used_usdc,
                "positions": positions
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen de cuenta: {str(e)}")
            return {
                "total_capital": 0,
                "available_capital": 0,
                "used_capital": 0,
                "positions": []
            }
    
    def get_min_order_size(self, asset: str) -> float:
        """
        Obtiene el tamaño mínimo de orden para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Tamaño mínimo de orden
        """
        symbol = f"{asset}/USDC:USDC"
        
        try:
            # Obtener información del mercado
            market = self.exchange.market(symbol)
            
            # Obtener límites
            limits = market.get('limits', {})
            amount = limits.get('amount', {})
            min_amount = amount.get('min', 0)
            
            # CORREGIDO: Verificar que min_amount no sea None antes de comparar
            if min_amount is not None and min_amount > 0:
                logger.info(f"Tamaño mínimo de orden para {asset}: {min_amount}")
                return float(min_amount)
            
            # Si no se encuentra, usar valores predeterminados
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
        
        if abs(size) < min_size:
            logger.warning(f"Tamaño de orden {size} para {asset} es menor que el mínimo {min_size}. Ajustando al mínimo.")
            # Mantener el signo original (para posiciones cortas)
            adjusted_size = min_size if size >= 0 else -min_size
            return False, adjusted_size
        
        return True, size

