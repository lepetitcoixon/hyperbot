"""
Módulo de trading usando ccxt para Hyperliquid.
Implementa las operaciones de trading usando la API de ccxt para mejorar la confiabilidad.
"""

import logging
import time
import ccxt
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger("ccxt_trader")

class CCXTTrader:
    """Clase para gestionar operaciones de trading usando ccxt."""
    
    def __init__(self, wallet_address: str, private_key: str, config: Dict[str, Any]):
        """
        Inicializa el trader con ccxt.
        
        Args:
            wallet_address: Dirección de la wallet
            private_key: Clave privada para firmar transacciones
            config: Configuración del bot
        """
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.config = config
        self.ccxt_config = config.get("ccxt", {})
        
        # Inicializar exchange ccxt
        self.exchange = None
        self._initialize_exchange()
        
        logger.info(f"CCXTTrader inicializado para wallet: {wallet_address}")
    
    def _initialize_exchange(self) -> None:
        """Inicializa la conexión con el exchange usando ccxt."""
        try:
            self.exchange = ccxt.hyperliquid({
                'walletAddress': self.wallet_address,
                'privateKey': self.private_key,
                'enableRateLimit': self.ccxt_config.get('enable_rate_limit', True),
                'timeout': self.ccxt_config.get('timeout', 30000),
                'options': {
                    'defaultType': self.ccxt_config.get('default_type', 'swap'),
                    'defaultSlippage': self.ccxt_config.get('default_slippage', 0.05)
                }
            })
            
            # Verificar conexión
            self._verify_connection()
            
            logger.info("Conexión ccxt establecida exitosamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar ccxt: {str(e)}")
            raise
    
    def _verify_connection(self) -> None:
        """Verifica que la conexión con ccxt funcione correctamente."""
        try:
            # Intentar obtener balance para verificar conexión
            balance = self.exchange.fetch_balance()
            logger.info("Conexión ccxt verificada exitosamente")
            
            # Log del balance total para información
            total_balance = balance.get('total', {})
            if total_balance:
                logger.info(f"Balance total disponible: {total_balance}")
            
        except Exception as e:
            logger.error(f"Error al verificar conexión ccxt: {str(e)}")
            raise
    
    def get_market_price(self, symbol: str) -> float:
        """
        Obtiene el precio actual de mercado para un símbolo.
        
        Args:
            symbol: Símbolo del activo (ej. 'BTC/USDC:USDC')
            
        Returns:
            Precio actual de mercado
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.debug(f"Precio de mercado para {symbol}: {price}")
            return float(price)
            
        except Exception as e:
            logger.error(f"Error al obtener precio de mercado para {symbol}: {str(e)}")
            raise
    
    def calculate_order_size(self, usd_amount: float, price: float) -> float:
        """
        Calcula el tamaño de la orden basado en el monto en USD y el precio.
        
        Args:
            usd_amount: Monto en USD a operar
            price: Precio actual del activo
            
        Returns:
            Tamaño de la orden en unidades del activo
        """
        try:
            size = round(usd_amount / price, 6)
            logger.debug(f"Tamaño calculado: {size} para ${usd_amount} a precio {price}")
            return size
            
        except Exception as e:
            logger.error(f"Error al calcular tamaño de orden: {str(e)}")
            raise
    
    def place_market_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Coloca una orden de mercado.
        
        Args:
            symbol: Símbolo del activo (ej. 'BTC/USDC:USDC')
            side: 'buy' o 'sell'
            amount: Cantidad a operar
            price: Precio de referencia (opcional, para logging)
            
        Returns:
            Resultado de la orden
        """
        try:
            logger.info(f"Colocando orden de mercado: {symbol}, {side}, {amount}")
            
            # Colocar orden usando ccxt
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount,
                price=price
            )
            
            logger.info(f"Orden de mercado ejecutada exitosamente: {order['id']}")
            logger.info(f"Detalles: {order}")
            
            return {
                "status": "ok",
                "order_id": order['id'],
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": order.get('price', price),
                "filled": order.get('filled', 0),
                "cost": order.get('cost', 0),
                "timestamp": order.get('timestamp'),
                "order_data": order
            }
            
        except Exception as e:
            logger.error(f"Error al colocar orden de mercado: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "symbol": symbol,
                "side": side,
                "amount": amount
            }
    
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Coloca una orden límite.
        
        Args:
            symbol: Símbolo del activo (ej. 'BTC/USDC:USDC')
            side: 'buy' o 'sell'
            amount: Cantidad a operar
            price: Precio límite
            
        Returns:
            Resultado de la orden
        """
        try:
            logger.info(f"Colocando orden límite: {symbol}, {side}, {amount} a {price}")
            
            # Colocar orden usando ccxt
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price
            )
            
            logger.info(f"Orden límite colocada exitosamente: {order['id']}")
            logger.info(f"Detalles: {order}")
            
            return {
                "status": "ok",
                "order_id": order['id'],
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "filled": order.get('filled', 0),
                "remaining": order.get('remaining', amount),
                "timestamp": order.get('timestamp'),
                "order_data": order
            }
            
        except Exception as e:
            logger.error(f"Error al colocar orden límite: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price
            }
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancela una orden existente.
        
        Args:
            order_id: ID de la orden a cancelar
            symbol: Símbolo del activo
            
        Returns:
            Resultado de la cancelación
        """
        try:
            logger.info(f"Cancelando orden: {order_id} para {symbol}")
            
            # Cancelar orden usando ccxt
            result = self.exchange.cancel_order(order_id, symbol)
            
            logger.info(f"Orden cancelada exitosamente: {order_id}")
            
            return {
                "status": "ok",
                "order_id": order_id,
                "symbol": symbol,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error al cancelar orden {order_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "order_id": order_id,
                "symbol": symbol
            }
    
    def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una orden.
        
        Args:
            order_id: ID de la orden
            symbol: Símbolo del activo
            
        Returns:
            Estado de la orden
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            
            return {
                "status": "ok",
                "order_id": order_id,
                "symbol": symbol,
                "order_status": order['status'],
                "filled": order.get('filled', 0),
                "remaining": order.get('remaining', 0),
                "price": order.get('price'),
                "average": order.get('average'),
                "cost": order.get('cost', 0),
                "timestamp": order.get('timestamp'),
                "order_data": order
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estado de orden {order_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "order_id": order_id,
                "symbol": symbol
            }
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Obtiene el balance de la cuenta.
        
        Returns:
            Balance de la cuenta
        """
        try:
            balance = self.exchange.fetch_balance()
            
            return {
                "status": "ok",
                "balance": balance,
                "total": balance.get('total', {}),
                "free": balance.get('free', {}),
                "used": balance.get('used', {})
            }
            
        except Exception as e:
            logger.error(f"Error al obtener balance: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_positions(self) -> Dict[str, Any]:
        """
        Obtiene las posiciones abiertas.
        
        Returns:
            Posiciones abiertas
        """
        try:
            positions = self.exchange.fetch_positions()
            
            # Filtrar solo posiciones con tamaño > 0
            active_positions = [pos for pos in positions if float(pos.get('size', 0)) != 0]
            
            return {
                "status": "ok",
                "positions": active_positions,
                "count": len(active_positions)
            }
            
        except Exception as e:
            logger.error(f"Error al obtener posiciones: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def close_position(self, symbol: str, size: Optional[float] = None) -> Dict[str, Any]:
        """
        Cierra una posición existente.
        
        Args:
            symbol: Símbolo del activo
            size: Tamaño a cerrar (opcional, si no se especifica cierra toda la posición)
            
        Returns:
            Resultado del cierre
        """
        try:
            # Obtener posición actual
            positions = self.get_positions()
            if positions["status"] != "ok":
                return positions
            
            # Buscar la posición para este símbolo
            target_position = None
            for pos in positions["positions"]:
                if pos["symbol"] == symbol:
                    target_position = pos
                    break
            
            if not target_position:
                return {
                    "status": "error",
                    "message": f"No se encontró posición abierta para {symbol}"
                }
            
            # Determinar tamaño y lado para cerrar
            position_size = float(target_position["size"])
            if size is None:
                size = abs(position_size)
            
            # Determinar el lado opuesto para cerrar
            side = "sell" if position_size > 0 else "buy"
            
            logger.info(f"Cerrando posición: {symbol}, tamaño: {size}, lado: {side}")
            
            # Colocar orden de mercado para cerrar
            result = self.place_market_order(symbol, side, size)
            
            if result["status"] == "ok":
                logger.info(f"Posición cerrada exitosamente para {symbol}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error al cerrar posición para {symbol}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "symbol": symbol
            }
    
    def convert_symbol_to_ccxt(self, asset: str) -> str:
        """
        Convierte un símbolo de activo a formato ccxt.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Símbolo en formato ccxt (ej. "BTC/USDC:USDC")
        """
        # Para Hyperliquid, la mayoría de activos se operan contra USDC
        if asset.upper() == "BTC":
            return "BTC/USDC:USDC"
        elif asset.upper() == "ETH":
            return "ETH/USDC:USDC"
        else:
            # Formato genérico para otros activos
            return f"{asset.upper()}/USDC:USDC"
    
    def execute_trade(self, asset: str, is_buy: bool, usd_amount: float, order_type: str = "market") -> Dict[str, Any]:
        """
        Ejecuta una operación de trading completa.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            is_buy: True para compra, False para venta
            usd_amount: Monto en USD a operar
            order_type: Tipo de orden ("market" o "limit")
            
        Returns:
            Resultado de la operación
        """
        try:
            # Convertir símbolo a formato ccxt
            symbol = self.convert_symbol_to_ccxt(asset)
            
            # Obtener precio actual
            current_price = self.get_market_price(symbol)
            
            # Calcular tamaño de la orden
            amount = self.calculate_order_size(usd_amount, current_price)
            
            # Determinar lado de la operación
            side = "buy" if is_buy else "sell"
            
            # Ejecutar según tipo de orden
            if order_type.lower() == "market":
                result = self.place_market_order(symbol, side, amount, current_price)
            else:
                # Para órdenes límite, ajustar precio ligeramente
                slippage = self.ccxt_config.get('default_slippage', 0.05)
                if is_buy:
                    limit_price = current_price * (1 + slippage)
                else:
                    limit_price = current_price * (1 - slippage)
                
                result = self.place_limit_order(symbol, side, amount, limit_price)
            
            # Añadir información adicional al resultado
            if result["status"] == "ok":
                result.update({
                    "asset": asset,
                    "is_buy": is_buy,
                    "usd_amount": usd_amount,
                    "current_price": current_price,
                    "calculated_amount": amount
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error al ejecutar trade para {asset}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "asset": asset,
                "is_buy": is_buy,
                "usd_amount": usd_amount
            }

