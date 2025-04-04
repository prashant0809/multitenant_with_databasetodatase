from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    db_url = Column(String, unique=True)

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # Hashed Password
    org_id = Column(Integer, ForeignKey("organizations.id"))
