# app/routers/companies.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="/app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_companies(request: Request, db: Session = Depends(get_db)):
    companies = crud.get_companies(db)
    return templates.TemplateResponse(
        "companies/list.html",
        {"request": request, "companies": companies}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_company_form(request: Request):
    return templates.TemplateResponse(
        "companies/create.html",
        {"request": request}
    )

@router.post("/create")
async def create_company(
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    company = schemas.CompanyCreate(name=name)
    crud.create_company(db, company)
    return RedirectResponse(url="/companies", status_code=302)

@router.get("/{company_id}", response_class=HTMLResponse)
async def view_company(request: Request, company_id: int, db: Session = Depends(get_db)):
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    locations = crud.get_locations_by_company(db, company_id)
    departments = crud.get_departments_by_company(db, company_id)
    
    return templates.TemplateResponse(
        "companies/detail.html",
        {
            "request": request,
            "company": company,
            "locations": locations,
            "departments": departments
        }
    )

@router.get("/{company_id}/edit", response_class=HTMLResponse)
async def edit_company_form(request: Request, company_id: int, db: Session = Depends(get_db)):
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return templates.TemplateResponse(
        "companies/edit.html",
        {"request": request, "company": company}
    )

@router.post("/{company_id}/edit")
async def update_company(
    company_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.name = name
    db.commit()
    
    return RedirectResponse(url=f"/companies/{company_id}", status_code=302)