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

# Securely pulls your hidden Discord URL from GitHub's server secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_to_discord(message):
    """Broadcasts clear formatted data directly to your Discord channel"""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL environment variable is missing on this GitHub repo.")
        return
        
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
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
    
    # Extract CMP safely directly at the data generation layer
    current_spot = master_df['CMP'].iloc[0] if (master_df is not None and not master_df.empty) else 0.0
    
    independent_setups = []
    for setup in all_setups:
        setup_copy = setup.copy()
        setup_copy['CMP'] = current_spot
        independent_setups.append(setup_copy)
        
    return independent_setups

def execute_scan_cycle():
    target_portfolio = ["AAPL", "GOOGL", "AMZN", "NVDA", "TSLA", "COST", "META", "MSFT"]
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    all_compiled_opportunities = []
    for ticker in target_portfolio:
        stock_setups = run_scanner(ticker)
        if not stock_setups:
            continue
        for setup in stock_setups:
            setup['Ticker'] = ticker
        all_compiled_opportunities.extend(stock_setups)
        time.sleep(0.5)
        
    if all_compiled_opportunities:
        master_leaderboard_df = pd.DataFrame(all_compiled_opportunities)
        filtered_df = master_leaderboard_df[master_leaderboard_df['Net Cost'] <= 3.00]
        
        if not filtered_df.empty:
            sorted_matrix = filtered_df.sort_values(by='Ratio', ascending=False)
            top_setups = sorted_matrix.head(10).to_dict('records')
            
            # 📱 MESSAGE 1: Top 1-5 Positions
            msg1 = f"🏆 **TOP 10 OPTIONS OPPORTUNITIES (1-5)** 🏆\n*Generated: {current_time_str} UTC*\n"
            msg1 += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for index, setup in enumerate(top_setups[:5], 1):
                risk_display = f"${setup['Max Risk']:.2f}" if setup['Max Risk'] > 0 else "$0.00"
                cmp_display = f"${setup['CMP']:.2f}" if 'CMP' in setup else "N/A"
                msg1 += (
                    f"🔥 **#{index} | {setup['Ticker']}** (CMP: {cmp_display})\n"
                    f"🔹 *Strategy:* {setup['Strategy']}\n"
                    f"🔹 *Strikes:* {setup['Strikes']}\n"
                    f"🔹 *Expiry:* {setup['Expiry']}\n"
                    f"💵 *Net Cost/Credit:* ${setup['Mid Price']:.2f}\n"
                    f"⚠️ *Max Risk:* {risk_display}\n"
                    f"💰 *Max Reward:* ${setup['Max Reward']:.2f}\n"
                    f"📈 *Ratio:* {setup['Ratio']:.2f}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                )
            send_to_discord(msg1)
            time.sleep(1)  # Brief pause to avoid rate limiting
            
            # 📱 MESSAGE 2: Positions 6-10 (If available)
            if len(top_setups) > 5:
                msg2 = f"🏆 **OPTIONS OPPORTUNITIES CONTINUED (6-10)** 🏆\n"
                msg2 += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for index, setup in enumerate(top_setups[5:10], 6):
                    risk_display = f"${setup['Max Risk']:.2f}" if setup['Max Risk'] > 0 else "$0.00"
                    cmp_display = f"${setup['CMP']:.2f}" if 'CMP' in setup else "N/A"
                    msg2 += (
                        f"🔥 **#{index} | {setup['Ticker']}** (CMP: {cmp_display})\n"
                        f"🔹 *Strategy:* {setup['Strategy']}\n"
                        f"🔹 *Strikes:* {setup['Strikes']}\n"
                        f"🔹 *Expiry:* {setup['Expiry']}\n"
                        f"💵 *Net Cost/Credit:* ${setup['Mid Price']:.2f}\n"
                        f"⚠️ *Max Risk:* {risk_display}\n"
                        f"💰 *Max Reward:* ${setup['Max Reward']:.2f}\n"
                        f"📈 *Ratio:* {setup['Ratio']:.2f}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    )
                send_to_discord(msg2)
        else:
            send_to_discord(f"⏰ **Scan at {current_time_str} UTC**: No setups found under $3.00.")
    else:
        send_to_discord(f"❌ **Scan at {current_time_str} UTC**: Strategy payload empty.")

if __name__ == "__main__":
    execute_scan_cycle()
