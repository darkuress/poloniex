import Core
reload(Core)
import json
import os

class poloniexRun(Core.Poloniex):
    def __init__(self, currency, currency_pair):
        """
        initializing variables
        """
               
        #- initializing Func
        Core.Poloniex.__init__(self)    
        #self.data_path = os.path.join("C:\\", "Users", "ARL_DARL", "Desktop", "poloniex.json")
        #self.data_path = os.path.join("F:\\", "poloniex_data", "poloniex.json")
        self.data_path = os.path.join("/home", "pi", "poloniex_data", "poloniex.json")
        
        self.currency = currency
        self.currency_pair = currency_pair
        self.data = {}
        
        self.updateData()
        
    def currentBalances(self, currency):
        """
        """
        return self.returnBalances()[currency]
    
    def currentPrice(self, currency_pair):
        """
        """
        return self.returnTicker()[currency_pair]['last']
    
    def writeJson(self, data):
        """
        """
        try:
            with open(self.data_path, 'w+') as outfile:
                json.dump(data, outfile)
            outfile.close()  

            return True
            
        except:
            # maybe send email here
            print 'failed'
            return False
    
    def readJson(self):
        """
        """
        jsonData = open(self.data_path)
        read_data = json.load(jsonData)        
        
        return read_data

    def updateData(self, hold = ''):
        """
        """
        self.data['currency']             = self.currency
        self.data['currency_pair']        = self.currency_pair
        self.data['current_price']        = self.currentPrice(self.currency_pair)
        self.data['current_btc_balance']  = self.returnBalances()['BTC']
        self.data['current_coin_balance'] = self.returnBalances()[self.currency]
        self.data['hold'] = hold
        
    def run(self):
        """
        """
        try:
            read_data = self.readJson()
        except:
            self.writeJson(self.data)
            read_data = self.readJson()
        
        ratio = float(self.data['current_price'])/float(read_data['current_price'])
        print ratio
        
        if ratio < 0.98 and read_data['hold'] == 'False':
            #-  buy
            print 'buy'
            rate = float(self.data['current_price']) + 0.0001
            amount = float(self.data['current_btc_balance'])/rate
            self.buy(self.currency_pair, rate, amount)
            
            #- update json file
            self.updateData(hold = 'True')
            self.writeJson(self.data)
        elif ratio > 1.02 and read_data['hold'] == 'True':
            #- sell
            print 'sell'
            rate = float(self.data['current_price']) - 0.0001
            amount = float(self.data['current_coin_balance'])
            self.sell(self.currency_pair, rate, amount)
            
            #- update json file
            self.updateData(hold = 'False')
            self.writeJson(self.data)
        else:
            print 'pass'
            #self.updateData(hold = 'False')
            #self.writeJson(self.data)
        