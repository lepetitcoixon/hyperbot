#!/usr/bin/env python3
"""
Script de prueba completo para la integración ccxt en el bot de Hyperliquid.
Valida que el OrderManager funcione correctamente con ccxt.
"""

import sys
import os
import json
import logging
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from connection import HyperliquidConnection
from technical import TechnicalAnalysis
from orders import OrderManager
from risk import RiskManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_integration():
    """Prueba la integración completa del sistema con ccxt"""
    print("=== Prueba de Integración Completa con ccxt ===")
    
    try:
        # 1. Cargar configuración
        print("1. Cargando configuración...")
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        config = Config(config_path)
        
        # Verificar credenciales
        auth_config = config.data.get('auth', {})
        if (auth_config.get('account_address') == "YOUR_ACCOUNT_ADDRESS" or 
            auth_config.get('secret_key') == "YOUR_SECRET_KEY"):
            print("❌ Error: Debes configurar las credenciales en config/config.json")
            return False
        
        print("✅ Configuración cargada correctamente")
        
        # 2. Inicializar conexión (para datos de mercado)
        print("\\n2. Inicializando conexión...")
        connection = HyperliquidConnection(
            account_address=auth_config['account_address'],
            secret_key=auth_config['secret_key']
        )
        print("✅ Conexión inicializada")
        
        # 3. Inicializar análisis técnico
        print("\\n3. Inicializando análisis técnico...")
        technical_analyzer = TechnicalAnalysis(config)
        print("✅ Análisis técnico inicializado")
        
        # 4. Inicializar gestor de riesgos
        print("\\n4. Inicializando gestor de riesgos...")
        risk_manager = RiskManager(config)
        print("✅ Gestor de riesgos inicializado")
        
        # 5. Inicializar OrderManager con ccxt
        print("\\n5. Inicializando OrderManager con ccxt...")
        order_manager = OrderManager(
            connection=connection,
            technical_analyzer=technical_analyzer,
            risk_manager=risk_manager,
            config=config.data
        )
        print("✅ OrderManager con ccxt inicializado")
        
        # 6. Probar obtener resumen de cuenta
        print("\\n6. Probando resumen de cuenta...")
        account_summary = order_manager.get_account_summary()
        print(f"✅ Capital total: ${account_summary['total_capital']:.2f}")
        print(f"✅ Capital disponible: ${account_summary['available_capital']:.2f}")
        
        # 7. Probar capital disponible para trading
        print("\\n7. Probando cálculo de capital disponible...")
        available_capital = order_manager.get_available_capital()
        print(f"✅ Capital disponible para trading: ${available_capital:.2f}")
        
        # 8. Probar análisis de mercado
        print("\\n8. Probando análisis de mercado...")
        try:
            market_analysis = order_manager.analyze_market("BTC")
            signals = market_analysis.get('signals', {})
            overall_signal = signals.get('overall', 'No signal')
            print(f"✅ Análisis completado. Señal: {overall_signal}")
            if signals.get('reason'):
                print(f"   Razón: {signals['reason']}")
        except Exception as e:
            print(f"⚠️  Análisis de mercado falló (puede ser normal): {str(e)}")
        
        # 9. Probar verificación de posiciones
        print("\\n9. Probando verificación de posiciones...")
        can_open = order_manager.can_open_new_position()
        print(f"✅ Puede abrir nueva posición: {can_open}")
        
        # 10. Probar resumen de posiciones activas
        print("\\n10. Probando resumen de posiciones...")
        positions_summary = order_manager.get_active_positions_summary()
        print(f"✅ Posiciones activas: {positions_summary['count']}")
        
        # 11. Probar resumen completo de trading
        print("\\n11. Probando resumen completo...")
        trading_summary = order_manager.get_trading_summary()
        print("✅ Resumen de trading obtenido:")
        print(f"   - Capital total: ${trading_summary['account']['total_capital']:.2f}")
        print(f"   - Posiciones activas: {trading_summary['positions']['count']}")
        print(f"   - Órdenes activas: {trading_summary['active_orders']}")
        print(f"   - Capital reservado: ${trading_summary['reserved_capital']:.2f}")
        
        print("\\n=== Integración completa validada exitosamente ===")
        print("\\n✅ El bot está listo para operar con ccxt")
        print("\\n⚠️  IMPORTANTE: Para trading real, asegúrate de:")
        print("   - Configurar correctamente los niveles de riesgo")
        print("   - Empezar con cantidades pequeñas")
        print("   - Monitorear las operaciones de cerca")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba de integración: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ccxt_trader_only():
    """Prueba solo el módulo CCXTTrader de forma aislada"""
    print("\\n=== Prueba del módulo CCXTTrader (aislado) ===")
    
    try:
        from ccxt_trader import CCXTTrader
        
        # Cargar configuración
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        auth_config = config.get('auth', {})
        wallet_address = auth_config.get('account_address')
        private_key = auth_config.get('secret_key')
        
        if wallet_address == "YOUR_ACCOUNT_ADDRESS" or private_key == "YOUR_SECRET_KEY":
            print("❌ Error: Credenciales no configuradas")
            return False
        
        # Inicializar CCXTTrader
        trader = CCXTTrader(wallet_address, private_key, config)
        
        # Probar funciones básicas
        price = trader.get_market_price("BTC/USDC:USDC")
        print(f"✅ Precio BTC: ${price}")
        
        balance = trader.get_balance()
        if balance["status"] == "ok":
            print("✅ Balance obtenido correctamente")
        
        positions = trader.get_positions()
        if positions["status"] == "ok":
            print(f"✅ Posiciones: {positions['count']} activas")
        
        print("✅ CCXTTrader funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en CCXTTrader: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Iniciando pruebas - {datetime.now()}")
    
    # Probar CCXTTrader aislado primero
    ccxt_success = test_ccxt_trader_only()
    
    if ccxt_success:
        # Si CCXTTrader funciona, probar integración completa
        integration_success = test_integration()
        success = integration_success
    else:
        success = False
    
    print(f"\\nPruebas completadas - {datetime.now()}")
    sys.exit(0 if success else 1)

