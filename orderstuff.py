import time
import sys
import pyautogui
import os
import csv
import math
import random
import pickle
from collections import defaultdict
from dateutil.parser import parse as DateUtilParser
import apistuff as api
import common as cm
from variables import *


def getAPandLH(bid):
	if bid:
		actingpointthing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		buylisttopleft = cm.Point(thing.left + 74, thing.top + 16)
		thing = pyautogui.locateOnScreen('imgs/myordersexport.png', confidence=0.9)
		buylistbottomleft = cm.Point(thing.left + 79, thing.top - 85)
		listheight = buylistbottomleft.y - buylisttopleft.y	+ 2
	else:
		actingpointthing = pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9)
		thing = pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9)
		selllisttopleft = cm.Point(thing.left + 74, thing.top + 16)
		thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		selllistbottomleft = cm.Point(thing.left + 74, thing.top - 7)
		listheight = selllistbottomleft.y - selllisttopleft.y + 2
	actingPoint = cm.Point(actingpointthing.left + 100, actingpointthing.top + 17)
	return actingPoint, listheight

def changeOrder(order, newprice, position, itemsinlist):
	print("changing order of item: " + api.getNameFromID(order.typeid))
	cm.clickMyOrders()
	actingPoint, listheight = getAPandLH(order.bid)
	pyautogui.moveTo(actingPoint.x, actingPoint.y)
	pyautogui.sleep(0.2)
	
	#this scrolls so the order is visible, and adjusts the position
	itemsfitinlist = math.ceil(listheight / 20)
	if(position >= itemsfitinlist):
		pagescrollcount = math.floor(position / itemsfitinlist)
		position -= (itemsinlist % itemsfitinlist)
		pyautogui.scroll(int(-130 * itemsfitinlist * pagescrollcount))
	pyautogui.move(0, 20 * position)
	pyautogui.click(button='right', clicks=1)
	pyautogui.sleep(0.2)
	pyautogui.move(35, 10)
	pyautogui.click()
	pyautogui.sleep(0.2)

	#todo, implement ocr check to see if we clicked the right item
	
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(str(newprice), interval=0.1)
	pyautogui.typewrite(['enter'])
	#reset scroll
	pyautogui.moveTo(actingPoint.x + 10, actingPoint.y + 10)
	pyautogui.scroll(100000)
	order.price = float(newprice)
	order.issuedate = cm.getEVETimestamp()

#todo implement check that we actually clicked the right order, ocr
def cancelOrder(order):
	if(order is None):
		print("tried to cancel a none order")
		return
	position, itemsinlist = getOrderPosition(order)
	print("cancelling buyorder: " + api.getNameFromID(order.typeid))
	cm.clickMyOrders()

	actingPoint, listheight = getAPandLH(order.bid)
	pyautogui.moveTo(actingPoint.x, actingPoint.y)
	pyautogui.sleep(0.2)
	
	#this scrolls so the order is visible, and adjusts the position
	itemsfitinlist = math.ceil(listheight / 20)
	if(position >= itemsfitinlist):
		pagescrollcount = math.floor(position / itemsfitinlist)
		position -= (itemsinlist % itemsfitinlist)
		pyautogui.scroll(int(-130 * itemsfitinlist * pagescrollcount))
	pyautogui.move(0, 20 * position)
	pyautogui.click(button='right', clicks=1)
	pyautogui.sleep(0.2)
	pyautogui.move(40, 115)
	pyautogui.click()
	order = None

#used for checking if orders are the same when orderid isnt set
def areOrdersTheSame(o1, o2):
	issuedateDelta = abs(o1.issuedate - o2.issuedate)
	if(o1.orderid == -1 or o2.orderid == -1):
		return (o1.typeid == o2.typeid) and (o1.bid == o2.bid) and (o1.volentered == o2.volentered) and (issuedateDelta < 5)
	else:
		return (o1.orderid == o2.orderid)
