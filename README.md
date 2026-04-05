# Earnings Call Analyzer

A full-stack investment research tool that turns earnings call transcripts into 
structured AI-powered reports w/ sentiment, key claims, red flags, opportunities, 
and post-earnings stock price reaction.

**Live:** [earnings-analyzer-vercel2.vercel.app](https://earnings-analyzer-vercel2.vercel.app)

![Earnings Analyzer Screenshot](<img width="1859" height="993" alt="image" src="https://github.com/user-attachments/assets/38ddd088-d72e-4bbf-a918-727544536aac" />)

## What it does

Type in a ticker, year, and quarter. The app fetches the earnings call transcript,
runs it through Gemini AI, and returns a clean breakdown of what management said 
and how the market reacted. Results are cached so repeat queries are instant.

The homepage shows every previously analyzed companies, and can be sorted in a variety of ways


## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy: deployed on Render
- **Frontend:** React, Recharts, Vite: deployed on Vercel
- **AI:** Google Gemini API (free Flash 2.5) for transcript analysis
- **Data:** defeatbeta-api for transcripts, yfinance for post-earnings price data

## Running locally
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create a .env file in /backend with:
# DATABASE_URL=postgresql://...
# GEMINI_API_KEY=...

uvicorn main:app --reload
```
```bash
# Frontend
cd frontend
npm install
npm run dev
```

## Features
- AI analysis of any earnings call from 2005 to present
- Sentiment scoring with visual bar
- Post-earnings stock price chart (earnings date + 5 trading days)
- Cached analyses with sort by recency, largest movement, top gainers, biggest drops
- Database caching where analyzed transcripts are stored and served instantly on 
  repeat requests
- Ticker autocomplete powered by Financial Modeling Prep :)
