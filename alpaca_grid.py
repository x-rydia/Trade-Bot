import datetime
import alpaca_trade_api as trade_api
import pandas as pd

from pandas import DataFrame
from datetime import date, timedelta, datetime
from dateutil.relativedelta import *
from time import sleep


class grid_bot:
    '''Upon initialization the HalpernGrid bot will do:
        -Connect to the Alpaca API
        -Loosely define the grid strategy
        -place stop loss and take profit orders
       Other Methods include:
        -continuosly placing orders in real time'''
    def __init__(self, key: str, secret: str, live: bool, accumulate_constant: float,
    number_of_buy_lines: int, number_of_sell_lines: int, grid_line_percentage,
    stop_loss_percentage: float, take_profit_percentage: float, symbol: str, qty_unit: str):

        #Establish API connection and determine if live or simulated
        #trading will be employed
        if live: end = 'live_end'
        else: end = 'https://paper-api.alpaca.markets'
        self.api = trade_api.REST(key, secret, end, 'v2')

        self.symbol = symbol
        self.qty_unit = qty_unit
        self.tick = 0

        #set of grid lines according to sepcifications in bot
        #initialization
        self.number_of_sell_lines = number_of_sell_lines
        self.number_of_buy_lines = number_of_buy_lines
        self.grid_line_percentage = grid_line_percentage
        self.buy_lines = []
        self.sell_lines = []

        #stop loss and take profit configuration
        self.stop_loss_percentage = stop_loss_percentage
        self.take_profit_percentage = take_profit_percentage

    def get_current_price_data(self) -> float:
        quote = self.api.get_last_quote(self.symbol)._raw
        price = round(quote['askprice'], 2)
        return price
    
    def get_historical_data(self) -> DataFrame:
        delta = timedelta(days=30)
        start_time = (datetime.now() - delta).isoformat()
        end_time = datetime.now().isoformat()
        bars = self.api.get_barset(self.symbol, '15Min', 1000, 
                                start=start_time, end=end_time)
        return bars.df
    
    def draw_grid_lines(self):
        self.buy_lines = []
        self.sell_lines = []
        price = self.get_current_price_data()
        for line in range(self.number_of_buy_lines):
            multiplier = 1 - (line * self.grid_line_percentage)
            self.buy_lines.append(price*multiplier)
        
        for line in range(self.number_of_sell_lines):
            multiplier = 1 + (line * self.grid_line_percentage)
            self.sell_lines.append(price*multiplier)
    
    def run(self):
        while True:
            data = self.get_historical_data()
            current = self.get_current_price_data()
            high_low_average = []
            for i in range(len(data.iloc[:,1])):
                high_low_average.append(round((data.iloc[i,2] + data.iloc[i,3])/2, 2))
                print(high_low_average)
            sleep(60)

            
        





        


if __name__ == '__main__':
    bot = grid_bot(
        key = 'PK6SY5LDSECA3CNRM26T',
        secret = 'vSX3hP6YJXbagElKQuBZy432yV2cL8qBfM47JG2u',
        live = False,
        accumulate_constant=1,
        number_of_buy_lines=5,
        number_of_sell_lines=5,
        grid_line_percentage=.01,
        stop_loss_percentage=5.0,
        take_profit_percentage=5.0,
        symbol='AAPL',
        qty_unit=1
    )
    bot.run()




    