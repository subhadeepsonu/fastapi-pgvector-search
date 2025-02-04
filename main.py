import json
import numpy 
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from db import supabase  # Assuming Supabase is used for storage

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load pre-trained Sentence Transformer
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dimension vectors

# Request body model
class QueryRequest(BaseModel):
    query: str

@app.get("/")
def home():
    return {"message": "Sentence Transformer API is running!"}

@app.post("/search")
async def search_query(data: QueryRequest):
    query = data.query

    try:
        # Convert query to vector
        query_vector = model.encode([query])

        # Fetch stored data from Supabase
        response = supabase.table("metrics").select("*").execute()
        stored_data = response.data

        if not stored_data:
            return {"success": True, "results": []}

        similarity_results = []

        for item in stored_data:
            try:
                # Load stored vectors (ensure they are lists)
                stored_vector = json.loads(item.get("query_vector", "[]"))
            except json.JSONDecodeError:
                continue  # Skip invalid data

            # Compute cosine similarity
            similarity = cosine_similarity([query_vector[0]], [stored_vector])[0][0]

            # Store results
            similarity_results.append({
                "id": item["id"],
                "query": item["query"],
                "chart": item["chart"],
                "metric_name": item["metric_name"],
                "similarity": float(similarity),
            })

        # Sort results by similarity (highest first)
        ranked_results = sorted(similarity_results, key=lambda x: x["similarity"], reverse=True)[:5]

        return {"success": True, "results": ranked_results}

    except Exception as e:
        return {"success": False, "message": "An error occurred", "error": str(e)}
