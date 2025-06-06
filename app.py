from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from ldap3 import Server, Connection, ALL, NTLM
from typing import Optional
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Active Directory Authentication API",
    description="API para autenticar usuarios contra Active Directory 2016",
    version="1.0.0"
)

security = HTTPBasic()

# Configuración de Active Directory (modificar según tu entorno)
AD_SERVER = os.getenv("ikeaspc.ikeasi.com")
AD_DOMAIN = os.getenv("ikeaspc.ikeasi.com")
AD_SEARCH_TREE = os.getenv("AD_USER_SEARCH_BASE")
AD_USER = os.getenv("AD_BIND_USER")  # Usuario con permisos de lectura
AD_PASSWORD = os.getenv("AD_BIND_PASSWORD")

class UserInfo(BaseModel):
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    groups: Optional[list] = None
    department: Optional[str] = None
    title: Optional[str] = None

def authenticate_ad_user(username: str, password: str) -> bool:
    """Autentica un usuario contra Active Directory"""
    try:
        user_dn = f"{username}@{AD_DOMAIN}"
        server = Server(AD_SERVER, get_info=ALL)
        conn = Connection(server, user=user_dn, password=password, authentication=NTLM)
        if conn.bind():
            conn.unbind()
            return True
        return False
    except Exception:
        return False

def get_ad_user_info(username: str) -> Optional[UserInfo]:
    """Obtiene información de un usuario desde Active Directory"""
    try:
        server = Server(AD_SERVER, get_info=ALL)
        conn = Connection(server, user=AD_USER, password=AD_PASSWORD, auto_bind=True)
        
        search_filter = f"(sAMAccountName={username})"
        conn.search(AD_SEARCH_TREE, search_filter, attributes=[
            'displayName', 
            'mail', 
            'memberOf', 
            'department',
            'title'
        ])
        
        if len(conn.entries) == 0:
            return None
            
        entry = conn.entries[0]
        user_info = UserInfo(
            username=username,
            display_name=str(entry.displayName) if 'displayName' in entry else None,
            email=str(entry.mail) if 'mail' in entry else None,
            groups=[str(group) for group in entry.memberOf] if 'memberOf' in entry else None,
            department=str(entry.department) if 'department' in entry else None,
            title=str(entry.title) if 'title' in entry else None
        )
        
        conn.unbind()
        return user_info
    except Exception as e:
        print(f"Error al consultar AD: {str(e)}")
        return None

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Valida las credenciales básicas y devuelve el nombre de usuario"""
    if not authenticate_ad_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/auth/userinfo", response_model=UserInfo)
async def get_user_info(username: str = Depends(get_current_username)):
    """Endpoint para obtener información del usuario autenticado"""
    user_info = get_ad_user_info(username)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en Active Directory"
        )
    return user_info

@app.post("/auth/validate")
async def validate_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint para validar credenciales sin retornar información del usuario"""
    if not authenticate_ad_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"message": "Credenciales válidas"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)