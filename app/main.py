from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from models import models
from models.database import engine, Base, get_db
from routers import items, companies, departments, locations, users, assignments
import uvicorn

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Inventario IT")

app.mount("/static", StaticFiles(directory="../app/static"), name="static")
templates = Jinja2Templates(directory="../app/templates")

# Incluir routers
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(departments.router, prefix="/departments", tags=["departments"])
app.include_router(locations.router, prefix="/locations", tags=["locations"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    items_count = db.query(models.Item).count()
    users_count = db.query(models.User).count()
    active_assignments = db.query(models.Assignment).filter(
        models.Assignment.returned_date == None
    ).count()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items_count": items_count,
            "users_count": users_count,
            "active_assignments": active_assignments
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)