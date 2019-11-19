import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
from MyUtils import *
from apistuff import *
from orderstuff import *
import random

time.sleep(5)

#close undock window

try:
	clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
	print("couldnt close undock window, was probably already closed")
	
#create buy orders for items that havent got one yet
orderlist = []
#50 million, todo keep track of this differently
usercapital = 15 * 10**5

def str2bool(string):
	string = string.strip()
	if(isinstance(string, bool)):
		return string
	if(string == "True"):
		return True
	elif(string == "False"):
		return False
	else:
		print("wrong type for str2bool, got: " + str(type(string)) + ", aborting")
		sys.exit()

with open('openorders.csv') as orders:
	data = list(csv.reader(orders, delimiter=','))
	for x in data:
		orderlist.append(Order(str(x[0]), float(x[1]), str2bool(x[2]), float(x[3])))

orderlist, _, _ = refreshOrders(orderlist)

def saveOrderList():
	f = open('openorders.csv', "w")
	for order in orderlist:
		f.write(order.csvdump() + "\n")
	f.close()
	
#every item in items.csv
tradinglist = []

#buy all the items that havent been bought yet at start of trading day
with open('items.csv') as items:
	data = list(csv.reader(items, delimiter=','))
	totalvolume = 0
	totalvolume += sum(int(x[1]) for x in data)
	for row in data:
		itemname = row[0]
		tradinglist.append(itemname)
		if(len(tradinglist) > 10):
			print("tradinglist length over 10, aborting")
			sys.exit()
		if(any(x for x in orderlist if x.name == itemname)):
			print("item " + itemname + " already in orders, skipping")
			continue
		itempercentage = int(row[1]) / totalvolume
		print(itemname)
		print(itempercentage)
		#we only get here if we dont have a buy order with that item name yet
		purchasetotal = usercapital * itempercentage
		usercapital -= purchasetotal
		buyprice = getItemPrices(itemname)[0]
		buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
		quantity = int(purchasetotal / buyprice)
		print(str(itemname) + " , " + str(buyprice) + " , " + str(quantity))
		buyorder(itemname, buyprice, quantity)
		orderlist.append(Order(itemname, buyprice, True, time.time()))
		saveOrderList()

#function i use for rebuying items in the items.csv
def buyItemProportionally(item):
	data = list(csv.reader(items, delimiter=','))
	totalvolume = 0
	totalvolume += sum(int(x[1]) for x in data)
	for row in data:
		if(row[0] == item):
			itemname = row[0]
			itempercentage = int(row[1]) / totalvolume
		#we only get here if we dont have a buy order with that item name yet
		purchasetotal = usercapital * itempercentage
		usercapital -= purchasetotal
		buyprice = getItemPrices(itemname)[0]
		buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
		quantity = int(purchasetotal / buyprice)
		print(str(itemname) + " , " + str(buyprice) + " , " + str(quantity))
		buyorder(itemname, buyprice, quantity)
		orderlist.append(Order(itemname, buyprice, True, time.time()))
		saveOrderList()


#underbid order loop logic


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
		orderlist, soldorders, finisheditems = refreshOrders(orderlist)
		#sell items from fulfilled buy orders
		newOrders = doSoldOrders(soldorders)
		orderlist += newOrders
		#make new buy orders for items that have been bought and sold
		for y in finisheditems:
			buyItemProportionally(y)

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