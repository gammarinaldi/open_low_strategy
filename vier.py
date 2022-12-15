import users
import login
import stock_info
import stock_all
import write_to_csv
import concurrent.futures
import traceback
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

today = date.today()

def execute_open_low(access_token, symbol):
    res = stock_info.call(access_token, symbol)
    if res.status_code == 200:
        data = res.json()
        symbol = data["data"]["symbol"]
        open = data["data"]["open"]
        low = data["data"]["low"]
        value = data["data"]["value"]
        prev = data["data"]["previous"]

        bids = []
        asks = []
        bid = data["data"]["bid"]
        ask = data["data"]["offer"]
        if bid != "None" or ask != "None":
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
                    write_to_csv.call(symbol, today, open, low, value)
            except:
                print("Error is here: " + symbol)
                print("Error traceback:")
                print(traceback.format_exc())
                print("Response data:")
                print(data["data"])
    else:
        print("HTTP error")
        print(res.text)

def async_screening(access_token):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = executor_submit(access_token, executor)
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
        return {executor.submit(execute_open_low, access_token, symbol): symbol for symbol in stock_all.list}

if __name__ == '__main__':
    t1 = time.time()
    res = login.call(users.list[0])

    if res.status_code == 200:
        data = res.json()
        access_token = "Bearer " + data["data"]["access_token"]
        async_screening(access_token)
        # execute_open_low(access_token, "PAMG")
    else:
        print("HTTP error")
        print(res.text)

    t2 = time.time()
    diff = t2 -t1
    print("Elapsed times: " + str(round(diff, 2)))
