"""
Módulo de gestión de órdenes para el bot de trading en Hyperliquid usando CCXT.
Implementa la estrategia optimizada para BTC con gestión de capital y órdenes.
CORREGIDO v4.8: Sincronización mejorada + Log de operaciones completo.
"""

import logging
import time
import json
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
        
        # NUEVO: Configurar logger de operaciones
        self.setup_operations_logger()
        
        # Inicializar capital desde la API
        account_summary = self.get_account_summary()
        logger.info(f"Gestor de órdenes CCXT inicializado con estrategia optimizada para BTC. "
                   f"Capital inicial: ${account_summary['total_capital']:.2f}, "
                   f"Porcentaje de capital a utilizar: {self.capital_percentage}%")
    
    def setup_operations_logger(self):
        """
        Configura un logger separado para el historial de operaciones.
        NUEVO: Log detallado de todas las operaciones.
        """
        # Crear timestamp para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configurar logger de operaciones
        self.operations_logger = logging.getLogger("operations_history")
        self.operations_logger.setLevel(logging.INFO)
        
        # Evitar duplicar handlers si ya existen
        if not self.operations_logger.handlers:
            # Handler para archivo de operaciones
            operations_handler = logging.FileHandler(f"logs/operations_history_{timestamp}.log")
            operations_handler.setLevel(logging.INFO)
            
            # Formato específico para operaciones
            operations_formatter = logging.Formatter('%(asctime)s - %(message)s')
            operations_handler.setFormatter(operations_formatter)
            
            self.operations_logger.addHandler(operations_handler)
            
            # Log inicial
            self.operations_logger.info("=== HISTORIAL DE OPERACIONES INICIADO ===")
            self.operations_logger.info("Formato: ACCION | Asset | Tipo | Tamaño | Precio | Capital | P/L | Razón")
            self.operations_logger.info("=" * 80)
    
    def log_operation(self, action: str, asset: str, operation_type: str, size: float, 
                     price: float, capital: float, pnl_usd: float = 0, pnl_percent: float = 0, 
                     reason: str = "", entry_price: float = 0, duration: str = ""):
        """
        Registra una operación en el log de historial.
        NUEVO: Log completo de operaciones.
        
        Args:
            action: "OPEN" o "CLOSE"
            asset: Símbolo del activo
            operation_type: "LONG" o "SHORT"
            size: Tamaño de la posición
            price: Precio de ejecución
            capital: Capital usado/liberado
            pnl_usd: P/L en dólares (solo para CLOSE)
            pnl_percent: P/L en porcentaje (solo para CLOSE)
            reason: Razón del cierre (solo para CLOSE)
            entry_price: Precio de entrada (solo para CLOSE)
            duration: Duración de la operación (solo para CLOSE)
        """
        if action == "OPEN":
            message = (f"OPEN | {asset} | {operation_type} | {size:.6f} | "
                      f"${price:.2f} | ${capital:.2f} | - | - | Señal detectada")
        else:  # CLOSE
            pnl_sign = "+" if pnl_usd >= 0 else ""
            message = (f"CLOSE | {asset} | {operation_type} | {size:.6f} | "
                      f"${price:.2f} | ${capital:.2f} | {pnl_sign}${pnl_usd:.2f} | "
                      f"{pnl_sign}{pnl_percent:.2f}% | {reason} | Entrada: ${entry_price:.2f} | {duration}")
        
        self.operations_logger.info(message)
    
    def sync_reserved_capital_with_real_positions(self) -> None:
        """
        Sincroniza el capital reservado con las posiciones reales de la cuenta.
        MEJORADO: Limpieza más agresiva de posiciones obsoletas.
        """
        try:
            # Obtener posiciones reales de la cuenta
            real_positions = self.connection.exchange.fetch_positions()
            
            # Calcular capital realmente usado
            real_reserved_capital = 0.0
            active_position_keys = []
            
            for position in real_positions:
                if position and position.get('contracts', 0) != 0:
                    # Hay una posición real abierta
                    symbol = position.get('symbol', '')
                    asset = symbol.split('/')[0] if '/' in symbol else symbol
                    contracts = float(position.get('contracts', 0))
                    is_buy = contracts > 0
                    size = abs(contracts)
                    entry_price = float(position.get('entryPrice', 0))
                    
                    # Calcular capital usado para esta posición
                    capital_used = size * entry_price
                    real_reserved_capital += capital_used
                    
                    # Crear clave de posición
                    position_key = f"{asset}_{is_buy}_{size}"
                    active_position_keys.append(position_key)
                    
                    # Si no está en nuestro registro, añadirla
                    if position_key not in self.active_positions:
                        logger.warning(f"Posición real detectada no registrada: {asset} {'LONG' if is_buy else 'SHORT'} {size}")
                        self.active_positions[position_key] = {
                            "asset": asset,
                            "is_buy": is_buy,
                            "size": size,
                            "entry_price": entry_price,
                            "capital_used": capital_used,
                            "entry_time": datetime.now(),  # Aproximado
                            "risk_levels": {}
                        }
            
            # MEJORADO: Eliminar TODAS las posiciones de nuestro registro que ya no existen
            positions_to_remove = []
            for position_key in list(self.active_positions.keys()):  # Usar list() para evitar modificar durante iteración
                if position_key not in active_position_keys:
                    position_data = self.active_positions[position_key]
                    logger.info(f"Posición cerrada detectada: {position_data['asset']} {'LONG' if position_data['is_buy'] else 'SHORT'}")
                    positions_to_remove.append(position_key)
            
            # Eliminar posiciones obsoletas
            for position_key in positions_to_remove:
                removed_position = self.active_positions.pop(position_key, None)
                if removed_position:
                    logger.info(f"Posición eliminada del registro: {position_key}")
            
            # Actualizar capital reservado
            old_reserved = self.reserved_capital
            self.reserved_capital = real_reserved_capital
            
            if abs(old_reserved - real_reserved_capital) > 1.0:  # Diferencia significativa
                logger.info(f"Capital reservado sincronizado: ${old_reserved:.2f} → ${real_reserved_capital:.2f}")
            
            # NUEVO: Log de estado de sincronización
            logger.debug(f"Sincronización completada: {len(self.active_positions)} posiciones activas, "
                        f"capital reservado: ${self.reserved_capital:.2f}")
            
        except Exception as e:
            logger.error(f"Error al sincronizar capital reservado: {str(e)}")
    
    def has_active_position_for_asset(self, asset: str) -> bool:
        """
        Verifica si hay una posición activa para un activo específico.
        NUEVO: Verificación más robusta después de sincronización.
        
        Args:
            asset: Símbolo del activo
            
        Returns:
            True si hay posición activa, False si no
        """
        # Sincronizar antes de verificar
        self.sync_reserved_capital_with_real_positions()
        
        # Verificar en registro interno
        for position_key, position_data in self.active_positions.items():
            if position_data["asset"] == asset:
                logger.debug(f"Posición activa encontrada para {asset}: {position_key}")
                return True
        
        logger.debug(f"No hay posiciones activas para {asset}")
        return False
    
    def analyze_market(self, asset: str) -> Dict[str, Any]:
        """
        Analiza el mercado para un activo y genera señales según la estrategia optimizada.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con resultados del análisis
        """
        # CORREGIDO: Usar el método get_candles de la conexión
        ohlc_data = self.connection.get_candles(asset, "5m", 100)
        
        if not ohlc_data:
            logger.error(f"No se pudieron obtener datos OHLC para {asset}")
            return {"signals": {"overall": "hold", "reason": "No hay datos disponibles"}}
        
        # Realizar análisis técnico
        analysis = self.technical_analyzer.analyze(ohlc_data)
        
        return analysis
    
    def execute_signal(self, asset: str, signal: str) -> Dict[str, Any]:
        """
        Ejecuta una señal de trading (compra o venta).
        CORREGIDO: Verificación mejorada de posiciones activas.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            signal: Tipo de señal ("buy" o "sell")
            
        Returns:
            Resultado de la ejecución
        """
        try:
            # CORREGIDO: Verificar posiciones activas con sincronización
            if self.has_active_position_for_asset(asset):
                logger.info(f"No se puede abrir nueva posición: ya existe una operación activa para {asset}")
                return {
                    "status": "skipped",
                    "message": f"Posición activa existente para {asset}"
                }
            
            # Obtener datos de mercado actuales
            market_data = self.connection.get_market_data(asset)
            if not market_data:
                logger.error(f"No se pudieron obtener datos de mercado para {asset}")
                return {
                    "status": "error",
                    "message": "No se pudieron obtener datos de mercado"
                }
            
            # Calcular tamaño de posición
            position_size, capital_used = self.technical_analyzer.calculate_position_size(
                available_capital=self.get_available_capital(),
                price=float(market_data.get("midPrice", 0))
            )
            
            if position_size <= 0:
                logger.warning(f"Tamaño de posición calculado inválido: {position_size}")
                return {
                    "status": "error",
                    "message": "Tamaño de posición inválido"
                }
            
            # Validar tamaño de orden
            is_valid, adjusted_size = self.connection.validate_order_size(asset, position_size)
            if not is_valid:
                logger.warning(f"Tamaño de orden ajustado de {position_size} a {adjusted_size}")
                position_size = adjusted_size
            
            # Determinar tipo de orden
            is_buy = signal == "buy"
            
            # Colocar orden de mercado
            order_result = self.connection.place_market_order(
                asset=asset,
                is_buy=is_buy,
                sz=position_size
            )
            
            if order_result.get("status") != "ok":
                logger.error(f"Error al colocar orden: {order_result}")
                return {
                    "status": "error",
                    "message": "Error al colocar orden",
                    "details": order_result
                }
            
            # Extraer información de la orden
            order_data = order_result.get("response", {}).get("data", {})
            statuses = order_data.get("statuses", [])
            
            if not statuses:
                logger.error("No se recibió información de estado de la orden")
                return {
                    "status": "error",
                    "message": "No se recibió información de la orden"
                }
            
            # Obtener información de la orden ejecutada
            order_info = statuses[0]
            filled_info = order_info.get("filled", {})
            
            if not filled_info:
                logger.error("La orden no se ejecutó correctamente")
                return {
                    "status": "error",
                    "message": "La orden no se ejecutó"
                }
            
            # Extraer datos de la ejecución
            executed_price = float(filled_info.get("price", market_data.get("midPrice", 0)))
            executed_size = float(filled_info.get("sz", position_size))
            
            # Calcular capital usado
            capital_used = executed_size * executed_price
            
            # Actualizar capital reservado
            self.reserved_capital += capital_used
            
            # Registrar posición activa
            position_key = f"{asset}_{is_buy}_{executed_size}"
            self.active_positions[position_key] = {
                "asset": asset,
                "is_buy": is_buy,
                "size": executed_size,
                "entry_price": executed_price,
                "capital_used": capital_used,
                "entry_time": datetime.now(),
                "risk_levels": {}
            }
            
            # Configurar niveles de riesgo
            risk_levels = self.risk_manager.set_risk_levels(
                asset=asset,
                is_buy=is_buy,
                size=executed_size,
                entry_price=executed_price
            )
            
            self.active_positions[position_key]["risk_levels"] = risk_levels
            
            # NUEVO: Log de operación abierta
            operation_type = "LONG" if is_buy else "SHORT"
            self.log_operation(
                action="OPEN",
                asset=asset,
                operation_type=operation_type,
                size=executed_size,
                price=executed_price,
                capital=capital_used
            )
            
            logger.info(f"Orden ejecutada: {asset}, {operation_type}, "
                       f"tamaño={executed_size}, precio={executed_price}, capital=${capital_used:.2f}")
            
            return {
                "status": "ok",
                "asset": asset,
                "is_buy": is_buy,
                "size": executed_size,
                "price": executed_price,
                "capital_used": capital_used,
                "position_key": position_key
            }
            
        except Exception as e:
            logger.error(f"Error al ejecutar señal: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error al ejecutar señal: {str(e)}"
            }
    
    def check_positions(self) -> None:
        """
        Verifica las posiciones activas y ejecuta stop loss, take profit o trailing stop si es necesario.
        CORREGIDO: Sincroniza con posiciones reales antes de verificar.
        """
        try:
            # Sincronizar con posiciones reales
            self.sync_reserved_capital_with_real_positions()
            
            if not self.active_positions:
                return
            
            positions_to_close = []
            
            for position_key, position_data in self.active_positions.items():
                asset = position_data["asset"]
                is_buy = position_data["is_buy"]
                size = position_data["size"]
                entry_price = position_data["entry_price"]
                
                # Obtener precio actual
                market_data = self.connection.get_market_data(asset)
                if not market_data:
                    logger.warning(f"No se pudo obtener precio actual para {asset}")
                    continue
                
                current_price = float(market_data.get("midPrice", 0))
                if current_price <= 0:
                    logger.warning(f"Precio actual inválido para {asset}: {current_price}")
                    continue
                
                # Verificar niveles de riesgo
                should_close, reason = self.risk_manager.check_risk_levels(
                    asset=asset,
                    is_buy=is_buy,
                    size=size,
                    entry_price=entry_price,
                    current_price=current_price
                )
                
                if should_close:
                    logger.info(f"Cerrando posición {asset} {'LONG' if is_buy else 'SHORT'}: {reason}")
                    positions_to_close.append((position_key, position_data, reason, current_price))
            
            # Cerrar posiciones que alcanzaron niveles de riesgo
            for position_key, position_data, reason, current_price in positions_to_close:
                self.close_position(position_key, reason, current_price)
                
        except Exception as e:
            logger.error(f"Error al verificar posiciones: {str(e)}", exc_info=True)
    
    def close_position(self, position_key: str, reason: str = "Manual", current_price: float = 0) -> Dict[str, Any]:
        """
        Cierra una posición específica.
        MEJORADO: Log completo de operación cerrada.
        
        Args:
            position_key: Clave de la posición a cerrar
            reason: Razón del cierre
            current_price: Precio actual (para cálculo de P/L)
            
        Returns:
            Resultado del cierre
        """
        try:
            if position_key not in self.active_positions:
                logger.warning(f"Posición {position_key} no encontrada en posiciones activas")
                return {
                    "status": "error",
                    "message": "Posición no encontrada"
                }
            
            position_data = self.active_positions[position_key]
            asset = position_data["asset"]
            is_buy = position_data["is_buy"]
            size = position_data["size"]
            entry_price = position_data["entry_price"]
            capital_used = position_data["capital_used"]
            entry_time = position_data["entry_time"]
            
            # Obtener precio actual si no se proporcionó
            if current_price <= 0:
                market_data = self.connection.get_market_data(asset)
                current_price = float(market_data.get("midPrice", 0)) if market_data else entry_price
            
            # Calcular P/L
            if is_buy:
                pnl_usd = (current_price - entry_price) * size
                pnl_percent = ((current_price / entry_price) - 1) * 100
            else:
                pnl_usd = (entry_price - current_price) * size
                pnl_percent = ((entry_price / current_price) - 1) * 100
            
            # Calcular duración
            duration = str(datetime.now() - entry_time).split('.')[0]  # Sin microsegundos
            
            # Colocar orden de cierre (opuesta a la posición)
            close_result = self.connection.place_market_order(
                asset=asset,
                is_buy=not is_buy,  # Orden opuesta
                sz=size
            )
            
            if close_result.get("status") == "ok":
                # Actualizar capital reservado
                self.reserved_capital -= capital_used
                if self.reserved_capital < 0:
                    self.reserved_capital = 0
                
                # NUEVO: Log de operación cerrada
                operation_type = "LONG" if is_buy else "SHORT"
                self.log_operation(
                    action="CLOSE",
                    asset=asset,
                    operation_type=operation_type,
                    size=size,
                    price=current_price,
                    capital=capital_used,
                    pnl_usd=pnl_usd,
                    pnl_percent=pnl_percent,
                    reason=reason,
                    entry_price=entry_price,
                    duration=duration
                )
                
                # Eliminar posición del registro
                self.active_positions.pop(position_key, None)
                
                # Eliminar niveles de riesgo
                self.risk_manager.remove_risk_levels(asset, is_buy, size)
                
                logger.info(f"Posición cerrada exitosamente: {asset} {operation_type}, "
                           f"razón: {reason}, P/L: ${pnl_usd:.2f} ({pnl_percent:.2f}%), "
                           f"duración: {duration}, capital liberado: ${capital_used:.2f}")
                
                return {
                    "status": "ok",
                    "message": f"Posición cerrada: {reason}",
                    "capital_freed": capital_used,
                    "pnl_usd": pnl_usd,
                    "pnl_percent": pnl_percent,
                    "duration": duration
                }
            else:
                logger.error(f"Error al cerrar posición {position_key}: {close_result}")
                return {
                    "status": "error",
                    "message": "Error al colocar orden de cierre",
                    "details": close_result
                }
                
        except Exception as e:
            logger.error(f"Error al cerrar posición {position_key}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error al cerrar posición: {str(e)}"
            }
    
    def get_available_capital(self) -> float:
        """
        Obtiene el capital disponible para nuevas operaciones.
        
        Returns:
            Capital disponible
        """
        account_summary = self.get_account_summary()
        return account_summary["available_capital"]
    
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
            
            # Usar capital reservado sincronizado
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
                "total_capital": 999.0,
                "reserved_capital": self.reserved_capital,
                "available_capital": 999.0 - self.reserved_capital,
                "excess_capital": 0.0,
                "active_positions": len(self.active_positions),
                "active_orders": len(self.active_orders),
                "capital_percentage": self.capital_percentage
            }
    
    def set_capital_percentage(self, percentage: int) -> Dict[str, Any]:
        """
        Configura el porcentaje de capital disponible a utilizar.
        
        Args:
            percentage: Porcentaje de capital a utilizar (1-100)
            
        Returns:
            Resultado de la configuración
        """
        if not 1 <= percentage <= 100:
            return {
                "status": "error",
                "message": "El porcentaje debe estar entre 1 y 100"
            }
        
        old_percentage = self.capital_percentage
        self.capital_percentage = percentage
        
        logger.info(f"Porcentaje de capital actualizado: {old_percentage}% → {percentage}%")
        
        return {
            "status": "ok",
            "message": f"Porcentaje de capital configurado: {percentage}%",
            "old_percentage": old_percentage,
            "new_percentage": percentage
        }