#refresh orders finished, volremaing and orderid
def refreshOrders(itemhandler):
	oldorders = []
	if itemhandler.buyorder is not None:
		oldorders.append(itemhandler.buyorder)
	if itemhandler.sellorderlist:
		oldorders += itemhandler.sellorderlist
	cm.clickMyOrders()
	pyautogui.sleep(0.3)
	cm.clickPointPNG('imgs/myordersexport.png', 10, 10)
	pyautogui.sleep(1)
	thing = pyautogui.locateOnScreen("imgs/nobuyorsell.png", confidence=0.9)
	if thing is not None:
		okbutton = cm.Point(thing.left + 169, thing.top + 194)
		cm.clickPoint(okbutton)
		return
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	neworders = []
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			neworders.append(cm.Order(int(l['typeID']), int(l['orderID']), str(l['bid']) == "True", float(l['price']),
							int(float(l['volEntered'])), int(float(l['volRemaining'])), DateUtilParser(l['issueDate']).timestamp()))
	os.remove(logfile)
	newfromoldorders = []
	#the newfromoldorders list will contain every order even finished ones, the itemhandler will remove those in its handle func
	for oo in oldorders:
		for no in neworders:
			if areOrdersTheSame(oo, no):
				oo.volremaining = no.volremaining
				if(oo.orderid == -1):
					oo.orderid = no.orderid
				break
		if not any(areOrdersTheSame(oo, no) for no in neworders):
			oo.finished = True
		newfromoldorders.append(oo)
	#sort each neworder back into the itemhandler
	itemhandler.sellorderlist = []
	for nfo in newfromoldorders:
		if(itemhandler.typeid == nfo.typeid):
			if nfo.bid:
				itemhandler.buyorder = nfo
			else:
				itemhandler.sellorderlist.append(nfo)
	refreshOrderCache(itemhandlerlist)

def sellitemininventory(typeid, price):
	item = api.getNameFromID(typeid)
	cm.clickPointPNG('imgs/inventorytopright.png', 0, 25, 2)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(item, interval=0.1)

	thing = pyautogui.locateOnScreen('imgs/inventoryitemhangar.png')
	inventorylist = cm.Area(thing.left + 25, thing.top + 70, 1000, 250)

	pyautogui.sleep(1)

	box = inventorylist.toAbsTuple()
	ocr = cm.grabandocr(box)

	for s in ocr.splitlines()[1:]:
		if(s.split()[-1][:5] in item.lower()):
			offsetpos = inventorylist
			mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
			mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
			cm.clickxy(mousex, mousey, clicks=1, right=True)
			pyautogui.sleep(0.2)

			box = (mousex + 15,mousey + 2 ,mousex + 15 + 135, mousey + 3 + 200)
			ocr = cm.grabandocr(box)

			for s in ocr.splitlines()[1:]:
				if(s.split()[-1] == "sell"):
					mousex = mousex + 18 + int(s.split()[6]) / 4 + 5
					mousey = mousey + 3 + int(s.split()[7]) / 4 + 5
					cm.clickxy(mousex, mousey)
					pyautogui.sleep(5)
					thing = pyautogui.locateOnScreen('imgs/sellitems.png')
					pricefield = cm.Point( thing.left + thing.width / 2 , thing.top + 80)
					thing = pyautogui.locateOnScreen('imgs/sellitemsellcancel.png')
					sellbutton = cm.Point( thing.left + 25, thing.top + 12)
					thing = pyautogui.locateOnScreen('imgs/sellitemduration.png')
					durationfield = cm.Point( thing.left - 50 , thing.top + 28)

					#set duration to 3 months
					cm.clickPoint(durationfield)
					cm.clickxy(durationfield.x, durationfield.y + 145)

					#set price
					pyautogui.moveTo(pricefield.x, pricefield.y)
					pyautogui.sleep(0.1)
					pyautogui.doubleClick(pricefield.x, pricefield.y)
					pyautogui.typewrite(['backspace'])
					pyautogui.typewrite(str(price), interval=0.1)

					cm.clickPoint(sellbutton)
					pyautogui.sleep(0.5)
					thing = pyautogui.locateOnScreen('imgs/sellitemconfirm.png')
					confirmbutton = cm.Point( thing.left +145 , thing.top + 193)
					cm.clickPoint(confirmbutton)

					return

