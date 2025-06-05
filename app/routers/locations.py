# app/routers/locations.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from models import crud, models, schemas
from models.database import get_db

router = APIRouter()

@router.post("/create")
async def create_location(
    name: str = Form(...),
    address: str = Form(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db)
):
    location = schemas.LocationCreate(
        name=name,
        address=address,
        company_id=company_id
    )
    crud.create_location(db, location)
    return RedirectResponse(url=f"/companies/{company_id}", status_code=302)

@router.get("/api/by-company/{company_id}")
async def get_locations_by_company(company_id: int, db: Session = Depends(get_db)):
    locations = crud.get_locations_by_company(db, company_id)
    return locations

@router.post("/{location_id}/edit")
async def update_location(
    location_id: int,
    name: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db)
):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location.name = name
    location.address = address
    db.commit()
    
    return RedirectResponse(url=f"/companies/{location.company_id}", status_code=302)

@router.post("/{location_id}/delete")
async def delete_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    company_id = location.company_id
    
    # Verificar si hay items asociados
    items_count = db.query(models.Item).filter(models.Item.location_id == location_id).count()
    if items_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete location with associated items")
    
    db.delete(location)
    db.commit()
    
    return RedirectResponse(url=f"/companies/{company_id}", status_code=302)
