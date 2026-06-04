# main.py — FastAPI backend: receives queries, runs guardrails, calls logic layer

from fastapi import FastAPI, HTTPException   
from pydantic import BaseModel, Field        
from guardrail import validate_query         
from logic import run_query                  

# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Scholaris API",
    description="Agentic academic Q&A — Math, Biology, History supervisor pipeline",
    version="1.0.0",
)


# ── Request / Response schemas ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Schema for incoming query from the frontend."""
    query: str = Field(
        ...,                          
        min_length=3,                 
        max_length=500,               
        description="The academic question to be answered",
    )


class QueryResponse(BaseModel):
    """Schema returned to the frontend after processing."""
    agent: str   
    answer: str  
    status: str  


# ── Health check endpoint ─────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Simple liveness probe — confirms the API is running."""
    return {"status": "ok", "service": "Scholaris"}


# ── Main query endpoint ───────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    """
    Accepts a user query, validates it through guardrails,
    and routes it through the LangGraph supervisor pipeline.
    """

    
    is_safe, sanitized_or_error = validate_query(request.query)

    if not is_safe:
        
        raise HTTPException(status_code=400, detail=sanitized_or_error)

    
    try:
        result = run_query(sanitized_or_error)  
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

 
    return QueryResponse(
        agent=result["agent"],
        answer=result["answer"],
        status="success",
    )
