"""
In your terminal make sure you're in the `backend` folder and run:
uvicorn main:app --reload

http://127.0.0.1:8000/docs for FastAPi auto-generated documentaiton
"""


"""
cd backend
source venv/bin/activate
"""


# 127.0.0.1 is localhost IP address
# we are listening on port 8000





from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import engine

import models

from transcript import fetch_transcript

from analysis import analyze_transcript

# tells SQLAlcehmy to look at all models (python classes) and create the corresponding tables in Postgres if they dont exist yet
# just a sfety net to keep models and DB in sync in case one is changed and forget to update the other (so Python and SQL schema always matching)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class AnalyzeRequest(BaseModel):
    ticker: str
    year: int
    quarter: int

@app.get("/")
def root():
    return {"message": "Earnings analayzer API is running"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    
    transcript = fetch_transcript(request.ticker, request.year, request.quarter)
    
    if not transcript:
        raise HTTPException(status_code=404, detail=f"No transcript found for {request.ticker} Q{request.quarter} {request.year}")
    
    result = analyze_transcript(
        ticker=request.ticker,
        year=request.year,
        quarter=request.quarter,
        transcript_text=transcript["content"]
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "ticker": request.ticker.upper(),
        "year": request.year,
        "quarter": request.quarter,
        "analysis": result
    }