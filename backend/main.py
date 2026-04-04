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



import json
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import engine, get_db

import models

from transcript import fetch_transcript

from analysis import analyze_transcript

from prices import get_stock_returns

# tells SQLAlcehmy to look at all models (python classes) and create the corresponding tables in Postgres if they dont exist yet
# just a sfety net to keep models and DB in sync in case one is changed and forget to update the other (so Python and SQL schema always matching)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    ticker: str
    year: int
    quarter: int

@app.get("/")
def root():
    return {"message": "Earnings analayzer API is running"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    # CHECK CACHE: Query for existing transcript with same ticker/year/quarter
    existing_transcript = db.query(models.Transcript).filter(
        models.Transcript.ticker == request.ticker.upper(),
        models.Transcript.year == request.year,
        models.Transcript.quarter == str(request.quarter)
    ).first()
    
    if existing_transcript:
        # CACHE HIT: Fetch the existing analysis instead of calling Gemini
        existing_analysis = db.query(models.Analysis).filter(
            models.Analysis.transcript_id == existing_transcript.id
        ).first()
        
        if existing_analysis:
            # Deserialize JSON fields back to lists
            cached_result = {
                "sentiment": existing_analysis.sentiment,
                "sentiment_score": existing_analysis.sentiment_score,
                "summary": existing_analysis.summary,
                "key_claims": json.loads(existing_analysis.key_claims),
                "red_flags": json.loads(existing_analysis.red_flags),
                "opportunities": json.loads(existing_analysis.opportunities)
            }
            
            # Deserialize daily_prices if available
            daily_prices = []
            if existing_analysis.daily_prices:
                daily_prices = json.loads(existing_analysis.daily_prices)
            
            return {
                "ticker": request.ticker.upper(),
                "year": request.year,
                "quarter": request.quarter,
                "analysis": cached_result,
                "return_1day": existing_analysis.return_1day,
                "return_5day": existing_analysis.return_5day,
                "daily_prices": daily_prices,
                "cached": True
            }
    
    # CACHE MISS: Proceed with normal flow (fetch transcript, call Gemini, save to DB)
    try:
        transcript = fetch_transcript(request.ticker, request.year, request.quarter)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    
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

    # Fetch stock returns (1-day and 5-day after earnings)
    stock_returns = get_stock_returns(request.ticker, request.year, request.quarter)

    # request.ticker, request.year, request.quarter come from the API request
    # transcript["content"] is the raw text fetched from defeatbeta
    db_transcript = models.Transcript(
        ticker=request.ticker.upper(),
        quarter=str(request.quarter),
        year=request.year,
        raw_text=transcript["content"]
    )
    
    # Stage the transcript to be saved — not written to DB yet
    db.add(db_transcript)
    
    # flush() sends the INSERT to the DB session so Postgres assigns an id
    # we need that id to link the analysis to this transcript below
    # without flush(), db_transcript.id would be None
    db.flush()
    
    # Create a new Analysis record linked to the transcript we just saved
    # result is the dictionary returned by Gemini
    # lists like key_claims need json.dumps() to convert them to a string for Text columns
    db_analysis = models.Analysis(
        transcript_id=db_transcript.id,
        user_id=None,
        sentiment=result.get("sentiment"),
        summary=result.get("summary"),
        key_claims=json.dumps(result.get("key_claims", [])),
        red_flags=json.dumps(result.get("red_flags", [])),
        opportunities=json.dumps(result.get("opportunities", [])),
        sentiment_score=result.get("sentiment_score"),
        return_1day=stock_returns.get("return_1day"),
        return_5day=stock_returns.get("return_5day"),
        daily_prices=json.dumps(stock_returns.get("daily_prices", []))
    )
    
    # Stage the analysis to be saved
    db.add(db_analysis)
    
    # commit() actually writes both the transcript and analysis to the database permanently
    db.commit()
    
    return {
        "ticker": request.ticker.upper(),
        "year": request.year,
        "quarter": request.quarter,
        "analysis": result,
        "return_1day": stock_returns.get("return_1day"),
        "return_5day": stock_returns.get("return_5day"),
        "daily_prices": stock_returns.get("daily_prices", []),
        "cached": False
    }
