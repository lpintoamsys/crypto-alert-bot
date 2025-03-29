import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask
import threading

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = 'https://api.coindcx.com'
SELECTED_TOKENS = ['DEFIINR', 'DFIINR', 'GOATSINR', 'MIGGLESINR', 'ALPACAINR', 'TOMIINR', 'UFTINR', 'PEIPEIINR', 'E4CINR', 'STCINR', 'XRINR']  # Only these trigger rise alerts
PRICE_THRESHOLD = 0.25  # 25% threshold

# Twilio setup
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
WHATSAPP_FROM = 'whatsapp:+14155238886'
WHATSAPP_TO = f'whatsapp:{os.getenv("YOUR_MOBILE_NUMBER")}'

# Track all coins for drops, but only selected for rises
price_history = {}

def send_alert(symbol, current_price, change_percent, is_rise):
    """Send WhatsApp alert"""
    alert_type = "🚀 SELECTED TOKEN RISE" if is_rise else "🚨 TOKEN DROP"
    emoji = "📈" if is_rise else "📉"
    
    message = (
        f"{alert_type}\n"
        f"• Token: {symbol}\n"
        f"• {emoji} Change: {'+' if is_rise else '-'}{abs(change_percent):.2f}%\n"
        f"• Price: ₹{current_price:,.2f}\n"
        f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        twilio_client.messages.create(
            body=message,
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO
        )
        print(f"Alert sent for {symbol}")
    except Exception as e:
        print(f"Alert failed: {e}")

def get_market_data():
    """Fetch all INR pairs"""
    try:
        response = requests.get(f"{BASE_URL}/exchange/ticker", timeout=10)
        return {
            ticker['market']: float(ticker['last_price'])
            for ticker in response.json()
            if isinstance(ticker, dict) 
            and ticker.get('market', '').endswith('INR')
            and 'last_price' in ticker
        }
    except Exception as e:
        print(f"API error: {e}")
        return None

def monitor_market():
    print(f"🔔 Monitoring:\n"
          f"- Rises: Only {SELECTED_TOKENS}\n"
          f"- Drops: All INR tokens")
    
    while True:
        prices = get_market_data()
        if prices:
            for symbol, current_price in prices.items():
                # Initialize if new token
                if symbol not in price_history:
                    price_history[symbol] = current_price
                    continue
                
                last_price = price_history[symbol]
                change = (current_price - last_price) / last_price
                
                # Check conditions
                if symbol in SELECTED_TOKENS and change >= PRICE_THRESHOLD:
                    send_alert(symbol, current_price, change*100, is_rise=True)
                elif change <= -PRICE_THRESHOLD:
                    send_alert(symbol, current_price, abs(change)*100, is_rise=False)
                
                # Update price
                price_history[symbol] = current_price

@app.route('/')
def status():
    return (f"Tracking {len(SELECTED_TOKENS)} tokens for rises<br>"
            f"Monitoring all INR tokens for drops")

if __name__ == "__main__":
    threading.Thread(target=monitor_market, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))