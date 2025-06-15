"""
Módulo para obtener datos de mercado para el bot de trading usando CCXT.
Implementa Hyperliquid como fuente principal y Binance como fallback.
"""

import os
import sys
import time
import json
import logging
import requests
import pandas as pd
import ccxt
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Configurar logging
logger = logging.getLogger("ccxt_data_provider")

class CCXTDataProvider:
    """Clase para obtener datos de mercado usando CCXT con Hyperliquid como fuente principal."""
    
    def __init__(self, ccxt_connection=None, base_url: str = None):
        """
        Inicializa el proveedor de datos con CCXT.
        
        Args:
            ccxt_connection: Conexión CCXT a Hyperliquid (opcional)
            base_url: URL base de la API de Hyperliquid (opcional, para fallback)
        """
        self.ccxt_connection = ccxt_connection
        self.base_url = base_url or "https://api.hyperliquid.xyz"
        
        # Inicializar Binance como fallback
        self.binance_exchange = None
        try:
            self.binance_exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            logger.info("Binance inicializado como fallback")
        except Exception as e:
            logger.warning(f"No se pudo inicializar Binance como fallback: {str(e)}")
        
        # Crear directorio de caché si no existe
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Caché de datos
        self._candles_cache = {}
        self._price_cache = {}
        
        logger.info(f"Proveedor de datos CCXT inicializado. Directorio de caché: {self.cache_dir}")
    
    def get_hyperliquid_candles_ccxt(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC desde Hyperliquid usando CCXT.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        if not self.ccxt_connection:
            logger.warning("No hay conexión CCXT disponible para Hyperliquid")
            return []
        
        try:
            symbol = f"{asset}/USDC:USDC"
            
            # Mapear el intervalo al formato de CCXT
            timeframe_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d"
            }
            
            timeframe = timeframe_map.get(interval, "5m")
            
            logger.info(f"Obteniendo velas de Hyperliquid (CCXT) para {symbol}, intervalo {timeframe}, límite {limit}")
            
            # Obtener velas OHLC usando CCXT
            ohlcv = self.ccxt_connection.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convertir al formato esperado por el bot
            candles = []
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                candles.append({
                    "time": timestamp,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })
            
            logger.info(f"Obtenidas {len(candles)} velas de Hyperliquid (CCXT) para {asset}")
            
            # Actualizar caché
            cache_key = f"{asset}_{interval}_{limit}"
            self._candles_cache[cache_key] = {
                "data": candles,
                "timestamp": time.time()
            }
            
            return candles
        except Exception as e:
            logger.error(f"Error al obtener velas de Hyperliquid (CCXT) para {asset}: {str(e)}")
            return []
    
    def get_hyperliquid_price_ccxt(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual desde Hyperliquid usando CCXT.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precios bid, ask y mid
        """
        if not self.ccxt_connection:
            logger.warning("No hay conexión CCXT disponible para Hyperliquid")
            return {}
        
        try:
            symbol = f"{asset}/USDC:USDC"
            
            logger.info(f"Obteniendo precio de Hyperliquid (CCXT) para {symbol}")
            
            # Obtener ticker usando CCXT
            ticker = self.ccxt_connection.exchange.fetch_ticker(symbol)
            
            # Extraer precios
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            last = ticker.get('last', 0)
            
            # Usar el precio 'last' como mid si no hay bid/ask
            if not bid or not ask:
                if last:
                    # Estimar bid y ask (±0.05% del precio)
                    bid = last * 0.9995
                    ask = last * 1.0005
                    mid = last
                else:
                    logger.error(f"No se pudieron obtener precios válidos para {asset}")
                    return {}
            else:
                mid = (bid + ask) / 2
            
            logger.info(f"Precios para {asset} (Hyperliquid CCXT): bid={bid}, ask={ask}, mid={mid}")
            
            # Actualizar caché de precios
            self._price_cache[asset] = {
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "timestamp": time.time()
            }
            
            return {
                "bid": bid,
                "ask": ask,
                "mid": mid
            }
        except Exception as e:
            logger.error(f"Error al obtener precio de Hyperliquid (CCXT) para {asset}: {str(e)}")
            return {}
    
    def get_binance_candles_ccxt(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC desde Binance usando CCXT como fallback.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        if not self.binance_exchange:
            logger.warning("No hay conexión CCXT disponible para Binance")
            return []
        
        try:
            symbol = f"{asset}/USDT"
            
            # Mapear el intervalo al formato de CCXT
            timeframe_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d"
            }
            
            timeframe = timeframe_map.get(interval, "5m")
            
            logger.info(f"Obteniendo velas de Binance (CCXT) para {symbol}, intervalo {timeframe}, límite {limit}")
            
            # Obtener velas OHLC usando CCXT
            ohlcv = self.binance_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convertir al formato esperado por el bot
            candles = []
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                candles.append({
                    "time": timestamp,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })
            
            logger.info(f"Obtenidas {len(candles)} velas de Binance (CCXT) para {asset}")
            
            # Actualizar caché
            cache_key = f"{asset}_{interval}_{limit}_binance"
            self._candles_cache[cache_key] = {
                "data": candles,
                "timestamp": time.time()
            }
            
            return candles
        except Exception as e:
            logger.error(f"Error al obtener velas de Binance (CCXT) para {asset}: {str(e)}")
            return []
    
    def get_binance_price_ccxt(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual desde Binance usando CCXT como fallback.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precios bid, ask y mid
        """
        if not self.binance_exchange:
            logger.warning("No hay conexión CCXT disponible para Binance")
            return {}
        
        try:
            symbol = f"{asset}/USDT"
            
            logger.info(f"Obteniendo precio de Binance (CCXT) para {symbol}")
            
            # Obtener ticker usando CCXT
            ticker = self.binance_exchange.fetch_ticker(symbol)
            
            # Extraer precios
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            last = ticker.get('last', 0)
            
            # Usar el precio 'last' como mid si no hay bid/ask
            if not bid or not ask:
                if last:
                    # Estimar bid y ask (±0.05% del precio)
                    bid = last * 0.9995
                    ask = last * 1.0005
                    mid = last
                else:
                    logger.error(f"No se pudieron obtener precios válidos de Binance para {asset}")
                    return {}
            else:
                mid = (bid + ask) / 2
            
            logger.info(f"Precios para {asset} (Binance CCXT): bid={bid}, ask={ask}, mid={mid}")
            
            # Actualizar caché de precios
            self._price_cache[f"{asset}_binance"] = {
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "timestamp": time.time()
            }
            
            return {
                "bid": bid,
                "ask": ask,
                "mid": mid
            }
        except Exception as e:
            logger.error(f"Error al obtener precio de Binance (CCXT) para {asset}: {str(e)}")
            return {}
    
    def get_cached_candles(self, asset: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        """
        Obtiene velas desde la caché si están disponibles y son recientes.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC o vacía si no hay caché válida
        """
        cache_key = f"{asset}_{interval}_{limit}"
        cached_data = self._candles_cache.get(cache_key, {})
        
        if cached_data:
            # Verificar si la caché es reciente (menos de 1 minuto para datos de 5m)
            cache_timeout = 60 if interval == "5m" else 300  # 1 minuto para 5m, 5 minutos para otros
            if time.time() - cached_data.get("timestamp", 0) < cache_timeout:
                logger.info(f"Usando velas en caché para {asset} ({interval})")
                return cached_data["data"]
        
        return []
    
    def get_cached_price(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio desde la caché si está disponible y es reciente.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precios o vacío si no hay caché válida
        """
        cached_data = self._price_cache.get(asset, {})
        if cached_data:
            # Verificar si la caché es reciente (menos de 30 segundos)
            if time.time() - cached_data.get("timestamp", 0) < 30:
                logger.info(f"Usando precio en caché para {asset}: {cached_data['mid']}")
                return {
                    "bid": cached_data["bid"],
                    "ask": cached_data["ask"],
                    "mid": cached_data["mid"]
                }
        return {}
    
    def get_candles(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC usando Hyperliquid como fuente principal y Binance como fallback.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        # Intentar obtener de la caché primero
        candles = self.get_cached_candles(asset, interval, limit)
        if candles:
            return candles
        
        # Intentar obtener de Hyperliquid usando CCXT
        candles = self.get_hyperliquid_candles_ccxt(asset, interval, limit)
        if candles:
            logger.info(f"Datos de velas obtenidos de Hyperliquid para {asset}")
            return candles
        
        # Intentar obtener de Binance como fallback
        candles = self.get_binance_candles_ccxt(asset, interval, limit)
        if candles:
            logger.info(f"Datos de velas obtenidos de Binance (fallback) para {asset}")
            return candles
        
        # Si todo falla, devolver una lista vacía
        logger.error(f"No se pudieron obtener datos de velas para {asset} de ninguna fuente")
        return []
    
    def get_current_price(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual usando Hyperliquid como fuente principal y Binance como fallback.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precios bid, ask y mid
        """
        # Intentar obtener de la caché primero
        price_data = self.get_cached_price(asset)
        if price_data:
            return price_data
        
        # Intentar obtener de Hyperliquid usando CCXT
        price_data = self.get_hyperliquid_price_ccxt(asset)
        if price_data:
            logger.info(f"Precio obtenido de Hyperliquid para {asset}")
            return price_data
        
        # Intentar obtener de Binance como fallback
        price_data = self.get_binance_price_ccxt(asset)
        if price_data:
            logger.info(f"Precio obtenido de Binance (fallback) para {asset}")
            return price_data
        
        # Si todo falla, devolver un diccionario vacío
        logger.error(f"No se pudo obtener el precio actual para {asset} de ninguna fuente")
        return {}
    
    def get_sz_decimals(self, asset: str) -> int:
        """
        Obtiene el número de decimales para el tamaño de orden de un activo.
        CORREGIDO: Siempre devuelve un entero válido.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Número de decimales (siempre un entero)
        """
        if not self.ccxt_connection:
            # Valores predeterminados si no hay conexión CCXT
            default_decimals = {
                "BTC": 3,  # 0.001
                "ETH": 2,  # 0.01
                "SOL": 1,  # 0.1
            }
            return default_decimals.get(asset, 2)
        
        try:
            symbol = f"{asset}/USDC:USDC"
            market = self.ccxt_connection.exchange.market(symbol)
            
            # Obtener precisión del amount
            precision = market.get('precision', {})
            amount_precision = precision.get('amount', None)
            
            # CORREGIDO: Verificar que amount_precision no sea None
            if amount_precision is not None and isinstance(amount_precision, (int, float)):
                return int(amount_precision)
            
            # Si no se encuentra o es None, usar valores predeterminados
            default_decimals = {
                "BTC": 3,  # 0.001
                "ETH": 2,  # 0.01
                "SOL": 1,  # 0.1
            }
            result = default_decimals.get(asset, 2)
            logger.warning(f"No se pudo determinar decimales para {asset}. Usando valor predeterminado: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error al obtener decimales para {asset}: {str(e)}")
            # Valores predeterminados seguros
            default_decimals = {
                "BTC": 3,  # 0.001
                "ETH": 2,  # 0.01
                "SOL": 1,  # 0.1
            }
            return default_decimals.get(asset, 2)
    
    def normalize_size(self, asset: str, size: float) -> float:
        """
        Normaliza el tamaño de una orden según los decimales permitidos.
        CORREGIDO: Maneja correctamente valores None en decimals.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            size: Tamaño de la orden
            
        Returns:
            Tamaño normalizado
        """
        try:
            decimals = self.get_sz_decimals(asset)
            
            # CORREGIDO: Asegurar que decimals sea un entero válido
            if not isinstance(decimals, int) or decimals < 0:
                logger.warning(f"Decimales inválidos para {asset}: {decimals}. Usando 3 por defecto.")
                decimals = 3
            
            # Limitar decimals a un rango razonable
            decimals = min(max(decimals, 0), 8)  # Entre 0 y 8 decimales
            
            return round(size, decimals)
            
        except Exception as e:
            logger.error(f"Error al normalizar tamaño para {asset}: {str(e)}")
            # En caso de error, usar 3 decimales por defecto
            return round(size, 3)

