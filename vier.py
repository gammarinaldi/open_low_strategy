import users
import login
import stock_info
import stock_all
import write_to_csv
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from datetime import date

today = date.today()

def execute_open_low(access_token, symbol):
    res = stock_info.call(access_token, symbol)
    data = res.json()
    symbol = data["data"]["symbol"]
    open = data["data"]["open"]
    low = data["data"]["low"]
    value = data["data"]["value"]
    prev = data["data"]["previous"]

    bids = []
    bid = data["data"]["bid"]
    for x in bid:
        for y in range(9):
            n = y+1
            if x == f"volume{str(n)}":
                if bid[x] != "-":
                    bids.append(int(bid[x]))
    total_bids = sum(bids)
    
    asks = []
    ask = data["data"]["offer"]
    for x in ask:
        for y in range(9):
            n = y+1
            if x == f"volume{str(n)}":
                if ask[x] != "-":
                    asks.append(int(ask[x]))
    total_asks = sum(asks)

    if open == low and total_bids > total_asks and open > prev and value > 100_000_000:
        write_to_csv.call(symbol, today, open, low, value)

def async_screening(access_token):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = executor_submit(access_token, executor)
        for future in concurrent.futures.as_completed(future_to_user):
            try:
                if future.result() == None:
                    print("Async result OK")
                else:
                    print("Async result ERROR")
                    print(future.result())
            except Exception as error:
                print(error)

def executor_submit(access_token, executor):
        return {executor.submit(execute_open_low, access_token, symbol): symbol for symbol in stock_all.list}

if __name__ == '__main__':
    res = login.call(users.list[0])
    if res.status_code == 200:
        data = res.json()
        access_token = "Bearer " + data["data"]["access_token"]
        async_screening(access_token)
        # execute_open_low(access_token, "BSSR")
