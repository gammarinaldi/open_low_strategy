import csv

def call(stock, today, o, l, value):
    data = [stock, today, o, l, value] #the data

    with open('vier.csv', 'a') as f:
        writer = csv.writer(f) #this is the writer object
        writer.writerow(data) #this is the data