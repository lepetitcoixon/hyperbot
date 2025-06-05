"""
Módulo de gestión de órdenes para el bot de trading en Hyperliquid.
Implementa la estrategia optimizada para BTC con gestión de capital y órdenes.
Versión actualizada con integración de ccxt para mejorar la confiabilidad de las operaciones.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .ccxt_trader import CCXTTrader

logger = logging.getLogger("orders")

class OrderManager:
    """Clase para gestionar las órdenes del bot con estrategia optimizada para BTC usando ccxt."""
    
    def __init__(self, connection, technical_analyzer, risk_manager, config):
        """
        Inicializa el gestor de órdenes.
        
        Args:
            connection: Conexión a Hyperliquid (para datos de mercado)
            technical_analyzer: Analizador técnico
            risk_manager: Gestor de riesgos
            config: Configuración del bot
        """
        self.connection = connection
        self.technical_analyzer = technical_analyzer
        self.risk_manager = risk_manager
        self.config = config
        self.active_orders = {}  # Diccionario para seguimiento de órdenes activas
        self.active_positions = {}  # Diccionario para seguimiento de posiciones activas
        self.reserved_capital = 0.0  # Capital reservado para operaciones activas
        
        # Inicializar CCXTTrader para operaciones de trading
        auth_config = config.get('auth', {})
        wallet_address = auth_config.get('account_address')
        private_key = auth_config.get('secret_key')
        
        if not wallet_address or not private_key:
            raise ValueError("Credenciales de autenticación no configuradas")
        
        self.ccxt_trader = CCXTTrader(wallet_address, private_key, config)
        
        # Inicializar capital desde la API
        account_summary = self.get_account_summary()
        logger.info(f"Gestor de órdenes inicializado con ccxt. Capital inicial: ${account_summary['total_capital']:.2f}")
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de la cuenta usando ccxt.
        
        Returns:
            Resumen de la cuenta con capital total y disponible
        """
        try:
            # Obtener balance usando ccxt
            balance_result = self.ccxt_trader.get_balance()
            
            if balance_result["status"] != "ok":
                logger.error(f"Error al obtener balance: {balance_result['message']}")
                return {"total_capital": 0.0, "available_capital": 0.0}
            
            balance = balance_result["balance"]
            total_balance = balance.get("total", {})
            free_balance = balance.get("free", {})
            
            # Calcular capital total (principalmente USDC)
            total_capital = float(total_balance.get("USDC", 0))
            available_capital = float(free_balance.get("USDC", 0))
            
            return {
                "total_capital": total_capital,
                "available_capital": available_capital,
                "balance_details": balance
            }
            
        except Exception as e:
            logger.error(f"Error al obtener resumen de cuenta: {str(e)}")
            return {"total_capital": 0.0, "available_capital": 0.0}
    
    def analyze_market(self, asset: str) -> Dict[str, Any]:
        """
        Analiza el mercado para un activo y genera señales según la estrategia optimizada.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con resultados del análisis
        """
        # Obtener datos de velas (timeframe de 5 minutos según la estrategia)
        candles = self.connection.get_candles(asset, interval="5m", limit=100)
        
        # Realizar análisis técnico con la estrategia optimizada
        analysis = self.technical_analyzer.analyze(candles)
        
        if analysis.get('signals', {}).get('overall'):
            logger.info(f"Análisis de mercado para {asset}: {analysis.get('signals', {}).get('overall')}")
            logger.info(f"Razón: {analysis.get('signals', {}).get('reason')}")
        
        return analysis
    
    def can_open_new_position(self) -> bool:
        """
        Verifica si se puede abrir una nueva posición según la estrategia.
        
        Returns:
            True si se puede abrir una nueva posición, False en caso contrario
        """
        # Según la estrategia, solo se permite una operación simultánea
        return len(self.active_positions) == 0
    
    def get_available_capital(self) -> float:
        """
        Calcula el capital disponible para nuevas operaciones.
        
        Returns:
            Capital disponible
        """
        # Obtener capital total actual desde la API
        account_summary = self.get_account_summary()
        total_capital = account_summary["total_capital"]
        
        # Según la estrategia, si el capital total supera los $10,000, 
        # solo se operan $10,000 y el resto se guarda como excedente
        available = total_capital - self.reserved_capital
        
        excess_capital = 0.0
        if available > 10000:
            excess_capital = available - 10000
            available = 10000
        
        return available
    
    def execute_signal(self, asset: str, signal: str) -> Dict[str, Any]:
        """
        Ejecuta una señal de trading según la estrategia optimizada usando ccxt.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            signal: Señal de trading ("buy" o "sell")
            
        Returns:
            Resultado de la operación
        """
        if signal not in ["buy", "sell"]:
            logger.warning(f"Señal no válida: {signal}")
            return {"status": "error", "message": "Señal no válida"}
        
        # Verificar si se puede abrir una nueva posición
        if not self.can_open_new_position():
            logger.info("No se puede abrir nueva posición: ya existe una operación activa")
            return {"status": "skipped", "message": "Ya existe una operación activa"}
        
        # Obtener precio actual usando ccxt
        try:
            symbol = self.ccxt_trader.convert_symbol_to_ccxt(asset)
            current_price = self.ccxt_trader.get_market_price(symbol)
        except Exception as e:
            logger.error(f"Error al obtener precio de mercado: {str(e)}")
            return {"status": "error", "message": "No se pudo obtener precio de mercado"}
        
        # Obtener capital disponible
        available_capital = self.get_available_capital()
        if available_capital <= 0:
            return {"status": "error", "message": "No hay capital disponible"}
        
        # Calcular tamaño de posición y capital a utilizar
        position_size, capital_used = self.technical_analyzer.calculate_position_size(
            available_capital=available_capital,
            price=current_price
        )
        
        # Verificar si el tamaño es válido
        if position_size <= 0:
            return {"status": "error", "message": "Tamaño de posición no válido"}
        
        # Ejecutar orden usando ccxt
        is_buy = signal == "buy"
        
        # Usar orden de mercado para ejecución rápida y confiable
        order_result = self.ccxt_trader.execute_trade(
            asset=asset,
            is_buy=is_buy,
            usd_amount=capital_used,
            order_type="market"
        )
        
        # Registrar orden
        if order_result.get("status") == "ok":
            order_id = order_result.get("order_id")
            
            # Reservar capital para esta operación
            self.reserved_capital += capital_used
            
            self.active_orders[order_id] = {
                "asset": asset,
                "is_buy": is_buy,
                "size": position_size,
                "price": current_price,
                "capital_used": capital_used,
                "time": datetime.now(),
                "status": "filled",  # Las órdenes de mercado se ejecutan inmediatamente
                "order_result": order_result
            }
            
            # Como es orden de mercado, registrar inmediatamente como posición activa
            position_key = f"{asset}_{order_id}"
            fill_price = order_result.get("price", current_price)
            
            # Configurar niveles de riesgo
            risk_levels = self.risk_manager.set_risk_levels(
                asset=asset,
                is_buy=is_buy,
                size=position_size,
                entry_price=fill_price
            )
            
            self.active_positions[position_key] = {
                "asset": asset,
                "is_buy": is_buy,
                "size": position_size,
                "entry_price": fill_price,
                "capital_used": capital_used,
                "entry_time": datetime.now(),
                "order_id": order_id,
                "position_key": position_key
            }
            
            logger.info(f"Orden ejecutada: {asset}, {'LONG' if is_buy else 'SHORT'}, "
                       f"tamaño={position_size}, precio={fill_price}, "
                       f"capital=${capital_used}")
            logger.info(f"Posición activa con niveles de riesgo configurados: "
                       f"SL=${risk_levels['stop_loss']['stop_level']}, "
                       f"TP=${risk_levels['take_profit']['take_profit_level']}, "
                       f"Trailing Stop activación=${risk_levels['trailing_stop']['activation_level']}")
            
            return {
                "status": "ok",
                "order_id": order_id,
                "asset": asset,
                "is_buy": is_buy,
                "size": position_size,
                "price": fill_price,
                "capital_used": capital_used,
                "position_key": position_key
            }
        
        logger.error(f"Error al colocar orden: {order_result}")
        return {"status": "error", "message": "Error al colocar orden", "details": order_result}
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Verifica el estado de una orden usando ccxt.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            Estado actualizado de la orden
        """
        if order_id not in self.active_orders:
            return {"status": "unknown", "message": "Orden no encontrada en seguimiento"}
        
        order_info = self.active_orders[order_id]
        asset = order_info["asset"]
        
        try:
            # Consultar estado usando ccxt
            symbol = self.ccxt_trader.convert_symbol_to_ccxt(asset)
            status_result = self.ccxt_trader.get_order_status(order_id, symbol)
            
            if status_result["status"] == "ok":
                order_status = status_result["order_status"]
                
                # Actualizar estado en seguimiento
                if order_status == "closed":
                    self.active_orders[order_id]["status"] = "filled"
                    fill_price = status_result.get("average", order_info["price"])
                    self.active_orders[order_id]["fill_price"] = fill_price
                    
                    logger.info(f"Orden {order_id} ejecutada a precio {fill_price}")
                
                elif order_status == "canceled":
                    self.active_orders[order_id]["status"] = "cancelled"
                    
                    # Liberar capital reservado
                    self.reserved_capital -= order_info.get("capital_used", 0)
                    
                    logger.info(f"Orden {order_id} cancelada, capital liberado: ${order_info.get('capital_used', 0)}")
            
            return {
                "order_id": order_id,
                "status": self.active_orders[order_id]["status"],
                "details": status_result
            }
            
        except Exception as e:
            logger.error(f"Error al verificar estado de orden {order_id}: {str(e)}")
            return {
                "order_id": order_id,
                "status": "error",
                "message": str(e)
            }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancela una orden activa usando ccxt.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            Resultado de la cancelación
        """
        if order_id not in self.active_orders:
            return {"status": "error", "message": "Orden no encontrada en seguimiento"}
        
        order_info = self.active_orders[order_id]
        asset = order_info["asset"]
        
        try:
            # Cancelar orden usando ccxt
            symbol = self.ccxt_trader.convert_symbol_to_ccxt(asset)
            cancel_result = self.ccxt_trader.cancel_order(order_id, symbol)
            
            # Actualizar estado en seguimiento
            if cancel_result.get("status") == "ok":
                self.active_orders[order_id]["status"] = "cancelled"
                
                # Liberar capital reservado
                self.reserved_capital -= order_info.get("capital_used", 0)
                
                logger.info(f"Orden {order_id} cancelada exitosamente")
                logger.info(f"Capital liberado: ${order_info.get('capital_used', 0)}")
                
                return {"status": "ok", "order_id": order_id}
            
            logger.error(f"Error al cancelar orden {order_id}: {cancel_result}")
            return {"status": "error", "message": "Error al cancelar orden", "details": cancel_result}
            
        except Exception as e:
            logger.error(f"Error al cancelar orden {order_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def close_position(self, position_key: str, reason: str = "manual") -> Dict[str, Any]:
        """
        Cierra una posición existente usando ccxt.
        
        Args:
            position_key: Clave de la posición a cerrar
            reason: Razón del cierre (manual, take_profit, stop_loss, trailing_stop)
            
        Returns:
            Resultado del cierre de posición
        """
        if position_key not in self.active_positions:
            return {"status": "error", "message": "Posición no encontrada"}
        
        position = self.active_positions[position_key]
        asset = position["asset"]
        is_buy = position["is_buy"]
        size = position["size"]
        entry_price = position["entry_price"]
        capital_used = position["capital_used"]
        
        try:
            # Obtener precio actual
            symbol = self.ccxt_trader.convert_symbol_to_ccxt(asset)
            current_price = self.ccxt_trader.get_market_price(symbol)
            
            # Cerrar posición usando ccxt (orden de mercado para cierre rápido)
            close_result = self.ccxt_trader.close_position(symbol, size)
            
            if close_result.get("status") == "ok":
                # Calcular PnL
                if is_buy:  # Long position
                    pnl = size * (current_price - entry_price)
                    pnl_percentage = ((current_price / entry_price) - 1) * 100 * 5  # 5x leverage
                else:  # Short position
                    pnl = size * (entry_price - current_price)
                    pnl_percentage = ((entry_price / current_price) - 1) * 100 * 5  # 5x leverage
                
                # Liberar capital reservado
                self.reserved_capital -= capital_used
                
                logger.info(f"Posición cerrada: {asset}, {'LONG' if is_buy else 'SHORT'}, "
                           f"entrada=${entry_price}, salida=${current_price}, "
                           f"PnL=${pnl:.2f} ({pnl_percentage:.2f}%), razón: {reason}")
                
                # Limpiar datos de riesgo
                self.risk_manager.clear_position_data(position_key)
                
                # Eliminar posición de activas
                del self.active_positions[position_key]
                
                return {
                    "status": "ok", 
                    "asset": asset, 
                    "pnl": pnl,
                    "pnl_percentage": pnl_percentage,
                    "reason": reason,
                    "close_result": close_result
                }
            
            logger.error(f"Error al cerrar posición: {close_result}")
            return {"status": "error", "message": "Error al cerrar posición", "details": close_result}
            
        except Exception as e:
            logger.error(f"Error al cerrar posición {position_key}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def check_positions(self) -> None:
        """
        Verifica todas las posiciones activas para take profit, stop loss y trailing stop.
        """
        if not self.active_positions:
            return
        
        positions_to_close = []
        
        for position_key, position in self.active_positions.items():
            asset = position["asset"]
            is_buy = position["is_buy"]
            size = position["size"]
            entry_price = position["entry_price"]
            
            try:
                # Obtener precio actual usando ccxt
                symbol = self.ccxt_trader.convert_symbol_to_ccxt(asset)
                current_price = self.ccxt_trader.get_market_price(symbol)
                
                # Verificar niveles de riesgo (stop loss, take profit, trailing stop)
                should_close, reason = self.risk_manager.check_risk_levels(
                    asset=asset,
                    is_buy=is_buy,
                    size=size,
                    entry_price=entry_price,
                    current_price=current_price
                )
                
                if should_close:
                    positions_to_close.append((position_key, reason))
                    
            except Exception as e:
                logger.error(f"Error al verificar posición {position_key}: {str(e)}")
        
        # Cerrar posiciones que alcanzaron TP, SL o trailing stop
        for position_key, reason in positions_to_close:
            self.close_position(position_key, reason)
    
    def get_active_positions_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de las posiciones activas.
        
        Returns:
            Resumen de posiciones activas
        """
        if not self.active_positions:
            return {"count": 0, "positions": []}
        
        positions_summary = []
        total_unrealized_pnl = 0.0
        
        for position_key, position in self.active_positions.items():
            asset = position["asset"]
            is_buy = position["is_buy"]
            size = position["size"]
            entry_price = position["entry_price"]
            capital_used = position["capital_used"]
            
            try:
                # Obtener precio actual
                symbol = self.ccxt_trader.convert_symbol_to_ccxt(asset)
                current_price = self.ccxt_trader.get_market_price(symbol)
                
                # Calcular PnL no realizado
                if is_buy:
                    unrealized_pnl = size * (current_price - entry_price)
                    pnl_percentage = ((current_price / entry_price) - 1) * 100 * 5
                else:
                    unrealized_pnl = size * (entry_price - current_price)
                    pnl_percentage = ((entry_price / current_price) - 1) * 100 * 5
                
                total_unrealized_pnl += unrealized_pnl
                
                positions_summary.append({
                    "position_key": position_key,
                    "asset": asset,
                    "side": "LONG" if is_buy else "SHORT",
                    "size": size,
                    "entry_price": entry_price,
                    "current_price": current_price,
                    "capital_used": capital_used,
                    "unrealized_pnl": unrealized_pnl,
                    "pnl_percentage": pnl_percentage,
                    "entry_time": position["entry_time"]
                })
                
            except Exception as e:
                logger.error(f"Error al calcular PnL para posición {position_key}: {str(e)}")
                positions_summary.append({
                    "position_key": position_key,
                    "asset": asset,
                    "side": "LONG" if is_buy else "SHORT",
                    "size": size,
                    "entry_price": entry_price,
                    "current_price": "Error",
                    "capital_used": capital_used,
                    "unrealized_pnl": "Error",
                    "pnl_percentage": "Error",
                    "entry_time": position["entry_time"]
                })
        
        return {
            "count": len(positions_summary),
            "positions": positions_summary,
            "total_unrealized_pnl": total_unrealized_pnl
        }
    
    def cleanup_completed_orders(self) -> None:
        """
        Limpia órdenes completadas o canceladas del seguimiento.
        """
        completed_orders = []
        
        for order_id, order_info in self.active_orders.items():
            if order_info["status"] in ["filled", "cancelled"]:
                completed_orders.append(order_id)
        
        for order_id in completed_orders:
            del self.active_orders[order_id]
            logger.debug(f"Orden {order_id} removida del seguimiento")
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del estado del trading.
        
        Returns:
            Resumen completo del estado
        """
        account_summary = self.get_account_summary()
        positions_summary = self.get_active_positions_summary()
        
        return {
            "account": account_summary,
            "positions": positions_summary,
            "active_orders": len(self.active_orders),
            "reserved_capital": self.reserved_capital,
            "available_capital": self.get_available_capital()
        }