def buyorder(typeid, price, quantity):
	cm.clickDetails()
	cm.openItem(typeid)
	pyautogui.sleep(3)
	thing = pyautogui.locateOnScreen('imgs/placebuyorder.png')
	buyorderpos = cm.Point( thing.left + thing.width / 2 , thing.top + thing.height / 2)
	cm.clickPoint(buyorderpos)
	pyautogui.sleep(2)
	thing = pyautogui.locateOnScreen('imgs/buyorderadvanced.png')
	if thing is not None:
		advanced = cm.Point( thing.left + thing.width / 2 , thing.top + thing.height / 2)
		cm.clickPoint(advanced)
		pyautogui.sleep(1)
	#make sure buy order is set to advanced
	#TODO implement advanced check
	thing = pyautogui.locateOnScreen('imgs/buyorderoriginpoint.png')
	bidpricefield = cm.Point( thing.left + 143 , thing.top + 33)
	quantityfield = cm.Point( thing.left + 143 , thing.top + 169)
	duration = cm.Point( thing.left + 143 , thing.top + 190)
	threemonths = cm.Point( thing.left + 143 , thing.top + 332)
	buything = pyautogui.locateOnScreen('imgs/buyandcancel.png')
	buybutton = cm.Point( buything.left + 25 , buything.top + 7)
	cm.clickPoint(bidpricefield, 2)
	pyautogui.sleep(0.1)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(str(price), interval=0.1)
	cm.clickPoint(quantityfield, 2)
	pyautogui.sleep(0.1)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(str(quantity), interval=0.1)
	cm.clickPoint(duration)
	cm.clickPoint(threemonths)
	cm.clickPoint(buybutton, 1)
	pyautogui.sleep(0.6)
	thing = pyautogui.locateOnScreen('imgs/confirmorder.png')
	confirmyes = cm.Point( thing.left + 149 , thing.top + 197)
	cm.clickPoint(confirmyes)

#returns the top six buy and sell orders
def getTopOrders(typeid):
	cm.openItem(typeid)
	cm.clickPointPNG("imgs/exporttofile.png", 5, 5)
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	buyorders, sellorders = [], []
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			if(int(l['jumps']) != 0):
				continue
			o = cm.Order(typeid, int(l['orderID']), str(l['bid']) == "True", float(l['price']), int(float(l['volEntered'])), int(float(l['volRemaining'])), DateUtilParser(l['issueDate']).timestamp())
			if(o.bid):
				buyorders.append(o)
			else:
				sellorders.append(o)
	os.remove(logfile)
	#highest first
	buyorders.sort(key=lambda x: x.price, reverse=True)
	#lowest first
	sellorders.sort(key=lambda x: x.price, reverse=False)
	return (buyorders[0:6], sellorders[0:6])

#call this every time you handle an itemhandler
#this is also just used for the positions, thats why we dont add finished orders to the list
def refreshOrderCache(itemhandlerlist):
	allorders = []
	for ih in itemhandlerlist:
		if ih.buyorder is not None and not ih.buyorder.finished:
			allorders.append(ih.buyorder)
		for so in ih.sellorderlist:
			if not so.finished:
				allorders.append(so)
	with open('ordercache.csv', 'wb') as oc:
		pickle.dump(allorders, oc)

def getOrderCache():
	allorders = []
	with open('ordercache.csv', 'rb') as oc:
		allorders = pickle.load(oc)
	return allorders

#returns the index and length of the list this order is in
def getOrderPosition(wantedorder):
	orderlist = getOrderCache()
	#splitting the orderlist into buy and sellorders
	buylist = []
	selllist = []
	#sort by boughtat, which is also the standard sorting in eve's my orders
	#todo implement check to look if "expires in" is sorted in the correct direction (oldest first)
	orderlist.sort(key=lambda x: x.issuedate, reverse=False)
	for order in orderlist:
		if(order.bid):
			buylist.append(order)
		else:
			selllist.append(order)
	if (wantedorder.bid):
		for idx, x in enumerate(buylist):
			if(areOrdersTheSame(x, wantedorder)):
				return (idx, len(buylist))
	else:
		for idx, x in enumerate(selllist):
			if(areOrdersTheSame(x, wantedorder)):
				return (idx, len(selllist))
	print("couldnt find order: " + api.getNameFromID(wantedorder.typeid) + "  in getorderposition, aborting")
	sys.exit()
	
