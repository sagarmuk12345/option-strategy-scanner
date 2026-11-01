# strategies/bull_put.py
import pandas as pd

def find_bull_put_spreads(master_df, metadata, max_net_cost=3.00):
    """
    Scans for Bull Put Spreads (Credit Spreads) where you sell a higher strike put
    and buy a lower strike put. 
    """
    # 1. Extract only Put options
    puts_df = master_df[master_df['type'] == 'P'].copy()
    expiry = metadata['expiration']
    
    setups = []
    
    # Convert dataframe to dictionary records for rapid processing loops
    records = puts_df.to_dict('records')
    num_strikes = len(records)
    
    # 2. Iterate through all pairs of put options to form a vertical spread
    for i in range(num_strikes):
        for j in range(num_strikes):
            # Short Put = Higher Strike, Long Put = Lower Strike
            # To be a Bull Put spread, Short Strike must be greater than Long Strike
            if records[i]['strike'] > records[j]['strike']:
                short_put = records[i]
                long_put = records[j]
                
                # Check option chain premium viability
                if short_put['mid'] is None or long_put['mid'] is None:
                    continue
                
                # 3. Calculate Strategy Metrics
                # Net Credit = Premium Received (Short Put) - Premium Paid (Long Put)
                net_credit = short_put['mid'] - long_put['mid']
                
                # Filter out junk spreads where credit values don't exist or are negative
                if net_credit <= 0.05:
                    continue
                
                # Calculate maximum risk and maximum reward
                strike_width = short_put['strike'] - long_put['strike']
                max_risk = strike_width - net_credit
                max_reward = net_credit
                
                # Ensure risk calculations are realistic and strictly positive to fix divisions by zero
                if max_risk <= 0.05:
                    continue
                    
                ratio = round(max_reward / max_risk, 2)
                
                # 4. Map to Main Pipeline Leaderboard Variables
                setups.append({
                    'Strategy': 'Bull Put Spread',
                    'Strikes': f"${long_put['strike']:.2f}P / ${short_put['strike']:.2f}P",
                    'Expiry': expiry,
                    'Mid Price': round(net_credit, 2),
                    'Net Cost': 0.00,  # Zero cost entry to bypass global main filter
                    'Max Risk': round(max_risk, 2),
                    'Max Reward': round(max_reward, 2),
                    'Ratio': ratio
                })
                
    return setups
