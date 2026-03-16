from defeatbeta_api.data.ticker import Ticker

def fetch_transcript(ticker: str, year: int, quarter: int):
    try:
        company = Ticker(ticker.upper())
        transcripts = company.earning_call_transcripts()
        transcript_data = transcripts.get_transcript(year, quarter)
        
        if transcript_data is None or transcript_data.empty:
            return None
        
        full_text = " ".join(transcript_data["content"].tolist())

        # print(full_text)
        
        return {
            "ticker": ticker.upper(),
            "quarter": quarter,
            "year": year,
            "content": full_text
        }
    except Exception as e:
        return None
    


# result = fetch_transcript("AAPL", 2024, 1)