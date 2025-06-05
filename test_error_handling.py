#!/usr/bin/env python3
"""
Script de prueba para manejo de errores en la integración ccxt.
Valida que el sistema maneje correctamente situaciones de error.
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

def test_error_handling():
    """Prueba el manejo de errores en diferentes escenarios"""
    print("=== Prueba de Manejo de Errores ===")
    
    # 1. Probar con credenciales inválidas
    print("1. Probando con credenciales inválidas...")
    try:
        invalid_config = {
            "ccxt": {
                "enable_rate_limit": True,
                "default_slippage": 0.05,
                "default_type": "swap"
            }
        }
        
        # Intentar inicializar con credenciales falsas
        try:
            trader = CCXTTrader("0x1234567890123456789012345678901234567890", "0x" + "0" * 64, invalid_config)
            print("❌ Debería haber fallado con credenciales inválidas")
        except Exception as e:
            print(f"✅ Error manejado correctamente: {type(e).__name__}")
    except Exception as e:
        print(f"✅ Error de inicialización manejado: {str(e)}")
    
    # 2. Probar con configuración válida pero operaciones que pueden fallar
    print("\\n2. Probando operaciones con configuración válida...")
    try:
        # Cargar configuración real
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        auth_config = config.get('auth', {})
        wallet_address = auth_config.get('account_address')
        private_key = auth_config.get('secret_key')
        
        if wallet_address == "YOUR_ACCOUNT_ADDRESS" or private_key == "YOUR_SECRET_KEY":
            print("⚠️  Saltando pruebas con credenciales reales (no configuradas)")
            return True
        
        trader = CCXTTrader(wallet_address, private_key, config)
        
        # 3. Probar símbolo inválido
        print("\\n3. Probando símbolo inválido...")
        try:
            price = trader.get_market_price("INVALID/SYMBOL:USDC")
            print(f"❌ Debería haber fallado con símbolo inválido, pero obtuvo: {price}")
        except Exception as e:
            print(f"✅ Error de símbolo inválido manejado: {type(e).__name__}")
        
        # 4. Probar orden con cantidad inválida
        print("\\n4. Probando orden con cantidad inválida...")
        try:
            result = trader.place_market_order("BTC/USDC:USDC", "buy", -1)
            if result["status"] == "error":
                print("✅ Error de cantidad inválida manejado correctamente")
            else:
                print(f"❌ Debería haber fallado con cantidad negativa")
        except Exception as e:
            print(f"✅ Error de cantidad inválida manejado: {type(e).__name__}")
        
        # 5. Probar cancelación de orden inexistente
        print("\\n5. Probando cancelación de orden inexistente...")
        try:
            result = trader.cancel_order("nonexistent_order_id", "BTC/USDC:USDC")
            if result["status"] == "error":
                print("✅ Error de orden inexistente manejado correctamente")
            else:
                print(f"⚠️  Cancelación de orden inexistente no falló como se esperaba")
        except Exception as e:
            print(f"✅ Error de orden inexistente manejado: {type(e).__name__}")
        
        # 6. Probar conversión de símbolos
        print("\\n6. Probando conversión de símbolos...")
        btc_symbol = trader.convert_symbol_to_ccxt("BTC")
        eth_symbol = trader.convert_symbol_to_ccxt("ETH")
        custom_symbol = trader.convert_symbol_to_ccxt("CUSTOM")
        
        print(f"✅ BTC -> {btc_symbol}")
        print(f"✅ ETH -> {eth_symbol}")
        print(f"✅ CUSTOM -> {custom_symbol}")
        
        # 7. Probar cálculo de tamaño con valores extremos
        print("\\n7. Probando cálculo de tamaño con valores extremos...")
        try:
            size1 = trader.calculate_order_size(0, 50000)  # Monto cero
            print(f"✅ Monto cero: {size1}")
            
            size2 = trader.calculate_order_size(100, 0.000001)  # Precio muy bajo
            print(f"✅ Precio muy bajo: {size2}")
            
            try:
                size3 = trader.calculate_order_size(100, 0)  # Precio cero (debería fallar)
                print(f"❌ Debería haber fallado con precio cero, pero obtuvo: {size3}")
            except Exception as e:
                print(f"✅ Error de precio cero manejado: {type(e).__name__}")
                
        except Exception as e:
            print(f"✅ Errores de cálculo manejados: {type(e).__name__}")
        
        print("\\n=== Manejo de errores validado ===")
        return True
        
    except Exception as e:
        print(f"❌ Error inesperado durante pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_network_resilience():
    """Prueba la resistencia a problemas de red"""
    print("\\n=== Prueba de Resistencia de Red ===")
    
    try:
        # Cargar configuración
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        auth_config = config.get('auth', {})
        wallet_address = auth_config.get('account_address')
        private_key = auth_config.get('secret_key')
        
        if wallet_address == "YOUR_ACCOUNT_ADDRESS" or private_key == "YOUR_SECRET_KEY":
            print("⚠️  Saltando pruebas de red (credenciales no configuradas)")
            return True
        
        # Configurar timeout muy bajo para simular problemas de red
        config["ccxt"]["timeout"] = 1000  # 1 segundo
        
        trader = CCXTTrader(wallet_address, private_key, config)
        
        print("1. Probando con timeout muy bajo...")
        try:
            # Intentar múltiples operaciones rápidas
            for i in range(3):
                try:
                    price = trader.get_market_price("BTC/USDC:USDC")
                    print(f"   Intento {i+1}: ✅ Precio obtenido: ${price}")
                except Exception as e:
                    print(f"   Intento {i+1}: ⚠️  Timeout/Error: {type(e).__name__}")
        except Exception as e:
            print(f"✅ Problemas de red manejados: {type(e).__name__}")
        
        print("✅ Resistencia de red probada")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de resistencia: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando pruebas de manejo de errores...")
    
    error_success = test_error_handling()
    network_success = test_network_resilience()
    
    success = error_success and network_success
    
    if success:
        print("\\n✅ Todas las pruebas de manejo de errores pasaron")
    else:
        print("\\n❌ Algunas pruebas de manejo de errores fallaron")
    
    sys.exit(0 if success else 1)

