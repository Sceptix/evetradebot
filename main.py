import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
from MyUtils import *
from apistuff import *
from orderstuff import *
import random
import pickle

#time.sleep(5)

#todo check items not more than 8 so you can have a sell and buy order of the same item type at all times (alpha account has 17 orders max)

#close undock window

try:
	clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
	print("couldnt close undock window, was pr7obably already closed")
	
#create buy orders for items that havent got one yet
orderlist = []
#50 million, todo keep track of this differently
usercapital = 15 * 10**5

#todo move this somewhere else


#deprecated
#with open('openorders.csv') as orders:
#	data = list(csv.reader(orders, delimiter=','))
#	for x in data:
#		orderlist.append(Order(str(x[0]), float(x[1]), str2bool(x[2]), float(x[3])))

#orderlist, _, _ = refreshOrders(orderlist)

#def saveOrderList():
#	f = open('openorders.csv', "w")
#	for order in orderlist:
#		f.write(order.csvdump() + "\n")
#	f.close()
	
#itemhandler for every item in items.csv
itemhandlerlist = []

def changeShit(ih):
	ih.volume = 696969

shittyih = ItemHandler("Spirits", 100000.2, 100, 0.2)
print(shittyih.__dict__)
changeShit(shittyih)
print(shittyih.__dict__)


print(pickle.dumps(itemhandlerlist))

sys.exit()

#buy all the items that havent been bought yet at start of trading day
with open('itemhandlers.json') as items:
	data = list(csv.reader(items, delimiter=','))
	totalvolume = 0
	totalvolume += sum(int(x[1]) for x in data)
	for row in data:
		itemname = row[0]
		tradinglist.append(itemname)
		if(len(tradinglist) > 8):
			print("tradinglist length over 8, aborting")
			sys.exit()
		if(any(x for x in orderlist if x.name == itemname)):
			print("item " + itemname + " already in orders, skipping")
			continue
		itempercentage = int(row[1]) / totalvolume
		print(itemname)
		print(itempercentage)
		#we only get here if we dont have a buy order with that item name yet
		purchasetotal = usercapital * itempercentage
		buyprice = getItemPrices(itemname)[0]
		buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
		quantity = int(purchasetotal / buyprice)
		print(str(itemname) + " , " + str(buyprice) + " , " + str(quantity))
		buyorder(itemname, buyprice, quantity)
		orderlist.append(Order(itemname, buyprice, True, time.time()))
		saveOrderList()

#function i use for rebuying items in the items.csv



#underbid order loop logic

#todo implement rebuying earlier, having sell and buy orders of the same type
#having multiple buy and or sell orders of the same type (implementing scrolling in myorders)
#rebuying items that sold out quickly more, not proportional to volume in items.csv
#todo ??? selling items after going offline doesnt work
#todo cant have buy and sell orders of same item type at the same time
#todo keep track of orders better
#todo make it only sell everything, no rebuying in the laste two or three hours, and delete the orders that didnt make it
#todo automatic loading from evetrade.space

#run for about 9 hours
tradedaystart = time.time()
while time.time() - tradedaystart < 3600 * 9:
	changeableOrders = []
	for item in tradinglist:
		for x in orderlist:
			if(x.canChange() and x.name == item):
				changeableOrders.append(x)
	for changeableOrder in changeableOrders:
		print("checking order: " + str(changeableOrder))
		time.sleep(random.random() * 7)

		orderlist, unprofitable = checkAndUnderBid(changeableOrder.name, orderlist)
		if(unprofitable):
			#cancel unprofitable buyorder
			position = getOrderPosition(changeableOrder.name, orderlist.copy(), True)
			cancelOrder(changeableOrder, position)
			for idx, y in enumerate(orderlist):
				if(y.name == changeableOrder.name and y.isbuy):
					orderlist.pop(idx)
					saveOrderList()
					break
			break
		saveOrderList()