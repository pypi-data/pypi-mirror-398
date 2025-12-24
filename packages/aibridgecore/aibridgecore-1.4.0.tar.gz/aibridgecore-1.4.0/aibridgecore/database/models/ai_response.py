from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AIResponse(Base):
    __tablename__ = "ai_reponse"
    id = Column(String, primary_key=True)
    model = Column(String)
    response = Column(String)
    updated_at = Column(Integer)
    created_at = Column(Integer)
