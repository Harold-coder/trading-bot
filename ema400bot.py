''' 
Buys when Price closes Above/Under 400 EMA
'''
from keep_alive import keep_alive
import websocket, json, numpy
import pandas_ta as ta
import time
import datetime
import pandas as pd
from binance.client import Client
from binance.enums import *
from futurespy import Client
from binance.client import Client as ClientReal
import config

SOCKET = "wss://fstream.binance.com/ws/ethusdt_perpetual@continuousKline_1m"

client = Client(config.KEY, config.SECRET)
clientreal = ClientReal(config.KEY, config.SECRET)



TRADE_SYMBOL = 'ETHUSDT'
LEVERAGE = 8
status = 0
RAINBOW_LONG = False
RAINBOW_SHORT = False
closes = []                   #array containing the last closes

#Retrieving data from previous candles before we start
candles = clientreal.futures_klines(symbol=TRADE_SYMBOL, 
                      interval=clientreal.KLINE_INTERVAL_15MINUTE, 
                      limit=1500)

#Adding this data into our array
df = pd.DataFrame(candles).iloc[:, : 6]

df = df.rename(columns={0 :'time', 1 : 'open', 2 : 'high', 3 : 'low', 4: 'close', 5: 'volume'})

df = df.apply(pd.to_numeric)

bugs = 0

print ("Let's start Trading!")

keep_alive()

while True:

  #Function to Enter/Close a Position
  def order(side, quantity, symbol):
    try:
      print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ACTION!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      order = client.new_order( side = side, quantity = quantity, symbol = symbol, orderType = 'MARKET')
      print("Leverage: ", LEVERAGE)
    except Exception as e:
      return False
    return True
  

  #Function to tell us the connection to Binance was successful
  def on_open(ws):
    print ("opened connection")

  #Function to tell us we closed the connection to Binance
  def on_close(ws):
    print ("closed connection")

  #Function called every 2 second when we receive a message from Binance
  def on_message(ws, message):

    global status
    global LEVERAGE
    global TRADE_QUANTITY
    global RAINBOW_LONG
    global RAINBOW_SHORT
    global TRADE_SYMBOL

    global bugs

    #Handling message info using Json to simplify it
    json_message = json.loads(message)
    candle = json_message['k']
    is_candle_closed = candle['x']                #True or False
    close = candle['c']                     
    close = float(close)                    #We have to make it a float

    amt_dollar = 75

    #Every time a candle closes
    if is_candle_closed:
      print('                                                                             TIME', datetime.datetime.now().strftime("%H:%M:%S"))
      print("candle closed at {}".format(close))

      bars = clientreal.futures_klines(symbol=TRADE_SYMBOL, 
                      interval=clientreal.KLINE_INTERVAL_15MINUTE, 
                      limit=1500)


      df = pd.DataFrame(bars).iloc[:, : 6]

      df = df.rename(columns={0 :'time', 1 : 'open', 2 : 'high', 3 : 'low', 4: 'close', 5: 'volume'})

      df = df.apply(pd.to_numeric)

      ema = df.ta.ema(length=400)

      print("before UPDATE")

      position = clientreal.futures_position_information()
      
      for future in position:
        amount = future["positionAmt"]
        if amount != "0" and float(future['unRealizedProfit']) != 0.00000000:
          if status == 0:
            bugs +=1
            if float(future["entryPrice"]) > float(future["liquidationPrice"]):
              print("WE ARE LONGING ALREADY")
              TRADE_QUANTITY = float(amount)
              status = 1

            elif float(future["entryPrice"]) < float(future["liquidationPrice"]):
              print("WE ARE SHORTING ALREADY")
              TRADE_QUANTITY = float(amount)
              status = 2
          
      print("after UPDATE")
      print("Bugs:", bugs)
      print(status)

      #Getting Stop loss based on the width of the BB
      if status == 0:
        LEVERAGE = 8
        print("We are here")
        #Updating Leverage
        print("Here")
        TRADE_QUANTITY = round(float((amt_dollar * LEVERAGE) / df['close'][len(df.index) - 1]), 3)
        
      last_ema = ema[len(ema) - 1]

      print(last_ema)

      if close > last_ema:

        RAINBOW_LONG = True
        RAINBOW_SHORT = False
        if status == 0:
          print("\nLONG, STATUS 0")

          order('BUY', TRADE_QUANTITY, TRADE_SYMBOL)
          status = 1

        elif status == 1:
          print("Still LONGING")

        elif status == 2:
          print("\nLONG, STATUS 2")
          order('BUY', TRADE_QUANTITY, TRADE_SYMBOL)

          LEVERAGE = 8
          #Updating Leverage
          TRADE_QUANTITY = round(float((amt_dollar * LEVERAGE) / df['close'][len(df.index) - 1]), 3)

          order('BUY', TRADE_QUANTITY, TRADE_SYMBOL)
          status = 1

      elif close < last_ema:

        RAINBOW_SHORT = True
        RAINBOW_LONG = False
        if status == 0:
          print("\nSHORT, STATUS 0")

          LEVERAGE = 8
          #Updating Leverage
          TRADE_QUANTITY = round(float((amt_dollar * LEVERAGE) / df['close'][len(df.index) - 1]), 3)

          order('SELL', TRADE_QUANTITY, TRADE_SYMBOL)
          status = 2

        elif status == 1:
          print ("\nSHORT, STATUS 1")
          order('SELL', TRADE_QUANTITY, TRADE_SYMBOL)

          LEVERAGE = 8
          #Updating Leverage
          TRADE_QUANTITY = round(float((amt_dollar * LEVERAGE) / df['close'][len(df.index) - 1]), 3)

          order('SELL', TRADE_QUANTITY, TRADE_SYMBOL)
          status = 2

        elif status == 2:
          print("Still SHORTING")

      print("Number of bugs: ", bugs)


  ws = websocket.WebSocketApp(SOCKET, on_open= on_open, on_close=on_close, on_message=on_message)

  ws.run_forever()


