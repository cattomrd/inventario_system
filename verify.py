#!/usr/bin/env python3
# verify_setup.py - Script para verificar que todo esté configurado correctamente

import os
import sys
from pathlib import Path

def check_file_structure():
    """Verificar estructura de archivos"""
    print("📁 Verificando estructura de archivos...")
    
    required_files = [
        "app/services/__init__.py",
        "app/services/ad_service.py", 
        "app/routers/users.py",
        "app/models/models.py",
        "app/models/database.py",
        "app/templates/base.html",
        "app/templates/users/list_ad.html",
        "app/templates/users/ad_debug.html",
        ".env"
    ]
    
    required_dirs = [
        "app",
        "app/services",
        "app/routers", 
        "app/models",
        "app/templates",
        "app/templates/users"
    ]
    
    # Verificar directorios
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directorio: {directory}")
        else:
            print(f"❌ Falta directorio: {directory}")
            os.makedirs(directory, exist_ok=True)
            print(f"   📁 Creado: {directory}")
    
    # Verificar archivos
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Archivo: {file_path}")
        else:
            print(f"❌ Falta archivo: {file_path}")
            missing_files.append(file_path)
    
    return missing_files

def check_dependencies():
    """Verificar dependencias de Python"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        "fastapi",
        "sqlalchemy", 
        "psycopg2-binary",
        "python-dotenv",
        "jinja2",
        "ldap3",
        "pandas",
        "openpyxl"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    return missing_packages

def check_env_config():
    """Verificar configuración de variables de entorno"""
    print("\n🔧 Verificando configuración .env...")
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "AD_SERVER_HOST",
        "AD_BASE_DN", 
        "AD_BIND_USER",
        "AD_BIND_PASSWORD"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {var}: configurado")
        else:
            print(f"❌ {var}: no configurado o vacío")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def test_ad_import():
    """Probar importación del servicio AD"""
    print("\n🔌 Probando importación de servicios...")
    
    try:
        # Agregar el directorio app al path para las importaciones
        sys.path.insert(0, 'app')
        
        from services.ad_service import ActiveDirectoryService
        print("✅ ActiveDirectoryService importado correctamente")
        
        # Intentar instanciar (sin conectar)
        ad_service = ActiveDirectoryService()
        print("✅ ActiveDirectoryService instanciado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando ActiveDirectoryService: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error instanciando ActiveDirectoryService: {e}")
        print("   (Esto puede ser normal si las variables de entorno no están configuradas)")
        return True

def create_missing_files():
    """Crear archivos básicos faltantes"""
    print("\n🛠️ Creando archivos básicos faltantes...")
    
    # Crear __init__.py para services si no existe
    services_init = "app/services/__init__.py"
    if not os.path.exists(services_init):
        with open(services_init, 'w') as f:
            f.write('from .ad_service import ActiveDirectoryService\n')
        print(f"✅ Creado: {services_init}")
    
    # Crear .env básico si no existe
    if not os.path.exists('.env'):
        env_content = """# Database
DATABASE_URL=postgresql://usuario:contraseña@localhost/inventory_db

# Active Directory Configuration
AD_SERVER_HOST=ikeaspc.ikeasi.com
AD_SERVER_PORT=389
AD_USE_SSL=false
AD_BASE_DN=DC=ikeasi,DC=com
AD_BIND_USER=su-jorge.romero@ikeasi.com
AD_BIND_PASSWORD=Isl@sV@leares,.,2025**
AD_USER_SEARCH_BASE=DC=ikeasi,DC=com

# Application Settings
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=true"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"✅ Creado: .env con configuración básica")

def main():
    """Función principal de verificación"""
    print("🚀 Verificación de configuración del Sistema de Inventario IT")
    print("=" * 65)
    
    # 1. Verificar estructura de archivos
    missing_files = check_file_structure()
    
    # 2. Crear archivos faltantes básicos
    if missing_files:
        create_missing_files()
    
    # 3. Verificar dependencias
    missing_packages = check_dependencies()
    
    # 4. Verificar configuración
    env_ok = check_env_config()
    
    # 5. Probar importaciones
    import_ok = test_ad_import()
    
    # Resumen final
    print("\n" + "=" * 65)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 65)
    
    if missing_packages:
        print("❌ DEPENDENCIAS FALTANTES:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n🔧 Para instalar:")
        print(f"   pip install {' '.join(missing_packages)}")
    else:
        print("✅ Todas las dependencias están instaladas")
    
    if not env_ok:
        print("\n❌ CONFIGURACIÓN INCOMPLETA:")
        print("   - Edita el archivo .env con tu configuración real de AD")
    else:
        print("\n✅ Configuración de variables de entorno completa")
    
    if not import_ok:
        print("\n❌ PROBLEMAS DE IMPORTACIÓN:")
        print("   - Verifica la estructura de archivos")
        print("   - Asegúrate de que app/services/ad_service.py existe")
    else:
        print("\n✅ Servicios importados correctamente")
    
    # Instrucciones finales
    print("\n🚀 PRÓXIMOS PASOS:")
    
    if missing_packages:
        print("1. Instalar dependencias faltantes:")
        print(f"   pip install {' '.join(missing_packages)}")
    
    if not env_ok:
        print("2. Editar archivo .env con configuración real:")
        print("   - Verificar servidor AD")
        print("   - Confirmar credenciales")
        print("   - Ajustar Base DN")
    
    print("3. Ejecutar diagnósticos:")
    print("   python verify_setup.py")
    print("   python test_ad_schema.py")
    
    print("4. Iniciar aplicación:")
    print("   python app/main.py")
    
    print("5. Probar en navegador:")
    print("   http://localhost:8000/users/ad-debug")
    
    # Verificación específica para el error actual
    print("\n🔍 VERIFICACIÓN ESPECÍFICA PARA TU ERROR:")
    print("=" * 50)
    
    print("El error 'object has no attribute search_users' indica:")
    print("✓ Reemplazar app/services/ad_service.py con la versión completa")
    print("✓ Verificar que app/services/__init__.py existe")
    print("✓ Reiniciar la aplicación después de los cambios")
    
    if all([not missing_packages, env_ok, import_ok]):
        print("\n🎉 ¡CONFIGURACIÓN COMPLETA!")
        print("Tu sistema debería funcionar correctamente ahora.")
        return True
    else:
        print("\n⚠️ Configuración incompleta. Sigue los pasos anteriores.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)