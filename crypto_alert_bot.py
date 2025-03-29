import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client

import os

# Load environment variables
load_dotenv()

# CoinDCX API configuration
COINDCX_API_KEY = os.getenv('COINDCX_API_KEY')
COINDCX_API_SECRET = os.getenv('COINDCX_API_SECRET')
BASE_URL = 'https://api.coindcx.com'

# Twilio SMS configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
YOUR_MOBILE_NUMBER = os.getenv('YOUR_MOBILE_NUMBER')  # Include country code (e.g., +91 for India)

# Threshold for alert (25% drop)
PRICE_DROP_THRESHOLD = 0.25

# Dictionary to store previous highs
price_history = {}

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms_alert(symbol, current_price, previous_high, percentage_drop):
    message_body = (
        f"🚨 CRYPTO ALERT: {symbol} dropped by {percentage_drop:.2f}%!\n"
        f"📉 Current Price: ₹{current_price}\n"
        f"📈 Previous High: ₹{previous_high}\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_MOBILE_NUMBER
        )
        print(f"SMS Alert Sent! Message SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

def get_market_data():
    url = f"{BASE_URL}/exchange/ticker"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market data: {e}")
        return None

def monitor_prices():
    while True:
        market_data = get_market_data()
        
        if market_data:
            for ticker in market_data:
                symbol = ticker['market']
                current_price = float(ticker['last_price'])
                
                if symbol not in price_history:
                    price_history[symbol] = {
                        'previous_high': current_price,
                        'last_checked': datetime.now()
                    }
                    continue
                
                previous_high = price_history[symbol]['previous_high']
                
                # Update high if current price is higher
                if current_price > previous_high:
                    price_history[symbol]['previous_high'] = current_price
                    price_history[symbol]['last_checked'] = datetime.now()
                else:
                    # Calculate drop percentage
                    if previous_high > 0:
                        percentage_drop = (previous_high - current_price) / previous_high
                        
                        # Trigger alert if drop >= 10%
                        if percentage_drop >= PRICE_DROP_THRESHOLD:
                            send_sms_alert(
                                symbol,
                                current_price,
                                previous_high,
                                percentage_drop * 100
                            )
                            # Reset high to avoid repeated alerts
                            price_history[symbol]['previous_high'] = current_price
        
        # Check every 5 minutes (adjust as needed)
        time.sleep(300)

if __name__ == "__main__":
    print("🚀 Starting Crypto Price Drop Alert Bot with SMS Notifications...")
    monitor_prices()