import csv

def call(symbol, today, prev, o, l, value, change):
    data = [symbol, today, prev, o, l, value, change] #the data

    with open('open_low_result.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f) #this is the writer object
        writer.writerow(data) #this is the data
        f.close()