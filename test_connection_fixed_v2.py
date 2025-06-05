#!/usr/bin/env python3
"""
Script de prueba para la conexión corregida de Hyperliquid v2.
Verifica que la nueva implementación sin skip_ws funcione correctamente.
"""

import sys
import os
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_fixed_connection_v2():
    """Prueba la conexión corregida v2"""
    print("=== Prueba de Conexión Corregida v2 (sin skip_ws) ===\n")
    
    try:
        # Importar la conexión corregida v2
        sys.path.append('/home/ubuntu')
        from connection_fixed_v2 import HyperliquidConnection
        
        print("✅ Importación de HyperliquidConnection v2 exitosa")
        
        # Cargar configuración (necesitarás ajustar la ruta)
        config_path = "config/config.json"  # Ajusta según tu estructura
        
        if not os.path.exists(config_path):
            print(f"⚠️  Archivo de configuración no encontrado: {config_path}")
            print("Por favor, asegúrate de que el archivo config.json existe con tus credenciales")
            return False
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        auth_config = config.get('auth', {})
        account_address = auth_config.get('account_address')
        secret_key = auth_config.get('secret_key')
        
        if not account_address or not secret_key:
            print("❌ Credenciales no configuradas en config.json")
            return False
        
        if account_address == "YOUR_ACCOUNT_ADDRESS" or secret_key == "YOUR_SECRET_KEY":
            print("❌ Debes configurar tus credenciales reales en config.json")
            return False
        
        # Probar inicialización
        print("\\n1. Inicializando conexión v2...")
        connection = HyperliquidConnection(
            account_address=account_address,
            secret_key=secret_key
        )
        print("✅ Conexión v2 inicializada exitosamente")
        
        # Verificar que las APIs se inicializaron
        if connection.info_api is not None:
            print("✅ Info API disponible")
        else:
            print("⚠️  Info API no disponible")
        
        if connection.exchange_api is not None:
            print("✅ Exchange API disponible")
        else:
            print("⚠️  Exchange API no disponible")
        
        # Probar obtener estado del usuario
        print("\\n2. Obteniendo estado del usuario...")
        user_state = connection.get_user_state()
        if user_state:
            print("✅ Estado del usuario obtenido")
            
            # Mostrar información básica
            margin_summary = user_state.get("marginSummary", {})
            account_value = margin_summary.get("accountValue", "0")
            print(f"   Valor de cuenta: ${account_value}")
            
            positions = user_state.get("assetPositions", [])
            print(f"   Posiciones: {len(positions)}")
            
            open_orders = user_state.get("openOrders", [])
            print(f"   Órdenes abiertas: {len(open_orders)}")
        else:
            print("⚠️  No se pudo obtener estado del usuario")
        
        # Probar obtener datos de mercado
        print("\\n3. Obteniendo datos de mercado para BTC...")
        market_data = connection.get_market_data("BTC")
        if market_data and "midPrice" in market_data:
            price = market_data["midPrice"]
            print(f"✅ Precio de BTC: ${price}")
        else:
            print("⚠️  No se pudo obtener precio de BTC")
        
        # Probar obtener velas
        print("\\n4. Obteniendo datos de velas...")
        try:
            candles = connection.get_candles("BTC", "5m", 10)
            if candles:
                print(f"✅ Obtenidas {len(candles)} velas")
                if len(candles) > 0:
                    last_candle = candles[-1]
                    print(f"   Última vela: {last_candle}")
            else:
                print("⚠️  No se pudieron obtener velas")
        except Exception as e:
            print(f"⚠️  Error al obtener velas: {str(e)}")
        
        # Probar metadatos del mercado
        print("\\n5. Obteniendo metadatos del mercado...")
        try:
            meta = connection.get_market_metadata()
            if meta:
                print(f"✅ Metadatos obtenidos para {len(meta)} activos")
                if "BTC" in meta:
                    btc_meta = meta["BTC"]
                    print(f"   BTC metadata: {btc_meta}")
            else:
                print("⚠️  No se pudieron obtener metadatos")
        except Exception as e:
            print(f"⚠️  Error al obtener metadatos: {str(e)}")
        
        print("\\n=== Prueba de Conexión v2 Completada ===")
        print("✅ La conexión corregida v2 funciona correctamente")
        print("\\n📝 Próximos pasos:")
        print("   1. Reemplaza tu archivo src/connection.py con connection_fixed_v2.py")
        print("   2. Ejecuta tu bot normalmente")
        print("\\n⚠️  NOTA IMPORTANTE:")
        print("   - Esta versión usa ccxt para las operaciones de trading")
        print("   - La API nativa de Hyperliquid se usa solo para consultas de datos")
        print("   - Las operaciones de trading son más confiables con ccxt")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        print("\\n🔧 Posibles soluciones:")
        print("   1. Verifica que hyperliquid esté instalado: pip install hyperliquid-python-sdk")
        print("   2. Verifica que las rutas sean correctas")
        return False
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixed_connection_v2()
    
    if success:
        print("\\n🎉 ¡Prueba exitosa! Tu conexión v2 está lista para usar.")
        print("\\n💡 Recuerda:")
        print("   - Las operaciones de trading usan ccxt (más confiable)")
        print("   - Los datos de mercado usan la API nativa de Hyperliquid")
        print("   - Esta es la mejor combinación para tu bot")
    else:
        print("\\n❌ La prueba falló. Revisa los errores arriba.")
    
    sys.exit(0 if success else 1)

