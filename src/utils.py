"""
Utilidades generales para el bot de trading en Hyperliquid testnet.
"""

import logging
import json
import os
import time
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("utils")

def safe_request(url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, 
                headers: Optional[Dict[str, str]] = None, max_retries: int = 3, 
                retry_delay: int = 2) -> Optional[Dict[str, Any]]:
    """
    Realiza una petición HTTP con reintentos en caso de error.
    
    Args:
        url: URL de la petición
        method: Método HTTP (GET, POST, etc.)
        data: Datos para enviar en la petición
        headers: Cabeceras HTTP
        max_retries: Número máximo de reintentos
        retry_delay: Tiempo de espera entre reintentos (segundos)
        
    Returns:
        Respuesta de la petición o None en caso de error
    """
    for attempt in range(max_retries):
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                logger.error(f"Método HTTP no soportado: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error en petición HTTP (intento {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Error en petición HTTP después de {max_retries} intentos: {str(e)}")
                return None
        
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar respuesta JSON: {str(e)}")
            return None

def calculate_position_size(capital: float, price: float, leverage: float) -> float:
    """
    Calcula el tamaño de posición basado en capital, precio y apalancamiento.
    
    Args:
        capital: Capital disponible
        price: Precio del activo
        leverage: Apalancamiento a utilizar
        
    Returns:
        Tamaño de posición
    """
    return (capital * leverage) / price

def round_to_lot_size(size: float, lot_size: float) -> float:
    """
    Redondea el tamaño a un múltiplo del tamaño de lote.
    
    Args:
        size: Tamaño original
        lot_size: Tamaño de lote
        
    Returns:
        Tamaño redondeado
    """
    return round(size / lot_size) * lot_size

def format_number(number: float, decimals: int = 8) -> str:
    """
    Formatea un número con un número específico de decimales.
    
    Args:
        number: Número a formatear
        decimals: Número de decimales
        
    Returns:
        Número formateado como string
    """
    format_str = f"{{:.{decimals}f}}"
    return format_str.format(number)

def calculate_pnl(entry_price: float, current_price: float, size: float, is_long: bool) -> float:
    """
    Calcula el PnL (Profit and Loss) de una posición.
    
    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        size: Tamaño de la posición
        is_long: True si es posición larga, False si es corta
        
    Returns:
        PnL calculado
    """
    if is_long:
        return size * (current_price - entry_price)
    else:
        return size * (entry_price - current_price)

def calculate_pnl_percentage(entry_price: float, current_price: float, is_long: bool) -> float:
    """
    Calcula el PnL como porcentaje.
    
    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        is_long: True si es posición larga, False si es corta
        
    Returns:
        PnL como porcentaje
    """
    if is_long:
        return ((current_price / entry_price) - 1) * 100
    else:
        return ((entry_price / current_price) - 1) * 100

def save_trade_history(trade_data: Dict[str, Any], file_path: str) -> None:
    """
    Guarda el historial de operaciones en un archivo JSON.
    
    Args:
        trade_data: Datos de la operación
        file_path: Ruta del archivo
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Cargar historial existente o crear nuevo
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Añadir nueva operación
        history.append(trade_data)
        
        # Guardar historial actualizado
        with open(file_path, 'w') as f:
            json.dump(history, f, indent=4)
        
        logger.info(f"Historial de operaciones actualizado: {file_path}")
    
    except Exception as e:
        logger.error(f"Error al guardar historial de operaciones: {str(e)}")
