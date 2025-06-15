"""
Módulo de análisis técnico para el bot de trading en Hyperliquid.
Implementa la estrategia optimizada para BTC con indicadores técnicos específicos.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("technical")

class TechnicalAnalysis:
    """Clase para realizar análisis técnico sobre datos de mercado con estrategia optimizada para BTC."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el analizador técnico con la configuración especificada.
        
        Args:
            config: Configuración de análisis técnico
        """
        self.config = config
        
        # Parámetros de la estrategia optimizada para BTC
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_lower_bound = config.get("rsi_lower_bound", 15)  # Reducido a 15 para capturar más señales LONG
        self.rsi_upper_bound = config.get("rsi_upper_bound", 35)  # CORREGIDO: Ahora usa el parámetro correcto
        self.rsi_upper_bound_short = config.get("rsi_upper_bound_short", 65)
        self.rsi_overbought_short = config.get("rsi_overbought_short", 85)  # Aumentado a 85 para capturar más señales SHORT
        
        self.bollinger_period = config.get("bollinger_period", 20)
        self.bollinger_std_dev = config.get("bollinger_std_dev", 2)
        
        self.bb_width_min = config.get("bb_width_min", 0.01)
        self.bb_width_max = config.get("bb_width_max", 0.08)
        
        self.take_profit_percentage = config.get("take_profit", 5.5)
        self.stop_loss_percentage = config.get("stop_loss", 1.25)
        
        self.max_capital = config.get("max_capital", 10000)
        self.leverage = config.get("leverage", 5)
        
        # Habilitar logs detallados
        self.detailed_logs = config.get("detailed_logs", True)
        
        # Log detallado de los parámetros cargados para verificación
        logger.info(f"Análisis técnico inicializado con estrategia optimizada para BTC: "
                   f"RSI periodo={self.rsi_period}, "
                   f"RSI long={self.rsi_lower_bound}-{self.rsi_upper_bound}, "
                   f"RSI short={self.rsi_upper_bound_short}-{self.rsi_overbought_short}, "
                   f"BB periodo={self.bollinger_period}, "
                   f"Take Profit={self.take_profit_percentage}%, "
                   f"Stop Loss={self.stop_loss_percentage}%, "
                   f"Logs detallados={'activados' if self.detailed_logs else 'desactivados'}")
        
        # Verificación adicional para asegurar que los parámetros se cargaron correctamente
        logger.info(f"VERIFICACIÓN DE PARÁMETROS RSI - Valores cargados: "
                   f"rsi_lower_bound={self.rsi_lower_bound}, "
                   f"rsi_upper_bound={self.rsi_upper_bound}, "
                   f"rsi_upper_bound_short={self.rsi_upper_bound_short}, "
                   f"rsi_overbought_short={self.rsi_overbought_short}")
    
    def prepare_dataframe(self, candles: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convierte los datos de velas a un DataFrame de pandas.
        
        Args:
            candles: Lista de velas en formato OHLC
            
        Returns:
            DataFrame con los datos procesados
        """
        df = pd.DataFrame(candles)
        
        # Convertir columnas a tipos numéricos
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
        
        # Ordenar por tiempo (más reciente al final)
        if 'time' in df.columns:
            df = df.sort_values('time')
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula el Índice de Fuerza Relativa (RSI).
        
        Args:
            df: DataFrame con datos OHLC
            
        Returns:
            DataFrame con RSI añadido
        """
        if len(df) < self.rsi_period + 1:
            logger.warning(f"No hay suficientes datos para calcular RSI (necesita {self.rsi_period+1}, tiene {len(df)})")
            return df
        
        # Calcular cambios
        delta = df['close'].diff()
        
        # Separar ganancias y pérdidas
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calcular promedio de ganancias y pérdidas
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        # Calcular RS y RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula las Bandas de Bollinger y el BB Width.
        
        Args:
            df: DataFrame con datos OHLC
            
        Returns:
            DataFrame con Bandas de Bollinger y BB Width añadidos
        """
        if len(df) < self.bollinger_period:
            logger.warning(f"No hay suficientes datos para calcular Bollinger (necesita {self.bollinger_period}, tiene {len(df)})")
            return df
        
        # Calcular media móvil
        df['bollinger_ma'] = df['close'].rolling(window=self.bollinger_period).mean()
        
        # Calcular desviación estándar
        df['bollinger_std'] = df['close'].rolling(window=self.bollinger_period).std()
        
        # Calcular bandas superior e inferior
        df['bollinger_upper'] = df['bollinger_ma'] + (df['bollinger_std'] * self.bollinger_std_dev)
        df['bollinger_lower'] = df['bollinger_ma'] - (df['bollinger_std'] * self.bollinger_std_dev)
        
        # Calcular BB Width
        df['bb_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / df['bollinger_ma']
        
        return df
    
    def analyze(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Realiza un análisis técnico completo sobre los datos de velas.
        
        Args:
            candles: Lista de velas en formato OHLC
            
        Returns:
            Diccionario con resultados del análisis y señales
        """
        if not candles or len(candles) < self.bollinger_period:
            logger.warning(f"No hay suficientes datos para análisis (necesita {self.bollinger_period}, tiene {len(candles) if candles else 0})")
            return {"error": "Datos insuficientes para análisis"}
        
        # Preparar DataFrame
        df = self.prepare_dataframe(candles)
        
        # Calcular indicadores
        df = self.calculate_rsi(df)
        df = self.calculate_bollinger_bands(df)
        
        # Obtener última fila para análisis
        last_row = df.iloc[-1].to_dict()
        
        # Logs detallados de los valores actuales
        if self.detailed_logs:
            timestamp = pd.to_datetime(last_row.get("time", 0), unit='ms')
            logger.info(f"Análisis detallado [{timestamp}]: "
                       f"Precio=${last_row.get('close', 0):.2f}, "
                       f"RSI={last_row.get('rsi', 0):.2f}, "
                       f"BB Upper=${last_row.get('bollinger_upper', 0):.2f}, "
                       f"BB Lower=${last_row.get('bollinger_lower', 0):.2f}, "
                       f"BB Width={last_row.get('bb_width', 0):.4f}")
        
        # Generar señales
        signals = self._generate_signals(df)
        
        # Preparar resultado
        result = {
            "last_price": last_row.get("close"),
            "rsi": last_row.get("rsi"),
            "bollinger_upper": last_row.get("bollinger_upper"),
            "bollinger_lower": last_row.get("bollinger_lower"),
            "bollinger_ma": last_row.get("bollinger_ma"),
            "bb_width": last_row.get("bb_width"),
            "signals": signals
        }
        
        return result
    
    def _generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Genera señales de trading basadas en la estrategia optimizada para BTC.
        
        Args:
            df: DataFrame con indicadores calculados
            
        Returns:
            Diccionario con señales de trading
        """
        if len(df) < 2:
            return {"error": "Datos insuficientes para generar señales"}
        
        # Obtener la última fila para análisis
        current = df.iloc[-1]
        
        signals = {
            "long_signal": False,
            "short_signal": False,
            "overall": None,
            "reason": ""
        }
        
        # Verificar condiciones para entrada LONG
        if (self.rsi_lower_bound <= current.get("rsi", 0) <= self.rsi_upper_bound and 
            current.get("close", 0) <= current.get("bollinger_lower", 0) and
            self.bb_width_min <= current.get("bb_width", 0) <= self.bb_width_max):
            
            signals["long_signal"] = True
            signals["overall"] = "buy"
            signals["reason"] = (f"RSI={current.get('rsi', 0):.2f} en rango {self.rsi_lower_bound}-{self.rsi_upper_bound}, "
                               f"precio toca/cruza banda inferior, "
                               f"BB Width={current.get('bb_width', 0):.4f} en rango {self.bb_width_min}-{self.bb_width_max}")
            
            logger.info(f"Señal LONG generada: RSI={current.get('rsi', 0):.2f}, "
                       f"BB Width={current.get('bb_width', 0):.4f}")
        
        # Verificar condiciones para entrada SHORT
        elif (self.rsi_upper_bound_short <= current.get("rsi", 0) <= self.rsi_overbought_short and 
              current.get("close", 0) >= current.get("bollinger_upper", 0) and
              self.bb_width_min <= current.get("bb_width", 0) <= self.bb_width_max):
            
            signals["short_signal"] = True
            signals["overall"] = "sell"
            signals["reason"] = (f"RSI={current.get('rsi', 0):.2f} en rango {self.rsi_upper_bound_short}-{self.rsi_overbought_short}, "
                               f"precio toca/cruza banda superior, "
                               f"BB Width={current.get('bb_width', 0):.4f} en rango {self.bb_width_min}-{self.bb_width_max}")
            
            logger.info(f"Señal SHORT generada: RSI={current.get('rsi', 0):.2f}, "
                       f"BB Width={current.get('bb_width', 0):.4f}")
        else:
            # Logs detallados de por qué no se generó señal
            if self.detailed_logs:
                # Verificar condición de RSI para SHORT
                rsi_value = current.get("rsi", 0)
                rsi_condition = self.rsi_upper_bound_short <= rsi_value <= self.rsi_overbought_short
                
                # Verificar condición de precio para SHORT
                price = current.get("close", 0)
                upper_band = current.get("bollinger_upper", 0)
                price_condition = price >= upper_band
                
                # Verificar condición de BB Width
                bb_width = current.get("bb_width", 0)
                bb_width_condition = self.bb_width_min <= bb_width <= self.bb_width_max
                
                # CORREGIDO: Usar variables de instancia en lugar de valores hardcodeados
                # Log detallado de condiciones SHORT
                logger.info(f"Análisis de condiciones SHORT: "
                           f"RSI={rsi_value:.2f} {'✓' if rsi_condition else '✗'} (debe estar entre {self.rsi_upper_bound_short}-{self.rsi_overbought_short}), "
                           f"Precio=${price:.2f} vs BB Upper=${upper_band:.2f} {'✓' if price_condition else '✗'}, "
                           f"BB Width={bb_width:.4f} {'✓' if bb_width_condition else '✗'} (debe estar entre {self.bb_width_min}-{self.bb_width_max})")
                
                # Verificar condición de RSI para LONG
                rsi_condition_long = self.rsi_lower_bound <= rsi_value <= self.rsi_upper_bound
                
                # Verificar condición de precio para LONG
                lower_band = current.get("bollinger_lower", 0)
                price_condition_long = price <= lower_band
                
                # CORREGIDO: Usar variables de instancia en lugar de valores hardcodeados
                # Log detallado de condiciones LONG
                logger.info(f"Análisis de condiciones LONG: "
                           f"RSI={rsi_value:.2f} {'✓' if rsi_condition_long else '✗'} (debe estar entre {self.rsi_lower_bound}-{self.rsi_upper_bound}), "
                           f"Precio=${price:.2f} vs BB Lower=${lower_band:.2f} {'✓' if price_condition_long else '✗'}, "
                           f"BB Width={bb_width:.4f} {'✓' if bb_width_condition else '✗'} (debe estar entre {self.bb_width_min}-{self.bb_width_max})")
        
        return signals
    
    def calculate_position_size(self, available_capital: float, price: float) -> Tuple[float, float]:
        """
        Calcula el tamaño óptimo de posición basado en el capital disponible y el apalancamiento.
        
        Args:
            available_capital: Capital disponible
            price: Precio actual del activo
            
        Returns:
            Tupla con (tamaño de posición, capital utilizado)
        """
        # Limitar el capital operativo a $10,000 según la estrategia
        capital_to_use = min(available_capital, self.max_capital)
        
        # Calcular tamaño de posición con apalancamiento fijo de 5x
        position_size = (capital_to_use * self.leverage) / price
        
        logger.info(f"Cálculo de posición: capital disponible=${available_capital}, "
                   f"capital utilizado=${capital_to_use}, "
                   f"precio=${price}, apalancamiento={self.leverage}x, "
                   f"tamaño={position_size}")
        
        return position_size, capital_to_use
    
    def calculate_take_profit_price(self, entry_price: float, is_long: bool) -> float:
        """
        Calcula el precio de take profit basado en el precio de entrada.
        
        Args:
            entry_price: Precio de entrada
            is_long: True si es posición larga, False si es corta
            
        Returns:
            Precio de take profit
        """
        if is_long:
            # Para posiciones largas, el TP está por encima del precio de entrada
            return entry_price * (1 + self.take_profit_percentage / 100)
        else:
            # Para posiciones cortas, el TP está por debajo del precio de entrada
            return entry_price * (1 - self.take_profit_percentage / 100)
    
    def calculate_stop_loss_price(self, entry_price: float, is_long: bool) -> float:
        """
        Calcula el precio de stop loss basado en el precio de entrada.
        
        Args:
            entry_price: Precio de entrada
            is_long: True si es posición larga, False si es corta
            
        Returns:
            Precio de stop loss
        """
        if is_long:
            # Para posiciones largas, el SL está por debajo del precio de entrada
            return entry_price * (1 - self.stop_loss_percentage / 100)
        else:
            # Para posiciones cortas, el SL está por encima del precio de entrada
            return entry_price * (1 + self.stop_loss_percentage / 100)
