# strategies/bull_call.py
import pandas as pd

def find_bull_call_spreads(df, metadata):
    """
    Scans the clean option chain DataFrame for viable Bull Call Vertical Spreads.
    Applies strict, granular adaptive minimum strike widths based on the asset's current price.
    """
    results = []
    spot = metadata['spot_price']
    expiry = metadata['expiration']
    
    # Granular adaptive strike interval matrix
    if spot <= 150:
        min_diff = 5.0
    elif 150 < spot <= 250:
        min_diff = 7.5
    elif 250 < spot <= 375:
        min_diff = 10.0
    elif 375 <= spot <= 500:
        min_diff = 15.0
    elif 501 <= spot < 650:
        min_diff = 20.0
    else:  # spot >= 650
        min_diff = 30.0

    calls = df[(df['type'] == 'C') & (df['strike'] >= spot * 0.95) & (df['strike'] <= spot * 1.05)]
    strikes = sorted(calls['strike'].unique())
    calls_indexed = calls.set_index('strike')
    
    for i in range(len(strikes)):
        for j in range(i + 1, len(strikes)):
            k1 = strikes[i]
            k2 = strikes[j]
            
            if (k2 - k1) < min_diff:
                continue
            
            try:
                buy_mid = calls_indexed.loc[k1, 'mid']
                sell_mid = calls_indexed.loc[k2, 'mid']
                
                net_debit = buy_mid - sell_mid
                width_of_spread = k2 - k1
                max_reward = width_of_spread - net_debit
                
                if net_debit > 0 and max_reward > 0 and net_debit < width_of_spread:
                    ratio = max_reward / net_debit
                    
                    results.append({
                        'Strategy': 'Bull Call Spread',
                        'Strikes': f"{k1}/{k2}",
                        'Expiry': expiry,
                        'Mid Price': round(net_debit, 2),
                        'Net Cost': round(net_debit, 2),
                        'Max Risk': round(net_debit, 2),
                        'Max Reward': round(max_reward, 2),
                        'Ratio': round(ratio, 2)
                    })
            except KeyError:
                continue
                
    return results
