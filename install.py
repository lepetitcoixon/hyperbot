#!/usr/bin/env python3
"""
Script de instalación rápida para Bot Hyperliquid Completo v2.
Configura todo automáticamente para uso inmediato.
"""

import subprocess
import sys
import os
import json
import shutil

def print_banner():
    """Muestra banner de bienvenida"""
    print("=" * 60)
    print("🚀 BOT HYPERLIQUID - INSTALACIÓN COMPLETA V2")
    print("=" * 60)
    print("✨ Versión con ccxt + Compatibilidad Universal")
    print("🔧 Instalación automática de dependencias")
    print("🧪 Pruebas integradas de funcionamiento")
    print("📚 Documentación completa incluida")
    print("=" * 60)
    print()

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}")
        if e.stderr.strip():
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Verifica la versión de Python"""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requiere Python 3.8+")
        return False

def install_dependencies():
    """Instala todas las dependencias necesarias"""
    print("\\n📦 Instalando dependencias...")
    
    dependencies = [
        "hyperliquid-python-sdk",
        "eth-account>=0.8.0",
        "web3>=6.0.0", 
        "requests>=2.28.0",
        "websocket-client>=1.5.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "ccxt>=4.0.0"
    ]
    
    success = True
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Instalando {dep}"):
            success = False
    
    return success

def setup_directories():
    """Crea directorios necesarios"""
    print("\\n📁 Configurando directorios...")
    
    directories = ["logs", "data"]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directorio {directory}/ creado")
        except Exception as e:
            print(f"⚠️  Error creando {directory}/: {str(e)}")

def check_config():
    """Verifica y guía la configuración"""
    print("\\n⚙️  Verificando configuración...")
    
    config_path = "config/config.json"
    
    if not os.path.exists(config_path):
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        auth = config.get('auth', {})
        account_address = auth.get('account_address', '')
        secret_key = auth.get('secret_key', '')
        
        if account_address == "YOUR_ACCOUNT_ADDRESS" or not account_address:
            print("⚠️  Necesitas configurar tu dirección de cuenta")
            print(f"   Edita {config_path} y cambia 'YOUR_ACCOUNT_ADDRESS'")
            return False
        
        if secret_key == "YOUR_SECRET_KEY" or not secret_key:
            print("⚠️  Necesitas configurar tu clave privada")
            print(f"   Edita {config_path} y cambia 'YOUR_SECRET_KEY'")
            return False
        
        print("✅ Configuración básica encontrada")
        print(f"   Cuenta: {account_address[:10]}...{account_address[-10:]}")
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo configuración: {str(e)}")
        return False

def run_diagnostics():
    """Ejecuta diagnósticos del sistema"""
    print("\\n🔍 Ejecutando diagnósticos...")
    
    # Diagnóstico del SDK
    if os.path.exists("diagnose_hyperliquid.py"):
        print("\\n--- Diagnóstico del SDK de Hyperliquid ---")
        if not run_command("python diagnose_hyperliquid.py", "Diagnóstico del SDK"):
            print("⚠️  Diagnóstico del SDK falló, pero continuando...")
    
    # Prueba de conexión v2
    if os.path.exists("test_connection_fixed_v2.py"):
        print("\\n--- Prueba de Conexión v2 ---")
        if run_command("python test_connection_fixed_v2.py", "Prueba de conexión v2"):
            print("✅ Conexión v2 funcionando correctamente")
            return True
        else:
            print("❌ Prueba de conexión v2 falló")
            return False
    
    return True

def show_next_steps():
    """Muestra los próximos pasos"""
    print("\\n" + "=" * 60)
    print("🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
    print("=" * 60)
    print()
    print("📝 PRÓXIMOS PASOS:")
    print()
    print("1. 📋 CONFIGURAR CREDENCIALES (si no lo has hecho):")
    print("   nano config/config.json")
    print("   # Cambia YOUR_ACCOUNT_ADDRESS y YOUR_SECRET_KEY")
    print()
    print("2. 🧪 EJECUTAR PRUEBAS:")
    print("   python test_connection_fixed_v2.py")
    print("   python test_integration.py")
    print()
    print("3. 🚀 EJECUTAR EL BOT:")
    print("   python src/main.py")
    print()
    print("4. 📊 MONITOREAR LOGS:")
    print("   tail -f logs/bot.log")
    print()
    print("=" * 60)
    print("💡 CONSEJOS IMPORTANTES:")
    print("=" * 60)
    print("• Empieza con cantidades pequeñas ($100-500)")
    print("• Monitorea las primeras operaciones de cerca")
    print("• Revisa los logs regularmente")
    print("• Ajusta parámetros según resultados")
    print()
    print("📚 DOCUMENTACIÓN:")
    print("• README.md - Guía completa")
    print("• MIGRATION_GUIDE.md - Guía de migración")
    print("• CHANGELOG.md - Registro de cambios")
    print()
    print("🆘 SOPORTE:")
    print("• python diagnose_hyperliquid.py - Diagnóstico")
    print("• Revisar logs/ para errores")
    print("• Verificar config/config.json")
    print()

def main():
    """Función principal de instalación"""
    print_banner()
    
    # Verificar Python
    if not check_python_version():
        print("\\n❌ Versión de Python incompatible. Instala Python 3.8 o superior.")
        return False
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("src") or not os.path.exists("config"):
        print("❌ Directorios src/ o config/ no encontrados")
        print("   Asegúrate de ejecutar este script desde el directorio raíz del bot")
        return False
    
    # Instalar dependencias
    if not install_dependencies():
        print("\\n❌ Error instalando dependencias. Revisa los errores arriba.")
        return False
    
    # Configurar directorios
    setup_directories()
    
    # Verificar configuración
    config_ok = check_config()
    
    # Ejecutar diagnósticos
    if config_ok:
        diagnostics_ok = run_diagnostics()
    else:
        print("\\n⚠️  Saltando diagnósticos - configura credenciales primero")
        diagnostics_ok = False
    
    # Mostrar próximos pasos
    show_next_steps()
    
    if config_ok and diagnostics_ok:
        print("🎯 ¡TODO LISTO! Tu bot está configurado y funcionando.")
        return True
    elif config_ok:
        print("⚠️  Bot instalado pero hay problemas de conexión. Revisa credenciales.")
        return True
    else:
        print("⚠️  Bot instalado pero necesitas configurar credenciales.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

