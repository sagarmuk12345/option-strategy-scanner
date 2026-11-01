# main.py
import option_chain
from strategies import bull_call
from strategies import butterfly
from strategies import broken_wing
from strategies import bull_put  # Imported your bull_put module
import pandas as pd
import time
import os
import requests
from datetime import datetime

# Securely pulls your hidden Discord URL from GitHub's server secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_to_discord(message):
    """Broadcasts the leaderboard text safely to your Discord channel"""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL environment variable is missing on this GitHub repo.")
        return
        
    # Safety Check: Truncate message if it exceeds Discord's 2000 character wall limit
    if len(message) > 1950:
        message = message[:1900] + "\n... (Truncated for Mobile Screen View)```"
    
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print("🚀 Success! Matrix table delivered to Discord API.")
        else:
            print(f"⚠️ Discord Webhook rejected with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to reach Discord servers: {e}")

def run_scanner(ticker):
    master_df, metadata = option_chain.fetch_option_data(ticker)
    if master_df is None or master_df.empty:
        print(f"⚠️ Skipping {ticker}: No data returned.")
        return []

    bull_calls = bull_call.find_bull_call_spreads(master_df, metadata)
    butterflies = butterfly.find_butterflies(master_df, metadata)
    broken_wings = broken_wing.find_broken_wings(master_df, metadata)
    bull_puts = bull_put.find_bull_put_spreads(master_df, metadata)  # Added bull put calculations
    
    all_setups = bull_calls + butterflies + broken_wings + bull_puts
    
    if not master_df.empty:
        current_spot = master_df['CMP'].iloc[0]
        for setup in all_setups:
            setup['CMP'] = current_spot
            
    return all_setups

def execute_scan_cycle():
    target_portfolio = ["AAPL", "GOOGL", "AMZN", "NVDA", "TSLA", "COST", "META", "MSFT"]
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
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
        time.sleep(0.5)
        
    if all_compiled_opportunities:
        master_leaderboard_df = pd.DataFrame(all_compiled_opportunities)
        filtered_df = master_leaderboard_df[master_leaderboard_df['Net Cost'] <= 3.00]
        
        if not filtered_df.empty:
            column_order = ['Ticker', 'CMP', 'Strategy', 'Strikes', 'Expiry', 'Net Cost', 'Max Risk', 'Max Reward', 'Ratio']
            final_display_df = filtered_df[column_order]
            sorted_matrix = final_display_df.sort_values(by='Ratio', ascending=False)
            
            # Print locally to GitHub internal logs for debugging
            print(sorted_matrix.head(50).to_string(index=False))
            
            # 💡 GRAB TOP 8 SO THE TABLE TEXT IS SLIM AND FITS ON A MOBILE DISCORD LAYOUT
            top_rows = sorted_matrix.head(8)
            
            discord_message = f"🏆 **OPTIONS LEADERBOARD ({current_time_str} UTC)** 🏆\n"
            discord_message += f"```\n{top_rows.to_string(index=False)}\n```"
            
            # Fire data to your phone!
            send_to_discord(discord_message)
        else:
            msg = f"⏰ **Scan at {current_time_str} UTC**: No strategies found matching criteria <= $3.00."
            print(msg)
            send_to_discord(msg)
    else:
        msg = f"❌ **Scan at {current_time_str} UTC**: Data pipeline failed to acquire tracking matrices."
        print(msg)
        send_to_discord(msg)

if __name__ == "__main__":
    execute_scan_cycle()
