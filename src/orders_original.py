"""
Módulo de gestión de órdenes para el bot de trading en Hyperliquid.
Implementa la estrategia optimizada para BTC con gestión de capital y órdenes.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("orders")

class OrderManager:
    """Clase para gestionar las órdenes del bot con estrategia optimizada para BTC."""
    
    def __init__(self, connection, technical_analyzer, risk_manager):
        """
        Inicializa el gestor de órdenes.
        
        Args:
            connection: Conexión a Hyperliquid
            technical_analyzer: Analizador técnico
            risk_manager: Gestor de riesgos
        """
        self.connection = connection
        self.technical_analyzer = technical_analyzer
        self.risk_manager = risk_manager
        self.active_orders = {}  # Diccionario para seguimiento de órdenes activas
        self.active_positions = {}  # Diccionario para seguimiento de posiciones activas
        self.reserved_capital = 0.0  # Capital reservado para operaciones activas
        
        # Inicializar capital desde la API
        account_summary = self.get_account_summary()
        logger.info(f"Gestor de órdenes inicializado con estrategia optimizada para BTC. Capital inicial: ${account_summary['total_capital']:.2f}")
    
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
        Ejecuta una señal de trading según la estrategia optimizada.
        
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
        
        # Obtener datos de mercado
        market_data = self.connection.get_market_data(asset)
        if not market_data:
            return {"status": "error", "message": "No se pudieron obtener datos de mercado"}
        
        # Obtener precio actual
        current_price = float(market_data.get("midPrice", 0))
        if current_price <= 0:
            return {"status": "error", "message": "Precio no válido"}
        
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
        
        # Ejecutar orden según la señal
        is_buy = signal == "buy"
        
        # Calcular precio límite (ligeramente mejor que el mercado para asegurar ejecución)
        slippage_factor = 0.001  # 0.1%
        limit_price = current_price * (1 + slippage_factor) if is_buy else current_price * (1 - slippage_factor)
        
        # Colocar orden
        order_result = self.connection.place_order(
            asset=asset,
            is_buy=is_buy,
            sz=position_size,
            limit_px=limit_price,
            order_type={"limit": {"tif": "Gtc"}}
        )
        
        # Registrar orden
        if order_result.get("status") == "ok":
            order_data = order_result.get("response", {}).get("data", {}).get("statuses", [{}])[0]
            if "resting" in order_data:
                order_id = order_data["resting"]["oid"]
                
                # Reservar capital para esta operación
                self.reserved_capital += capital_used
                
                self.active_orders[order_id] = {
                    "asset": asset,
                    "is_buy": is_buy,
                    "size": position_size,
                    "price": limit_price,
                    "capital_used": capital_used,
                    "time": datetime.now(),
                    "status": "active"
                }
                
                logger.info(f"Orden colocada: {asset}, {'LONG' if is_buy else 'SHORT'}, "
                           f"tamaño={position_size}, precio={limit_price}, "
                           f"capital=${capital_used}")
                
                return {
                    "status": "ok",
                    "order_id": order_id,
                    "asset": asset,
                    "is_buy": is_buy,
                    "size": position_size,
                    "price": limit_price,
                    "capital_used": capital_used
                }
        
        logger.error(f"Error al colocar orden: {order_result}")
        return {"status": "error", "message": "Error al colocar orden", "details": order_result}
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Verifica el estado de una orden.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            Estado actualizado de la orden
        """
        if order_id not in self.active_orders:
            return {"status": "unknown", "message": "Orden no encontrada en seguimiento"}
        
        order_info = self.active_orders[order_id]
        asset = order_info["asset"]
        
        # Consultar estado de la orden
        order_status = self.connection.info.query_order_by_oid(
            self.connection.account_address, 
            order_id
        )
        
        # Actualizar estado en seguimiento
        if order_status:
            if "filled" in order_status:
                self.active_orders[order_id]["status"] = "filled"
                fill_price = order_status["filled"]["price"]
                self.active_orders[order_id]["fill_price"] = fill_price
                
                # Registrar posición activa
                position_key = f"{asset}_{order_id}"
                is_buy = order_info["is_buy"]
                size = order_info["size"]
                
                # Configurar niveles de riesgo (stop loss, take profit, trailing stop)
                risk_levels = self.risk_manager.set_risk_levels(
                    asset=asset,
                    is_buy=is_buy,
                    size=size,
                    entry_price=fill_price
                )
                
                self.active_positions[position_key] = {
                    "asset": asset,
                    "is_buy": is_buy,
                    "size": size,
                    "entry_price": fill_price,
                    "capital_used": order_info["capital_used"],
                    "entry_time": datetime.now(),
                    "order_id": order_id,
                    "position_key": position_key
                }
                
                logger.info(f"Orden {order_id} ejecutada a precio {fill_price}")
                logger.info(f"Posición activa con niveles de riesgo configurados: "
                           f"SL=${risk_levels['stop_loss']['stop_level']}, "
                           f"TP=${risk_levels['take_profit']['take_profit_level']}, "
                           f"Trailing Stop activación=${risk_levels['trailing_stop']['activation_level']}")
            
            elif "cancelled" in order_status:
                self.active_orders[order_id]["status"] = "cancelled"
                
                # Liberar capital reservado
                self.reserved_capital -= order_info.get("capital_used", 0)
                
                logger.info(f"Orden {order_id} cancelada, capital liberado: ${order_info.get('capital_used', 0)}")
        
        return {
            "order_id": order_id,
            "status": self.active_orders[order_id]["status"],
            "details": order_status
        }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancela una orden activa.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            Resultado de la cancelación
        """
        if order_id not in self.active_orders:
            return {"status": "error", "message": "Orden no encontrada en seguimiento"}
        
        order_info = self.active_orders[order_id]
        
        # Cancelar orden
        cancel_result = self.connection.cancel_order(order_info["asset"], order_id)
        
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
    
    def close_position(self, position_key: str, reason: str = "manual") -> Dict[str, Any]:
        """
        Cierra una posición existente.
        
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
        
        # Para cerrar, hacemos lo contrario de la posición original
        close_is_buy = not is_buy
        
        # Obtener precio actual
        market_data = self.connection.get_market_data(asset)
        if not market_data:
            return {"status": "error", "message": "No se pudieron obtener datos de mercado"}
        
        current_price = float(market_data.get("midPrice", 0))
        
        # Colocar orden de mercado para cierre rápido
        close_result = self.connection.place_market_order(
            asset=asset,
            is_buy=close_is_buy,
            sz=size
        )
        
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
                "reason": reason
            }
        
        logger.error(f"Error al cerrar posición: {close_result}")
        return {"status": "error", "message": "Error al cerrar posición", "details": close_result}
    
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
            
            # Obtener precio actual
            market_data = self.connection.get_market_data(asset)
            if not market_data:
                continue
            
            current_price = float(market_data.get("midPrice", 0))
            if current_price <= 0:
                continue
            
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
        
        # Cerrar posiciones que alcanzaron TP, SL o trailing stop
        for position_key, reason in positions_to_close:
            self.close_position(position_key, reason)
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de la cuenta y el estado actual desde la API de Hyperliquid.
        
        Returns:
            Diccionario con resumen de la cuenta
        """
        try:
            # Obtener estado de la cuenta desde la API
            user_state = self.connection.get_user_state()
            
            # Obtener valores de la cuenta perpetual
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            wallet_value = float(margin_summary.get("walletValue", 0))
            
            # Verificar si hay posiciones abiertas
            positions = user_state.get("assetPositions", [])
            has_positions = len(positions) > 0
            
            # Si no hay valor en la cuenta pero hay posiciones, usar un valor predeterminado
            if account_value == 0 and wallet_value == 0 and not has_positions:
                # Verificar si hay fondos en la cuenta spot
                try:
                    spot_user_state = self.connection.info.spot_user_state(self.connection.account_address)
                    spot_balances = spot_user_state.get("balances", [])
                    
                    for balance in spot_balances:
                        if balance.get("coin") == "USDC":
                            usdc_balance = float(balance.get("free", 0))
                            if usdc_balance > 0:
                                logger.info(f"Fondos encontrados en cuenta spot: {usdc_balance} USDC")
                                account_value = usdc_balance
                                break
                except Exception as e:
                    logger.error(f"Error al verificar fondos en cuenta spot: {str(e)}")
            
            # Si aún no hay valor, usar el valor de la cuenta de testnet (999 USDC)
            if account_value == 0 and wallet_value == 0:
                logger.warning("No se detectaron fondos en la API, usando valor de testnet (999 USDC)")
                account_value = 999.0
            
            # Calcular capital disponible y excedente
            total_capital = account_value
            available_capital = total_capital - self.reserved_capital
            
            # Según la estrategia, si el capital total supera los $10,000, 
            # solo se operan $10,000 y el resto se guarda como excedente
            excess_capital = 0.0
            if available_capital > 10000:
                excess_capital = available_capital - 10000
                available_capital = 10000
            
            return {
                "total_capital": total_capital,
                "reserved_capital": self.reserved_capital,
                "available_capital": available_capital,
                "excess_capital": excess_capital,
                "active_positions": len(self.active_positions),
                "active_orders": len(self.active_orders)
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen de cuenta: {str(e)}")
            # En caso de error, devolver valores predeterminados
            return {
                "total_capital": 999.0,  # Valor predeterminado para testnet
                "reserved_capital": self.reserved_capital,
                "available_capital": 999.0 - self.reserved_capital,
                "excess_capital": 0.0,
                "active_positions": len(self.active_positions),
                "active_orders": len(self.active_orders)
            }
