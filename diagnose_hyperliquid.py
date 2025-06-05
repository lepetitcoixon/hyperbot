#!/usr/bin/env python3
"""
Script de diagnóstico para el SDK de Hyperliquid.
Identifica la versión instalada y las clases disponibles.
"""

import sys
import importlib
import inspect

def diagnose_hyperliquid():
    """Diagnostica la instalación del SDK de Hyperliquid"""
    print("=== Diagnóstico del SDK de Hyperliquid ===\n")
    
    try:
        # Intentar importar el módulo principal
        import hyperliquid
        print(f"✅ Módulo hyperliquid importado exitosamente")
        
        # Verificar versión si está disponible
        if hasattr(hyperliquid, '__version__'):
            print(f"📦 Versión: {hyperliquid.__version__}")
        else:
            print("📦 Versión: No disponible")
        
        # Listar todos los atributos disponibles
        print(f"📁 Ubicación: {hyperliquid.__file__}")
        print(f"📋 Atributos disponibles en hyperliquid:")
        
        attributes = dir(hyperliquid)
        for attr in sorted(attributes):
            if not attr.startswith('_'):
                try:
                    obj = getattr(hyperliquid, attr)
                    obj_type = type(obj).__name__
                    print(f"   - {attr} ({obj_type})")
                except:
                    print(f"   - {attr} (no accesible)")
        
        print("\n" + "="*50)
        
        # Intentar importaciones específicas
        imports_to_test = [
            'HyperliquidSync',
            'Hyperliquid', 
            'HyperliquidAPI',
            'HyperLiquid',
            'Client',
            'API',
            'Exchange'
        ]
        
        print("🔍 Probando importaciones específicas:")
        available_classes = []
        
        for import_name in imports_to_test:
            try:
                obj = getattr(hyperliquid, import_name)
                print(f"   ✅ {import_name} - Disponible")
                available_classes.append(import_name)
                
                # Si es una clase, mostrar sus métodos principales
                if inspect.isclass(obj):
                    methods = [method for method in dir(obj) if not method.startswith('_')]
                    if methods:
                        print(f"      Métodos: {', '.join(methods[:5])}{'...' if len(methods) > 5 else ''}")
                        
            except AttributeError:
                print(f"   ❌ {import_name} - No disponible")
        
        print("\n" + "="*50)
        
        # Intentar importar desde submódulos
        print("🔍 Explorando submódulos:")
        try:
            # Intentar importar desde diferentes submódulos posibles
            submodules_to_test = [
                'hyperliquid.exchange',
                'hyperliquid.api',
                'hyperliquid.client',
                'hyperliquid.sync',
                'hyperliquid.utils'
            ]
            
            for submodule in submodules_to_test:
                try:
                    module = importlib.import_module(submodule)
                    print(f"   ✅ {submodule} - Disponible")
                    
                    # Listar clases en el submódulo
                    classes = [name for name, obj in inspect.getmembers(module, inspect.isclass)]
                    if classes:
                        print(f"      Clases: {', '.join(classes[:3])}{'...' if len(classes) > 3 else ''}")
                        
                except ImportError:
                    print(f"   ❌ {submodule} - No disponible")
                    
        except Exception as e:
            print(f"   ⚠️  Error explorando submódulos: {e}")
        
        print("\n" + "="*50)
        
        # Información del sistema
        print("🖥️  Información del sistema:")
        print(f"   Python: {sys.version}")
        print(f"   Plataforma: {sys.platform}")
        
        # Verificar otras dependencias relacionadas
        print("\n🔗 Dependencias relacionadas:")
        related_packages = ['eth_account', 'web3', 'requests', 'websocket-client']
        
        for package in related_packages:
            try:
                module = importlib.import_module(package.replace('-', '_'))
                version = getattr(module, '__version__', 'Desconocida')
                print(f"   ✅ {package}: {version}")
            except ImportError:
                print(f"   ❌ {package}: No instalado")
        
        print("\n" + "="*50)
        print("📝 Resumen:")
        if available_classes:
            print(f"   Clases disponibles para usar: {', '.join(available_classes)}")
            print(f"   Recomendación: Usar {available_classes[0]} en lugar de HyperliquidSync")
        else:
            print("   ⚠️  No se encontraron clases principales del SDK")
            print("   Recomendación: Reinstalar o actualizar hyperliquid-python-sdk")
        
        return available_classes
        
    except ImportError as e:
        print(f"❌ Error al importar hyperliquid: {e}")
        print("\n🔧 Soluciones sugeridas:")
        print("   1. pip install hyperliquid-python-sdk")
        print("   2. pip install --upgrade hyperliquid-python-sdk")
        print("   3. pip uninstall hyperliquid && pip install hyperliquid-python-sdk")
        return []
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []

if __name__ == "__main__":
    available = diagnose_hyperliquid()
    
    if available:
        print(f"\n✅ Diagnóstico completado. Clases disponibles: {len(available)}")
    else:
        print(f"\n❌ Diagnóstico completado. No se encontraron clases utilizables.")
    
    print("\n💡 Envía la salida completa de este script para recibir ayuda específica.")

