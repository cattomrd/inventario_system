# app/routers/users.py - Router corregido con imports apropiados

from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
from datetime import datetime

# Imports del proyecto
from models import crud, models, schemas
from models.database import get_db

# Import del servicio AD con manejo de errores
try:
    from services.ad_service import ActiveDirectoryService
    AD_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ActiveDirectoryService: {e}")
    AD_AVAILABLE = False
    ActiveDirectoryService = None

# Import del servicio de export con manejo de errores  
try:
    from services.export_service import ExportService
    EXPORT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ExportService: {e}")
    EXPORT_AVAILABLE = False
    ExportService = None

router = APIRouter()
templates = Jinja2Templates(directory="../app/templates")

# Instanciar servicios solo si están disponibles
if AD_AVAILABLE:
    try:
        ad_service = ActiveDirectoryService()
    except Exception as e:
        print(f"Warning: Could not initialize AD service: {e}")
        ad_service = None
        AD_AVAILABLE = False
else:
    ad_service = None

if EXPORT_AVAILABLE:
    try:
        export_service = ExportService()
    except Exception as e:
        print(f"Warning: Could not initialize Export service: {e}")
        export_service = None
        EXPORT_AVAILABLE = False
else:
    export_service = None

@router.get("/", response_class=HTMLResponse)
async def list_users(
    request: Request, 
    search: Optional[str] = Query(None),
    source: Optional[str] = Query("local"),
    db: Session = Depends(get_db)
):
    """Lista usuarios desde base local o Active Directory"""
    
    if source == "ad":
        # Verificar si AD está disponible
        if not AD_AVAILABLE or not ad_service:
            return templates.TemplateResponse(
                "users/list_ad.html",
                {
                    "request": request, 
                    "users": [],
                    "search_term": search or "",
                    "source": "ad",
                    "error": "Active Directory no está configurado o disponible",
                    "config_error": True
                }
            )
        
        # Verificar configuración antes de intentar buscar
        try:
            config_status = ad_service.get_config_status()
            if config_status["status"] == "invalid":
                return templates.TemplateResponse(
                    "users/list_ad.html",
                    {
                        "request": request, 
                        "users": [],
                        "search_term": search or "",
                        "source": "ad",
                        "error": f"Configuración de AD inválida: {config_status['error']}",
                        "config_error": True
                    }
                )
        except Exception as e:
            return templates.TemplateResponse(
                "users/list_ad.html",
                {
                    "request": request, 
                    "users": [],
                    "search_term": search or "",
                    "source": "ad",
                    "error": f"Error al verificar configuración: {str(e)}",
                    "config_error": True
                }
            )
        
        # Buscar en Active Directory
        search_term = search if search else ""
        try:
            ad_users = ad_service.search_users(search_term, max_results=200)
            
            return templates.TemplateResponse(
                "users/list_ad.html",
                {
                    "request": request, 
                    "users": ad_users,
                    "search_term": search_term,
                    "source": "ad",
                    "config_status": config_status
                }
            )
        except Exception as e:
            return templates.TemplateResponse(
                "users/list_ad.html",
                {
                    "request": request, 
                    "users": [],
                    "search_term": search_term,
                    "source": "ad",
                    "error": f"Error al buscar usuarios: {str(e)}",
                    "search_error": True
                }
            )
    else:
        # Buscar en base local (comportamiento original)
        users = crud.get_users(db)
        if search:
            users = [u for u in users if search.lower() in u.full_name.lower() or search.lower() in u.email.lower()]
        
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request, 
                "users": users,
                "search_term": search,
                "source": "local"
            }
        )

@router.get("/test-ad-connection")
async def test_ad_connection():
    """Probar conexión con Active Directory"""
    if not AD_AVAILABLE or not ad_service:
        return {
            "success": False,
            "error": "Active Directory service not available",
            "details": "Check if AD service is properly configured and imported"
        }
    
    try:
        result = ad_service.test_connection()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "details": "Check logs for more information"
        }

@router.get("/ad-config-status")
async def get_ad_config_status():
    """Obtener estado detallado de la configuración de AD"""
    if not AD_AVAILABLE or not ad_service:
        return {
            "status": "unavailable",
            "error": "Active Directory service not available"
        }
    
    try:
        return ad_service.get_config_status()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/ad-debug", response_class=HTMLResponse)
async def ad_debug_page(request: Request):
    """Página de diagnóstico de Active Directory"""
    
    if not AD_AVAILABLE or not ad_service:
        config_status = {"status": "unavailable", "error": "AD service not available"}
        connection_test = {"success": False, "error": "AD service not available"}
    else:
        try:
            config_status = ad_service.get_config_status()
            connection_test = ad_service.test_connection()
        except Exception as e:
            config_status = {"status": "error", "error": str(e)}
            connection_test = {"success": False, "error": str(e)}
    
    return templates.TemplateResponse(
        "users/ad_debug.html",
        {
            "request": request,
            "config_status": config_status,
            "connection_test": connection_test,
            "ad_available": AD_AVAILABLE
        }
    )

@router.get("/ad-user/{username}")
async def view_ad_user(request: Request, username: str):
    """Ver detalles de un usuario de AD"""
    
    if not AD_AVAILABLE or not ad_service:
        raise HTTPException(status_code=503, detail="Active Directory service not available")
    
    try:
        user = ad_service.get_user_by_username(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en Active Directory")
        
        # Obtener grupos del usuario
        user['groups'] = ad_service.get_user_groups(username)
        
        return templates.TemplateResponse(
            "users/ad_detail.html",
            {"request": request, "user": user}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing AD user: {str(e)}")

# Mantener las rutas originales para compatibilidad
@router.get("/create", response_class=HTMLResponse)
async def create_user_form(request: Request, db: Session = Depends(get_db)):
    departments = db.query(models.Department).all()
    return templates.TemplateResponse(
        "users/create.html",
        {"request": request, "departments": departments}
    )

@router.post("/create")
async def create_user(
    email: str = Form(...),
    full_name: str = Form(...),
    department_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Verificar si el email ya existe
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = schemas.UserCreate(
        email=email,
        full_name=full_name,
        department_id=department_id
    )
    crud.create_user(db, user)
    return RedirectResponse(url="/users", status_code=302)

@router.get("/{user_id}", response_class=HTMLResponse)
async def view_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Obtener asignaciones activas del usuario
    active_assignments = db.query(models.Assignment).filter(
        models.Assignment.user_id == user_id,
        models.Assignment.returned_date == None
    ).all()
    
    # Obtener historial de asignaciones
    assignment_history = db.query(models.Assignment).filter(
        models.Assignment.user_id == user_id
    ).order_by(models.Assignment.assigned_date.desc()).all()
    
    return templates.TemplateResponse(
        "users/detail.html",
        {
            "request": request,
            "user": user,
            "active_assignments": active_assignments,
            "assignment_history": assignment_history
        }
    )