class TenPercentBot:
    whitelist = []
    defaultlist = ['AAPL', 'GOOG','AMZN','BA','AA','JPM','JNJ','WMT','V','TSM','TSMC','MA','NVDA','TSLA']

    def __init__(self, api_key, api_secret, base_url) -> None:
        '''Configure API with inputs given at start of object creation'''
        self.api = tradeapi.REST(api_key, api_secret, base_url)
    
    def auto_stocks_whitelist(self) -> None:
        '''uses csv file of NASDAQ to get tickers 
        of stocks to automatically whitelist'''
        nasdaq = pd.read_csv('nasdaq_screener_1627684683783.csv')
        nasdaqMC, nasdaqTICK = round(nasdaq.iloc[:,5], 2), nasdaq.iloc[:,0]
        for stockMC in range(len(nasdaqMC)):
            if nasdaqMC[stockMC] > 100000000000:
                self.whitelist.append(nasdaqTICK[stockMC])
        print(self.whitelist)

    def get_stocks_whitelist(self) -> list:
        '''If 'USE DEFAULT' inputed then default to 
        well known default list of securities, else
        use only stocks inputed by user.'''
        #instructions
        print('''INPUT VALID TICKERS IN ALL-CAPS, INPUT 'USE DEFAULT' TO USE
        DEFAULT WHITELIST FOR TRADING. ALGORITHM WILL ONLY ACCOUNT 
        FOR STOCKS IN WHITELIST. INPUT 'STOP INPUT' TO STOP.''')
        while True:
            inp = input('Enter Ticker: ')
            if inp == 'USE DEFAULT':
                self.whitelist = [item for item in self.defaultlist]
            elif inp == 'STOP INPUT':
                break
            elif inp == 'GO BACK':
                self.whitelist = self.whitelist[:1]
                print('value deleted successfully')
            else: 
                self.whitelist.append(inp)
        return self.whitelist
    
    def collect_data(self) -> list:
        data = []
        for stock in self.whitelist:
            i = self.api.get_barset(stock, '1D')
            sleep(0.01)
            i = i.df
            data.append(i)
            print(i)
        return data
    
    def identify_buys_in_data_by_ma(self, data: list) -> tuple:
        '''returns a tuple of lists of tickers
        that are buys, sells, or holds respectively
        based on comparison between 10-day and 100-day
        averages'''
        buys, sells, holds = [], [], []

        for stock in range(len(data)):
            #compute 100-day moving average
            avg100List = round(data[stock].mean(), 2)
            MA100 = round((1/2)*(avg100List[1] + avg100List[2]), 2)
            
            #compute 10-day moving average
            df10 = data[stock].iloc[90:]
            avg10List = round(df10.mean(), 2)
            MA10 = round((1/2)*(avg10List[1] + avg10List[2]), 2)
            
            #identify as buy or sell by if up or down
            #by 10% and append ticker to buy or sell
            if .90*MA10 > MA100:
                sells.append(self.whitelist[stock])
            elif .90*MA100 > MA10:
                buys.append(self.whitelist[stock])
            else:
                holds.append(self.whitelist[stock])

        return (buys, sells, holds)
    
    def buy(self, buys: list) -> None:
        '''Takes output from identify buys by ma
        and trades the stocks'''
        for stock in buys:
            try:
                self.api.submit_order(symbol = stock, 
                                    qty = quantity_constant, 
                                    side = 'buy',
                                    type = 'market',
                                    time_in_force= 'gtc')
            except exception as e:
                print(e)

    def sell(self, sells: list) -> None:
        '''checks to see if any of the stocks identified as 
        sells are in the portfolio and sells them if they are
        for more than they were bought for'''
        for stock in sells:
            try:
                self.api.submit_order(symbol = stock, 
                                    qty = quantity_constant,
                                    side = 'sell',
                                    type = 'market',
                                    time_in_force= 'gtc')
            except exception as e:
                print(e)

class FivePercentBot(TenPercentBot):
    '''Inherits from tenpercent bot and
    changes the threshold for identifying a 
    stock as a buy or sell to five percent(from ten)'''
    def identify_buys_in_data_by_ma(self, data: list) -> tuple:
        '''returns a tuple of lists of tickers
        that are buys, sells, or holds respectively
        based on comparison between 10-day and 100-day
        averages'''
        buys, sells, holds = [], [], []

        for stock in range(len(data)):
            #compute 100-day moving average
            avg100List = round(data[stock].mean(), 2)
            MA100 = round((1/2)*(avg100List[1] + avg100List[2]), 2)
            
            #compute 10-day moving average
            df10 = data[stock].iloc[90:]
            avg10List = round(df10.mean(), 2)
            MA10 = round((1/2)*(avg10List[1] + avg10List[2]), 2)
            
            #identify as buy or sell by if up or down
            #by 10% and append ticker to buy or sell
            if .95*MA10 > MA100:
                sells.append(self.whitelist[stock])
            elif .95*MA100 > MA10:
                buys.append(self.whitelist[stock])
            else:
                holds.append(self.whitelist[stock])

        return (buys, sells, holds)

class OnePercentBot(TenPercentBot):
    '''Welp, this shit is gonna be so fucking
    volatile, it will be a miracle if its profitable.
    pattern day trader? hell fucking yeah apparently...'''
    def identify_buys_in_data_by_ma(self, data: list) -> tuple:
        '''returns a tuple of lists of tickers
        that are buys, sells, or holds respectively
        based on comparison between 10-day and 100-day
        averages'''
        buys, sells, holds = [], [], []

        for stock in range(len(data)):
        #compute 100-day moving average
            avg100List = round(data[stock].mean(), 2)
            MA100 = round((1/2)*(avg100List[1] + avg100List[2]), 2)

        #compute 10-day moving average
            df10 = data[stock].iloc[90:]
            avg10List = round(df10.mean(), 2)
            MA10 = round((1/2)*(avg10List[1] + avg10List[2]), 2)

        #identify as buy or sell by if up or down
        #by 10% and append ticker to buy or sell
            if .99*MA10 > MA100:
                sells.append(self.whitelist[stock])
            elif .99*MA100 > MA10:
                buys.append(self.whitelist[stock])
            else:
                holds.append(self.whitelist[stock])

        return (buys, sells, holds)



if __name__ == '__main__':
    api_key = 'PKQW2NLKSTEM08FTL56T'
    api_secret = '03li9945K52bKBZiAZjx7t0DbAloEfp8biFX6iDX'
    base_url = 'https://paper-api.alpaca.makerts'
        
    Main = TenPercentBot(api_key, api_secret, base_url)

    
            
