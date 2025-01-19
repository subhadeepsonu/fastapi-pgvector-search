from sqlalchemy import Column, Integer, String
from db import Base
from pgvector.sqlalchemy import Vector

class User(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, index=True)
    query = Column(String, index=True)
    description = Column(String, index=True)
    embedding = Column(Vector(384)) 

