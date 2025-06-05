#!/usr/bin/env python3
"""
Script de instalación y configuración para la corrección de Hyperliquid v2.
Instala dependencias faltantes y configura el entorno con la versión corregida.
"""

import subprocess
import sys
import os
import shutil

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}")
        print(f"   Error: {e.stderr.strip()}")
        return False

def install_dependencies():
    """Instala dependencias faltantes"""
    print("=== Instalación de Dependencias v2 ===\\n")
    
    # Lista de dependencias necesarias
    dependencies = [
        "websocket-client",
        "ccxt>=4.0.0"
    ]
    
    success = True
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Instalando {dep}"):
            success = False
    
    return success

def backup_original_files():
    """Crea respaldo de archivos originales"""
    print("\\n=== Creando Respaldos v2 ===\\n")
    
    files_to_backup = [
        "src/connection.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                shutil.copy2(file_path, backup_path)
                print(f"✅ Respaldo creado: {backup_path}")
            except Exception as e:
                print(f"⚠️  Error creando respaldo de {file_path}: {str(e)}")
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")

def apply_fixes_v2():
    """Aplica las correcciones v2 necesarias"""
    print("\\n=== Aplicando Correcciones v2 ===\\n")
    
    # Verificar que los archivos corregidos existen
    if not os.path.exists("connection_fixed_v2.py"):
        print("❌ Archivo connection_fixed_v2.py no encontrado")
        print("   Asegúrate de haber descargado todos los archivos de la corrección v2")
        return False
    
    # Reemplazar archivo de conexión
    try:
        if os.path.exists("src/connection.py"):
            shutil.copy2("connection_fixed_v2.py", "src/connection.py")
            print("✅ Archivo src/connection.py actualizado con versión v2")
        else:
            print("❌ Directorio src/ no encontrado")
            return False
    except Exception as e:
        print(f"❌ Error aplicando corrección v2: {str(e)}")
        return False
    
    return True

def verify_installation_v2():
    """Verifica que la instalación v2 sea correcta"""
    print("\\n=== Verificación v2 ===\\n")
    
    # Verificar importaciones
    try:
        print("🔍 Verificando importaciones v2...")
        
        # Verificar hyperliquid
        import hyperliquid.exchange
        import hyperliquid.api
        print("✅ hyperliquid.exchange y hyperliquid.api disponibles")
        
        # Verificar websocket-client
        import websocket
        print("✅ websocket-client disponible")
        
        # Verificar ccxt
        import ccxt
        print(f"✅ ccxt disponible (versión: {ccxt.__version__})")
        
        # Verificar que la nueva conexión se puede importar
        sys.path.append('.')
        from connection_fixed_v2 import HyperliquidConnection
        print("✅ HyperliquidConnection v2 se puede importar correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 Configuración de Corrección v2 para Hyperliquid Bot\\n")
    print("Esta versión corrige el problema con skip_ws y mejora la compatibilidad\\n")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("src"):
        print("❌ No se encontró el directorio 'src'")
        print("   Asegúrate de ejecutar este script desde el directorio raíz del bot")
        return False
    
    # Paso 1: Instalar dependencias
    if not install_dependencies():
        print("\\n❌ Error instalando dependencias")
        return False
    
    # Paso 2: Crear respaldos
    backup_original_files()
    
    # Paso 3: Aplicar correcciones v2
    if not apply_fixes_v2():
        print("\\n❌ Error aplicando correcciones v2")
        return False
    
    # Paso 4: Verificar instalación v2
    if not verify_installation_v2():
        print("\\n❌ Error en verificación v2")
        return False
    
    print("\\n🎉 ¡Configuración v2 completada exitosamente!")
    print("\\n📝 Próximos pasos:")
    print("   1. Ejecuta: python test_connection_fixed_v2.py")
    print("   2. Si la prueba es exitosa, ejecuta tu bot normalmente")
    print("   3. Si hay problemas, revisa los respaldos en *.backup")
    print("\\n💡 Mejoras en v2:")
    print("   - Eliminado parámetro skip_ws problemático")
    print("   - Mejor manejo de errores de inicialización")
    print("   - Compatibilidad mejorada con tu versión del SDK")
    print("   - Integración optimizada con ccxt para trading")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

