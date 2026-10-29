import time
import math
import threading
import requests
import numpy as np
from collections import deque
from pybit.unified_trading import WebSocket, HTTP

# =====================================================================
# CONFIGURATION PASTE ZONE (RESTORED KEYS & ADDED NTFY PROFILE)
# =====================================================================
TESTNET_API_KEY = "dflRDmqEPlzK9r2PVb"
TESTNET_API_SECRET = "GgBe22xCJeUVlST41bCKP1UyLWLwO0fIjgUt"

# 🔔 PUT YOUR UNIQUE NTFY TOPIC STRING INSIDE THESE QUOTES:
NTFY_TOPIC = "orderflow-bot"

SIMULATED_BALANCE = 1000.0   # Your Demo Account Target Balance
MAX_RISK_PCT = 0.02          # Your strict 2% Capital Defender Rule

# Indicators Lookback Memory Window
WINDOW_SIZE = 30 
price_history = deque(maxlen=WINDOW_SIZE)
cvd_history = deque(maxlen=WINDOW_SIZE)
rolling_cvd = 0.0

# Initialize Secure Private Execution Client
session = HTTP(
    testnet=True, 
    api_key=TESTNET_API_KEY,
    api_secret=TESTNET_API_SECRET
)

def send_ntfy_alert(title, message, priority="default"):
    """Transmits real-time trade signals straight to your phone via Ntfy app"""
    if not NTFY_TOPIC or "YOUR_EXISTING" in NTFY_TOPIC:
        return
    try:
        url = f"https://ntfy.sh{NTFY_TOPIC}"
        headers = {"Title": title, "Priority": priority}
        requests.post(url, data=message, headers=headers, timeout=5)
    except Exception as e:
        print(f"\n⚠️ Ntfy Dispatch Alert Failed: {e}")

def calculate_regression_slope(data_series):
    if len(data_series) < 15:
        return 0.0
    y = np.array(data_series)
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

def calculate_position_size(entry_price, stop_loss_price):
    allowed_loss_usd = SIMULATED_BALANCE * MAX_RISK_PCT 
    price_distance_pct = abs(entry_price - stop_loss_price) / entry_price
    if price_distance_pct == 0:
        return 0.0
    position_value_usd = allowed_loss_usd / price_distance_pct
    token_quantity = position_value_usd / entry_price
    return round(token_quantity, 3)

def execute_testnet_short(symbol, entry_price, stop_loss):
    try:
        qty = calculate_position_size(entry_price, stop_loss)
        if qty <= 0:
            return
        
        real_exposure = qty * entry_price
        
        # Dispatch Pre-Trade Notification
        send_ntfy_alert(
            title="🐋 ORDER FLOW SIGNAL INTERCEPTED",
            message=f"Absorption wall found at ${entry_price:,.2f}.\nTransmitting market short order for {qty} BTC (~${real_exposure:,.2f}).",
            priority="high"
        )
        
        print(f"\n[🚀 TRANSMITTING ORDER] Deploying short order for {qty} BTC...")
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side="Sell",
            orderType="Market",
            qty=str(qty),
            timeInForce="GTC",
            stopLoss=str(round(stop_loss, 1)),
            slTriggerBy="LastPrice"
        )
        
        order_id = order['result']['orderId']
        print(f" └─ Order Placed on Testnet! Order ID: {order_id}")
        
        # Dispatch Execution Confirmation Notification
        send_ntfy_alert(
            title="🚀 POSITION FULLY EXECUTED",
            message=f"SHORT Entry Filled successfully!\nSize: {qty} BTC at ${entry_price:,.2f}\nStop-Loss Bound Set: ${stop_loss:,.2f}\nID: {order_id}",
            priority="urgent"
        )
    except Exception as e:
        print(f"Execution Engine Error: {e}")
        send_ntfy_alert("❌ Execution Refused", f"Bybit Error: {e}", priority="high")

def process_live_market_flow(message):
    global rolling_cvd
    try:
        if 'data' in message:
            trade_data = message['data']
            
            # Silent background monitoring to optimize server performance
            print(f"📡 SCANNING RAW DATA TAPE: Received {len(trade_data)} fresh transactions...", end="\r")
            
            for tick in trade_data:
                price = float(tick['p'])      
                quantity = float(tick['v'])   
                side = tick['S']       
                
                net_delta = quantity if side == "Buy" else -quantity
                rolling_cvd += net_delta
                
                price_history.append(price)
                cvd_history.append(rolling_cvd)
                
                s_price = calculate_regression_slope(price_history)
                s_cvd = calculate_regression_slope(cvd_history)
                
                if s_cvd > 5.0 and s_price <= 0.0:
                    print(f"\n🐋 PRO TRIGGER: Institutional Absorption exposed on Testnet!")
                    target_stop_loss = price * 1.005 
                    execute_testnet_short("BTCUSDT", price, target_stop_loss)
                    time.sleep(10) 
    except Exception as e:
        pass

def run_dummy_port_server():
    """Binds an empty background socket server to satisfy Render's Free Web Service rules"""
    import socket
    import os
    port = int(os.environ.get("PORT", 10000))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(1)
    print(f"🔓 DUMMY SERVER ONLINE: Port binding secured on Port {port}.")
    while True:
        try:
            client, addr = server.accept()
            client.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nBot Active!")
            client.close()
        except:
            time.sleep(1)

print("=====================================================================")
print("          INITIALIZING BYBIT MICROSTRUCTURE TESTNET BOT              ")
print(f" Risk Parameters Locked: Balance ${SIMULATED_BALANCE} | Risk Cap: {MAX_RISK_PCT*100}% ")
print("=====================================================================")

# Send a boot notification to verify the link works instantly on startup
send_ntfy_alert("🤖 ALGORITHM CONNECTED", "Bybit Orderflow Engine is running successfully on Frankfurt Free Tier Cloud Instance.", "low")

# Launch the Render dummy port responder in a separate background thread
server_thread = threading.Thread(target=run_dummy_port_server, daemon=True)
server_thread.start()

# Initialize Real-Time Streaming Data Channel Pipe Hook
ws = WebSocket(testnet=True, channel_type="linear")
ws.trade_stream(symbol="BTCUSDT", callback=process_live_market_flow)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nDisconnecting cleanly from Bybit Testnet. Bot sleeping.")

