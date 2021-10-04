from typing import Any, List
import alpaca_trade_api as trade_api
from alpaca_trade_api.entity import Account
from constants import *
from datetime import datetime
from time import sleep, time


def ord_id(symbol: str, price: float, tick: int) -> str:
    return f'{symbol}{price * tick}'

class grid_bot:
    def __init__(self, api_key: str, api_secret: str, symbol: str,
                grid_interval: float, buy_lines: int, sell_lines: int,
                stop_loss: float=5, take_profit: float=5, live:bool=False,
                initial_investment: float=100000, buy_unit:float=1, 
                sell_unit:float=0.2):
        #Grid Configuration
        self.symbol = symbol
        self.grid_interval = grid_interval
        self.buy_lines = buy_lines
        self.sell_lines = sell_lines
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.buy_unit = buy_unit
        self.sell_unit = sell_unit
        self.is_live = live

        #tick system -- Aw shit, here we go again
        self.tick = 0
        self.orders = []
        
        #Create Alpaca API connection according to provided mode
        if live: 
            self.api = trade_api.REST(api_key, api_secret, LIVE_ENDPT)
        else:
            self.api = trade_api.REST(api_key, api_secret, PAPER_ENDPT)
    
    def __str__(self):
        return f"""
        GRID-BOT STATS/CONFIG:
         ___________________________________________________
        |Ticker:          |{self.symbol}                    |
        |Buy/Sell Ratio:  |{self.buy_unit}/{self.sell_unit} |
        |Live:            |{self.is_live}                   |
        |Buy Lines:       |{self.buy_lines}                 |
        |Sell Lines       |{self.sell_lines}                |
         ___________________________________________________|
        """

    def get_current_price(self) -> float:
        current_price = list(dict.values(self.api.get_last_quote(self.symbol)._raw))
        return float(current_price[0])
    
    def is_market_open(self) -> bool:
        clock = self.api.get_clock()._raw
        if clock['is_open']:
            print('The Market is Open')
        else:
            print(f'Market not open at timestamp: {datetime.now()}')
        return clock['is_open']
    
    def optimal_buy_size(self) -> float:
        account_data = self.api.get_account()._raw
        buying_power = account_data['buying_power']
        cash = account_data['cash']
        print(f'Buying power: {buying_power}, Cash: {cash}')
        return self.buy_unit
    
    def optimal_sell_size(self) -> float:
        account_data = self.api.get_account()._raw
        buying_power = account_data['buying_power']
        cash = account_data['cash']
        print(f'Buying power: {buying_power}, Cash: {cash}')
        return self.sell_unit
    
    
    def set_buy_lines(self) -> List:
        buy_lines, price = [], self.get_current_price()
        for i in range(self.buy_lines):
            buy_lines.append(price - (i * self.grid_interval))
        return buy_lines
    
    
    def set_sell_lines(self) -> List:
        sell_lines, price = [], self.get_current_price()
        for i in range(self.buy_lines):
            sell_lines.append(price + (i * self.grid_interval))
        return sell_lines
    
    def run(self):
        while True:
            
            if self.tick == 0:
                print("""
                TRADEBOT IS NOW LIVE, PLEASE DO NOT CLOSE THIS WINDOW 
                OR POWER OFF/SLEEP MODE YOUR PC WHILE STOCK MARKET OPEN
                """)
                self.api.cancel_all_orders()
                self.tick += 1
                print(f'SETUP ITERATION: {self.tick}')

                
            elif (self.tick % 10 == 0 or self.tick == 2) and self.is_market_open():
                print(f'ORDER ITERATION: {self.tick}')
                price = self.get_current_price()
                lines = (self.set_buy_lines(), self.set_sell_lines())
                for i in range(self.buy_lines):
                    self.api.submit_order(symbol=self.symbol,
                                          qty=str(self.buy_unit),
                                          side='buy',
                                          type='limit',
                                          time_in_force='gtc',
                                          limit_price=str(lines[0][i]),
                                          client_order_id=ord_id(self.symbol, lines[0][i], self.tick))
                    print(f'Submitted order to buy {self.symbol} at {lines[0][i]}')                
                    self.orders.append(str(ord_id(self.symbol, lines[0][i], self.tick)))

                for order in self.orders:
                     if self.api.get_order_by_client_order_id(order)._raw['filled_at'] != None:
                        try:
                            self.api.submit_order(self.symbol, str(self.sell_unit), 
                                    'sell', 'limit', 'day', str(lines[1][self.orders.index(order)]))
                            print(f'Submitted order to sell {self.symbol} at {lines[1][self.orders.index(order)]}')
                            self.orders.remove(order)
                        except:
                            pass 

                sleep(60)
                print(self)
                self.tick += 1
            else:
                sleep(60)
                self.tick += 1
                                        
                

if __name__ == '__main__':
    bot = grid_bot(
        api_key=API_KEY,
        api_secret=API_SECRET,
        symbol='QQQ',
        grid_interval=1.0,
        buy_lines=5,
        sell_lines=5,
        stop_loss=5,
        take_profit=5,
        live=False,
        buy_unit=5,
        sell_unit=1
    )
    print(bot.run())
