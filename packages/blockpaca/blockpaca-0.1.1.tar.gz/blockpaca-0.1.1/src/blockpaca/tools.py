from datetime import datetime,time 
import pytz 
import pandas_market_calendars as mcal 
import pandas as pd 
import csv 
import os 
from multiprocessing import Process
from functools import partial 


def check_datetime():
    eastern = pytz.timezone("US/Eastern")

    # Get the current time in Eastern Time
    now = datetime.now(eastern).time()

    # Define the start and end times
    start_time = time(16, 30)  # 4:30 PM
    end_time = time(21, 0)     # 9:00 PM

    # Check if the current time is within the range
    if start_time <= now <= end_time:
        return True 
    else:
        return False 
    


def check_market_open():
    # Get the NYSE calendar
    nyse = mcal.get_calendar('NYSE')
    
    # Get the current date and time
    now = pd.Timestamp.now(tz='America/New_York')
    today = now.strftime('%Y-%m-%d')
    
    # Retrieve the trading schedule for today
    schedule_df = nyse.schedule(start_date=today, end_date=today)  # Call schedule as a function

    # Check if there are trading hours for today
    if schedule_df.empty:
        return False  # Market is closed on weekends or holidays

    # Get the market open and close times
    today_schedule = schedule_df.loc[today]
    market_open = today_schedule['market_open']
    market_close = today_schedule['market_close']
    
    # Check if the current time is within market hours
    return market_open <= now <= market_close


def log_csv(path,row):

    if os.path.exists(path):
        with open(path,'a',newline='') as csvfile:
            fieldnames = row.keys()
            writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
            writer.writerow(row)

    else: 
        with open(path,'w',newline='') as csvfile:
            fieldnames = row.keys()
            writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)



def csv_trade_logging(ticker,quantity,order_type,order_id,
                       amount_completed,price_completed,time_to_complete,
                       start_quote,end_quote,name,method):
    #this will be called after the trade is completed (fed the return message from the paper or live trade)
    signal_bid = 0 
    signal_ask = 0 
    execution_bid = 0 
    execution_ask = 0 
    trade_profit = 0 
    date = None 
    if method == 'live':
        csv_save_path = os.path.join('/Users/henry/Computer_Science/Quant-Finance/data_logs/trade_logs/live',f'{name}.csv')
    elif method == 'paper':
        csv_save_path = os.path.join('/Users/henry/Computer_Science/Quant-Finance/data_logs/trade_logs/paper',f'{name}.csv')
    
    df = {
        'date':date,
        'ticker':ticker,
        'quantity': quantity,
        'order_type':order_type,
        'order_id':order_id,
        'amount_completed':amount_completed,
        'price_completed':price_completed,
        'time_to_complete':time_to_complete,
        'signal_bid': signal_bid,
        'signal_ask':signal_ask,
        'execution_bid':execution_bid,
        'execution_ask':execution_ask,
        'trade_profit':trade_profit 
    }

    log_csv(csv_save_path,df)


def csv_quotes_logging(message):

    df = {
        'type':message['T'],
        'ticker':message['S'],
        'bid_exchange':message['bx'],
        'bid_price':message['bp'],
        'bid_size':message['bs'],
        'ask_exchange':message['ax'],
        'ask_price':message['ap'],
        'ask_size':message['as'],
        'conditions':message['c'],
        'tape':message['z'],
        'timestamp':message['t']
    }

    csv_save_path = '/Users/henry/Computer_Science/Quant-Finance/data_logs/historical/tick/quotes.csv'
    log_csv(csv_save_path,df)



def write_to_shared_memory(shared_data,lock,data):
    with lock: 
        shared_data['data'] = data 

def write_owned_tickers_to_memory(shared_data,lock,data):
    with lock: 
        shared_data['tickers'] = data

def write_quote_to_shared_memory(shared_data,lock,data):
    with lock: 
        shared_data['quote'] = data 

def write_positions_to_shared_memory(shared_data,lock,data): 
    with lock: 
        shared_data['positions'] = data

#read from shared memory 
def read_from_shared_memory(shared_data,lock):
    with lock: 
        return shared_data.get('data',None)

def read_quote_from_shared_memory(shared_data,lock):
    with lock: 
        return shared_data.get('quote',None)

def read_positions_from_memory(shared_data,lock): 
    with lock: 
        return shared_data.get('positions',None)
    
def read_tickers_from_shared_memory(shared_data,lock):
    with lock: 
        return shared_data.get('tickers',None)
    
def read_active_trade_flag(shared_data,lock):
    with lock: 
        return shared_data.get('active_status',None)
    
def set_active_trade_flag_true(shared_data,lock):
    with lock: 
        shared_data['active_status'] = True 

def set_active_trade_flag_false(shared_data,lock):
    with lock: 
        shared_data['active_status'] = False  

def increment_avail_processors(shared_data,lock): 
    with lock: 
        shared_data["available_cpu"] += 1 

def decrement_avail_processors(shared_data,lock): 
    with lock: 
        shared_data["available_cpu"] -= 1  

def set_avail_processors(shared_data,lock,processors): 
    with lock: 
        shared_data["available_cpu"] = processors 


    


def weight_update(stock_split_stream,data):
    print()

