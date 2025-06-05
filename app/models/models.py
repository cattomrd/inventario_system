from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class ItemType(str, enum.Enum):
    LAPTOP = "laptop"
    DESKTOP = "desktop"
    PHONE = "phone"
    PRINTER = "printer"
    TABLET = "tablet"
    MONITOR = "monitor"
    ROUTER = "router"
    OTHER = "other"

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    locations = relationship("Location", back_populates="company")
    departments = relationship("Department", back_populates="company")

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(Text)
    company_id = Column(Integer, ForeignKey("companies.id"))
    
    company = relationship("Company", back_populates="locations")
    items = relationship("Item", back_populates="location")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    
    company = relationship("Company", back_populates="departments")
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    department = relationship("Department", back_populates="users")
    assignments = relationship("Assignment", back_populates="user")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String)
    model = Column(String)
    item_type = Column(Enum(ItemType))
    serial_number = Column(String, unique=True, index=True)
    purchase_date = Column(Date)
    warranty_end_date = Column(Date)
    supplier = Column(String)
    location_id = Column(Integer, ForeignKey("locations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    location = relationship("Location", back_populates="items")
    assignments = relationship("Assignment", back_populates="item")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    assigned_date = Column(DateTime, default=datetime.utcnow)
    returned_date = Column(DateTime, nullable=True)
    notes = Column(Text)
    
    item = relationship("Item", back_populates="assignments")
    user = relationship("User", back_populates="assignments")