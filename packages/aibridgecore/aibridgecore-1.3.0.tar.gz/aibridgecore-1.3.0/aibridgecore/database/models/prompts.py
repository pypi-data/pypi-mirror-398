from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class Prompts(Base):
    __tablename__ = 'prompts'
    id = Column(String, primary_key=True)
    name = Column(String,unique=True)
    prompt=Column(String)
    prompt_data=Column(String)
    variables=Column(String)
    updated_at = Column(Integer)
    created_at = Column(Integer)