#this is to avoid over or underbidding somebody with low quantity
#if overbid is set to false, we dont add the random ammount
def getGoodPrices(typeid, overbid=True):
	refreshOrderCache(itemhandlerlist)
	toporders = getTopOrders(typeid)
	buyprice, sellprice = -1, -1
	highestbidderflag = False
	for o in toporders[0]:
		if(o.volremaining > minquantity):
			if overbid:
				buyprice = round(o.price + random.random() / 7 + 0.01, 2)
			else:
				buyprice = o.price
			break
	#highest bidder checks for sell orders
	for o in toporders[1]:
		if(o.volremaining > minquantity):
			highestbidderflag = any(areOrdersTheSame(o, co) for co in getOrderCache())
			if overbid:
				sellprice = round(o.price - random.random() / 7 - 0.01, 2)
			else:
				sellprice = o.price
			break
	return (buyprice, sellprice, highestbidderflag)

def buyItem(itemhandler):
	quantity = itemhandler.volume
	buyprice = getGoodPrices(itemhandler.typeid)[0]
	if(buyprice == -1):
		print("Warning, not buying item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		return
	print("itemhandler initiating initialbuyorder: " + str(itemhandler.typeid) + " , " + str(buyprice) + " , " + str(quantity))
	buyorder(itemhandler.typeid, buyprice, quantity)
	itemhandler.buyorder = cm.Order(itemhandler.typeid, -1, True, buyprice, quantity, quantity, cm.getEVETimestamp())
	#this line sets the orderid from -1 to something else
	refreshOrders(itemhandler)
	refreshOrderCache(itemhandlerlist)

def sellItem(itemhandler):
	sellPrice = getGoodPrices(itemhandler.typeid)[1]
	if(sellprice == -1):
		print("Warning, not selling item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		return
	sellitemininventory(itemhandler.typeid, sellPrice)
	quantity = 0
	if itemhandler.buyorder.finished:
		#adjust the quantity if there are previous sellorders
		quantity = itemhandler.volume
		for sellorder in itemhandler.sellorderlist:
			quantity -= sellorder.volentered
	else:
		#we only get here once, because we check if sellorderlist has no
		#elements in the ifstatement in the selling part in itemhandler's handle()
		quantity = itemhandler.buyorder.volentered - itemhandler.buyorder.volremaining
	itemhandler.sellorderlist.append(cm.Order(itemhandler.typeid, -1, False, sellPrice, quantity, quantity, cm.getEVETimestamp()))
	#this line sets the orderid from -1 to something else
	refreshOrders(itemhandler)
	refreshOrderCache(itemhandlerlist)

def refreshUnprofitable(itemhandler):
	prices = getGoodPrices(itemhandler.typeid, overbid=False)
	pricemargin = (prices[1] - prices[0]) / prices[1]
	itemhandler.unprofitable = (pricemargin < minmargin)

def checkAndUnderBid(itemhandler):
	prices = getGoodPrices(itemhandler.typeid, overbid=False)
	#manage buyorder
	if itemhandler.buyorder is not None and itemhandler.buyorder.canChange():
		curPrice = prices[0]
		if(curPrice == -1):
			print("Warning, not adjusting item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		else:
			print("curprice of item called \"" + api.getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
			if(curPrice > float(itemhandler.buyorder.price)):
				print("Adjusting buyorder!")
				position, itemsinlist = getOrderPosition(itemhandler.buyorder)
				newprice = round(curPrice + random.random() / 7 + 0.01, 2)
				print("Bidding for newprice: " + str(newprice))
				changeOrder(itemhandler.buyorder, newprice, position, itemsinlist)
	#manage sellorders
	#this makes all of your sellorders have the same price
	if itemhandler.sellorderlist:
		highestBidder = prices[2]
		for sellorder, idx in enumerate(itemhandler.sellorderlist):
			if sellorder.canChange():
				curPrice = prices[1]
				print("curprice of item called \"" + api.getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
				if(curPrice < float(sellorder.price)):
					print("Adjusting sellorder!")
					position, itemsinlist = getOrderPosition(sellorder)
					newprice = round(curPrice - random.random() / 7 - 0.01, 2)
					#if we are already top order, make this order the same as that one, so we dont onderbid ourselves
					if highestBidder:
						newprice = curPrice
					print("Bidding for newprice: " + str(newprice))
					changeOrder(sellorder, newprice, position, itemsinlist)

