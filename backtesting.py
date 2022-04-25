from binance.client import Client
import pandas as pd
import numpy as np
import config

from datetime import datetime

client = Client(config.KEY, config.SECRET)

TRADE_SYMBOL = 'ETHUSDT'

#Convert date into time stamp in millie seconds
#Add end_str at the end

klines = client.futures_historical_klines(symbol=TRADE_SYMBOL, 
                      interval=client.KLINE_INTERVAL_30MINUTE, start_str=1620721071000,
                      end_str=1625991471000)


data = pd.DataFrame(klines)

df_first = data.loc[:, [0, 1, 2, 3, 4]]

df = df_first.rename(columns={0 :'time', 1 : 'open', 2 : 'high', 3 : 'low', 4: 'close'})

emaUsed = [3,5,8,10,12,15,30,35,40,45,50,60]

for x in emaUsed:
	ema=x
	df["Ema_"+str(ema)] = round(df.iloc[:, 4].ewm(span = ema, adjust = False).mean(), 2)

print(df.tail())

pos = 0
num = 0
percentage = []

for i in df.index:
	cmin = min(df["Ema_3"][i], df["Ema_5"][i], df["Ema_8"][i], df["Ema_10"][i], df["Ema_12"][i], df["Ema_15"][i])
	cmax = max(df["Ema_30"][i], df["Ema_35"][i], df["Ema_40"][i], df["Ema_45"][i], df["Ema_50"][i], df["Ema_60"][i])

	close = df["close"][i]

	if(cmin > cmax):
		#print("Red White Blue")
		if(pos==0):
			bp = float(close)
			pos = 1
			#print("Buying now at", bp)

	elif (cmin < cmax):
		#print("Blue White Red")
		if (pos==1):
			pos = 0
			sp = float(close)
			#print("Selling now at ", sp)
			pc = (sp / bp-1) * 100
			percentage.append(pc)

	if(num == df["close"].count()-1 and pos==1):
		pos = 0
		sp = float(close)
		#print("Selling now at ", sp)
		pc = (sp/bp-1) * 100
		percentage.append(pc)

	num += 1


print(percentage)


'''

PART B

'''

gains = 0
ng = 0
losses = 0
nl = 0
totalR = 1

for i in percentage:
	if(i>0):
		gains += i
		ng += 1

	else:
		losses += i
		nl += 1
	totalR = totalR*((i/100) + 1)

totalR = round((totalR-1) * 100, 2)

if (ng > 0):
	avgGain = gains/ng
	maxR = str(max(percentage))

else:
	avgGain = 0
	maxR = "Undefined"

if(nl>0):
	avgLoss=losses/nl
	maxL=str(min(percentage))
	ratio=str(-avgGain/avgLoss)
else:
	avgLoss=0
	maxL="undefined"
	ratio="inf"

if(ng>0 or nl>0):
	battingAvg=ng/(ng+nl)
else:
	battingAvg=0

print()
print("Results for "+ TRADE_SYMBOL +" going back to "+str(df.index[0])+", Sample size: "+str(ng+nl)+" trades")
#print("EMAs used: "+str(emaUsed))
#print("Batting Avg: "+ str(battingAvg))
#print("Gain/loss ratio: "+ ratio)
#print("Average Gain: "+ str(avgGain))
#print("Average Loss: "+ str(avgLoss))
print("Max Return: "+ maxR)
print("Max Loss: "+ maxL)
print("Total return over "+str(ng+nl)+ " trades: "+ str(totalR)+"%" )
print("Win Rate: ", ng/(ng+nl), "%")
#print("Example return Simulating "+str(n)+ " trades: "+ str(nReturn)+"%" )
