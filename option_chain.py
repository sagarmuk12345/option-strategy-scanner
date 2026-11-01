# option_chain.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_option_data(ticker_symbol):
    """
    Connects to Yahoo Finance and pulls a clean option chain table
    along with crucial market metadata. Filters out any expiration dates
    that are less than 7 days into the future.
    """
    print(f"Connecting to Yahoo Finance to pull data for {ticker_symbol}...")
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Fetch current stock price (CMP)
    try:
        underlying_price = ticker.fast_info['lastPrice']
    except Exception:
        # Fallback method if fast_info fails
        underlying_price = ticker.history(period="1d")['Close'].iloc[-1]
    
    # 2. Get available expiration dates
    expirations = ticker.options
    if not expirations:
        print(f"❌ No options data found for {ticker_symbol}")
        return None, {'spot_price': underlying_price}
        
    # Find the closest expiration date that is at least 7 days away
    target_exp = None
    today = datetime.now().date()
    min_expiry_date = today + timedelta(days=7)
    
    for exp_str in expirations:
        try:
            # Yahoo Finance dates are formatted as 'YYYY-MM-DD'
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            if exp_date >= min_expiry_date:
                target_exp = exp_str
                break  # Stop at the first (closest) date that meets the requirement
        except ValueError:
            continue
            
    # Safeguard if no dates match the 7-day requirement
    if not target_exp:
        print(f"❌ No expirations found for {ticker_symbol} that are >= 7 days away.")
        return None, {'spot_price': underlying_price}
    
    # 3. Download option chain tables from Yahoo
    chain = ticker.option_chain(target_exp)
    
    # 4. Standardize Calls Data
    calls = chain.calls[['strike', 'bid', 'ask', 'lastPrice', 'impliedVolatility']].copy()
    calls['mid'] = (calls['bid'] + calls['ask']) / 2
    calls['mid'] = calls['mid'].fillna(calls['lastPrice'])  # Fallback if bid/ask are blank
    calls['type'] = 'C'
    
    # 5. Standardize Puts Data
    puts = chain.puts[['strike', 'bid', 'ask', 'lastPrice', 'impliedVolatility']].copy()
    puts['mid'] = (puts['bid'] + puts['ask']) / 2
    puts['puts'] = puts['mid'].fillna(puts['lastPrice'])
    puts['type'] = 'P'
    
    # 6. Combine into a unified master DataFrame sorted by strike price
    master_chain = pd.concat([calls, puts]).sort_values('strike').reset_index(drop=True)
    
    # Append the contextual structural tracking fields
    master_chain['Expiry'] = target_exp
    master_chain['CMP'] = round(underlying_price, 2)  # Inject Current Market Price column
    
    # 7. Collect structural details to pass along to your scanners later
    metadata = {
        'spot_price': underlying_price,
        'expiration': target_exp
    }
    
    print(f"✅ Successfully downloaded {len(master_chain)} contracts for expiration: {target_exp}")
    return master_chain, metadata
