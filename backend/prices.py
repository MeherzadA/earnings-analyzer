import yfinance as yf
from datetime import datetime, timedelta
import duckdb
from pathlib import Path


TRANSCRIPTS_CACHE_PATH = Path(__file__).resolve().parent / ".cache" / "stock_earning_call_transcripts.parquet"


def get_earnings_date(ticker: str, year: int, quarter: int) -> str | None:
    """
    Fetch the earnings date from the parquet dataset.
    
    Returns: Date string in format "YYYY-MM-DD" or None if not found
    """
    try:
        if not TRANSCRIPTS_CACHE_PATH.exists():
            return None
        
        connection = duckdb.connect(":memory:")
        try:
            row = connection.execute(
                """
                SELECT report_date
                FROM read_parquet(?)
                WHERE symbol = ? AND fiscal_year = ? AND fiscal_quarter = ?
                LIMIT 1
                """,
                [str(TRANSCRIPTS_CACHE_PATH), ticker.upper(), year, quarter],
            ).fetchone()

            print(f"DEBUG: earnings date row = {row}")
        
        except Exception as e:
            print(f"DEBUG: get_earnings_date error = {e}")
            raise RuntimeError(f"Failed to get earnings date for {ticker.upper()} Q{quarter} {year}: {e}") from e



        finally:
            connection.close()
        
        if row and row[0]:
            # Return date as string (should already be in YYYY-MM-DD format)
            return str(row[0])
        return None
    except Exception as e:
        raise RuntimeError(f"Failed to get earnings date for {ticker.upper()} Q{quarter} {year}: {e}") from e