def overall_performance():
    print()
    #monitors the performance of overall portfolio +/- 
    #monitors performance of portfolio compared to the market 
    #should include moving averages, peak to valley drawdown, 
        #research evaulation metrics from inside the black box book 
    #ok to leave this as a function  




def multiprocess_test(shared_data,lock): 
    while True: 
        read_data = read_from_shared_memory(shared_data,lock)
        print(f'Test: {read_data}')
        read_portfolio = read_positions_from_memory(shared_data,lock)
        print(f'portfolio test: {read_portfolio}')
        time.sleep(5)
    #now need a way for 


def buy_test(shared_data,lock,portfolio):
    #need to find an easier way to execute the buy function without having to pass in 
    #the shared data and lock functions every time
    time.sleep(5)
    portfolio.buy_stock('MSFT','market',20,shared_data,lock)
    time.sleep(2)
    portfolio.buy_stock('AAPL','market',20,shared_data,lock)
    time.sleep(3)
    portfolio.buy_stock('TSLA','market',20,shared_data,lock)
    time.sleep(10)
    portfolio.sell_stock('AAPL','market',10,shared_data,lock)


def buy_stocks(shared_data,lock,portfolio,order_list):

    print('###  TEST ###')
    time.sleep(20)
    processes = []
    max_processes = os.cpu_count() - 4
    if max_processes < 1: 
        raise Exception("### NO AVAILABLE CPU CORES ###")
    if len(order_list) > max_processes: 
        order_list = order_list[:max_processes]
        print('### MORE PROCESSORS THAN AVAILABLE REQUESTED ###')
        print(f"### NOT EXECUTING {[order['ticker'] for order in order_list[max_processes:]]}")
        print(f'### EXECUTING {[order['ticker'] for order in order_list[:max_processes]]}')
    for order in order_list: 
        if order['side'] == 'buy':
            process = Process(target=partial(portfolio.buy_stock,order['ticker'],order['type'],order['quantity'],shared_data,lock))
            processes.append(process)
        if order['side'] == 'sell':
            print()
            #current placeholder

    print('finished making processes')

    for trade_process in processes: 
        trade_process.start()

    # for trade_process in processes: 
    #     trade_process.join()  



def get_socket(): 
    in_hours = check_datetime()
    check_open = check_market_open()
    if check_open is True: 
        socket = 'wss://stream.data.alpaca.markets/v2/iex' 
    else: 
        socket = 'wss://stream.data.alpaca.markets/v2/test' 

    return socket   



from datetime import datetime, timedelta
import pytz
import pandas_market_calendars as mcal

def convert_run_duration_to_seconds(duration: str) -> int:
    """
    Converts a run duration string into seconds, ensuring it does not extend into the last 30 seconds before market close.
    
    Args:
        duration (str): The run duration. Supported formats:
                        - "EOD" (end of day)
                        - "1h", "2h" (hours)
                        - "1m", "2m" (minutes)
                        - Raw seconds as an integer string (e.g., "3600")
    
    Returns:
        int: The total run duration in seconds.
    
    Raises:
        ValueError: If the duration format is invalid or if the run time extends into the last 30 seconds before market close.
    """
    # Get the NYSE calendar
    nyse = mcal.get_calendar('NYSE')
    now = pd.Timestamp.now(tz='America/New_York')
    today = now.strftime('%Y-%m-%d')

    # Retrieve today's trading schedule
    schedule_df = nyse.schedule(start_date=today, end_date=today)
    if schedule_df.empty:
        raise ValueError("Market is closed today. Cannot calculate run duration.")

    # Get market open and close times
    today_schedule = schedule_df.loc[today]
    market_close = today_schedule['market_close']

    # Ensure we are not within 30 seconds of market close
    if now >= market_close - timedelta(seconds=30):
        raise ValueError("Cannot start a run within 30 seconds of market close.")

    # Convert duration to seconds
    if duration.lower() == "eod":
        # Calculate seconds until the end of the day (market close)
        run_seconds = int((market_close - now).total_seconds()) - 30
        if run_seconds <= 0:
            raise ValueError("Run duration extends into the last 30 seconds before market close.")
        return run_seconds
    elif duration.endswith("h"):
        # Convert hours to seconds
        hours = int(duration[:-1])
        run_seconds = hours * 3600
    elif duration.endswith("m"):
        # Convert minutes to seconds
        minutes = int(duration[:-1])
        run_seconds = minutes * 60
    elif duration.isdigit():
        # Raw seconds
        run_seconds = int(duration)
    else:
        raise ValueError(f"Invalid duration format: {duration}")

    # Ensure the run duration does not extend into the last 30 seconds before market close
    if now + timedelta(seconds=run_seconds) >= market_close - timedelta(seconds=30):
        raise ValueError("Run duration extends into the last 30 seconds before market close.")

    return run_seconds 



import os
import csv

def trade_update_to_csv(path, message):
    """
    Accept either a dict (single message) or a list of dicts.
    Append rows to CSV, creating parent dir and header when needed.
    """
    # normalize to list of dicts
    rows = message if isinstance(message, list) else [message]
    # keep only dict rows
    rows = [r for r in rows if isinstance(r, dict)]
    if not rows:
        return

    # derive fieldnames: start with first row keys, then add any missing keys from others
    fieldnames = list(rows[0].keys())
    for r in rows[1:]:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)













