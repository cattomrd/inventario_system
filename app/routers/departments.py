# app/routers/departments.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="../app/templates")

@router.get("/")
async def list_departaments(request: Request, db: Session = Depends(get_db)):
    companies = crud.get_departaments(db)
    return templates.TemplateResponse(
        "departaments/list.html",
        {"request": request, "companies": companies}
    )


@router.post("/create")
async def create_department(
    name: str = Form(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db)
):
    department = schemas.DepartmentCreate(name=name, company_id=company_id)
    crud.create_department(db, department)
    return RedirectResponse(url=f"/companies/{company_id}", status_code=302)

@router.get("/api/by-company/{company_id}")
async def get_departments_by_company(company_id: int, db: Session = Depends(get_db)):
    departments = crud.get_departments_by_company(db, company_id)
    return departments

@router.post("/{department_id}/delete")
async def delete_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    company_id = department.company_id
    
    # Verificar si hay usuarios asociados
    users_count = db.query(models.User).filter(models.User.department_id == department_id).count()
    if users_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete department with associated users")
    
    db.delete(department)
    db.commit()
    
    return RedirectResponse(url=f"/companies/{company_id}", status_code=302)

