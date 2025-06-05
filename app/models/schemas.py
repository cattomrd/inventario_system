from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from .models import ItemType

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    company_id: int

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str
    company_id: int

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    full_name: str
    department_id: int

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    brand: str
    model: str
    item_type: ItemType
    serial_number: str
    purchase_date: date
    warranty_end_date: Optional[date] = None
    supplier: str
    location_id: int

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssignmentBase(BaseModel):
    item_id: int
    user_id: int
    notes: Optional[str] = None

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    assigned_date: datetime
    returned_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True