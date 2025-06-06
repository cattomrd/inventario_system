# app/routers/users.py - Versión actualizada con AD
from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
import datetime
from typing import Optional
import io

from models import crud, models, schemas
from models.database import get_db
from services.add_service import ActiveDirectoryService
from services.export_service import ExportService

router = APIRouter()
templates = Jinja2Templates(directory="../app/templates")

# Instancia del servicio de AD
ad_service = ActiveDirectoryService()
export_service = ExportService()

@router.get("/", response_class=HTMLResponse)
async def list_users(
    request: Request, 
    search: Optional[str] = Query(None),
    source: Optional[str] = Query("local"),  # "local" o "ad"
    db: Session = Depends(get_db)
):
    """Lista usuarios desde base local o Active Directory"""
    
    if source == "ad":
        # Buscar en Active Directory
        search_term = search if search else ""
        ad_users = ad_service.search_users(search_term, max_results=200)
        
        return templates.TemplateResponse(
            "users/list_ad.html",
            {
                "request": request, 
                "users": ad_users,
                "search_term": search_term,
                "source": "ad"
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

@router.get("/ad-search", response_class=HTMLResponse)
async def ad_search_form(request: Request):
    """Formulario de búsqueda en Active Directory"""
    return templates.TemplateResponse(
        "users/ad_search.html",
        {"request": request}
    )

@router.post("/ad-search")
async def ad_search_users(
    request: Request,
    search_term: str = Form(""),
    max_results: int = Form(100),
    include_groups: bool = Form(False)
):
    """Buscar usuarios en Active Directory"""
    
    # Verificar conexión AD
    if not ad_service.test_connection():
        return templates.TemplateResponse(
            "users/ad_search.html",
            {
                "request": request,
                "error": "No se pudo conectar a Active Directory. Verifique la configuración."
            }
        )
    
    users = ad_service.search_users(search_term, max_results)
    
    # Incluir grupos si se solicita
    if include_groups:
        for user in users:
            user['groups'] = ad_service.get_user_groups(user['username'])
    
    return templates.TemplateResponse(
        "users/ad_results.html",
        {
            "request": request,
            "users": users,
            "search_term": search_term,
            "include_groups": include_groups,
            "total_results": len(users)
        }
    )

@router.get("/ad-user/{username}")
async def view_ad_user(request: Request, username: str):
    """Ver detalles de un usuario de AD"""
    user = ad_service.get_user_by_username(username)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en Active Directory")
    
    # Obtener grupos del usuario
    user['groups'] = ad_service.get_user_groups(username)
    
    return templates.TemplateResponse(
        "users/ad_detail.html",
        {"request": request, "user": user}
    )

@router.post("/import-from-ad")
async def import_user_from_ad(
    username: str = Form(...),
    department_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Importar usuario desde AD a la base local"""
    
    # Buscar usuario en AD
    ad_user = ad_service.get_user_by_username(username)
    if not ad_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en Active Directory")
    
    # Verificar si ya existe en la base local
    existing_user = db.query(models.User).filter(
        models.User.email == ad_user['email']
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe en la base local")
    
    # Crear usuario en base local
    user_data = schemas.UserCreate(
        email=ad_user['email'] or f"{username}@{ad_user['company']}.com",
        full_name=ad_user['display_name'] or f"{ad_user['first_name']} {ad_user['last_name']}",
        department_id=department_id
    )
    
    crud.create_user(db, user_data)
    return RedirectResponse(url="/users", status_code=302)

@router.get("/export")
async def export_users_form(request: Request):
    """Formulario para exportar usuarios"""
    return templates.TemplateResponse(
        "users/export.html",
        {"request": request}
    )

@router.post("/export")
async def export_users(
    format: str = Form(...),
    source: str = Form("local"),
    search_term: str = Form(""),
    include_groups: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Exportar usuarios en diferentes formatos"""
    
    if source == "ad":
        # Exportar desde Active Directory
        users = ad_service.search_users(search_term, max_results=1000)
        
        if include_groups:
            for user in users:
                user['groups'] = ', '.join(ad_service.get_user_groups(user['username']))
        
        data = users
        filename_prefix = "usuarios_ad"
    
    else:
        # Exportar desde base local
        users = crud.get_users(db)
        if search_term:
            users = [u for u in users if search_term.lower() in u.full_name.lower() or search_term.lower() in u.email.lower()]
        
        # Convertir a diccionarios
        data = []
        for user in users:
            user_dict = {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'department': user.department.name if user.department else '',
                'company': user.department.company.name if user.department else '',
                'created_at': user.created_at
            }
            data.append(user_dict)
        
        filename_prefix = "usuarios_local"
    
    # Generar export según formato
    if format == "excel":
        buffer = export_service.export_to_excel(data)
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif format == "csv":
        csv_data = export_service.export_to_csv(data)
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif format == "json":
        json_data = export_service.export_to_json(data)
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            io.StringIO(json_data),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Formato de exportación no válido")

@router.get("/test-ad-connection")
async def test_ad_connection():
    """Probar conexión con Active Directory"""
    try:
        connection_ok = ad_service.test_connection()
        if connection_ok:
            return {"status": "success", "message": "Conexión a Active Directory exitosa"}
        else:
            return {"status": "error", "message": "No se pudo conectar a Active Directory"}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

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