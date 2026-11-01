# strategies/bull_put.py
import pandas as pd

def find_bull_put_spreads(master_df, metadata, max_net_cost=3.00):
    """
    Scans for Bull Put Spreads (Credit Spreads) where you sell a higher strike put
    and buy a lower strike put. Includes a dynamic stock price cushion rule and 
    a minimum credit requirement.
    """
    # 1. Extract only Put options
    puts_df = master_df[master_df['type'] == 'P'].copy()
    spot_price = metadata['spot_price']
    expiry = metadata['expiration']
    
    # 2. Dynamic Cushion Rule: Determine minimum distance below spot for the short strike
    if spot_price <= 150:
        min_diff = 5.0
    elif 150 < spot_price <= 250:
        min_diff = 7.5
    elif 250 < spot_price <= 375:
        min_diff = 10.0
    elif 375 < spot_price <= 500:
        min_diff = 15.0
    elif 500 < spot_price < 650:
        min_diff = 20.0
    else:  # spot_price >= 650
        min_diff = 30.0
        
    setups = []
    
    # Convert dataframe to dictionary records for rapid processing loops
    records = puts_df.to_dict('records')
    num_strikes = len(records)
    
    # 3. Iterate through all pairs of put options to form a vertical spread
    for i in range(num_strikes):
        for j in range(num_strikes):
            # Short Put = Higher Strike (i), Long Put = Lower Strike (j)
            if records[i]['strike'] > records[j]['strike']:
                short_put = records[i]
                long_put = records[j]
                
                # Check option chain premium viability
                if short_put['mid'] is None or long_put['mid'] is None:
                    continue
                
                # 🛑 RULE 1: Short Put Strike must be safely out-of-the-money
                # It must be at least 'min_diff' below the current spot price
                if short_put['strike'] > (spot_price - min_diff):
                    continue
                
                # 4. Calculate Strategy Metrics
                # Net Credit = Premium Received (Short Put) - Premium Paid (Long Put)
                net_credit = short_put['mid'] - long_put['mid']
                
                # 🛑 RULE 2: Minimum premium collected must be more than $7.00 ($700 total credit)
                if net_credit <= 7.00:
                    continue
                
                # Calculate maximum risk and maximum reward
                strike_width = short_put['strike'] - long_put['strike']
                max_risk = strike_width - net_credit
                max_reward = net_credit
                
                # Ensure risk calculations are realistic and strictly positive to fix divisions by zero
                if max_risk <= 0.05:
                    continue
                    
                ratio = round(max_reward / max_risk, 2)
                
                # 5. Map to Main Pipeline Leaderboard Variables
                setups.append({
                    'Strategy': 'Bull Put Spread',
                    'Strikes': f"${long_put['strike']:.2f}P / ${short_put['strike']:.2f}P",
                    'Expiry': expiry,
                    'Mid Price': round(net_credit, 2),
                    'Net Cost': 0.00,  # Zero upfront cost allows it to bypass main.py filter
                    'Max Risk': round(max_risk, 2),
                    'Max Reward': round(max_reward, 2),
                    'Ratio': ratio
                })
                
    return setups