def get_next_trading_day(date_str: str) -> str:
    """
    Given a date string (YYYY-MM-DD), return the next trading day.
    Skips weekends. Handles US market holidays via yfinance.
    
    Returns: Date string in format "YYYY-MM-DD"
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Start checking from the next day
    current = date + timedelta(days=1)
    
    # yfinance API uses weekday() where Monday=0, Sunday=6
    max_iterations = 10  # Safety limit to prevent infinite loops
    iterations = 0
    
    while iterations < max_iterations:
        # Check if it's a weekend
        if current.weekday() < 5:  # Monday=0 to Friday=4
            # Try to fetch data for this date
            # If yfinance returns empty for this date, it's likely a holiday
            try:
                data = yf.download("SPY", start=current, end=current + timedelta(days=1), progress=False)
                if not data.empty:
                    return current.strftime("%Y-%m-%d")
            except:
                pass
        
        current += timedelta(days=1)
        iterations += 1
    
    # Fallback: if we can't find a trading day, return the date + 1 day
    return (date + timedelta(days=1)).strftime("%Y-%m-%d")


def calculate_returns(ticker: str, earnings_date: str) -> dict:
    """
    Calculate 1-day and 5-day returns after earnings.
    
    1-day return: earnings_date close → next_trading_day close
    5-day return: earnings_date close → (5 trading days later) close
    
    Returns: {
        "return_1day": float (percentage, e.g., 2.34 for +2.34%)
        "return_5day": float (percentage, e.g., 1.87 for +1.87%)
        "earnings_date": str (the date used, YYYY-MM-DD)
        "return_1day_date": str (the date of 1-day return calculation)
        "return_5day_date": str (the date of 5-day return calculation)
    }
    """
    try:
        # Parse earnings date
        earnings_date_obj = datetime.strptime(earnings_date, "%Y-%m-%d")
        
        # Fetch stock data around the earnings date
        # Get data from earnings_date to 2 weeks after to ensure we have trading days
        start_date = (earnings_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (earnings_date_obj + timedelta(days=15)).strftime("%Y-%m-%d")
        
        data = yf.download(ticker.upper(), start=start_date, end=end_date, progress=False)
        
        if data.empty:
            raise RuntimeError(f"No price data available for {ticker.upper()} around {earnings_date}")
        
        # Ensure the dataframe is sorted by date
        data = data.sort_index()

        # Flatten MultiIndex columns — yfinance returns ('Close', 'NVDA') style columns
        # We just want a simple 'Close' column with scalar values
        close_prices = data["Close"].squeeze()

        print(f"DEBUG: data shape = {data.shape}")
        print(f"DEBUG: data columns = {data.columns.tolist()}")
        print(f"DEBUG: earnings date row = {data.loc[earnings_date] if earnings_date in data.index.strftime('%Y-%m-%d').values else 'not found'}")
        
        # Get the close price on earnings date
        earnings_date_close = None
        if earnings_date in close_prices.index.strftime("%Y-%m-%d").values:
            earnings_date_close = float(close_prices.loc[earnings_date])
        else:
            # If exact date not found, find the most recent date before or on earnings_date
            valid_dates = close_prices.index[close_prices.index <= earnings_date_obj]
            if not valid_dates.empty:
                earnings_date_close = float(close_prices.loc[valid_dates[-1]])
        
        if earnings_date_close is None:
            raise RuntimeError(f"Could not find price data for {ticker.upper()} on or before {earnings_date}")
        
        # Get trading days after earnings
        trading_days = []
        for date_index in data.index:
            if date_index > earnings_date_obj:
                trading_days.append(date_index)
        
        if len(trading_days) < 5:
            raise RuntimeError(f"Not enough trading days after {earnings_date} for {ticker.upper()}")
        
        # 1-day return (next trading day)
        one_day_date = trading_days[0]
        one_day_close = float(close_prices.loc[one_day_date])
        return_1day = float(((one_day_close - earnings_date_close) / earnings_date_close) * 100)
        
        # 5-day return (5 trading days later)
        five_day_date = trading_days[4]
        five_day_close = float(close_prices.loc[five_day_date])

        return_5day = float(((five_day_close - earnings_date_close) / earnings_date_close) * 100)
        
        # Collect daily prices for charting (earnings date + 5 trading days after)
        daily_prices = [
            {
                "date": earnings_date,
                "price": float(round(earnings_date_close, 2)),
                "label": "Earnings"
            }
        ]
        
        for i, trade_day in enumerate(trading_days[:5]):
            close_price = float(close_prices.loc[trade_day])
            daily_prices.append({
                "date": trade_day.strftime("%Y-%m-%d"),
                "price": float(round(close_price, 2)),
                "label": f"Day {i+1}"
            })
        
        return {
            "return_1day": round(return_1day, 2),
            "return_5day": round(return_5day, 2),
            "earnings_date": earnings_date,
            "return_1day_date": one_day_date.strftime("%Y-%m-%d"),
            "return_5day_date": five_day_date.strftime("%Y-%m-%d"),
            "daily_prices": daily_prices
        }
    
    except Exception as e:
        # Return None values if we can't calculate returns (missing data, delisted stock, etc.)
        # This allows the analysis to proceed without blocking on price data
        print(f"Warning: Could not calculate returns for {ticker.upper()} on {earnings_date}: {e}")
        return {
            "return_1day": None,
            "return_5day": None,
            "earnings_date": earnings_date,
            "return_1day_date": None,
            "return_5day_date": None,
            "daily_prices": [],
            "error": str(e)
        }


def get_stock_returns(ticker: str, year: int, quarter: int) -> dict:

    print(f"DEBUG: Looking for earnings date for {ticker} Q{quarter} {year}")
    print(f"DEBUG: Cache path = {TRANSCRIPTS_CACHE_PATH}")
    print(f"DEBUG: Cache exists = {TRANSCRIPTS_CACHE_PATH.exists()}")

    """
    Main function: fetch earnings date and calculate returns.
    
    Returns: {
        "return_1day": float or None
        "return_5day": float or None
        "earnings_date": str
        "error": str (if any)
    }
    """
    try:
        earnings_date = get_earnings_date(ticker, year, quarter)
        
        if not earnings_date:
            return {
                "return_1day": None,
                "return_5day": None,
                "error": f"Could not find earnings date for {ticker.upper()} Q{quarter} {year}"
            }
        
        returns = calculate_returns(ticker, earnings_date)
        return returns
    
    except Exception as e:
        return {
            "return_1day": None,
            "return_5day": None,
            "error": str(e)
        }
