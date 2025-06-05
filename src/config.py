"""
Módulo de configuración para el bot de trading en Hyperliquid.
Gestiona la carga y validación de parámetros de configuración.
"""

import json
import os
import logging
from typing import Dict, Any, List

# Configurar logging
# Asegurar que el directorio de logs exista
import os
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "bot.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("config")

class Config:
    """Clase para gestionar la configuración del bot."""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa la configuración del bot.
        
        Args:
            config_path: Ruta al archivo de configuración principal
        """
        # Buscar el archivo config.json en varias ubicaciones posibles si no se especifica
        if config_path is None:
            possible_paths = [
                # Ruta relativa al módulo actual
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json"),
                # Ruta relativa al directorio de trabajo
                os.path.join(os.getcwd(), "config", "config.json"),
                # Directorio actual + hyperliquid_bot
                os.path.join(os.getcwd(), "hyperliquid_bot", "config", "config.json"),
                # Directorio actual + hyperliquid_bot_final
                os.path.join(os.getcwd(), "hyperliquid_bot_final", "config", "config.json"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    logger.info(f"Usando archivo de configuración: {config_path}")
                    break
            
            if config_path is None:
                logger.error("No se pudo encontrar el archivo config.json")
                logger.error("Por favor, asegúrese de que el archivo config.json existe en alguna de estas ubicaciones:")
                for path in possible_paths:
                    logger.error(f"  - {path}")
                raise FileNotFoundError("No se pudo encontrar el archivo config.json")
        
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self._validate_config()
        
        # Configurar nivel de logging
        log_level = getattr(logging, self.config.get("general", {}).get("log_level", "INFO"))
        logging.getLogger().setLevel(log_level)
        
        logger.info("Configuración cargada correctamente")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo JSON.
        
        Args:
            config_path: Ruta al archivo de configuración
            
        Returns:
            Diccionario con la configuración
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Archivo de configuración cargado: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error al cargar la configuración: {str(e)}")
            raise
    
    def _validate_config(self) -> None:
        """Valida que la configuración tenga todos los campos requeridos."""
        required_sections = ["general", "strategy", "technical_analysis", "auth"]
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Sección requerida no encontrada en la configuración: {section}")
                raise ValueError(f"Sección requerida no encontrada en la configuración: {section}")
    
    def get_general_config(self) -> Dict[str, Any]:
        """Retorna la configuración general."""
        return self.config["general"]
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Retorna la configuración de la estrategia."""
        return self.config["strategy"]
    
    def get_technical_analysis_config(self) -> Dict[str, Any]:
        """Retorna la configuración del análisis técnico."""
        return self.config["technical_analysis"]
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Retorna la configuración de autenticación."""
        return self.config["auth"]
