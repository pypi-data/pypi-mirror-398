from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class Variables(Base):
    __tablename__ = 'variables'
    id = Column(String, primary_key=True)
    key=Column(String,unique=True)
    value=Column(String)
    updated_at = Column(Integer)
    created_at = Column(Integer)

