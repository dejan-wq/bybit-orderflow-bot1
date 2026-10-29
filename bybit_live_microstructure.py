def process_live_market_flow(message):
    global rolling_cvd
    try:
        if 'data' in message:
            trade_data = message['data']
            
            for tick in trade_data:
                price = float(tick['p'])      
                quantity = float(tick['v'])   
                side = tick['S']       
                
                # 🟢 FORCE RENDER LOGS TO SHOW CONTINUOUS SCROLLING DATA:
                print(f"📡 CLOUD FEEDS: {side} | Price: ${price:,.2f} | Vol: {quantity} BTC | CVD: {rolling_cvd:,.0f}")
                
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
