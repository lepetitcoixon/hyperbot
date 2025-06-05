#!/usr/bin/env python3
"""
Script de prueba para validar la conexión a Hyperliquid y la obtención de metadatos.
"""

import logging
import sys
import os
import json
from src.connection import HyperliquidConnection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_connection")

def load_config():
    """Carga la configuración desde config.json."""
    config_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json"),
        os.path.join(os.getcwd(), "config", "config.json"),
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            logger.info(f"Cargando configuración desde: {config_path}")
            with open(config_path, "r") as f:
                return json.load(f)
    
    logger.error("No se encontró el archivo de configuración.")
    return None

def main():
    """Función principal."""
    logger.info("Iniciando prueba de conexión a Hyperliquid")
    
    # Cargar configuración
    config = load_config()
    if not config:
        logger.error("No se pudo cargar la configuración.")
        return
    
    # Obtener credenciales
    auth_config = config.get("auth", {})
    account_address = auth_config.get("account_address")
    secret_key = auth_config.get("secret_key")
    
    if not account_address or not secret_key:
        logger.error("Credenciales incompletas en el archivo de configuración.")
        return
    
    # Obtener URL base
    general_config = config.get("general", {})
    base_url = general_config.get("base_url")
    
    # Inicializar conexión
    try:
        logger.info("Inicializando conexión a Hyperliquid...")
        connection = HyperliquidConnection(
            account_address=account_address,
            secret_key=secret_key,
            base_url=base_url
        )
        logger.info("Conexión inicializada correctamente.")
        
        # Probar obtención de metadatos para BTC
        logger.info("Obteniendo metadatos para BTC...")
        btc_metadata = connection.get_market_metadata("BTC")
        logger.info(f"Metadatos de BTC: {json.dumps(btc_metadata, indent=2)}")
        
        # Probar obtención de tamaño mínimo
        logger.info("Obteniendo tamaño mínimo de orden para BTC...")
        min_size = connection.get_min_order_size("BTC")
        logger.info(f"Tamaño mínimo de orden para BTC: {min_size}")
        
        # Probar validación de tamaño
        test_size = 0.0005
        logger.info(f"Validando tamaño de orden: {test_size}...")
        is_valid, adjusted_size = connection.validate_order_size("BTC", test_size)
        logger.info(f"Resultado de validación: válido={is_valid}, tamaño ajustado={adjusted_size}")
        
        logger.info("Prueba completada con éxito.")
        
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
