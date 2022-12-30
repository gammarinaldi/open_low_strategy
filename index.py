import users
import login
import stock_info
import stock_all
import concurrent.futures
import traceback
import time
import get_security_token
import login_security
import buy
import sell
import portfolio
import csv
import os
import requests
import json
import telegram
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from math import floor
from dotenv import load_dotenv

load_dotenv()

prev_data_path = os.getenv('PREV_DATA_PATH')
dir_path = os.getenv('DIR_PATH')
params = dict(apiKey=os.getenv('PROXY_ROTATOR_KEY'))
resp = requests.get(url=os.getenv('PROXY_ROTATOR_URL'), params=params)
resp_text = json.loads(resp.text)
proxies = {
   "http": f"http://{resp_text['proxy']}"
}

enable_buy = 0
enable_sell = 0

today = date.today()
email = users.list[0]
password = users.list[1]
pin = users.list[2]

prev_list = []
log_list = []

def get_tele_data():
    load_dotenv()
    tele_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tele_log_id = os.getenv('TELEGRAM_LOGGER_ID')

    return tele_bot_token, tele_log_id

def get_tele_bot():
    tele_bot_token, tele_log_id = get_tele_data()
    bot = telegram.Bot(token=tele_bot_token)
    return bot, tele_log_id

def send_log():
    bot, tele_log_id = get_tele_bot()
    bot.send_message(chat_id=tele_log_id, text=join_msg(log_list))

def join_msg(list):
    if list:
        return '\n'.join(list)
    else:
        return "Message is empty"

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
    res = buy.call(access_security_token, symbol, buy_price, shares, proxies)
    if res.status_code == 200:
        data = res.json()
        msg = data["message"]
        order_id = data["data"]["orderid"]
        event = f"{symbol}: {msg} with order id: {order_id} sent"
        log_list.append(event)
        print(event)
    else:
        event = symbol + ": HTTP error: buy"
        log_list.append(event)
        print(event)
        print(res.text)

def send_sell_order(access_security_token, symbol, ask_price):
    res = portfolio.call(access_security_token, proxies)
    if res.status_code == 200:
        data = res.json()
        porto_dicts = data["data"]["result"]
        dict = [i for i in porto_dicts if i["symbol"] == symbol]
        if dict != []:
            shares = dict[0]["available_lot"] * 100
            sell_price = ask_price + (tick(ask_price) * 3)
            res = sell.call(access_security_token, symbol, sell_price, shares, proxies)
            if res.status_code == 200:
                data = res.json()
                msg = data["message"]
                order_id = data["data"]["orderid"]
                event = f"{symbol}: {msg} with order id: {order_id} sent"
                log_list.append(event)
                print(event)
            else:
                event = symbol + ": HTTP error: sell"
                log_list.append(event)
                print(event)
                print(res.text)
        else:
            event = f"{symbol}: not exists in portfolio"
            log_list.append(event)
            print(event)
    else:
        event = symbol + ": HTTP error: portfolio"
        log_list.append(event)
        print(event)
        print(res.text)

def is_empty_csv(path):
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        for i, _ in enumerate(reader):
            if i:  # Found the second row
                return False
    return True

def get_prev_data():
    event = "Load previous market quotes."
    log_list.append(event)
    print(event)

    with open(prev_data_path, "r") as file:
        csvreader = csv.reader(file)
        if is_empty_csv(prev_data_path) == False:
            next(csvreader, None) # Skip first row (header)
            for row in csvreader:
                prev_date = row[1]
                prev_symbol = row[2]
                prev_low = row[5]
                prev_list.append([prev_symbol, prev_date, prev_low])
        file.close()
        
