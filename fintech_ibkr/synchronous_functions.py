
import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import threading
import time

# If you want different default values, configure it here.
default_hostname = '127.0.0.1'
default_port = 7497
default_client_id = 10645 # can set and use your Master Client ID

# This is the main app that we'll be using for sync and async functions.
class ibkr_app(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.error_messages = pd.DataFrame(columns=[
            'reqId', 'errorCode', 'errorString'
        ])
        self.next_valid_id = None
        ########################################################################
        # Here, you'll need to change Line 30 to initialize
        # self.historical_data as a dataframe having the column names you
        # want to use. Clearly, you'll want to make sure your colnames match
        # with what you tell the candlestick figure to expect when you create
        # it in your app!
        # I've already done the same general process you need to go through
        # in the self.error_messages instance variable, so you can use that as
        # a guide.
        self.historical_data = pd.DataFrame([], columns=['date','high','low','close', 'volume','average', 'barCount'])
        self.historical_data_end = ''
        self.contract_details = ''
        self.contract_details_end = ''

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)
        self.error_messages = pd.concat(
            [self.error_messages, pd.DataFrame({
                "reqId": [reqId],
                "errorCode": [errorCode],
                "errorString": [errorString]
            })])

    def managedAccounts(self, accountsList):
        self.managed_accounts = [i for i in accountsList.split(",") if i]

    def nextValidId(self, orderId: int):
        self.next_valid_id = orderId

    def historicalData(self, reqId, bar):
        # YOUR CODE GOES HERE: Turn "bar" into a pandas dataframe, formatted
        #   so that it's accepted by the plotly candlestick function.
        # Take a look at candlestick_plot.ipynb for some help!
        # assign the dataframe to self.historical_data.
        print(reqId, bar)
        self.historical_data = pd.concat([self.historical_data, pd.DataFrame({'date': [bar.date], 'open':[bar.open],
                                                                              'high':[bar.high], 'low':[bar.low],
                                                                              'close':[bar.close], 'volume':[bar.volume],
                                                                              'average':[bar.average], 'barCount': [bar.barCount]})])

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        # super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        self.historical_data_end = reqId

def fetch_managed_accounts(hostname=default_hostname, port=default_port,
                           client_id=default_client_id):
    app = ibkr_app()
    app.connect(hostname, port, client_id)
    while not app.isConnected():
        time.sleep(0.01)
    def run_loop():
        app.run()
    api_thread = threading.Thread(target=run_loop, daemon=True)
    api_thread.start()
    while isinstance(app.next_valid_id, type(None)):
        time.sleep(0.01)
    app.disconnect()
    return app.managed_accounts

def fetch_historical_data(contract, endDateTime='', durationStr='30 D',
                          barSizeSetting='1 hour', whatToShow='MIDPOINT',
                          useRTH=True, hostname=default_hostname,
                          port=default_port, client_id=default_client_id):
    app = ibkr_app()
    app.connect(hostname, port, client_id)
    while not app.isConnected():
        time.sleep(0.01)
    def run_loop():
        app.run()
    api_thread = threading.Thread(target=run_loop, daemon=True)
    api_thread.start()
    while isinstance(app.next_valid_id, type(None)):
        time.sleep(0.01)
    tickerId = app.next_valid_id
    app.reqHistoricalData(
        tickerId, contract, endDateTime, durationStr, barSizeSetting,
        whatToShow, useRTH, formatDate=1, keepUpToDate=False, chartOptions=[])
    while app.historical_data_end != tickerId:
        time.sleep(0.01)
    app.disconnect()
    return app.historical_data
