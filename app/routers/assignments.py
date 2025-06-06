# app/routers/assignments.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="../app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_assignments(request: Request, db: Session = Depends(get_db)):
    assignments = crud.get_active_assignments(db)
    return templates.TemplateResponse(
        "assignments/list.html",
        {"request": request, "assignments": assignments}
    )

@router.get("/history", response_class=HTMLResponse)
async def assignment_history(request: Request, db: Session = Depends(get_db)):
    # Obtener todas las asignaciones (activas e históricas)
    all_assignments = db.query(models.Assignment).order_by(
        models.Assignment.assigned_date.desc()
    ).all()
    
    return templates.TemplateResponse(
        "assignments/history.html",
        {"request": request, "assignments": all_assignments}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_assignment_form(request: Request, db: Session = Depends(get_db)):
    # Obtener items no asignados
    all_items = db.query(models.Item).all()
    assigned_items = db.query(models.Assignment).filter(
        models.Assignment.returned_date == None
    ).all()
    assigned_item_ids = [a.item_id for a in assigned_items]
    
    available_items = [item for item in all_items if item.id not in assigned_item_ids]
    users = crud.get_users(db)
    
    return templates.TemplateResponse(
        "assignments/create.html",
        {
            "request": request,
            "available_items": available_items,
            "users": users
        }
    )

@router.post("/create")
async def create_assignment(
    item_id: int = Form(...),
    user_id: int = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    # Verificar que el item no esté ya asignado
    existing_assignment = db.query(models.Assignment).filter(
        models.Assignment.item_id == item_id,
        models.Assignment.returned_date == None
    ).first()
    
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Item is already assigned")
    
    assignment = schemas.AssignmentCreate(
        item_id=item_id,
        user_id=user_id,
        notes=notes
    )
    crud.create_assignment(db, assignment)
    return RedirectResponse(url="/assignments", status_code=302)

@router.post("/{assignment_id}/return")
async def return_assignment(
    assignment_id: int,
    db: Session = Depends(get_db)
):
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.returned_date:
        raise HTTPException(status_code=400, detail="Item already returned")
    
    assignment.returned_date = datetime.utcnow()
    db.commit()
    
    return RedirectResponse(url="/assignments", status_code=302)

@router.get("/{assignment_id}", response_class=HTMLResponse)
async def view_assignment(request: Request, assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return templates.TemplateResponse(
        "assignments/detail.html",
        {"request": request, "assignment": assignment}
    )

@router.post("/{assignment_id}/update-notes")
async def update_assignment_notes(
    assignment_id: int,
    notes: str = Form(...),
    db: Session = Depends(get_db)
):
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.notes = notes
    db.commit()
    
    return RedirectResponse(url=f"/assignments/{assignment_id}", status_code=302)