def execute_open_low(access_token, access_security_token, symbol):
    res = stock_info.call(access_token, symbol, proxies)
    try:
        if res.status_code == 200:
            data = res.json()
            if data["data"] == None:
                print(symbol + ": No data")
            else:
                symbol = data["data"]["symbol"]
                open = data["data"]["open"]
                low = data["data"]["low"]
                value = data["data"]["value"]
                freq = data["data"]["frequency"]
                change = data["data"]["percentage_change"]

                bids = []
                asks = []
                bid = data["data"]["bid"]
                ask = data["data"]["offer"]
                
                if bid is None or ask is None:
                    print(symbol + ": Bid/Ask is empty")
                else:
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

                    # Get prev low
                    for data in prev_list:
                        prev_symbol = data[0]
                        prev_date = data[1]
                        d = 3 if today.strftime('%A') == 'Monday' else 1
                        date = today - timedelta(days=d)
                        yesterday = date.strftime('%Y-%m-%d')
                        
                        if symbol == prev_symbol and yesterday == prev_date:
                            prev_low = int(data[2].replace('.0', ''))
                            if (
                                    open == low and total_bids > total_asks and 
                                    low > prev_low and value > 100_000_000
                                ):
                                event = f"{symbol},{today},{open},{low},{prev_low},{value},{freq},{change}"
                                log_list.append(event)
                                print(event)
                                
                                save_result(symbol, today, open, low, prev_low, value, freq, change)
                                buy_price = ask["price1"]
                                # amount = 1_000_000
                                # shares = floor(( amount / float(buy_price)))
                                shares = 100
                                if enable_buy == 1: 
                                    send_buy_order(access_security_token, symbol, buy_price, shares)

                    # print(symbol + ": done")
        else:
            event = symbol + ": HTTP error"
            log_list.append(event)
            print(event)
            print(res.text)
    except:
            save_failed(symbol)
            # print(symbol + ": Exception error")
            # print("Error traceback:")
            # print(traceback.format_exc())
            print("Response:")
            print(res)

def save_result(symbol, date, o, l, prev_low, value, freq, change):
    with open(f'{dir_path}\\open_low_result.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f) #this is the writer object
        writer.writerow([symbol, date, o, l, prev_low, value, freq, change]) #this is the data
        f.close()

def save_failed(symbol):
    with open(f'{dir_path}\\failed.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f) #this is the writer object
        writer.writerow([symbol]) #this is the data
        f.close()

def executor_submit(executor, access_token, access_security_token):
    return {executor.submit(execute_open_low, access_token, access_security_token, symbol): symbol for symbol in stock_all.list}

def async_screening(access_token, access_security_token):
    event = "Start async screening..."
    log_list.append(event)
    print(event)

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = executor_submit(executor, access_token, access_security_token)
        for future in concurrent.futures.as_completed(future_to_user):
            try:
                if future.result() != None:
                    print("Async result error")
                    print(future.result())
            except Exception as error:
                print("Exeption error occured:")
                print(error)
                print(traceback.format_exc())

if __name__ == '__main__':
    event = "Start strategy: open == low"
    log_list.append(event)
    print("Start strategy: open == low")
    t1 = time.time()
    event = "Using proxies: " + proxies["http"]
    log_list.append(event)
    print(event)

    event = f"Execution settings: buy={enable_buy}, sell={enable_sell}"
    log_list.append(event)
    print(event)

    get_prev_data()

    res = login.call(email, password, proxies)
    if res.status_code == 200:
        data = res.json()
        access_token = "Bearer " + data["data"]["access_token"]
        res = get_security_token.call(access_token, proxies)
        if res.status_code == 200:
            data = res.json()
            res = login_security.call(pin, data["data"]["token"], proxies)
            if res.status_code == 200:
                data = res.json()
                access_security_token = "Bearer " + data["data"]["access_token"]
                event = "Login to Stockbit success."
                log_list.append(event)
                print(event)

                async_screening(access_token, access_security_token)
                # execute_open_low(access_token, access_security_token, "GOTO")
                # send_buy_order(access_security_token, "GOTO", 80, 100)
                # send_sell_order(access_security_token, "GOTO", 95)

                event = "Async screening finish."
                log_list.append(event)
                print(event)

                if enable_sell == 1:
                    time.sleep(180)
                    path = "open_low_result.csv"
                    with open(path, "r") as file:
                        csvreader = csv.reader(file)
                        if is_empty_csv(path) == False:
                            for row in csvreader:
                                symbol = row[0]
                                ask_price = int(row[7])
                                send_sell_order(access_security_token, symbol, ask_price)
                        file.close()
            else:
                event = "HTTP error: login_security"
                log_list.append(event)
                print("HTTP error: login_security")
                print(res.text)
        else:
            event = "HTTP error: get_security_token"
            log_list.append(event)
            print(event)
            print(res.text)
    else:
        event = "HTTP error"
        log_list.append(event)
        print("HTTP error")
        print(res.text)

    t2 = time.time()
    diff = t2 -t1
    event = f"Elapsed times: {str(round(diff, 2))} seconds."
    log_list.append(event)
    print(f"Elapsed times: {str(round(diff, 2))} seconds.")

    send_log()
    