import users
import login
import stock_info
import stock_all
import write_to_csv
import concurrent.futures
import traceback
import time
import get_security_token
import login_security
import buy
import sell
import portfolio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from math import floor

enable_buy = 0
enable_sell = 1

today = date.today()
email = users.list[0]
password = users.list[1]
pin = users.list[2]

def tick(price):
    if price <= 200: 
        return 1
    elif price > 200 and price <= 500: 
        return 2
    elif price > 500 and price <= 2000: 
        return 5
    elif price > 2000 and price <= 5000: 
        return 10
    else: 
        return 25

def send_buy_order(access_security_token, symbol, buy_price, shares):
    res = buy.call(access_security_token, symbol, buy_price, shares)
    if res.status_code == 200:
        data = res.json()
        msg = data["message"]
        order_id = data["data"]["orderid"]
        print(f"{symbol}: {msg} with order id: {order_id}")
    else:
        print("HTTP error: buy")
        print(res.text)

def send_sell_order(access_security_token, symbol, ask_price):
    res = portfolio.call(access_security_token)
    if res.status_code == 200:
        data = res.json()
        porto_dicts = data["data"]["result"]
        dict = [i for i in porto_dicts if i["symbol"] == symbol]
        if dict != []:
            shares = dict[0]["available_lot"] * 100
            sell_price = ask_price + (tick(ask_price) * 3)
            res = sell.call(access_security_token, symbol, sell_price, shares)
            if res.status_code == 200:
                data = res.json()
                msg = data["message"]
                order_id = data["data"]["orderid"]
                print(f"{symbol}: {msg} with order id: {order_id}")
            else:
                print("HTTP error: sell")
                print(res.text)
        else:
            print(f"{symbol}: not exists in portfolio")
    else:
        print("HTTP error: portfolio")
        print(res.text)

def execute_open_low(access_token, access_security_token, symbol):
    res = stock_info.call(access_token, symbol)
    if res.status_code == 200:
        data = res.json()
        symbol = data["data"]["symbol"]
        open = data["data"]["open"]
        low = data["data"]["low"]
        value = data["data"]["value"]
        prev = data["data"]["previous"]
        change = data["data"]["percentage_change"]

        bids = []
        asks = []
        bid = data["data"]["bid"]
        ask = data["data"]["offer"]
        
        if bid is None or ask is None:
            print(symbol + ": Bid/Ask is not available")
        else:
            try:
                for x in bid:
                    for y in range(9):
                        n = y+1
                        if x == f"volume{str(n)}":
                            if bid[x] != "-":
                                bids.append(int(bid[x]))
                total_bids = sum(bids)
            
                for x in ask:
                    for y in range(9):
                        n = y+1
                        if x == f"volume{str(n)}":
                            if ask[x] != "-":
                                asks.append(int(ask[x]))
                total_asks = sum(asks)

                if open == low and total_bids > total_asks and open > prev and value > 1_000_000_000:
                    write_to_csv.call(symbol, today, prev, open, low, value, change)
                    buy_price = ask["price1"]
                    # amount = 1_000_000
                    # shares = floor(( amount / float(buy_price)))
                    shares = 100
                    if enable_buy == 1: send_buy_order(access_security_token, symbol, buy_price, shares)
                    time.sleep(180) # delay 3 minutes
                    if enable_sell == 1: send_sell_order(access_security_token, symbol, ask["price1"])
            except:
                print("Error is here: " + symbol)
                print("Error traceback:")
                print(traceback.format_exc())
                print("Response data:")
                print(data["data"])
    else:
        print("HTTP error")
        print(res.text)

def async_screening(access_token, access_security_token):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = executor_submit(access_token, access_security_token, executor)
        for future in concurrent.futures.as_completed(future_to_user):
            try:
                if future.result() != None:
                    print("Async result error")
                    print(future.result())
            except Exception as error:
                print("Exeption error occured:")
                print(error)
                print(traceback.format_exc())

def executor_submit(access_token, executor):
        return {executor.submit(execute_open_low, access_token, access_security_token, symbol): symbol for symbol in stock_all.list}

if __name__ == '__main__':
    t1 = time.time()
    res = login.call(email, password)
    if res.status_code == 200:
        data = res.json()
        access_token = "Bearer " + data["data"]["access_token"]
        res = get_security_token.call(access_token)
        if res.status_code == 200:
            data = res.json()
            res = login_security.call(pin, data["data"]["token"])
            if res.status_code == 200:
                data = res.json()
                access_security_token = "Bearer " + data["data"]["access_token"]
                # async_screening(access_token, access_security_token)
                # execute_open_low(access_token, access_security_token, "SAME")
                # send_buy_order(access_security_token, "GOTO", 80, 100)
                send_sell_order(access_security_token, "GOTO", 95)
            else:
                print("HTTP error: login_security")
                print(res.text)
        else:
            print("HTTP error: get_security_token")
            print(res.text)
    else:
        print("HTTP error")
        print(res.text)

    t2 = time.time()
    diff = t2 -t1
    print("Elapsed times: " + str(round(diff, 2)))
