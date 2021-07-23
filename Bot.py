import alpaca_trade_api as tradeapi
import datetime as dt
import json

class Algo:
    def __init__(self):
        #API information
        self.api_key = 'PKQW2NLKSTEM08FTL56T'
        self.api_secret = '03li9945K52bKBZiAZjx7t0DbAloEfp8biFX6iDX'
        self.base_url = 'https://paper-api.alpaca.makerts'
        self.api = tradeapi.REST(self.api_key, self.api_secret, self.base_url)
        
        #Stonk information
        self.stonkList = []
        self.listOfStockData = []

    def check_if_market_open(self):
        '''Checks if the market is open'''
        clock = self.api.get_clock()
        if clock.is_open():
            return True
        else: 
            return False
    
    #all stock list methods, controls the stocks that can be
    #interacted with, including getting data, buying, selling, etc.
    def add_stock_list(self):
        print("Type 'STOP' to stop, enter only valid Symbols: " )
        while True:
            stonk = input('Enter Symbol:')
            if stonk == 'STOP': 
                break
            elif stonk in self.stonkList:
                print('Stock already in list')
            else:
                self.stonkList.append(stonk)

    def delete_stock_list(self):
        print("Type 'STOP' to stop, enter only valid Symbols" )
        while True:
            stonk = input('Enter Symbol of Stock to Delete: ')
            try:
                self.stonkList.remove(stonk)
            except ValueError as e:
                print('Stock not in list')
    
    def auto_stock_list(self, stocks):
        for s in stocks: self.stonkList.append(s)
    
    def print_stock_list(self):
        print(self.stonkList)

    def collect_assets(self):
        pos = []
        for stonk in self.stonkList:
            pos.append(self.api.get_asset(stonk))
        return pos

#Gets data for each stock in stock list
    def collect_data(self, start, end):
        #startTime = str(dt.datetime.now() - dt.timedelta(days=365))
        try: 
            startDate = start
            endDate = end
            for stock in self.stonkList:
                response = self.api.get_trades(stock, startDate, endDate, limit=1000)
                
                #transcribe API response 
                fwrite = open(f'responses/{stock}.txt', 'w')
                fwrite.write(str(response))
                fwrite.close()
                
                data = {}
                fread = open(f'responses/{stock}.txt', 'r') 
                
                #take trade data and turn it into a dictionary
                    
                pcount, tcount = 0, 0
                for line in fread:
                    if "p" in line: 
                        data.update({'p'+ str(pcount):line[9:-2]})
                        pcount += 1
                    
                    if "t" in line:
                        data.update({'t'+ str(tcount):line[9:-3]})
                        tcount += 1
                fread.close()
                self.listOfStockData.append(data)
            
        except Exception as e:
            print(e)
            e, dateTimeOfError = str(e), str(dt.datetime.now())
            f = open('error_log.txt', 'w')
            errorEntry = e + 'on ' + dateTimeOfError +  '\n'
            f.write(errorEntry)
            f.close()
    
    def run(self, mode):
        '''mode 1 is conservative, mode 2 is risky, and mode 3 is 
        r/wallstreetbets levels of stupid'''
        
        #Guarantees the market is open during runtime
        try: 
            assert self.check_if_market_open() == True
        except AssertionError as e:
            print(e)
            e, dateTimeOfError = str(e), str(dt.datetime.now())
            f = open('error_log.txt', 'w')
            errorEntry ='\n'+ e + 'on ' + dateTimeOfError + '\n' 
            f.write(errorEntry)
            raise RuntimeError

        #risk tolerance modes
        if mode == 1:
            while True:
                #collects data for past year
                self.collect_data('2020-07-22', '2021-07-22')
                for stock in self.listOfStockData: 
                    # for each stock in watchlist:
                    # filter through dictionary of alternating entries, 
                    # first representing the price then representing the date
                    pd_values = stock.values()
                    for v in pd_values:
                        if v.index() % 2 == 0:
                            stock.append([v])
                        else:
                            stock[v.index() - 1].append(v)
                            



                    #CONSERVATIVE STRATEGY HERE
        
        if mode == 2:
            while True:
                self.collect_data()
                for stock in self.listOfStockData:
                    #MODERATE STRATEGY HERE
        
        if mode == 3:
            while True:
                self.collect_data()
                for stock in self.listOfStockData:
                    #BALLS TO THE WALL "STRATEGY" HERE

    
if __name__ == '__main__':
    boob = Algo()
    boob.add_stock_list()
    boob.collect_data()
    print(boob.listOfStockData)
    
    