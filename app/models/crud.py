from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

# Company CRUD
def get_company(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# Location CRUD
def create_location(db: Session, location: schemas.LocationCreate):
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_locations_by_company(db: Session, company_id: int):
    return db.query(models.Location).filter(models.Location.company_id == company_id).all()

# Department CRUD
def create_department(db: Session, department: schemas.DepartmentCreate):
    db_department = models.Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def get_departments_by_company(db: Session, company_id: int):
    return db.query(models.Department).filter(models.Department.company_id == company_id).all()

# User CRUD
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# Item CRUD
def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items_by_location(db: Session, location_id: int):
    return db.query(models.Item).filter(models.Item.location_id == location_id).all()

# Assignment CRUD
def create_assignment(db: Session, assignment: schemas.AssignmentCreate):
    db_assignment = models.Assignment(**assignment.dict())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def get_active_assignments(db: Session):
    return db.query(models.Assignment).filter(models.Assignment.returned_date == None).all()

def return_item(db: Session, assignment_id: int):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if assignment:
        assignment.returned_date = datetime.utcnow()
        db.commit()
        db.refresh(assignment)
    return assignment