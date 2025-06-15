"""
Módulo para obtener datos de mercado para el bot de trading.
Implementa una solución híbrida: precio actual de Hyperliquid y datos históricos de Binance.
"""

import os
import sys
import time
import json
import logging
import requests
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Configurar logging
logger = logging.getLogger("data_provider")

class DataProvider:
    """Clase para obtener datos de mercado de diferentes fuentes."""
    
    def __init__(self, base_url: str = None):
        """
        Inicializa el proveedor de datos.
        
        Args:
            base_url: URL base de la API de Hyperliquid (opcional)
        """
        self.base_url = base_url or "https://api.hyperliquid.xyz"
        
        # Crear directorio de caché si no existe
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Caché de metadatos
        self._meta_cache = {}
        self._meta_timestamp = 0
        
        # Caché de precios recientes (como fallback)
        self._price_cache = {}
        
        logger.info(f"Proveedor de datos inicializado para Hyperliquid. Directorio de caché: {self.cache_dir}")
    
    def get_hyperliquid_price_l2book(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual desde Hyperliquid usando l2Book.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precios bid, ask y mid
        """
        try:
            logger.info(f"Solicitando l2Book para {asset}")
            
            url = f"{self.base_url}/info"
            payload = {
                "type": "l2Book",
                "coin": asset
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extraer precios bid y ask
            asks = data.get("asks", [])
            bids = data.get("bids", [])
            
            if not asks or not bids:
                logger.error(f"No se encontraron datos de orderbook para {asset}")
                return {}
            
            # Obtener el mejor precio de compra y venta
            best_ask = float(asks[0][0])
            best_bid = float(bids[0][0])
            
            # Calcular el precio medio
            mid_price = (best_ask + best_bid) / 2
            
            logger.info(f"Precios para {asset} (l2Book): ask={best_ask}, bid={best_bid}, mid={mid_price}")
            
            # Actualizar caché de precios
            self._price_cache[asset] = {
                "bid": best_bid,
                "ask": best_ask,
                "mid": mid_price,
                "timestamp": time.time()
            }
            
            return {
                "bid": best_bid,
                "ask": best_ask,
                "mid": mid_price
            }
        except Exception as e:
            logger.error(f"Error al obtener datos de l2Book para {asset}: {str(e)}")
            return {}
    
    def get_hyperliquid_price_ticker(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual desde Hyperliquid usando ticker.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precio mid
        """
        try:
            logger.info(f"Solicitando ticker para {asset}")
            
            url = f"{self.base_url}/info"
            payload = {
                "type": "allMids"
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Buscar el activo en la respuesta
            for item in data:
                if item.get("name") == asset:
                    mid_price = float(item.get("mid", 0))
                    
                    if mid_price > 0:
                        logger.info(f"Precio para {asset} (ticker): mid={mid_price}")
                        
                        # Estimar bid y ask (±0.05% del mid)
                        bid = mid_price * 0.9995
                        ask = mid_price * 1.0005
                        
                        # Actualizar caché de precios
                        self._price_cache[asset] = {
                            "bid": bid,
                            "ask": ask,
                            "mid": mid_price,
                            "timestamp": time.time()
                        }
                        
                        return {
                            "bid": bid,
                            "ask": ask,
                            "mid": mid_price
                        }
            
            logger.error(f"No se encontró {asset} en la respuesta de ticker")
            return {}
        except Exception as e:
            logger.error(f"Error al obtener datos de ticker para {asset}: {str(e)}")
            return {}
    
    def get_hyperliquid_price_trades(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual desde Hyperliquid usando trades recientes.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precio mid
        """
        try:
            logger.info(f"Solicitando trades recientes para {asset}")
            
            url = f"{self.base_url}/info"
            payload = {
                "type": "recentTrades",
                "coin": asset
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.error(f"No se encontraron trades recientes para {asset}")
                return {}
            
            # Obtener el precio del trade más reciente
            latest_trade = data[0]
            price = float(latest_trade.get("px", 0))
            
            if price > 0:
                logger.info(f"Precio para {asset} (trades): {price}")
                
                # Estimar bid y ask (±0.05% del precio)
                bid = price * 0.9995
                ask = price * 1.0005
                
                # Actualizar caché de precios
                self._price_cache[asset] = {
                    "bid": bid,
                    "ask": ask,
                    "mid": price,
                    "timestamp": time.time()
                }
                
                return {
                    "bid": bid,
                    "ask": ask,
                    "mid": price
                }
            
            logger.error(f"No se pudo obtener un precio válido de trades para {asset}")
            return {}
        except Exception as e:
            logger.error(f"Error al obtener datos de trades para {asset}: {str(e)}")
            return {}
    
    def get_binance_current_price(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual desde Binance.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precio mid
        """
        try:
            # Convertir el símbolo al formato de Binance
            symbol = f"{asset}USDT"
            
            logger.info(f"Solicitando precio actual de Binance para {symbol}")
            
            # Usar el endpoint de ticker de precio
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": symbol}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            price = float(data.get("price", 0))
            
            if price > 0:
                logger.info(f"Precio para {asset} (Binance): {price}")
                
                # Estimar bid y ask (±0.05% del precio)
                bid = price * 0.9995
                ask = price * 1.0005
                
                # Actualizar caché de precios
                self._price_cache[asset] = {
                    "bid": bid,
                    "ask": ask,
                    "mid": price,
                    "timestamp": time.time()
                }
                
                return {
                    "bid": bid,
                    "ask": ask,
                    "mid": price
                }
            
            logger.error(f"No se pudo obtener un precio válido de Binance para {asset}")
            return {}
        except Exception as e:
            logger.error(f"Error al obtener precio de Binance para {asset}: {str(e)}")
            return {}
    
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
            # Verificar si la caché es reciente (menos de 5 minutos)
            if time.time() - cached_data.get("timestamp", 0) < 300:
                logger.info(f"Usando precio en caché para {asset}: {cached_data['mid']}")
                return {
                    "bid": cached_data["bid"],
                    "ask": cached_data["ask"],
                    "mid": cached_data["mid"]
                }
        return {}
    
    def get_current_price(self, asset: str) -> Dict[str, float]:
        """
        Obtiene el precio actual usando múltiples fuentes con fallback.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Diccionario con precios bid, ask y mid
        """
        # Intentar obtener de la caché primero
        price_data = self.get_cached_price(asset)
        if price_data:
            return price_data
        
        # Intentar con l2Book de Hyperliquid
        price_data = self.get_hyperliquid_price_l2book(asset)
        if price_data:
            return price_data
        
        # Intentar con ticker de Hyperliquid
        price_data = self.get_hyperliquid_price_ticker(asset)
        if price_data:
            return price_data
        
        # Intentar con trades recientes de Hyperliquid
        price_data = self.get_hyperliquid_price_trades(asset)
        if price_data:
            return price_data
        
        # Intentar con Binance como último recurso
        price_data = self.get_binance_current_price(asset)
        if price_data:
            return price_data
        
        # Si todo falla, devolver un diccionario vacío
        logger.error(f"No se pudo obtener el precio actual para {asset} de ninguna fuente")
        return {}
    
    def get_hyperliquid_candles(self, asset: str, interval: str = "5m", limit: int = 1) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC actuales desde Hyperliquid usando múltiples fuentes.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (no utilizado, solo para compatibilidad)
            limit: Número máximo de velas (no utilizado, solo para compatibilidad)
            
        Returns:
            Lista con un único elemento que contiene el precio actual
        """
        try:
            # Obtener el precio actual usando la función robusta
            price_data = self.get_current_price(asset)
            
            if not price_data:
                logger.error(f"No se pudo obtener el precio actual para {asset}")
                return []
            
            # Crear una vela con el precio actual
            current_time = int(time.time() * 1000)
            candle = {
                "time": current_time,
                "open": price_data["mid"],
                "high": price_data["ask"],
                "low": price_data["bid"],
                "close": price_data["mid"],
                "volume": 0  # No tenemos datos de volumen
            }
            
            return [candle]
        except Exception as e:
            logger.error(f"Error al crear vela con precio actual para {asset}: {str(e)}")
            return []
    
    def get_binance_historical_candles(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC históricos desde Binance.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        try:
            # Convertir el símbolo al formato de Binance
            symbol = f"{asset}USDT"
            
            # Mapear el intervalo al formato de Binance
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d",
                "1w": "1w"
            }
            binance_interval = interval_map.get(interval, "5m")
            
            # Construir la URL de la API de Binance
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": binance_interval,
                "limit": limit
            }
            
            # Realizar la solicitud
            logger.info(f"Solicitando datos históricos de Binance para {symbol}, intervalo {binance_interval}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convertir los datos al formato esperado
            candles = []
            for item in data:
                candle = {
                    "time": item[0],  # Timestamp de apertura
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5])
                }
                candles.append(candle)
            
            logger.info(f"Obtenidas {len(candles)} velas históricas de Binance para {symbol}")
            return candles
        except Exception as e:
            logger.error(f"Error al obtener datos históricos de Binance para {asset}: {str(e)}")
            return []
    
    def get_combined_candles(self, asset: str, interval: str = "5m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene datos OHLC combinando datos históricos de Binance con el precio actual.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            interval: Intervalo de tiempo (ej. "5m", "1h", "1d")
            limit: Número máximo de velas
            
        Returns:
            Lista de velas OHLC
        """
        try:
            # Obtener datos históricos de Binance
            historical_candles = self.get_binance_historical_candles(asset, interval, limit - 1)
            
            if not historical_candles:
                logger.warning(f"No se pudieron obtener datos históricos de Binance para {asset}")
                return []
            
            # Obtener el precio actual
            current_candle = self.get_hyperliquid_candles(asset, interval, 1)
            
            if not current_candle:
                logger.warning(f"No se pudo obtener el precio actual para {asset}")
                # Usar la última vela histórica como actual
                if historical_candles:
                    logger.info(f"Usando la última vela histórica como actual para {asset}")
                    return historical_candles
                return []
            
            # Combinar los datos
            combined_candles = historical_candles + current_candle
            
            # Ordenar por tiempo
            combined_candles.sort(key=lambda x: x["time"])
            
            # Limitar al número solicitado
            if len(combined_candles) > limit:
                combined_candles = combined_candles[-limit:]
            
            logger.info(f"Datos combinados para {asset}: {len(combined_candles)} velas")
            return combined_candles
        except Exception as e:
            logger.error(f"Error al combinar datos para {asset}: {str(e)}")
            return []
    
    def get_sz_decimals(self, asset: str) -> int:
        """
        Obtiene el número de decimales para el tamaño de orden de un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Número de decimales para el tamaño de orden
        """
        try:
            # Verificar si la caché es válida (menos de 1 hora)
            current_time = time.time()
            if current_time - self._meta_timestamp > 3600 or asset not in self._meta_cache:
                # Obtener metadatos del mercado
                url = f"{self.base_url}/info"
                payload = {"type": "meta"}
                headers = {"Content-Type": "application/json"}
                
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Procesar y almacenar en caché
                universe = data.get("universe", [])
                
                for asset_data in universe:
                    name = asset_data.get("name", "")
                    if name:
                        self._meta_cache[name] = asset_data
                
                self._meta_timestamp = current_time
            
            # Obtener decimales para el activo
            asset_data = self._meta_cache.get(asset, {})
            sz_decimals = asset_data.get("szDecimals", 0)
            
            logger.info(f"Decimales para tamaño de orden de {asset}: {sz_decimals}")
            return sz_decimals
        except Exception as e:
            logger.error(f"Error al obtener decimales para {asset}: {str(e)}")
            return 0  # Valor predeterminado seguro
    
    def get_step_size(self, asset: str) -> float:
        """
        Obtiene el tamaño de paso (step size) para un activo.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            
        Returns:
            Tamaño de paso para el activo
        """
        try:
            # Obtener decimales
            sz_decimals = self.get_sz_decimals(asset)
            
            if sz_decimals > 0:
                step_size = 10 ** -sz_decimals
                return step_size
            
            # Valores predeterminados seguros
            default_step_sizes = {
                "BTC": 0.001,
                "ETH": 0.01,
                "SOL": 0.1,
            }
            return default_step_sizes.get(asset, 0.01)
        except Exception as e:
            logger.error(f"Error al obtener step size para {asset}: {str(e)}")
            return 0.001  # Valor predeterminado seguro para BTC
    
    def normalize_size(self, asset: str, size: float) -> float:
        """
        Normaliza el tamaño de una orden para que sea un múltiplo del step size.
        
        Args:
            asset: Símbolo del activo (ej. "BTC")
            size: Tamaño original
            
        Returns:
            Tamaño normalizado
        """
        try:
            step_size = self.get_step_size(asset)
            
            if step_size <= 0:
                return size
            
            # Redondear al múltiplo más cercano del step size
            normalized_size = round(size / step_size) * step_size
            
            # Redondear a un número de decimales seguro para evitar errores de punto flotante
            decimals = len(str(step_size).split('.')[-1])
            normalized_size = round(normalized_size, decimals)
            
            if normalized_size != size:
                logger.info(f"Tamaño normalizado para {asset}: {size} -> {normalized_size} (step size: {step_size})")
            
            return normalized_size
        except Exception as e:
            logger.error(f"Error al normalizar tamaño para {asset}: {str(e)}")
            return size  # Devolver el tamaño original en caso de error
