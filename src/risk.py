"""
Módulo de gestión de riesgos para el bot de trading en Hyperliquid.
Implementa la lógica para stop loss, take profit y trailing stop.
CORREGIDO: Cálculos basados en ganancia/pérdida real de la operación con apalancamiento.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("risk")

class RiskManager:
    """Clase para gestionar los riesgos del bot con estrategia optimizada para BTC."""
    
    def __init__(self, config):
        """
        Inicializa el gestor de riesgos.
        
        Args:
            config: Configuración del bot
        """
        self.config = config
        self.strategy_config = config.get_strategy_config()
        
        # Parámetros de gestión de riesgo (porcentajes de ganancia/pérdida de la operación)
        self.take_profit_percentage = self.strategy_config.get("take_profit", 2.5)  # 2.5% ganancia de la operación
        self.stop_loss_percentage = self.strategy_config.get("stop_loss", 1.25)    # 1.25% pérdida de la operación
        self.trailing_stop_activation = self.strategy_config.get("trailing_stop_activation", 1.5)  # 1.5% ganancia para activar
        self.trailing_stop_distance = self.strategy_config.get("trailing_stop_distance", 1.5)      # 1.5% distancia del trailing
        self.leverage = self.strategy_config.get("leverage", 5)
        
        # Diccionarios para seguimiento de niveles
        self.stop_loss_levels = {}
        self.take_profit_levels = {}
        self.trailing_stop_levels = {}
        
        logger.info(f"Gestor de riesgos inicializado (CORREGIDO - basado en ganancia/pérdida de operación):")
        logger.info(f"  • Take Profit: {self.take_profit_percentage}% ganancia de la operación")
        logger.info(f"  • Stop Loss: {self.stop_loss_percentage}% pérdida de la operación")
        logger.info(f"  • Trailing Stop activación: {self.trailing_stop_activation}% ganancia de la operación")
        logger.info(f"  • Trailing Stop distancia: {self.trailing_stop_distance}% de la operación")
        logger.info(f"  • Apalancamiento: {self.leverage}x")
    
    def calculate_price_levels_from_operation_pnl(self, entry_price: float, is_buy: bool, 
                                                  operation_pnl_percentage: float) -> float:
        """
        Calcula el precio objetivo basándose en el porcentaje de ganancia/pérdida deseado de la operación.
        
        Args:
            entry_price: Precio de entrada
            is_buy: True para LONG, False para SHORT
            operation_pnl_percentage: Porcentaje de ganancia/pérdida deseado de la operación
            
        Returns:
            Precio objetivo que genera el P/L deseado
        """
        # Convertir el porcentaje de ganancia/pérdida de la operación a cambio de precio necesario
        # Con apalancamiento, el cambio de precio necesario es: operation_pnl_percentage / leverage
        price_change_percentage = operation_pnl_percentage / self.leverage
        
        if is_buy:
            # Para LONG: precio objetivo = entrada * (1 + cambio_precio_porcentaje/100)
            target_price = entry_price * (1 + price_change_percentage / 100)
        else:
            # Para SHORT: precio objetivo = entrada * (1 - cambio_precio_porcentaje/100)
            target_price = entry_price * (1 - price_change_percentage / 100)
        
        return target_price
    
    def calculate_operation_pnl_percentage(self, entry_price: float, current_price: float, is_buy: bool) -> float:
        """
        Calcula el porcentaje de ganancia/pérdida actual de la operación.
        
        Args:
            entry_price: Precio de entrada
            current_price: Precio actual
            is_buy: True para LONG, False para SHORT
            
        Returns:
            Porcentaje de ganancia/pérdida de la operación
        """
        if is_buy:
            # Para LONG: ganancia cuando precio sube
            price_change_percentage = ((current_price / entry_price) - 1) * 100
        else:
            # Para SHORT: ganancia cuando precio baja
            price_change_percentage = ((entry_price / current_price) - 1) * 100
        
        # Con apalancamiento, la ganancia/pérdida de la operación se multiplica
        operation_pnl_percentage = price_change_percentage * self.leverage
        
        return operation_pnl_percentage
    
    def set_risk_levels(self, asset: str, is_buy: bool, size: float, entry_price: float) -> Dict[str, Any]:
        """
        Configura los niveles de take profit, stop loss y trailing stop para una posición.
        CORREGIDO: Basado en ganancia/pérdida real de la operación.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            is_buy: True para posiciones largas, False para cortas
            size: Tamaño de la posición
            entry_price: Precio de entrada
            
        Returns:
            Información de los niveles configurados
        """
        position_key = f"{asset}_{is_buy}_{size}"
        
        # CORREGIDO: Calcular niveles basándose en ganancia/pérdida de la operación
        
        # Stop Loss: Precio que genera la pérdida máxima permitida
        stop_level = self.calculate_price_levels_from_operation_pnl(
            entry_price, is_buy, -self.stop_loss_percentage  # Negativo para pérdida
        )
        
        # Take Profit: Precio que genera la ganancia objetivo
        take_profit_level = self.calculate_price_levels_from_operation_pnl(
            entry_price, is_buy, self.take_profit_percentage  # Positivo para ganancia
        )
        
        # Trailing Stop Activation: Precio que genera la ganancia mínima para activar trailing
        trailing_activation_level = self.calculate_price_levels_from_operation_pnl(
            entry_price, is_buy, self.trailing_stop_activation  # Positivo para ganancia
        )
        
        # Registrar stop loss
        self.stop_loss_levels[position_key] = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "entry_price": entry_price,
            "stop_level": stop_level,
            "operation_loss_percentage": self.stop_loss_percentage,
            "time": datetime.now()
        }
        
        # Registrar take profit
        self.take_profit_levels[position_key] = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "entry_price": entry_price,
            "take_profit_level": take_profit_level,
            "operation_profit_percentage": self.take_profit_percentage,
            "time": datetime.now()
        }
        
        # Registrar trailing stop (inicialmente inactivo)
        self.trailing_stop_levels[position_key] = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "entry_price": entry_price,
            "activation_level": trailing_activation_level,
            "current_level": None,  # Se establecerá cuando se active
            "is_active": False,
            "operation_activation_percentage": self.trailing_stop_activation,
            "operation_distance_percentage": self.trailing_stop_distance,
            "time": datetime.now()
        }
        
        # Calcular los cambios de precio equivalentes para logging
        if is_buy:
            stop_price_change = ((stop_level / entry_price) - 1) * 100
            tp_price_change = ((take_profit_level / entry_price) - 1) * 100
            trailing_price_change = ((trailing_activation_level / entry_price) - 1) * 100
        else:
            stop_price_change = ((entry_price / stop_level) - 1) * 100
            tp_price_change = ((entry_price / take_profit_level) - 1) * 100
            trailing_price_change = ((entry_price / trailing_activation_level) - 1) * 100
        
        logger.info(f"Niveles de riesgo configurados para {asset} {'LONG' if is_buy else 'SHORT'} (CORREGIDO):")
        logger.info(f"  • Entrada: ${entry_price:.2f}")
        logger.info(f"  • Stop Loss: ${stop_level:.2f} (operación: -{self.stop_loss_percentage}%, precio: {stop_price_change:+.2f}%)")
        logger.info(f"  • Take Profit: ${take_profit_level:.2f} (operación: +{self.take_profit_percentage}%, precio: {tp_price_change:+.2f}%)")
        logger.info(f"  • Trailing Stop activación: ${trailing_activation_level:.2f} (operación: +{self.trailing_stop_activation}%, precio: {trailing_price_change:+.2f}%)")
        
        return {
            "stop_loss": self.stop_loss_levels[position_key],
            "take_profit": self.take_profit_levels[position_key],
            "trailing_stop": self.trailing_stop_levels[position_key]
        }
    
    def check_risk_levels(self, asset: str, is_buy: bool, size: float, entry_price: float, 
                         current_price: float) -> Tuple[bool, str]:
        """
        Verifica si se ha alcanzado alguno de los niveles de riesgo (stop loss, take profit, trailing stop).
        CORREGIDO: Basado en ganancia/pérdida real de la operación.
        
        Args:
            asset: Símbolo del activo
            is_buy: True para posiciones largas, False para cortas
            size: Tamaño de la posición
            entry_price: Precio de entrada
            current_price: Precio actual
            
        Returns:
            Tupla (debe_cerrar, razón)
        """
        position_key = f"{asset}_{is_buy}_{size}"
        
        # Calcular P/L actual de la operación
        current_operation_pnl = self.calculate_operation_pnl_percentage(entry_price, current_price, is_buy)
        
        # Verificar stop loss
        if position_key in self.stop_loss_levels:
            stop_data = self.stop_loss_levels[position_key]
            target_loss = -stop_data["operation_loss_percentage"]  # Negativo
            
            if current_operation_pnl <= target_loss:
                logger.warning(f"🛑 STOP LOSS ACTIVADO para {asset}: "
                             f"P/L operación actual: {current_operation_pnl:.2f}% <= objetivo: {target_loss:.2f}%")
                return True, f"Stop Loss: P/L operación {current_operation_pnl:.2f}%"
        
        # Verificar take profit
        if position_key in self.take_profit_levels:
            tp_data = self.take_profit_levels[position_key]
            target_profit = tp_data["operation_profit_percentage"]  # Positivo
            
            if current_operation_pnl >= target_profit:
                logger.info(f"🎯 TAKE PROFIT ACTIVADO para {asset}: "
                           f"P/L operación actual: {current_operation_pnl:.2f}% >= objetivo: {target_profit:.2f}%")
                return True, f"Take Profit: P/L operación {current_operation_pnl:.2f}%"
        
        # Verificar trailing stop
        if position_key in self.trailing_stop_levels:
            trailing_data = self.trailing_stop_levels[position_key]
            activation_profit = trailing_data["operation_activation_percentage"]
            distance_percentage = trailing_data["operation_distance_percentage"]
            
            # Verificar si debe activarse el trailing stop
            if not trailing_data["is_active"] and current_operation_pnl >= activation_profit:
                # Activar trailing stop
                trailing_data["is_active"] = True
                # Establecer nivel inicial del trailing stop
                trailing_level_pnl = current_operation_pnl - distance_percentage
                trailing_data["current_level"] = trailing_level_pnl
                
                logger.info(f"📈 TRAILING STOP ACTIVADO para {asset}: "
                           f"P/L operación: {current_operation_pnl:.2f}% >= activación: {activation_profit:.2f}%")
                logger.info(f"📍 Trailing Stop inicial: {trailing_level_pnl:.2f}% P/L operación")
            
            # Si está activo, verificar si debe actualizarse o ejecutarse
            elif trailing_data["is_active"]:
                current_trailing_level = trailing_data["current_level"]
                
                # Actualizar trailing stop si el P/L ha mejorado
                new_trailing_level = current_operation_pnl - distance_percentage
                if new_trailing_level > current_trailing_level:
                    trailing_data["current_level"] = new_trailing_level
                    logger.info(f"📈 TRAILING STOP ACTUALIZADO para {asset}: "
                               f"Nuevo nivel: {new_trailing_level:.2f}% P/L operación")
                
                # Verificar si debe ejecutarse el trailing stop
                if current_operation_pnl <= current_trailing_level:
                    logger.info(f"📉 TRAILING STOP EJECUTADO para {asset}: "
                               f"P/L operación actual: {current_operation_pnl:.2f}% <= trailing: {current_trailing_level:.2f}%")
                    return True, f"Trailing Stop: P/L operación {current_operation_pnl:.2f}%"
        
        return False, ""
    
    def remove_risk_levels(self, asset: str, is_buy: bool, size: float):
        """
        Elimina los niveles de riesgo para una posición cerrada.
        
        Args:
            asset: Símbolo del activo
            is_buy: True para posiciones largas, False para cortas
            size: Tamaño de la posición
        """
        position_key = f"{asset}_{is_buy}_{size}"
        
        # Eliminar de todos los diccionarios
        self.stop_loss_levels.pop(position_key, None)
        self.take_profit_levels.pop(position_key, None)
        self.trailing_stop_levels.pop(position_key, None)
        
        logger.info(f"Niveles de riesgo eliminados para {asset} {'LONG' if is_buy else 'SHORT'}")
    
    def get_risk_summary(self, asset: str, is_buy: bool, size: float, entry_price: float, 
                        current_price: float) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado actual de los niveles de riesgo.
        CORREGIDO: Incluye información de P/L de la operación.
        
        Args:
            asset: Símbolo del activo
            is_buy: True para posiciones largas, False para cortas
            size: Tamaño de la posición
            entry_price: Precio de entrada
            current_price: Precio actual
            
        Returns:
            Resumen del estado de riesgo
        """
        position_key = f"{asset}_{is_buy}_{size}"
        
        # Calcular P/L actual de la operación
        current_operation_pnl = self.calculate_operation_pnl_percentage(entry_price, current_price, is_buy)
        
        summary = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "entry_price": entry_price,
            "current_price": current_price,
            "current_operation_pnl_percentage": current_operation_pnl,
            "stop_loss": None,
            "take_profit": None,
            "trailing_stop": None
        }
        
        # Información de stop loss
        if position_key in self.stop_loss_levels:
            sl_data = self.stop_loss_levels[position_key]
            summary["stop_loss"] = {
                "price_level": sl_data["stop_level"],
                "operation_loss_target": -sl_data["operation_loss_percentage"],
                "distance_to_trigger": current_operation_pnl - (-sl_data["operation_loss_percentage"])
            }
        
        # Información de take profit
        if position_key in self.take_profit_levels:
            tp_data = self.take_profit_levels[position_key]
            summary["take_profit"] = {
                "price_level": tp_data["take_profit_level"],
                "operation_profit_target": tp_data["operation_profit_percentage"],
                "distance_to_trigger": tp_data["operation_profit_percentage"] - current_operation_pnl
            }
        
        # Información de trailing stop
        if position_key in self.trailing_stop_levels:
            ts_data = self.trailing_stop_levels[position_key]
            summary["trailing_stop"] = {
                "activation_level": ts_data["activation_level"],
                "operation_activation_target": ts_data["operation_activation_percentage"],
                "is_active": ts_data["is_active"],
                "current_level": ts_data.get("current_level"),
                "distance_to_activation": ts_data["operation_activation_percentage"] - current_operation_pnl if not ts_data["is_active"] else None
            }
        
        return summary

