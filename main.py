from fastapi import Depends, FastAPI
import os
import numpy as np
import redis
from requests import Session
import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from torch import cosine_similarity
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import models
from db import engine,SessionLocal
from typing import Annotated


load_dotenv()


# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# REDIS_DB = int(os.getenv("REDIS_DB", 0))
# REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


# Initialize FastAPI
models.Base.metadata.create_all(bind=engine)
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  
    allow_credentials=True,  
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# def get_redis():
#     return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Load Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')
db_dependency = Annotated[SessionLocal(), Depends(get_db)]
class metric(BaseModel):
    query: str
    description: str
    metric_name: str
  
@app.get("/")
def get_one(key:str=None,db:Session = Depends(get_db)):
    output=[]

    if key is None:
        result = db.query(models.User).all()
        for item in result:
            output.append({"id":item.id,"metric_name":item.metric_name,"query":item.query,"description":item.description})
        return {"data": output}
            
    else:
        query_vector = model.encode(key)
        query_tensor = torch.tensor(query_vector) 
        for item in db.query(models.User).all():
            key_vector = item.embedding
            key_tensor = torch.tensor(key_vector)
            similarity = cosine_similarity(query_tensor.unsqueeze(0), key_tensor.unsqueeze(0)).item()
            output.append({"id":item.id,"metric_name":item.metric_name,"query":item.query,"description":item.description,"similarity":similarity})
            output = sorted(output, key=lambda x: x['similarity'], reverse=True)
            output = output[:5]
        return {"data": output}

@app.post("/")
def create_item(metrics: metric, db: Session = Depends(get_db)):
    # Generate vector embedding
    vector = model.encode(metrics.metric_name).tolist()

    # Check if the metric already exists
    check = db.query(models.User).filter(models.User.metric_name == metrics.metric_name).first()
    if check is None:
        new_metric = models.User(
            metric_name=metrics.metric_name,
            query=metrics.query,
            description=metrics.description,
            embedding=np.array(vector)  
        )
        db.add(new_metric)
        db.commit()
        db.refresh(new_metric)
        return {"message": "Created"}
    else:
        return {"message": "Already exists"}
        

@app.patch("/")
def update_item(id:int,metrics:metric,db=Depends(get_db)):

    check = db.query(models.User).filter(models.User.id == id).first()
    if check is None:
        return {"text": "Does not exist"}
    check_metricname = db.query(models.User).filter(models.User.metric_name == metrics.metric_name).first()
    if check_metricname is not None:
        return {"text": "Metric name already exists"}
    else:
        check.metric_name = metrics.metric_name
        check.query = metrics.query
        check.description = metrics.description
        db.commit()
    return {"text": "Updated"}

@app.delete("/")
def delete_item(id: int,db=Depends(get_db)):
    check = db.query(models.User).filter(models.User.id == id).first()
    if check is None:
        return {"text": "Does not exist"}
    else:
        db.delete(check)
        db.commit()
        return {"text": "Deleted"}



    