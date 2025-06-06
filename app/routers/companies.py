# app/routers/companies.py
from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="../app/templates")

@router.get("/")
async def list_companies(request: Request, db: Session = Depends(get_db)):
    companies = crud.get_companies(db)
    return templates.TemplateResponse(
        "companies/list.html",
        {"request": request, "companies": companies}
    )

@router.get("/create")
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

