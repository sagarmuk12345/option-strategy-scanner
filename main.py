# main.py
import option_chain
from strategies import bull_call
from strategies import butterfly
from strategies import broken_wing
from strategies import bull_put
import pandas as pd
import time
import os
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_to_discord(message):
    """Broadcasts the clean data to your Discord channel"""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL environment variable is missing on this GitHub repo.")
        return
        
    if len(message) > 1950:
        message = message[:1900] + "\n... (Truncated for Mobile Screen View)"
    
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print("🚀 Success! Clean layout delivered to Discord.")
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
    bull_puts = bull_put.find_bull_put_spreads(master_df, metadata)
    
    all_setups = bull_calls + butterflies + broken_wings + bull_puts
    
    if not master_df.empty:
        current_spot = master_df['CMP'].iloc[0]
        for setup in all_setups:
            setup['CMP'] = current_spot
            
    return all_setups

def execute_scan_cycle():
    target_portfolio = ["AAPL", "GOOGL", "AMZN", "NVDA", "TSLA", "COST", "META", "MSFT"]
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    all_compiled_opportunities = []
    
    for ticker in target_portfolio:
        stock_setups = run_scanner(ticker)
        for setup in stock_setups:
            setup['Ticker'] = ticker
        all_compiled_opportunities.extend(stock_setups)
        time.sleep(0.5)
        
    if all_compiled_opportunities:
        master_leaderboard_df = pd.DataFrame(all_compiled_opportunities)
        filtered_df = master_leaderboard_df[master_leaderboard_df['Net Cost'] <= 3.00]
        
        if not filtered_df.empty:
            # Sort globally by the best Reward-to-Risk ratio
            sorted_matrix = filtered_df.sort_values(by='Ratio', ascending=False)
            
            # Take only the Top 5 setups to avoid cluttering your text feed
            top_setups = sorted_matrix.head(5).to_dict('records')
            
            # 📱 BUILD THE NEW MOBILE-FRIENDLY VERTICAL ALERT CARD FORMAT
            discord_message = f"🏆 **TOP 5 OPTIONS OPPORTUNITIES** 🏆\n*Generated: {current_time_str} UTC*\n"
            discord_message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for index, setup in enumerate(top_setups, 1):
                # Safeguard against infinite calculations dividing by zero
                risk_val = f"${setup['Max Risk']:.2f}" if setup['Max Risk'] > 0 else "$0.00"
                
                # Format each setup as a clear vertical text block
                discord_message += (
                    f"🔥 **#{index} | {setup['Ticker']}** (CMP: ${setup['CMP']:.2f})\n"
                    f"🔹 *Strategy:* {setup['Strategy']}\n"
                    f"🔹 *Strikes:* {setup['Strikes']}\n"
                    f"🔹 *Expiry:* {setup['Expiry']}\n"
                    f"💵 *Net Cost/Credit:* ${setup['Mid Price']:.2f}\n"
                    f"⚠️ *Max Risk:* {risk_val}\n"
                    f"💰 *Max Reward:* ${setup['Max Reward']:.2f}\n"
                    f"📈 *Reward/Risk Ratio:* {setup['Ratio']}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                )
            
            send_to_discord(discord_message)
        else:
            send_to_discord(f"⏰ **Scan at {current_time_str} UTC**: No strategies found matching criteria <= $3.00.")
    else:
        send_to_discord(f"❌ **Scan at {current_time_str} UTC**: Data pipeline payload empty.")

if __name__ == "__main__":
    execute_scan_cycle()
