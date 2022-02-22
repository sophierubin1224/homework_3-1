import dash
import numpy as np

from fintech_ibkr import *
from ibapi.contract import Contract
from dash import dcc
from dash import html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import pickle
from datetime import date
from time import sleep
from os import listdir

# Make a Dash app!
app = dash.Dash(__name__)

# Define the layout.
app.layout = html.Div([

    # Section title
    html.H3("Section 1: Fetch & Display exchange rate historical data"),
    html.P(
        children=[
            "See the various currency pairs here: ",
                  html.A(
                      "currency pairs",
                      href='https://www.interactivebrokers.com/en/index.php?f=2222&exch=ibfxpro&showcategories=FX'
                  )
        ]
    ),

    # Currency pair text input, within its own div.
    html.Div(
        # The input object itself
        ["Input Currency: ", dcc.Input(
            id='currency-input', value='AUD.CAD', type='text'
        )],
        # Style it so that the submit button appears beside the input.
        style={'display': 'inline-block'}
    ),
    # Line break
    html.Br(),
    # Div to hold the initial instructions and the updated info once submit is pressed
    html.Div(id='currency-output', children='Enter a currency code'),
    # Numeric input for the trade amount
    html.Br(),
    html.Div(['End Date in YYYYMMDD HH:MM:SS Format:', dcc.Input(id='end-date', value='',type='text')]),
    html.Br(),
    html.Div(['Duration:', dcc.Input(id='duration-num', value='30', type='number')]),
    html.Div([dcc.RadioItems(['S', 'D', 'W', 'M', 'Y'], value='D', id='duration-unit', inline=True)]),
    html.Br(),
    html.Div(['Bar Size:', dcc.Dropdown(['1 secs','5 secs','10 secs','15 sec','30 secs',
                                         '1 min','2 mins','3 mins', '5 mins','10 mins','15 mins','20 mins','30 mins','1 hour','2 hours',
                                         '3 hours','4 hours','8 hours', '1 day', '1 week', '1 month'],value='1 day',id='bar-size')]),
    html.Br(),
    html.Div(['What to Show:', dcc.Dropdown(['MIDPOINT','TRADES', 'BID', 'ASK'], value='MIDPOINT', id='what-to-show')]),
    html.Br(),
    html.Div(['Retrieve Data Only From Regular Trading Hours?:', dcc.RadioItems(["Yes", "No"], value='Yes', id='use-RTH')]),
    html.Br(),
    # Submit button
    html.Button('Submit', id='submit-button', n_clicks=0),
    html.Br(),
    # Div to hold the candlestick graph
    html.Div([dcc.Graph(id='candlestick-graph')]),
    # Another line break
    html.Br(),
    # Section title
    html.H6("Make a Trade"),
    # Div to confirm what trade was made
    html.Div(id='trade-output'),
    # Radio items to select buy or sell
    dcc.RadioItems(
        id='buy-or-sell',
        options=[
            {'label': 'BUY', 'value': 'BUY'},
            {'label': 'SELL', 'value': 'SELL'}
        ],
        value='BUY'
    ),
    # Text input for the currency pair to be traded
    dcc.Input(id='trade-currency', value='AUDCAD', type='text'),
    # Numeric input for the trade amount
    dcc.Input(id='trade-amt', value='20000', type='number'),
    # Submit button for the trade
    html.Button('Trade', id='trade-button', n_clicks=0)

])

# Callback for what to do when submit-button is pressed
@app.callback(
    [ # there's more than one output here, so you have to use square brackets to pass it in as an array.
    Output(component_id='currency-output', component_property='children'),
    Output(component_id='candlestick-graph', component_property='figure')
    ],
    Input('submit-button', 'n_clicks'),# The callback function will fire when the submit button's n_clicks changes
    # The currency input's value is passed in as a "State" because if the user is typing and the value changes, then
    #   the callback function won't run. But the callback does run because the submit button was pressed, then the value
    #   of 'currency-input' at the time the button was pressed DOES get passed in.
    [State('currency-input', 'value'), State('end-date', 'value'), State('duration-num','value'), State('duration-unit','value'),
     State('bar-size', 'value'),State('what-to-show', 'value'), State('use-RTH', 'value')]
)
def update_candlestick_graph(n_clicks, currency, date, duration_num, duration_unit,bar_size,what_to_show,use_rth): # n_clicks doesn't get used, we only include it for the dependency.

    # First things first -- what currency pair history do you want to fetch?
    # Define it as a contract object!
    contract = Contract()
    contract.symbol  = currency.split('.')[0] # set this to the FIRST currency (before the ".")
    contract.secType  = 'CASH'
    contract.exchange = 'IDEALPRO' # 'IDEALPRO' is the currency exchange.
    contract.currency = currency.split('.')[1] # set this to the FIRST currency (before the ".")

    # Wait until ibkr_app runs the query and saves the historical prices csv
    #while not 'currency_pair_history.csv' in listdir():
        #sleep(1)

    # Make the historical data request.
    # Where indicated below, you need to make a REACTIVE INPUT for each one of
    #   the required inputs for req_historical_data().
    # This resource should help a lot: https://dash.plotly.com/dash-core-components

    # Some default values are provided below to help with your testing.
    # Don't forget -- you'll need to update the signature in this callback
    #   function to include your new vars!
    if use_rth =='Yes':
        rth = True
    else:
        rth= False
    cph = fetch_historical_data(
        contract = contract,
        endDateTime= date,           # <-- make a reactive input
        durationStr= duration_num + ' ' + duration_unit,       # <-- make a reactive input
        barSizeSetting=bar_size,  # <-- make a reactive input
        whatToShow=what_to_show,    # <-- make a reactive input
        useRTH=rth,              # <-- make a reactive input
    )

    # Make the candlestick figure
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=cph['date'],
                open=cph['open'],
                high=cph['high'],
                low=cph['low'],
                close=cph['close']
            )
        ]
    )

    # Give the candlestick figure a title
    fig.update_layout(title=('Exchange Rate: ' + currency))

    # Return your updated text to currency-output, and the figure to candlestick-graph outputs
    return ('Submitted query for ' + currency), fig

# Callback for what to do when trade-button is pressed
@app.callback(
    # We're going to output the result to trade-output
    Output(component_id='trade-output', component_property='children'),
    # We only want to run this callback function when the trade-button is pressed
    Input('trade-button', 'n_clicks'),
    # We DON'T want to run this function whenever buy-or-sell, trade-currency, or trade-amt is updated, so we pass those
    #   in as States, not Inputs:
    [State('buy-or-sell', 'value'), State('trade-currency', 'value'), State('trade-amt', 'value')],
    # We DON'T want to start executing trades just because n_clicks was initialized to 0!!!
    prevent_initial_call=True
)
def trade(n_clicks, action, trade_currency, trade_amt): # Still don't use n_clicks, but we need the dependency

    # Make the message that we want to send back to trade-output
    msg = action + ' ' + trade_amt + ' ' + trade_currency

    # Make our trade_order object -- a DICTIONARY.
    trade_order = {
        "action": action,
        "trade_currency": trade_currency,
        "trade_amt": trade_amt
    }

    # Dump trade_order as a pickle object to a file connection opened with write-in-binary ("wb") permission:
    pickle.dump(trade_order, open('trade_order.p', 'wb'))

    # Return the message, which goes to the trade-output div's "children" attribute.
    return msg

# Run it!
if __name__ == '__main__':
    app.run_server(debug=True)
