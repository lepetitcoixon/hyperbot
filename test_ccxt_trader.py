#!/usr/bin/env python3
"""
Script de prueba para el módulo ccxt_trader.
Verifica que las funciones básicas de trading funcionen correctamente.
"""

import sys
import os
import json
import logging

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ccxt_trader import CCXTTrader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_config():
    """Carga la configuración desde el archivo config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def test_ccxt_trader():
    """Prueba las funciones básicas del CCXTTrader"""
    print("=== Prueba del módulo CCXTTrader ===")
    
    # Cargar configuración
    config = load_config()
    
    # Verificar que las credenciales estén configuradas
    wallet_address = config['auth']['account_address']
    private_key = config['auth']['secret_key']
    
    if wallet_address == "YOUR_ACCOUNT_ADDRESS" or private_key == "YOUR_SECRET_KEY":
        print("❌ Error: Debes configurar las credenciales en config/config.json")
        return False
    
    try:
        # Inicializar trader
        print("1. Inicializando CCXTTrader...")
        trader = CCXTTrader(wallet_address, private_key, config)
        print("✅ CCXTTrader inicializado correctamente")
        
        # Probar obtener precio de mercado
        print("\\n2. Probando obtener precio de mercado...")
        symbol = "BTC/USDC:USDC"
        price = trader.get_market_price(symbol)
        print(f"✅ Precio de BTC: ${price}")
        
        # Probar cálculo de tamaño de orden
        print("\\n3. Probando cálculo de tamaño de orden...")
        usd_amount = 100
        size = trader.calculate_order_size(usd_amount, price)
        print(f"✅ Tamaño calculado para ${usd_amount}: {size} BTC")
        
        # Probar obtener balance
        print("\\n4. Probando obtener balance...")
        balance_result = trader.get_balance()
        if balance_result["status"] == "ok":
            print("✅ Balance obtenido correctamente")
            total_balance = balance_result["balance"].get("total", {})
            if total_balance:
                print(f"   Balance total: {total_balance}")
        else:
            print(f"❌ Error al obtener balance: {balance_result['message']}")
        
        # Probar obtener posiciones
        print("\\n5. Probando obtener posiciones...")
        positions_result = trader.get_positions()
        if positions_result["status"] == "ok":
            print(f"✅ Posiciones obtenidas: {positions_result['count']} posiciones activas")
            if positions_result["count"] > 0:
                for pos in positions_result["positions"]:
                    print(f"   - {pos['symbol']}: {pos['size']} (PnL: {pos.get('unrealizedPnl', 'N/A')})")
        else:
            print(f"❌ Error al obtener posiciones: {positions_result['message']}")
        
        # Probar conversión de símbolos
        print("\\n6. Probando conversión de símbolos...")
        btc_symbol = trader.convert_symbol_to_ccxt("BTC")
        eth_symbol = trader.convert_symbol_to_ccxt("ETH")
        print(f"✅ BTC -> {btc_symbol}")
        print(f"✅ ETH -> {eth_symbol}")
        
        print("\\n=== Todas las pruebas básicas completadas exitosamente ===")
        print("\\n⚠️  NOTA: Para pruebas de trading real, usar el modo de prueba o cantidades muy pequeñas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_ccxt_trader()
    sys.exit(0 if success else 1)

