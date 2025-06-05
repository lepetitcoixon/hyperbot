"""
Módulo de gestión de riesgos para el bot de trading en Hyperliquid.
Implementa la lógica para stop loss, take profit y trailing stop.
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
        
        # Parámetros de gestión de riesgo actualizados
        self.take_profit_percentage = self.strategy_config.get("take_profit", 5.3)
        self.stop_loss_percentage = self.strategy_config.get("stop_loss", 1.25)
        self.trailing_stop_activation = self.strategy_config.get("trailing_stop_activation", 1.5)
        self.trailing_stop_distance = self.strategy_config.get("trailing_stop_distance", 1.5)
        self.leverage = self.strategy_config.get("leverage", 5)
        
        # Diccionarios para seguimiento de niveles
        self.stop_loss_levels = {}
        self.take_profit_levels = {}
        self.trailing_stop_levels = {}
        
        logger.info(f"Gestor de riesgos inicializado: take profit={self.take_profit_percentage}%, "
                   f"stop loss={self.stop_loss_percentage}%, "
                   f"trailing stop activación={self.trailing_stop_activation}%, "
                   f"trailing stop distancia={self.trailing_stop_distance}%, "
                   f"apalancamiento={self.leverage}x")
    
    def set_risk_levels(self, asset: str, is_buy: bool, size: float, entry_price: float) -> Dict[str, Any]:
        """
        Configura los niveles de take profit, stop loss y trailing stop para una posición.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            is_buy: True para posiciones largas, False para cortas
            size: Tamaño de la posición
            entry_price: Precio de entrada
            
        Returns:
            Información de los niveles configurados
        """
        position_key = f"{asset}_{is_buy}_{size}"
        
        # Calcular nivel de stop loss
        if is_buy:
            # Para posiciones largas, el stop loss está por debajo del precio de entrada
            stop_level = entry_price * (1 - self.stop_loss_percentage / 100)
            # Para posiciones largas, el take profit está por encima del precio de entrada
            take_profit_level = entry_price * (1 + self.take_profit_percentage / 100)
            # Nivel de activación del trailing stop
            trailing_activation_level = entry_price * (1 + self.trailing_stop_activation / 100)
        else:
            # Para posiciones cortas, el stop loss está por encima del precio de entrada
            stop_level = entry_price * (1 + self.stop_loss_percentage / 100)
            # Para posiciones cortas, el take profit está por debajo del precio de entrada
            take_profit_level = entry_price * (1 - self.take_profit_percentage / 100)
            # Nivel de activación del trailing stop
            trailing_activation_level = entry_price * (1 - self.trailing_stop_activation / 100)
        
        # Registrar stop loss
        self.stop_loss_levels[position_key] = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "entry_price": entry_price,
            "stop_level": stop_level,
            "time": datetime.now()
        }
        
        # Registrar take profit
        self.take_profit_levels[position_key] = {
            "asset": asset,
            "is_buy": is_buy,
            "size": size,
            "entry_price": entry_price,
            "take_profit_level": take_profit_level,
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
            "time": datetime.now()
        }
        
        logger.info(f"Niveles de riesgo configurados para {asset} {'LONG' if is_buy else 'SHORT'}: "
                   f"entrada=${entry_price}, stop loss=${stop_level} ({self.stop_loss_percentage}%), "
                   f"take profit=${take_profit_level} ({self.take_profit_percentage}%), "
                   f"trailing stop activación=${trailing_activation_level} ({self.trailing_stop_activation}%)")
        
        return {
            "stop_loss": self.stop_loss_levels[position_key],
            "take_profit": self.take_profit_levels[position_key],
            "trailing_stop": self.trailing_stop_levels[position_key]
        }
    
    def check_risk_levels(self, asset: str, is_buy: bool, size: float, entry_price: float, 
                         current_price: float) -> Tuple[bool, str]:
        """
        Verifica si se ha alcanzado alguno de los niveles de riesgo (stop loss, take profit, trailing stop).
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            is_buy: True para posiciones largas, False para cortas
            size: Tamaño de la posición
            entry_price: Precio de entrada
            current_price: Precio actual
            
        Returns:
            Tupla con (cerrar_posición, razón)
        """
        position_key = f"{asset}_{is_buy}_{size}"
        
        # Si no hay niveles configurados, configurarlos ahora
        if position_key not in self.stop_loss_levels:
            self.set_risk_levels(asset, is_buy, size, entry_price)
        
        # Obtener niveles configurados
        stop_level = self.stop_loss_levels[position_key]["stop_level"]
        take_profit_level = self.take_profit_levels[position_key]["take_profit_level"]
        trailing_stop_info = self.trailing_stop_levels[position_key]
        
        # Verificar si se ha alcanzado el nivel de take profit
        if is_buy:
            # Para posiciones largas
            if current_price >= take_profit_level:
                logger.info(f"Take profit alcanzado para {asset} LONG: "
                           f"precio actual=${current_price}, take profit=${take_profit_level}")
                return True, "take_profit"
        else:
            # Para posiciones cortas
            if current_price <= take_profit_level:
                logger.info(f"Take profit alcanzado para {asset} SHORT: "
                           f"precio actual=${current_price}, take profit=${take_profit_level}")
                return True, "take_profit"
        
        # Verificar y actualizar trailing stop
        trailing_stop_triggered = self._check_and_update_trailing_stop(
            position_key, is_buy, current_price, entry_price)
        
        if trailing_stop_triggered:
            return True, "trailing_stop"
        
        # Verificar si se ha alcanzado el nivel de stop loss
        if is_buy:
            # Para posiciones largas, cerrar si el precio cae por debajo del stop
            if current_price <= stop_level:
                logger.warning(f"Stop loss activado para {asset} LONG: "
                              f"precio actual=${current_price}, stop=${stop_level}")
                return True, "stop_loss"
        else:
            # Para posiciones cortas, cerrar si el precio sube por encima del stop
            if current_price >= stop_level:
                logger.warning(f"Stop loss activado para {asset} SHORT: "
                              f"precio actual=${current_price}, stop=${stop_level}")
                return True, "stop_loss"
        
        return False, ""
    
    def _check_and_update_trailing_stop(self, position_key: str, is_buy: bool, 
                                       current_price: float, entry_price: float) -> bool:
        """
        Verifica y actualiza el trailing stop para una posición.
        
        Args:
            position_key: Clave de la posición
            is_buy: True para posiciones largas, False para cortas
            current_price: Precio actual
            entry_price: Precio de entrada
            
        Returns:
            True si se debe cerrar la posición por trailing stop, False en caso contrario
        """
        if position_key not in self.trailing_stop_levels:
            return False
        
        trailing_info = self.trailing_stop_levels[position_key]
        activation_level = trailing_info["activation_level"]
        
        # Verificar si el trailing stop ya está activo
        if trailing_info["is_active"]:
            current_trailing_level = trailing_info["current_level"]
            
            # Verificar si se ha alcanzado el nivel de trailing stop
            if is_buy:
                # Para posiciones largas
                if current_price <= current_trailing_level:
                    logger.info(f"Trailing stop activado para {trailing_info['asset']} LONG: "
                               f"precio actual=${current_price}, nivel=${current_trailing_level}")
                    return True
                
                # Actualizar nivel de trailing stop si el precio sube
                potential_new_level = current_price * (1 - self.trailing_stop_distance / 100)
                if potential_new_level > current_trailing_level:
                    trailing_info["current_level"] = potential_new_level
                    logger.info(f"Trailing stop actualizado para {trailing_info['asset']} LONG: "
                               f"nuevo nivel=${potential_new_level}")
            else:
                # Para posiciones cortas
                if current_price >= current_trailing_level:
                    logger.info(f"Trailing stop activado para {trailing_info['asset']} SHORT: "
                               f"precio actual=${current_price}, nivel=${current_trailing_level}")
                    return True
                
                # Actualizar nivel de trailing stop si el precio baja
                potential_new_level = current_price * (1 + self.trailing_stop_distance / 100)
                if potential_new_level < current_trailing_level:
                    trailing_info["current_level"] = potential_new_level
                    logger.info(f"Trailing stop actualizado para {trailing_info['asset']} SHORT: "
                               f"nuevo nivel=${potential_new_level}")
        else:
            # Verificar si se debe activar el trailing stop
            if is_buy:
                # Para posiciones largas, activar si el precio supera el nivel de activación
                if current_price >= activation_level:
                    # Activar trailing stop
                    trailing_info["is_active"] = True
                    # Establecer nivel inicial de trailing stop
                    trailing_info["current_level"] = current_price * (1 - self.trailing_stop_distance / 100)
                    logger.info(f"Trailing stop activado para {trailing_info['asset']} LONG: "
                               f"nivel inicial=${trailing_info['current_level']}")
            else:
                # Para posiciones cortas, activar si el precio cae por debajo del nivel de activación
                if current_price <= activation_level:
                    # Activar trailing stop
                    trailing_info["is_active"] = True
                    # Establecer nivel inicial de trailing stop
                    trailing_info["current_level"] = current_price * (1 + self.trailing_stop_distance / 100)
                    logger.info(f"Trailing stop activado para {trailing_info['asset']} SHORT: "
                               f"nivel inicial=${trailing_info['current_level']}")
        
        return False
    
    def clear_position_data(self, position_key: str) -> None:
        """
        Elimina los datos de una posición cerrada.
        
        Args:
            position_key: Clave de la posición
        """
        if position_key in self.stop_loss_levels:
            del self.stop_loss_levels[position_key]
        
        if position_key in self.take_profit_levels:
            del self.take_profit_levels[position_key]
        
        if position_key in self.trailing_stop_levels:
            del self.trailing_stop_levels[position_key]
        
        logger.info(f"Datos de posición {position_key} eliminados")
    
    def get_risk_levels(self, position_key: str) -> Dict[str, Any]:
        """
        Obtiene los niveles de riesgo configurados para una posición.
        
        Args:
            position_key: Clave de la posición
            
        Returns:
            Diccionario con los niveles de riesgo
        """
        result = {}
        
        if position_key in self.stop_loss_levels:
            result["stop_loss"] = self.stop_loss_levels[position_key]
        
        if position_key in self.take_profit_levels:
            result["take_profit"] = self.take_profit_levels[position_key]
        
        if position_key in self.trailing_stop_levels:
            result["trailing_stop"] = self.trailing_stop_levels[position_key]
        
        return result
