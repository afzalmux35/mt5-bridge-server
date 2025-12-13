# EXNESS TRADING BRIDGE WITH DEBUG
from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import time

app = Flask(__name__)

print("🔥 EXNESS Trading Bridge Started")
print("=" * 60)

@app.route('/')
def home():
    return "✅ Trading Bridge Running. Send POST requests to /trade"

@app.route('/test')
def test():
    return jsonify({
        "status": "online",
        "broker": "Exness",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/trade', methods=['POST'])
def trade():
    try:
        # Get signal from Firebase
        data = request.json
        print(f"\n📡 📡 📡 NEW SIGNAL RECEIVED 📡 📡 📡")
        print(f"   Signal: {data}")
        
        # ========== STEP 1: Connect to MT5 ==========
        print("\n1. 🔌 CONNECTING TO MT5...")
        mt5_path = r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
        print(f"   Path: {mt5_path}")
        
        if not mt5.initialize(path=mt5_path):
            error_code = mt5.last_error()
            error_desc = mt5.last_error()[1] if isinstance(mt5.last_error(), tuple) else "Unknown error"
            print(f"   ❌❌❌ MT5 CONNECTION FAILED!")
            print(f"   Error Code: {error_code}")
            print(f"   Error Description: {error_desc}")
            print(f"   💡 SOLUTION: Ensure MT5 is running as Administrator!")
            return jsonify({
                "status": "error",
                "message": f"MT5 Connection Failed: {error_desc}",
                "code": error_code
            }), 500
        
        print("   ✅ MT5 CONNECTED SUCCESSFULLY")
        
        # ========== STEP 2: Login to Exness ==========
        print("\n2. 🔐 LOGGING INTO EXNESS...")
        login = 261813562
        password = "Mohyuddin@1107"
        server = "Exness-MT5Trial16"
        print(f"   Account: {login}")
        print(f"   Server: {server}")
        
        if not mt5.login(login=login, password=password, server=server):
            error_code = mt5.last_error()
            error_desc = mt5.last_error()[1] if isinstance(mt5.last_error(), tuple) else "Unknown error"
            mt5.shutdown()
            print(f"   ❌❌❌ LOGIN FAILED!")
            print(f"   Error Code: {error_code}")
            print(f"   Error Description: {error_desc}")
            print(f"   💡 SOLUTION: Check credentials in MT5 terminal")
            return jsonify({
                "status": "error",
                "message": f"Login Failed: {error_desc}",
                "code": error_code
            }), 500
        
        print(f"   ✅ LOGGED INTO ACCOUNT: {login}")
        
        # ========== STEP 3: Get account info ==========
        account = mt5.account_info()
        print(f"   Balance: ${account.balance}")
        print(f"   Equity: ${account.equity}")
        
        # ========== ADD NEW CODE HERE ==========
        print("\n🔧 Checking available symbols...")
        all_symbols = mt5.symbols_get()
        print(f"   Found {len(all_symbols)} symbols")
        
        # Check for XAUUSD or similar
        for sym in all_symbols[:10]:  # Show first 10 symbols
            print(f"   - {sym.name}")
        # ========== END NEW CODE ==========

        # ========== STEP 4: Prepare order ==========
        print("\n3. 📊 PREPARING ORDER...")
        symbol = data.get('symbol', 'XAUUSDm')
        action = data.get('action', 'BUY').upper()
        volume = float(data.get('volume', 0.01))
        
        print(f"   Symbol: {symbol}")
        print(f"   Action: {action}")
        print(f"   Volume: {volume} lots")
        
        # Check if symbol exists
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            mt5.shutdown()
            print(f"   ❌ SYMBOL NOT FOUND: {symbol}")
            return jsonify({
                "status": "error",
                "message": f"Symbol {symbol} not available"
            }), 500
        
        # Select the symbol
        mt5.symbol_select(symbol, True)
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            mt5.shutdown()
            print(f"   ❌ CANNOT GET PRICE FOR: {symbol}")
            return jsonify({
                "status": "error",
                "message": f"Cannot get price for {symbol}"
            }), 500
        
        if action == "BUY":
            price = tick.ask
            order_type = mt5.ORDER_TYPE_BUY
            print(f"   Buy Price (Ask): {price}")
        else:
            price = tick.bid
            order_type = mt5.ORDER_TYPE_SELL
            print(f"   Sell Price (Bid): {price}")
        
        # ========== STEP 5: Create order ==========
        order = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 999888,
            "comment": "Firebase-Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # ========== STEP 6: Execute trade ==========
        print(f"\n4. ⚡ EXECUTING {action} ORDER...")
        print(f"   Symbol: {symbol}")
        print(f"   Volume: {volume}")
        print(f"   Price: {price}")
        
        result = mt5.order_send(order)
        
        # ========== STEP 7: Shutdown MT5 ==========
        mt5.shutdown()
        
        # ========== STEP 8: Return result ==========
        print(f"\n5. 📝 ORDER RESULT:")
        print(f"   Return Code: {result.retcode}")
        print(f"   Comment: {result.comment}")
        print(f"   Order ID: {result.order}")
        print(f"   Price Executed: {result.price}")
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print("   ✅ ✅ ✅ TRADE SUCCESSFUL! ✅ ✅ ✅")
            return jsonify({
                "status": "success",
                "ticket": result.order,
                "price": result.price,
                "symbol": symbol,
                "action": action,
                "volume": volume,
                "comment": result.comment,
                "balance": account.balance
            })
        else:
            print("   ❌❌❌ TRADE FAILED! ❌❌❌")
            return jsonify({
                "status": "error",
                "code": result.retcode,
                "message": result.comment,
                "details": str(result)
            })
            
    except Exception as e:
        print(f"\n⚠️ ⚠️ ⚠️ UNEXPECTED ERROR ⚠️ ⚠️ ⚠️")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/account', methods=['GET'])
def account_info():
    try:
        print("\n📊 ACCOUNT INFO REQUESTED")
        
        if not mt5.initialize(path=r"C:\Program Files\MetaTrader 5\terminal64.exe"):
            return jsonify({"error": "MT5 not connected"}), 500
        
        if not mt5.login(261813562, "PFhijnUj", "Exness-MT5Trial16"):
            mt5.shutdown()
            return jsonify({"error": "Login failed"}), 500
        
        account = mt5.account_info()
        mt5.shutdown()
        
        return jsonify({
            "login": account.login,
            "balance": account.balance,
            "equity": account.equity,
            "profit": account.profit,
            "currency": account.currency,
            "leverage": account.leverage,
            "margin_free": account.margin_free,
            "margin_level": account.margin_level
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 BRIDGE READY FOR TRADING")
    print("=" * 60)
    print("🌐 Local URL: http://localhost:8000")
    print("🧪 Test URL: http://localhost:8000/test")
    print("💰 Account Info: http://localhost:8000/account")
    print("⚡ Trade Endpoint: http://localhost:8000/trade")
    print("=" * 60)
    print("📡 Waiting for trading signals from Firebase...")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=False)