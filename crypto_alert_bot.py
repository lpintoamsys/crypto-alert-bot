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

# CoinDCX API configuration
BASE_URL = 'https://api.coindcx.com'

# Twilio SMS configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
YOUR_MOBILE_NUMBER = os.getenv('YOUR_MOBILE_NUMBER')

@app.route('/')
def home():
    return "Crypto Alert Bot (INR) - Monitoring 5%↑/10%↑/25%↓"

def run_bot():
    monitor_prices()

# Alert thresholds
PRICE_DROP_THRESHOLD = 0.25  # 25% drop
PRICE_RISE_STRONG = 0.10     # 10% rise (significant)
PRICE_RISE_MILD = 0.05       # 5% rise (new threshold)

# Dictionary to store price history (only INR pairs)
price_history = {}

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms_alert(symbol, current_price, reference_price, percentage_change, alert_type):
    """Send SMS alert with different formats for each alert type"""
    if alert_type == "strong_rise":
        emoji = "🚀🔥"
        title = "STRONG RISE"
    elif alert_type == "mild_rise":
        emoji = "🚀"
        title = "PRICE RISE"
    else:  # drop
        emoji = "🚨"
        title = "PRICE DROP"
    
    message_body = (
        f"{emoji} {symbol} {title}\n"
        f"📈 Change: +{percentage_change:.2f}%\n" if alert_type in ["strong_rise", "mild_rise"] else
        f"📉 Change: -{percentage_change:.2f}%\n"
        f"💰 Current: ₹{current_price:,.2f}\n"
        f"🔍 Reference: ₹{reference_price:,.2f}\n"
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_MOBILE_NUMBER
        )
        print(f"SMS Alert Sent! {symbol} {title}")
    except Exception as e:
        print(f"SMS Failed: {e}")

def get_market_data():
    """Fetch only INR pairs from CoinDCX"""
    url = f"{BASE_URL}/exchange/ticker"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return [ticker for ticker in response.json() 
                if isinstance(ticker, dict) 
                and ticker.get('market', '').endswith('INR')]
    except Exception as e:
        print(f"API Error: {e}")
        return None

def monitor_prices():
    print("🚀 Starting INR Crypto Monitor: 5%↑/10%↑/25%↓")
    while True:
        market_data = get_market_data()
        
        if market_data:
            for ticker in market_data:
                try:
                    symbol = ticker['market']
                    current_price = float(ticker['last_price'])
                    
                    # Initialize new pair
                    if symbol not in price_history:
                        price_history[symbol] = {
                            'high': current_price,
                            'low': current_price,
                            'last_price': current_price
                        }
                        continue
                    
                    last_price = price_history[symbol]['last_price']
                    price_change = (current_price - last_price) / last_price
                    
                    # Check for 5% rise (new)
                    if PRICE_RISE_MILD <= price_change < PRICE_RISE_STRONG:
                        send_sms_alert(
                            symbol, current_price, last_price,
                            abs(price_change)*100, "mild_rise"
                        )
                    
                    # Check for 10%+ rise
                    elif price_change >= PRICE_RISE_STRONG:
                        send_sms_alert(
                            symbol, current_price, last_price,
                            abs(price_change)*100, "strong_rise"
                        )
                    
                    # Check for 25% drop
                    elif price_change <= -PRICE_DROP_THRESHOLD:
                        send_sms_alert(
                            symbol, current_price, price_history[symbol]['high'],
                            abs(price_change)*100, "drop"
                        )
                        price_history[symbol]['high'] = current_price
                    
                    # Update price history
                    price_history[symbol]['high'] = max(current_price, price_history[symbol]['high'])
                    price_history[symbol]['last_price'] = current_price
                
                except (KeyError, ValueError) as e:
                    print(f"Data error in {ticker.get('market')}: {e}")
                    continue
        
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))