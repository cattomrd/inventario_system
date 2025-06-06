# credential_test.py - Script para probar diferentes formatos de credenciales

import os
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL

load_dotenv()

def test_different_credential_formats():
    """Probar diferentes formatos de credenciales para AD"""
    
    server_host = os.getenv("AD_SERVER_HOST")
    server_port = int(os.getenv("AD_SERVER_PORT", 389))
    base_dn = os.getenv("AD_BASE_DN")
    password = os.getenv("AD_BIND_PASSWORD")
    
    print("🔍 Probando diferentes formatos de credenciales...")
    print("=" * 60)
    
    # Crear servidor
    server = Server(server_host, port=server_port, get_info=ALL)
    
    # Diferentes formatos a probar
    credential_formats = [
        # Formato actual
        ("UPN Original", os.getenv("AD_BIND_USER")),
        
        # Formato DN si el usuario está en una OU específica
        ("DN Format", f"CN=Jorge Romero,OU=Users,{base_dn}"),
        ("DN Format Alt", f"CN=su-jorge.romero,OU=Users,{base_dn}"),
        ("DN Format Service", f"CN=Jorge Romero,OU=Service Accounts,{base_dn}"),
        
        # Formato SAM Account Name
        ("SAM@Domain", "su-jorge.romero@ikeasi.com"),
        ("SAM Only", "su-jorge.romero"),
        
        # Formato Domain\User
        ("Domain\\User", "ikeasi\\su-jorge.romero"),
        ("NETBIOS\\User", "IKEASI\\su-jorge.romero"),
        
        # Sin prefijo su-
        ("Without prefix", "jorge.romero@ikeasi.com"),
        
        # Formatos alternativos comunes
        ("Uppercase domain", "su-jorge.romero@IKEASI.COM"),
        ("Different OU", f"CN=su-jorge.romero,CN=Users,{base_dn}"),
    ]
    
    successful_formats = []
    
    for format_name, username in credential_formats:
        if not username:
            continue
            
        print(f"\n🔐 Probando: {format_name}")
        print(f"   Usuario: {username}")
        
        try:
            conn = Connection(
                server,
                user=username,
                password=password,
                auto_bind=True
            )
            
            print("   ✅ ÉXITO - Credenciales válidas!")
            successful_formats.append((format_name, username))
            conn.unbind()
            
        except Exception as e:
            error_msg = str(e)
            if "invalidCredentials" in error_msg:
                print(f"   ❌ Credenciales inválidas")
            elif "invalidDNSyntax" in error_msg:
                print(f"   ⚠️  Sintaxis DN inválida")
            elif "noSuchObject" in error_msg:
                print(f"   ⚠️  Usuario no encontrado")
            else:
                print(f"   ❌ Error: {error_msg}")
    
    print("\n" + "=" * 60)
    if successful_formats:
        print("✅ FORMATOS EXITOSOS:")
        for format_name, username in successful_formats:
            print(f"   - {format_name}: {username}")
        print(f"\n💡 Usa el primer formato exitoso en tu archivo .env")
    else:
        print("❌ NINGÚN FORMATO FUNCIONÓ")
        print("\n🔧 Posibles causas:")
        print("   1. Contraseña incorrecta")
        print("   2. Usuario bloqueado o deshabilitado")
        print("   3. Usuario no existe")
        print("   4. Políticas de dominio restrictivas")
        print("   5. Servidor AD incorrecto")

def verify_account_status():
    """Información adicional para verificar el estado de la cuenta"""
    
    print("\n🔍 VERIFICACIONES ADICIONALES A REALIZAR:")
    print("=" * 60)
    
    print("\n1. Verificar en Active Directory Users and Computers:")
    print("   - ¿El usuario 'su-jorge.romero' existe?")
    print("   - ¿Está habilitado? (sin X roja)")
    print("   - ¿No está bloqueado?")
    print("   - ¿No ha expirado?")
    
    print("\n2. Verificar contraseña:")
    print("   - ¿La contraseña es correcta?")
    print("   - ¿No ha expirado?")
    print("   - ¿Funciona para login normal en Windows?")
    
    print("\n3. Verificar permisos:")
    print("   - ¿El usuario tiene permisos de login como servicio?")
    print("   - ¿Puede hacer consultas LDAP?")
    
    print("\n4. Probar manualmente:")
    print(f"   ldapsearch -H ldap://{os.getenv('AD_SERVER_HOST')}:389 \\")
    print(f"     -D 'su-jorge.romero@ikeasi.com' \\")
    print(f"     -W \\")
    print(f"     -b '{os.getenv('AD_BASE_DN')}' \\")
    print(f"     '(objectClass=user)'")

if __name__ == "__main__":
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado!")
        exit(1)
    
    # Verificar variables básicas
    required_vars = ['AD_SERVER_HOST', 'AD_BASE_DN', 'AD_BIND_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Variables faltantes: {missing}")
        exit(1)
    
    test_different_credential_formats()
    verify_account_status()