# app/routers/users.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="../app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_users(request: Request, db: Session = Depends(get_db)):
    users = crud.get_users(db)
    return templates.TemplateResponse(
        "users/list.html",
        {"request": request, "users": users}
    )

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

@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    departments = db.query(models.Department).all()
    
    return templates.TemplateResponse(
        "users/edit.html",
        {
            "request": request,
            "user": user,
            "departments": departments
        }
    )

@router.post("/{user_id}/edit")
async def update_user(
    user_id: int,
    email: str = Form(...),
    full_name: str = Form(...),
    department_id: int = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar si el nuevo email ya existe (excepto para el mismo usuario)
    existing_user = db.query(models.User).filter(
        models.User.email == email,
        models.User.id != user_id
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user.email = email
    user.full_name = full_name
    user.department_id = department_id
    db.commit()
    
    return RedirectResponse(url=f"/users/{user_id}", status_code=302)

@router.post("/{user_id}/delete")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar si tiene asignaciones activas
    active_assignments = db.query(models.Assignment).filter(
        models.Assignment.user_id == user_id,
        models.Assignment.returned_date == None
    ).count()
    
    if active_assignments > 0:
        raise HTTPException(status_code=400, detail="Cannot delete user with active assignments")
    
    db.delete(user)
    db.commit()
    
    return RedirectResponse(url="/users", status_code=302)

