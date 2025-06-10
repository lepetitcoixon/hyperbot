"""
Módulo de gestión de órdenes para el bot de trading en Hyperliquid usando CCXT.
Implementa la estrategia optimizada para BTC con gestión de capital y órdenes.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("ccxt_orders")

class CCXTOrderManager:
    """Clase para gestionar las órdenes del bot con estrategia optimizada para BTC usando CCXT."""
    
    def __init__(self, connection, technical_analyzer, risk_manager, capital_percentage=100):
        """
        Inicializa el gestor de órdenes con CCXT.
        
        Args:
            connection: Conexión CCXT a Hyperliquid
            technical_analyzer: Analizador técnico
            risk_manager: Gestor de riesgos
            capital_percentage: Porcentaje del capital disponible a utilizar (1-100)
        """
        self.connection = connection
        self.technical_analyzer = technical_analyzer
        self.risk_manager = risk_manager
        self.capital_percentage = min(max(1, capital_percentage), 100)  # Asegurar que esté entre 1 y 100
        self.active_orders = {}  # Diccionario para seguimiento de órdenes activas
        self.active_positions = {}  # Diccionario para seguimiento de posiciones activas
        self.reserved_capital = 0.0  # Capital reservado para operaciones activas
        
        # Inicializar capital desde la API
        account_summary = self.get_account_summary()
        logger.info(f"Gestor de órdenes CCXT inicializado con estrategia optimizada para BTC. "
                   f"Capital inicial: ${account_summary['total_capital']:.2f}, "
                   f"Porcentaje de capital a utilizar: {self.capital_percentage}%")
    
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
        
        # Aplicar el porcentaje de capital configurado
        total_capital_to_use = total_capital * (self.capital_percentage / 100)
        
        # Calcular disponible restando el reservado
        available = total_capital_to_use - self.reserved_capital
        
        # Según la estrategia, si el capital total supera los $10,000, 
        # solo se operan $10,000 y el resto se guarda como excedente
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
        
        # Validar y ajustar el tamaño de la orden si es necesario
        is_valid, adjusted_size = self.connection.validate_order_size(asset, position_size)
        if not is_valid:
            logger.warning(f"Tamaño de posición ajustado de {position_size} a {adjusted_size}")
            position_size = adjusted_size
            # Recalcular capital usado
            capital_used = position_size * current_price
        
        # Colocar orden de mercado usando CCXT
        order_result = self.connection.place_market_order(
            asset=asset,
            is_buy=is_buy,
            sz=position_size
        )
        
        # Registrar orden
        if order_result.get("status") == "ok":
            order_data = order_result.get("response", {}).get("data", {}).get("statuses", [{}])[0]
            if "filled" in order_data:
                order_id = order_data["filled"]["oid"]
                fill_price = float(order_data["filled"]["price"])
                
                # Reservar capital para esta operación
                self.reserved_capital += capital_used
                
                # Registrar orden como completada directamente
                self.active_orders[order_id] = {
                    "asset": asset,
                    "is_buy": is_buy,
                    "size": position_size,
                    "price": fill_price,
                    "capital_used": capital_used,
                    "time": datetime.now(),
                    "status": "filled"
                }
                
                # Registrar posición activa
                position_key = f"{asset}_{order_id}"
                
                # Configurar niveles de riesgo (stop loss, take profit, trailing stop)
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
                    "position_key": position_key,
                    "risk_levels": risk_levels
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
        
        # Consultar estado de la orden usando CCXT
        order_status = self.connection.get_order_status(asset, order_id)
        
        # Actualizar estado en seguimiento
        if order_status:
            if "filled" in order_status:
                self.active_orders[order_id]["status"] = "filled"
                fill_price = order_status["filled"]["price"]
                self.active_orders[order_id]["fill_price"] = fill_price
                
                # Si la orden no estaba registrada como posición activa, registrarla
                position_key = f"{asset}_{order_id}"
                if position_key not in self.active_positions:
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
                        "position_key": position_key,
                        "risk_levels": risk_levels
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
        
        # Cancelar orden usando CCXT
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
        
        # Colocar orden de mercado para cierre rápido usando CCXT
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
            
            # Actualizar información de la posición para mostrar en logs
            if is_buy:  # Long position
                pnl = size * (current_price - entry_price)
                pnl_percentage = ((current_price / entry_price) - 1) * 100 * 5  # 5x leverage
            else:  # Short position
                pnl = size * (entry_price - current_price)
                pnl_percentage = ((entry_price / current_price) - 1) * 100 * 5  # 5x leverage
            
            # Actualizar cada 5 minutos (para no saturar los logs)
            last_update = position.get("last_update_time", datetime.min)
            if (datetime.now() - last_update).total_seconds() > 300:
                logger.info(f"Posición activa: {asset}, {'LONG' if is_buy else 'SHORT'}, "
                           f"entrada=${entry_price}, actual=${current_price}, "
                           f"PnL=${pnl:.2f} ({pnl_percentage:.2f}%)")
                
                # Actualizar tiempo de última actualización
                self.active_positions[position_key]["last_update_time"] = datetime.now()
        
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
            # Obtener resumen de cuenta desde CCXT
            account_summary = self.connection.get_account_summary()
            
            # Obtener valores relevantes
            total_capital = account_summary.get("total_capital", 0)
            
            # Calcular capital disponible y excedente
            available_capital = total_capital - self.reserved_capital
            
            # Según la estrategia, si el capital total supera los $10,000, 
            # solo se operan $10,000 y el resto se guarda como excedente
            excess_capital = 0.0
            if available_capital > 10000:
                excess_capital = available_capital - 10000
                available_capital = 10000
            
            # Aplicar el porcentaje de capital configurado
            available_capital = available_capital * (self.capital_percentage / 100)
            
            return {
                "total_capital": total_capital,
                "reserved_capital": self.reserved_capital,
                "available_capital": available_capital,
                "excess_capital": excess_capital,
                "active_positions": len(self.active_positions),
                "active_orders": len(self.active_orders),
                "capital_percentage": self.capital_percentage
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
                "active_orders": len(self.active_orders),
                "capital_percentage": self.capital_percentage
            }
    
    def set_capital_percentage(self, percentage: int) -> Dict[str, Any]:
        """
        Configura el porcentaje de capital a utilizar.
        
        Args:
            percentage: Porcentaje de capital a utilizar (1-100)
            
        Returns:
            Resultado de la operación
        """
        # Validar porcentaje
        if percentage < 1 or percentage > 100:
            logger.warning(f"Porcentaje de capital inválido: {percentage}. Debe estar entre 1 y 100.")
            return {"status": "error", "message": "Porcentaje de capital inválido"}
        
        # Actualizar porcentaje
        self.capital_percentage = percentage
        logger.info(f"Porcentaje de capital actualizado: {percentage}%")
        
        return {"status": "ok", "capital_percentage": percentage}

