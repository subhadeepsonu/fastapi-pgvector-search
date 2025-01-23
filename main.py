import json
from fastapi import  FastAPI, HTTPException

import numpy as np



from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from torch import cosine_similarity
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from typing import  Optional


from db import supabase


load_dotenv()



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  
    allow_credentials=True,  
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


model = SentenceTransformer('all-MiniLM-L6-v2')

class metric(BaseModel):
    query: Optional[str] = None
    metric_name: Optional[str] = None
    description: Optional[str] = None

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0
    vec1, vec2 = np.array(vec1), np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

@app.get("/")
async def get_query(query: Optional[str] = None):
    try:
        if not query:
            response = supabase.table("metrics").select("*").execute()
           
            return {"success": True, "results": response.data[:50]  }

        # Transform query locally using SentenceTransformer
        transformed_query = model.encode(query).tolist()

        # Fetch stored queries with vector data~
        response = supabase.table("metrics").select("*").execute()

        data = response.data
        if not data:
            return {"success": True, "results": []}

        similarity_results = []

        for item in data:
            query_vector = item.get("query_vector", [])
            description_vector = item.get("description_vector", [])
            metric_name_vector = item.get("metric_name_vector", [])
            try:
                query_vector = json.loads(item.get("query_vector", "[]")) if isinstance(item.get("query_vector"), str) else item.get("query_vector", [])
                description_vector = json.loads(item.get("description_vector", "[]")) if isinstance(item.get("description_vector"), str) else item.get("description_vector", [])
                metric_name_vector = json.loads(item.get("metric_name_vector", "[]")) if isinstance(item.get("metric_name_vector"), str) else item.get("metric_name_vector", [])
            except json.JSONDecodeError:
                continue  

            # Compute cosine similarity
            sim1 = cosine_similarity(transformed_query, query_vector)
            sim2 = cosine_similarity(transformed_query, description_vector)
            sim3 = cosine_similarity(transformed_query, metric_name_vector)

            max_similarity = max(sim1, sim2, sim3)

            # Append to the results list
            similarity_results.append({
                "id": item["id"],
                "query": item["query"],
                "chart": item["chart"],
                "metric_name": item["metric_name"],
                "similarity": max_similarity
            })

        # Rank results by similarity and return top 5
        ranked_queries = sorted(similarity_results, key=lambda x: x["similarity"], reverse=True)[:5]

        return {"success": True, "results": ranked_queries}

    except Exception as e:
        return {"success": False, "message": "An error occurred", "error": str(e)}



    




