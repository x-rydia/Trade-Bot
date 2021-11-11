from os import error
from typing import Dict
from numpy.lib.shape_base import hsplit
from pandas import DataFrame, read_csv
from robin_stocks.robinhood import crypto
from robin_stocks.robinhood.orders import( 
    order_buy_crypto_by_price, 
    order_buy_crypto_limit_by_price,
    order_buy_fractional_by_price, 
    order_sell_crypto_by_price, 
    order_sell_fractional_by_price)

import robin_stocks.robinhood as r
from ta.utils import dropna
from ta.wrapper import add_momentum_ta, add_others_ta, add_trend_ta, add_volatility_ta
from ta.volatility import keltner_channel_hband_indicator, keltner_channel_lband_indicator
from ta.momentum import ppo_signal
from random import choice

def indicator_method(func):
    def wrapper():
        pass
    return wrapper

class bot:
    def __init__(self, username: str, password: str, 
            min_val: float=5.0, debug: bool=False, crypto: bool=False,
            qauntity_constant: float=20, min_mark_cap: float=10000000000) -> None:
        self.username = username
        self.password = password
        self.whitelist = []
        self.rhlogin = None
        self.quantity_constant = qauntity_constant
        self.trade_hist_dict = {}
        self.crypto = crypto
        self.min_mark_cap = min_mark_cap
    
    def _list_indicators(self, data: DataFrame) -> None:
        '''
        Utility method for TA lib, ignore
        '''
        print(list(data))
    
    def _count_h_scores(self, vals: list) -> dict:
        counts = {
            'zeroes': 0,
            'ones': 0,
            'twos': 0,
            'threes': 0,
            'fours': 0,
            'neg_ones': 0,
            'neg_twos': 0,
            'neg_threes': 0,
            'neg_fours': 0
        }
        for entry in vals:
            if entry == 1:
                counts['ones'] += 1
            elif entry == 2:
                counts['twos'] += 1
            elif entry == 3:
                counts['threes'] += 1
            elif entry == 4:
                counts['fours'] += 1
            elif entry == -1:
                counts['neg_ones'] += 1
            elif entry == -2:
                counts['neg_twos'] += 1
            elif entry == -3:
                counts['neg_threes'] += 1
            elif entry == -4:
                counts['neg_fours'] += 1
            else:
                counts['zeroes'] += 1 
                
        return counts

        

    def login(self) -> None:
        '''
        Handles login and 2fa on the RH side of things,
        must be called before any interaction can occur
        '''
        try:
            self.rhlogin = r.login(username=self.username, password=self.password)
        except error as e:
            print(e)
            print(f'''Please Re-Run the bot, making sure that the provided information is correct:
                        username: {self.username} password: {self.password}''')
        
    def market_open(self) -> bool:
        if r.get_market_today_hours()['is_open']:
            return True
        else:
            return False

    def build_whitelist(self) -> None:
        if not self.crypto:
            stocks = read_csv(open('nasdaq.csv', 'r'))
            symbols = list(stocks['Symbol'])
            market_caps = list(stocks['Market Cap'])

            for stock in market_caps:
                if stock != 'nan' and float(stock) > self.min_mark_cap:
                    self.whitelist.append(symbols[market_caps.index(stock)])
                    self.trade_hist_dict.update({symbols[market_caps.index(stock)]: 0})
            for stock in self.whitelist:
                print(f'Considering Trading: {stock}')
        else:
            self.whitelist = ['BTC', 'ETH', 'DOGE', 'LTC', 'BSV', 'BCH', 'ETC']    
            
    def get_hist_data(self, tickers: list) -> list:
        '''
        Gather data on a set of tickers from RH and return a 2D array whereby each 
        stock's historicals are represented by a df
        '''
        print('Getting Historical Data . . .')
        ret_data = []
        for t in tickers:
            print(f'processing: {t}')
            data = r.get_stock_historicals(t)
            for dicti in data:
                if type(dicti) != dict:
                    continue
                dicti['open_price'] = float(dicti['open_price'])
                dicti['close_price'] = float(dicti['close_price'])
                dicti['high_price'] = float(dicti['high_price'])
                dicti['low_price'] = float(dicti['low_price'])
                dicti['volume'] = float(dicti['volume'])

            ret_data.append([dict for dict in data if dict['symbol'] == t])

        new_data = []
        for stock in ret_data:
            print('Analyzing data...')
            ta_df = dropna(DataFrame(stock))
            ta_df['open_price'] = ta_df['open_price'].astype(float)
            ta_df['close_price'] = ta_df['close_price'].astype(float)
            ta_df['high_price'] = ta_df['high_price'].astype(float)
            ta_df['low_price'] = ta_df['low_price'].astype(float)
            ta_df['volume'] = ta_df['volume'].astype(float)
            ta_df = add_trend_ta(
                 ta_df, 
                 close='close_price', 
                 high='high_price', 
                 low='low_price',  
                 fillna=True
                 )
            ta_df = add_momentum_ta(
                 ta_df, 
                 close='close_price', 
                 high='high_price', 
                 low='low_price', 
                 volume='volume', 
                 fillna=True
            )
            ta_df = add_volatility_ta(
                 ta_df, 
                 close='close_price', 
                 high='high_price', 
                 low='low_price', 
                 fillna=True
            )
            ta_df_kelt_low = keltner_channel_lband_indicator( 
                 close=ta_df['close_price'], 
                 high=ta_df['high_price'], 
                 low=ta_df['low_price'], 
                 fillna=True
            )
            ta_df_kelt_high = keltner_channel_hband_indicator(
                 close=ta_df['close_price'], 
                 high=ta_df['high_price'], 
                 low=ta_df['low_price'], 
                 fillna=True
            )
            ta_df['keltner_channel_hband_indicator'] = ta_df_kelt_high
            ta_df['keltner_channel_lband_idnicator'] = ta_df_kelt_low
            ta_df_ppo = ppo_signal(
                close = ta_df['close_price'],
                fillna=True
            )
            ta_df['ppo'] = ta_df_ppo
        

            new_data.append(ta_df)
        return new_data
    
    def get_cur_price(self, ticker: str) -> float:
        quotes = r.get_quotes(ticker)
        return float(quotes[0]['last_trade_price'])


    def is_buy_rsi(self, data: DataFrame) -> bool:
        '''
        determines if the stock is a buy or sell given the RSI
        '''
        if data['momentum_rsi'].iloc[-1] <= 30:
            return True
        else: 
            return False


    def is_sell_rsi(self, data: DataFrame) -> bool:
        '''
        determines if the stock is a buy or sell given the RSI
        '''
        if data['momentum_rsi'].iloc[-1] >= 70:
            return True
        else: 
            return False
    

    def is_buy_ema(self, data: DataFrame, current_price: float) -> bool:
        if data['trend_ema_fast'].iloc[-1] < 0.95 * current_price:
            return True
        else: 
            return False
    

    def is_sell_ema(self, data: DataFrame, current_price: float) -> bool:
        if data['trend_ema_fast'].iloc[-1] > 1.05 * current_price:
            return True
        else: 
            return False


    def is_buy_psar(self, data: DataFrame) -> bool:
        if data['trend_psar_down_indicator'].iloc[-1]:
            return True
        else:
            return False

    def is_sell_psar(self, data: DataFrame) -> bool:
        if data['trend_psar_up_indicator'].iloc[-1]:
            return True
        else:
            return False
    
    def is_buy_ketlner(self, data: DataFrame) -> bool:
        if int(data['keltner_channel_lband_idnicator'].iloc[-1]) == 1:
            return True
        else:
            return False

    def is_sell_ketlner(self, data: DataFrame) -> bool:
        if int(data['keltner_channel_hband_indicator'].iloc[-1]) != 1:
            return True
        else:
            return False
    
    def is_buy_ppo(self, data: DataFrame) -> bool:
        if int(data['ppo'].iloc[-1]) > 0:
            return True
        else:
            return False

    def is_sell_ppo(self, data: DataFrame) -> bool:
        if int(data['ppo'].iloc[-1]) < 0:
            return True
        else:
            return False
    def is_buy_rsi(self, data: DataFrame) -> bool:
        if data['momentum_rsi'].iloc[-1] <= 30:
            return True
        else: 
            return False

    def is_sell_rsi(self, data: DataFrame) -> bool:
        if data['momentum_rsi'].iloc[-1] >= 70:
            return True
        else:
            return False

    def run(self):
        self.build_whitelist()
        for i in range(25):
            stock = choice(self.whitelist)
            try: 
                r.order_buy_fractional_by_price(
                    symbol=stock,
                    amountInDollars=self.quantity_constant
                )
                print(f'Bought {stock}')
            except:
                pass
        
    def _test_run(self) -> bool:
        self.build_whitelist()
        h_scores = []
        whitelist_historicals = self.get_hist_data(self.whitelist)
        print(whitelist_historicals)
        print(self.whitelist)


        for stock in range(len(whitelist_historicals)):
            ticker = self.whitelist[stock]
            H_score = 0
            if self.is_buy_rsi(whitelist_historicals[stock]):
                H_score += 1
            if self.is_buy_ema(whitelist_historicals[stock], self.get_cur_price(ticker)):
                H_score += 1
            if self.is_buy_psar(whitelist_historicals[stock]):
                H_score += 1
            if self.is_sell_ema(whitelist_historicals[stock], self.get_cur_price(ticker)):
                H_score += -1
            if self.is_sell_psar(whitelist_historicals[stock]):
                H_score += -1
            if self.is_sell_rsi(whitelist_historicals[stock]):
                H_score += -1
            if self.is_sell_ketlner(whitelist_historicals[stock]):
                H_score += -1
            if self.is_buy_ketlner(whitelist_historicals[stock]):
                H_score += 1
            if self.is_sell_ppo(whitelist_historicals[stock]):
                H_score += 1
            if self.is_buy_ppo(whitelist_historicals[stock]):
                H_score += 1
            h_scores.append(H_score)
            if H_score > 0 and self.trade_hist_dict[ticker] < 4:
                try:
                    order_buy_fractional_by_price(
                        symbol=ticker,
                        amountInDollars=H_score * self.quantity_constant
                    )
                except error as e:
                    print(e)
                print(f'Bought ${H_score * self.quantity_constant} of {ticker} with score {H_score}')
                self.trade_hist_dict[ticker] += 1
            if H_score < 0 and self.trade_hist_dict[ticker] < 4:
                order_sell_fractional_by_price(
                    symbol=ticker,
                    amountInDollars= (-1 * H_score) * self.quantity_constant
                )
                self.trade_hist_dict[ticker] += 1
                print(f'Sold ${-1 * H_score * self.quantity_constant} of {ticker} with score {-1 * H_score}')
            

        print(self.trade_hist_dict)
        print(h_scores)


            

    def run_crypto(self):
        self.build_whitelist()
        h_scores = []
        whitelist_historicals = self.get_hist_data(self.whitelist)
        print(whitelist_historicals)
        print(self.whitelist)


        for stock in range(len(whitelist_historicals)):
            ticker = self.whitelist[stock]
            H_score = 0
            if self.is_buy_rsi(whitelist_historicals[stock]):
                H_score += 1
            if self.is_buy_ema(whitelist_historicals[stock], self.get_cur_price(ticker)):
                H_score += 1
            if self.is_buy_psar(whitelist_historicals[stock]):
                H_score += 1
            if self.is_sell_ema(whitelist_historicals[stock], self.get_cur_price(ticker)):
                H_score += -1
            if self.is_sell_psar(whitelist_historicals[stock]):
                H_score += -1
            if self.is_sell_rsi(whitelist_historicals[stock]):
                H_score += -1
            if self.is_sell_ketlner(whitelist_historicals[stock]):
                H_score += -1
            if self.is_buy_ketlner(whitelist_historicals[stock]):
                H_score += 1
            if self.is_sell_ppo(whitelist_historicals[stock]):
                H_score += 1
            if self.is_buy_ppo(whitelist_historicals[stock]):
                H_score += 1
            h_scores.append(H_score)
            if H_score > 0 and self.trade_hist_dict[ticker] < 4:
                try:
                    order_buy_crypto_by_price(
                        symbol=ticker,
                        amountInDollars=H_score * self.quantity_constant
                    )
                except error as e:
                    print(e)
                print(f'Bought ${H_score * self.quantity_constant} of {ticker} with score {H_score}')
                self.trade_hist_dict[ticker] += 1
            if H_score < 0 and self.trade_hist_dict[ticker] < 4:
                order_sell_crypto_by_price(
                    symbol=ticker,
                    amountInDollars= (-1 * H_score) * self.quantity_constant
                )
                self.trade_hist_dict[ticker] += 1
                print(f'Sold ${-1 * H_score * self.quantity_constant} of {ticker} with score {-1 * H_score}')
            
        if H_score >= 3:
            try:
                r.order_buy_crypto_by_price(
                    symbol=ticker,
                    amountInDollars= self.quantity_constant
                )
                self.trade_hist_dict[ticker] +=1
            except:
                pass
        elif H_score == -4:
            try:
                r.order_sell_crypto_by_price(
                    symbol=ticker,
                    amountInDollars=self.quantity_constant * .25
                )
                self.trade_hist_dict[ticker] +=1
            except:
                pass
    def _test_func(self):
        # order_sell_crypto_by_price(
        #     symbol='ETH',
        #     amountInDollars=1000
        # )
        # print('Sold ETH')
        # order_buy_crypto_limit_by_price(
        #     symbol='ETH',
        #     amountInDollars=1000,
        #     limitPrice=4293.00
        # )
        # print('limit bought eth')
        buys = ['BTC', 'ETH', 'LTC', 'BHC']
        for stock in buys:
            order_buy_crypto_by_price(
                symbol=stock,
                amountInDollars= 250
            )
            print(f'bought {stock}')

