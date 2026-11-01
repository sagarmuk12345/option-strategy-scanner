# main.py
import option_chain
from strategies import bull_call
from strategies import butterfly
from strategies import broken_wing
import pandas as pd
import time

def run_scanner(ticker):
    master_df, metadata = option_chain.fetch_option_data(ticker)
    if master_df is None or master_df.empty:
        print(f"⚠️ Skipping {ticker}: No data returned.")
        return []

    bull_calls = bull_call.find_bull_call_spreads(master_df, metadata)
    butterflies = butterfly.find_butterflies(master_df, metadata)
    broken_wings = broken_wing.find_broken_wings(master_df, metadata)
    
    # Propagate the CMP down to each generated strategy object
    # assuming strategies preserve row values or read from metadata
    all_setups = bull_calls + butterflies + broken_wings
    
    if not master_df.empty:
        current_spot = master_df['CMP'].iloc[0]
        for setup in all_setups:
            setup['CMP'] = current_spot
            
    return all_setups

if __name__ == "__main__":
    target_portfolio = ["AAPL", "GOOGL", "AMZN", "NVDA", "TSLA", "COST", "META", "MSFT"]
    
    print("==================================================================")
    print(f"🚀 SYSTEM SCANNER STARTED Across {len(target_portfolio)} High-Liquidity Stocks")
    print("🎯 Target Criteria: Max Strategy Net Cost <= $3.00")
    print("==================================================================")
    
    all_compiled_opportunities = []
    
    for ticker in target_portfolio:
        print(f"🔍 Polling chains for {ticker}...")
        stock_setups = run_scanner(ticker)
        
        for setup in stock_setups:
            setup['Ticker'] = ticker
            
        all_compiled_opportunities.extend(stock_setups)
        time.sleep(1)
        
    print("\n" + "="*80)
    print("🏆 GLOBAL TOP 50 STRATEGY LEADERBOARD (Net Cost <= $3.00)")
    print("="*80)
    
    if all_compiled_opportunities:
        master_leaderboard_df = pd.DataFrame(all_compiled_opportunities)
        
        # Filter for entries equal to or under $3.00
        filtered_df = master_leaderboard_df[master_leaderboard_df['Net Cost'] <= 3.00]
        
        if not filtered_df.empty:
            # Added 'CMP' column directly right next to Ticker for easy scanning
            column_order = ['Ticker', 'CMP', 'Strategy', 'Strikes', 'Expiry', 'Mid Price', 'Net Cost', 'Max Risk', 'Max Reward', 'Ratio']
            final_display_df = filtered_df[column_order]
            
            # Sort globally by the best Reward-to-Risk ratio
            sorted_matrix = final_display_df.sort_values(by='Ratio', ascending=False)
            
            # Extended window layout selection to show top 50 positions
            print(sorted_matrix.head(50).to_string(index=False))
            print("="*80)
        else:
            print("❌ No strategy layouts found across the portfolio that cost $3.00 or less.")
    else:
        print("❌ Data pipeline failed to acquire options data during execution.")
