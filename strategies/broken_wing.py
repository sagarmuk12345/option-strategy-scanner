# strategies/broken_wing.py
import pandas as pd

def find_broken_wings(df, metadata):
    """
    Scans the options chain for BOTH Call and Put asymmetrical Broken Wing Butterflies.
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

    for option_type in ['C', 'P']:
        subset = df[(df['type'] == option_type) & (df['strike'] >= spot * 0.95) & (df['strike'] <= spot * 1.05)]
        strikes = sorted(list(subset['strike'].unique()))
        indexed_data = subset.set_index('strike')
        
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
                    
                    if option_type == 'C' and wing2 <= wing1:
                        continue
                    if option_type == 'P' and wing1 <= wing2:
                        continue
                        
                    try:
                        mid1 = indexed_data.loc[k1, 'mid']
                        mid2 = indexed_data.loc[k2, 'mid']
                        mid3 = indexed_data.loc[k3, 'mid']
                        
                        if option_type == 'C':
                            net_cost = mid1 - (2 * mid2) + mid3
                            max_reward = wing1 - net_cost
                            embedded_gap = wing2 - wing1
                        else:
                            net_cost = mid3 - (2 * mid2) + mid1
                            max_reward = wing2 - net_cost
                            embedded_gap = wing1 - wing2
                        
                        if net_cost > 0:
                            max_risk = net_cost + embedded_gap
                        else:
                            max_risk = embedded_gap - abs(net_cost)
                        
                        if max_risk > 0 and max_reward > 0:
                            ratio = max_reward / max_risk
                            strategy_name = "Broken Wing Call Fly" if option_type == 'C' else "Broken Wing Put Fly"
                            
                            results.append({
                                'Strategy': strategy_name,
                                'Strikes': f"{k1}/{k2}/{k3}",
                                'Expiry': expiry,
                                'Mid Price': round(net_cost, 2),
                                'Net Cost': round(net_cost, 2),
                                'Max Risk': round(max_risk, 2),
                                'Max Reward': round(max_reward, 2),
                                'Ratio': round(ratio, 2)
                            })
                    except KeyError:
                        continue
                        
    return results
