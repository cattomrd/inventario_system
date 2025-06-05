from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def list_items(request: Request, db: Session = Depends(get_db)):
    items = crud.get_items(db)
    return templates.TemplateResponse(
        "items/list.html",
        {"request": request, "items": items}
    )

@router.get("/create")
async def create_item_form(request: Request, db: Session = Depends(get_db)):
    locations = db.query(models.Location).all()
    return templates.TemplateResponse(
        "items/create.html",
        {
            "request": request,
            "locations": locations,
            "item_types": [t.value for t in models.ItemType]
        }
    )

@router.post("/create")
async def create_item(
    brand: str = Form(...),
    model: str = Form(...),
    item_type: str = Form(...),
    serial_number: str = Form(...),
    purchase_date: date = Form(...),
    warranty_end_date: date = Form(None),
    supplier: str = Form(...),
    location_id: int = Form(...),
    db: Session = Depends(get_db)
):
    item = schemas.ItemCreate(
        brand=brand,
        model=model,
        item_type=item_type,
        serial_number=serial_number,
        purchase_date=purchase_date,
        warranty_end_date=warranty_end_date,
        supplier=supplier,
        location_id=location_id
    )
    crud.create_item(db, item)
    return RedirectResponse(url="/items", status_code=302)

@router.get("/{item_id}")
async def view_item(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    return templates.TemplateResponse(
        "items/detail.html",
        {"request": request, "item": item}
    )