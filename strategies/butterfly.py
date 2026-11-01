# strategies/butterfly.py
import pandas as pd
import numpy as np

def find_butterflies(df, metadata):
    """
    Scans the options chain for symmetric 3-leg Long Call Butterflies.
    Applies strict, granular adaptive minimum strike widths based on the asset's current price.
    """
    results = []
    spot = metadata['spot_price']
    expiry = metadata['expiration']
    
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
    strikes = sorted(list(calls['strike'].unique()))
    calls_indexed = calls.set_index('strike')
    
    for i in range(len(strikes)):
        for j in range(i + 1, len(strikes)):
            for h in range(j + 1, len(strikes)):
                k1 = strikes[i]
                k2 = strikes[j]
                k3 = strikes[h]
                
                wing1 = k2 - k1
                wing2 = k3 - k2
                
                if wing1 < min_diff or wing2 < min_diff:
                    continue
                
                if not np.isclose(wing1, wing2, atol=0.05):
                    continue
                    
                try:
                    mid1 = calls_indexed.loc[k1, 'mid']
                    mid2 = calls_indexed.loc[k2, 'mid']
                    mid3 = calls_indexed.loc[k3, 'mid']
                    
                    net_debit = mid1 - (2 * mid2) + mid3
                    max_reward = wing1 - net_debit
                    
                    if net_debit > 0 and max_reward > 0:
                        ratio = max_reward / net_debit
                        
                        results.append({
                            'Strategy': 'Long Call Butterfly',
                            'Strikes': f"{k1}/{k2}/{k3}",
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
