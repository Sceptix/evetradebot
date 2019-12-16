import sys
import pyautogui
import pyperclip
import os
import csv
import math
import random
from dateutil.parser import parse as DateUtilParser
import apistuff as api
import common as cm
import variables
import copy
import shutil

def changeOrder(order, newprice):
	position, itemsinlist = getOrderPosition(order)
	itemname = api.getNameFromID(order.typeid)
	print("changing order of item: " + itemname + " in position: " + str(position))
	if order.bid:
		actingPoint, listheight = variables.bidaplh
	else:
		actingPoint, listheight = variables.sellaplh
	pyautogui.moveTo(actingPoint.x, actingPoint.y)
	cm.sleep(0.2)
	
	#this scrolls so the order is visible, and adjusts the position
	itemsfitinlist = math.ceil(listheight / 20)
	if(position >= itemsfitinlist):
		pagescrollcount = math.floor(position / itemsfitinlist)
		position -= (itemsinlist % itemsfitinlist)
		pyautogui.scroll(int(-130 * itemsfitinlist * pagescrollcount))
	pyautogui.move(0, 20 * position)
	pyautogui.click(button='right', clicks=1)
	cm.sleep(0.4)
	pyautogui.move(35, 10)
	pyautogui.click()
	thing = pyautogui.locateOnScreen("imgs/modifyorder.png", confidence=0.9)
	while thing is None:
		thing = pyautogui.locateOnScreen("imgs/modifyorder.png", confidence=0.9)
		cm.sleep(0.1)
	box = cm.Area(thing.left + 100, thing.top + 21, 300, 19)
	ocr = cm.grabandocr(box).splitlines()
	ocrname = ""
	for line in ocr:
		if(len(line.split()) > 11):
			ocrname += line.split()[-1] + " "
	print("checking if we clicked the right order...")
	print("itemname: " + itemname.lower() + ", ocrname: " + ocrname)
	if cm.similar(ocrname.lower(), itemname.lower()) < 0.5:
		print("failed similar check")
		cm.clickxy(thing.left + 265, thing.top + 192)
		cm.sleep(0.2)
		refreshAllOrders()
		changeOrder(order, newprice)
		return
	cm.sleep(0.2)
	pyautogui.keyDown('ctrl')
	pyautogui.keyDown('c')
	cm.sleep(0.2)
	pyautogui.keyUp('c')
	pyautogui.keyUp('ctrl')
	realprice = pyperclip.paste()
	cm.safetypewrite(newprice)
	cm.sleep(0.2)
	pyautogui.typewrite(['enter'])
	cm.sleep(0.5)
	thing = pyautogui.locateOnScreen("imgs/warning.png", confidence=0.9)
	if thing is not None:
		cm.clickPointPNG("imgs/yesno.png", 20, 10)
	#reset scroll
	pyautogui.moveTo(actingPoint.x + 10, actingPoint.y + 10)
	pyautogui.scroll(100000)
	order.price = float(newprice)
	order.issuedate = cm.getEVETimestamp()

def cancelOrder(order):
	if(order is None or order.finished or not order.canChange()):
		print("Invalid cancel, ignoring")
		return

	refreshAllOrders()

	position, itemsinlist = getOrderPosition(order)
	print("cancelling buyorder: " + api.getNameFromID(order.typeid))

	if order.bid:
		actingPoint, listheight = variables.bidaplh
	else:
		actingPoint, listheight = variables.sellaplh
	pyautogui.moveTo(actingPoint.x, actingPoint.y)
	cm.sleep(0.2)
	#this scrolls so the order is visible, and adjusts the position
	itemsfitinlist = math.ceil(listheight / 20)
	if(position >= itemsfitinlist):
		pagescrollcount = math.floor(position / itemsfitinlist)
		position -= (itemsinlist % itemsfitinlist)
		pyautogui.scroll(int(-130 * itemsfitinlist * pagescrollcount))
	pyautogui.move(0, 20 * position)
	pyautogui.click(button='right', clicks=1)
	cm.sleep(0.2)
	#clicking market details on order and checking if we clicked the right order
	pyautogui.move(40, 68)
	pyautogui.click()
	cm.sleep(0.5)
	thing = pyautogui.locateOnScreen('imgs/search.png', confidence=0.9)
	marketnamearea = cm.Area(thing.left + 158, thing.top + 14, 375, 30)
	ocr = cm.grabandocr(marketnamearea)
	marketname = ""
	for line in ocr.splitlines():
		if len(line.split()) > 11:
			marketname += line.split()[-1] + ' '
	marketname = marketname.strip()
	print("read marketname while cancelling order: " + marketname)
	if(cm.similar(marketname.lower(), api.getNameFromID(order.typeid).lower()) < 0.5):
		print("clicked wrong order while cancelling, retrying")
		cancelOrder(order)
		return
	
	pyautogui.moveTo(actingPoint.x, actingPoint.y)
	cm.sleep(0.2)
	if(position >= itemsfitinlist):
		pagescrollcount = math.floor(position / itemsfitinlist)
		position -= (itemsinlist % itemsfitinlist)
		pyautogui.scroll(int(-130 * itemsfitinlist * pagescrollcount))
	pyautogui.move(0, 20 * position)
	pyautogui.click(button='right', clicks=1)
	cm.sleep(0.2)

	pyautogui.move(40, 115)
	pyautogui.click()
	for ih in variables.itemhandlerlist:
		if order.bid:
			if areOrdersTheSame(ih.buyorder, order):
				ih.buyorder = None
		else:
			for so in ih.sellorderlist:
				if areOrdersTheSame(so, order):
					so = None

#used for checking if orders are the same when orderid isnt set
def areOrdersTheSame(o1, o2):
	if o1 is None or o2 is None:
		return False
	issuedateDelta = abs(o1.issuedate - o2.issuedate)
	aresame = ((o1.typeid == o2.typeid) and (issuedateDelta < 10) and (o1.bid == o2.bid)) or (o1.orderid == o2.orderid)
	return aresame

def deleteMarketLogs():
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	for filename in os.listdir(marketlogsfolder):
		file_path = os.path.join(marketlogsfolder, filename)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except:
			print("failed deleting all files in marketlogs")

#refresh orders finished, volremaing and orderid
def refreshAllOrders():
	itemhandlerlist = variables.itemhandlerlist
	
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	deleteMarketLogs()

	cm.exportMyOrders()

	loopidx = 0
	while True:
		if(len(os.listdir(marketlogsfolder)) > 0):
			break
		thing = pyautogui.locateOnScreen("imgs/nobuyorsell.png", confidence=0.9)
		if thing is not None:
			okbutton = cm.Point(thing.left + 169, thing.top + 194)
			cm.clickPoint(okbutton)
			return
		if loopidx % 5 == 0:
			cm.exportMyOrders()
		else:
			cm.sleep(0.5)
		loopidx += 1

	if not os.listdir(marketlogsfolder)[-1].startswith('My Orders'):
		refreshAllOrders()
		return
	
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	neworders = []
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			neworders.append(cm.Order(int(l['typeID']), int(l['orderID']), str(l['bid']) == "True", float(l['price']),
							int(float(l['volEntered'])), int(float(l['volRemaining'])), DateUtilParser(l['issueDate']).timestamp()))
	os.remove(logfile)

	oldorders = []
	for itemhandler in itemhandlerlist:
		ihcopy = copy.deepcopy(itemhandler)
		if ihcopy.buyorder is not None:
			oldorders.append(ihcopy.buyorder)
		if ihcopy.sellorderlist:
			oldorders += ihcopy.sellorderlist
			

	newfromoldorders = []
	#the newfromoldorders list will contain every order even finished ones, the itemhandler will remove those in its handle func
	for oo in oldorders:
		curorder = copy.deepcopy(oo)
		for no in neworders:
			if areOrdersTheSame(oo, no):
				curorder.volremaining = no.volremaining
				if(curorder.volremaining > curorder.volentered):
					curorder.volremaining = curorder.volentered
				if(curorder.orderid == -1):
					curorder.orderid = no.orderid
				curorder.issuedate = no.issuedate
				break
		curorder.finished = (not any(areOrdersTheSame(oo, no) for no in neworders) and cm.getEVETimestamp() - oo.issuedate > 20)
		newfromoldorders.append(curorder)
	#the order export can be heavily delayed sometimes, so we just add old orders that are freshly made 
	for oo in oldorders:
		if (not any(areOrdersTheSame(nfo, oo) for nfo in newfromoldorders) and cm.getEVETimestamp() - oo.issuedate < 20):
			newfromoldorders.append(oo)
	#sort each neworder back into the itemhandlers
	for itemhandler in itemhandlerlist:
		itemhandler.sellorderlist = []
		itemhandler.buyorder = None
		for nfo in newfromoldorders:
			if(itemhandler.typeid == nfo.typeid):
				if nfo.bid:
					itemhandler.buyorder = nfo
				else:
					itemhandler.sellorderlist.append(nfo)

#loads all orders from export, overwriting old ones
def loadOrders():
	itemhandlerlist = variables.itemhandlerlist
	
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	deleteMarketLogs()

	cm.exportMyOrders()

	loopidx = 0
	while True:
		if(len(os.listdir(marketlogsfolder)) > 0):
			break
		thing = pyautogui.locateOnScreen("imgs/nobuyorsell.png", confidence=0.9)
		if thing is not None:
			okbutton = cm.Point(thing.left + 169, thing.top + 194)
			cm.clickPoint(okbutton)
			return
		if loopidx % 5 == 0:
			cm.exportMyOrders()
		else:
			cm.sleep(0.5)
		loopidx += 1

	if not os.listdir(marketlogsfolder)[-1].startswith('My Orders'):
		loadOrders()
		return
	
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	neworders = []
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			neworders.append(cm.Order(int(l['typeID']), int(l['orderID']), str(l['bid']) == "True", float(l['price']),
							int(float(l['volEntered'])), int(float(l['volRemaining'])), DateUtilParser(l['issueDate']).timestamp()))
	os.remove(logfile)
	for no in neworders:
		if not any(no.typeid == ih.typeid for ih in itemhandlerlist):
			#todo make a new itemhandlertype that only takes care of existing orders and then stops existing
			#it would be useful for selling leftover items and stuff
			print("you still have an order that won't get an itemhandler, please cancel it:")
			print(api.getNameFromID(no.typeid))
			sys.exit()
	#sort each neworder back into the itemhandlers
	for itemhandler in itemhandlerlist:
		itemhandler.sellorderlist = []
		itemhandler.buyorder = None
		for no in neworders:
			if(itemhandler.typeid == no.typeid):
				if no.bid:
					itemhandler.buyorder = no
				else:
					itemhandler.sellorderlist.append(no)

def sellitemininventory(typeid, price):
	item = api.getNameFromID(typeid)
	cm.clickPointPNG('imgs/inventorytopright.png', 0, 25, 2, cache=True)
	cm.sleep(0.2)
	cm.safetypewrite(item)

	thing = pyautogui.locateOnScreen('imgs/inventoryitemhangar.png')
	inventorylist = cm.Area(thing.left + 25, thing.top + 70, 500, 250)

	cm.sleep(1)

	box = inventorylist.toAbsTuple()
	ocr = cm.grabandocr(box)

	#todo implement ocr with highestsim check
	for s in ocr.splitlines():
		if(s.split()[-1][:5] in item.lower()):
			offsetpos = inventorylist
			mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
			mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
			cm.clickxy(mousex, mousey, clicks=1, right=True)
			cm.sleep(0.2)

			box = (mousex + 15,mousey + 2 ,mousex + 15 + 135, mousey + 3 + 200)
			ocr = cm.grabandocr(box)

			for s in ocr.splitlines():
				if(s.split()[-1] == "sell"):
					mousex = mousex + 18 + int(s.split()[6]) / 4 + 5
					mousey = mousey + 3 + int(s.split()[7]) / 4 + 5
					cm.clickxy(mousex, mousey)
					cm.sleep(5)
					#todo replace this with clickpointpng
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
					cm.sleep(0.3)
					pyautogui.doubleClick(pricefield.x, pricefield.y)
					cm.safetypewrite(price)

					cm.clickPoint(sellbutton)
					cm.sleep(0.5)
					thing = pyautogui.locateOnScreen('imgs/sellitemconfirm.png')
					confirmbutton = cm.Point( thing.left +145 , thing.top + 193)
					cm.clickPoint(confirmbutton)
					thing = pyautogui.locateOnScreen("imgs/warning.png", confidence=0.9)
					if thing is not None:
						cm.clickPointPNG("imgs/yesno.png", 20, 10)

					return 1
	return 0

def buyorder(typeid, price, quantity):
	cm.openItem(typeid)
	cm.sleep(3)
	thing = pyautogui.locateOnScreen('imgs/placebuyorder.png')
	buyorderpos = cm.Point( thing.left + thing.width / 2 , thing.top + thing.height / 2)
	cm.clickPoint(buyorderpos)
	cm.sleep(2)
	thing = pyautogui.locateOnScreen('imgs/buyorderadvanced.png')
	if thing is not None:
		advanced = cm.Point( thing.left + thing.width / 2 , thing.top + thing.height / 2)
		cm.clickPoint(advanced)
		cm.sleep(1)
	thing = pyautogui.locateOnScreen('imgs/buyorderoriginpoint.png')
	bidpricefield = cm.Point( thing.left + 143 , thing.top + 33)
	quantityfield = cm.Point( thing.left + 143 , thing.top + 169)
	duration = cm.Point( thing.left + 143 , thing.top + 190)
	threemonths = cm.Point( thing.left + 143 , thing.top + 332)
	buything = pyautogui.locateOnScreen('imgs/buyandcancel.png')
	buybutton = cm.Point( buything.left + 25 , buything.top + 7)
	cm.clickPoint(bidpricefield, 2)
	cm.sleep(0.3)
	cm.safetypewrite(price)
	cm.clickPoint(quantityfield, 2)
	cm.sleep(0.3)
	cm.safetypewrite(quantity)
	cm.clickPoint(duration)
	cm.clickPoint(threemonths)
	cm.clickPoint(buybutton, 1)
	cm.sleep(0.6)
	thing = pyautogui.locateOnScreen('imgs/confirmorder.png')
	confirmyes = cm.Point( thing.left + 149 , thing.top + 197)
	cm.clickPoint(confirmyes)
	thing = pyautogui.locateOnScreen("imgs/warning.png", confidence=0.9)
	if thing is not None:
		cm.clickPointPNG("imgs/yesno.png", 20, 10)

#returns the top six buy and sell orders
def getTopOrders(typeid):
	cm.openItem(typeid)
	cm.sleep(0.2)

	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	deleteMarketLogs()
	
	cm.clickPointPNG("imgs/exporttofile.png", 5, 5, cache=True)
	
	loopidx = 0
	while True:
		if(len(os.listdir(marketlogsfolder)) > 0):
			break
		if loopidx % 5 == 0:
			cm.openItem(typeid)
			cm.clickPointPNG("imgs/exporttofile.png", 5, 5, cache=True)
		else:
			cm.sleep(0.5)
		loopidx += 1

	if os.listdir(marketlogsfolder)[-1].startswith('My Orders'):
		getTopOrders(typeid)
		return

	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	buyorders, sellorders = [], []
	exitflag = False
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			#if we didnt wait long enough for item to load
			if(int(l['typeID']) != typeid):
				exitflag = True
			if(int(l['jumps']) != 0):
				continue
			o = cm.Order(typeid, int(l['orderID']), str(l['bid']) == "True", float(l['price']), int(float(l['volEntered'])), int(float(l['volRemaining'])), DateUtilParser(l['issueDate']).timestamp())
			if(o.bid):
				buyorders.append(o)
			else:
				sellorders.append(o)
	os.remove(logfile)
	if(exitflag):
		return getTopOrders(typeid)
	#highest first
	buyorders.sort(key=lambda x: x.price, reverse=True)
	#lowest first
	sellorders.sort(key=lambda x: x.price, reverse=False)
	return (buyorders[0:6], sellorders[0:6])

#used for getting all orders from every itemhandler which exist and arent finished
def getOrderCache():
	itemhandlerlist = variables.itemhandlerlist
	allorders = []
	for ih in itemhandlerlist:
		if ih.buyorder is not None and not ih.buyorder.finished:
			allorders.append(ih.buyorder)
		for so in ih.sellorderlist:
			if not so.finished:
				allorders.append(so)
	return allorders

#returns the index and length of the list this order is in
def getOrderPosition(wantedorder):
	orderlist = getOrderCache()
	#splitting the orderlist into buy and sellorders
	buylist = []
	selllist = []
	#sort by boughtat, which is also the standard sorting in eve's my orders
	#todo implement check to look if "expires in" is sorted in the correct direction (lowest timestamp first)
	orderlist.sort(key=lambda x: x.issuedate, reverse=False)
	print(orderlist)
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
def getGoodPrices(typeid):
	toporders = getTopOrders(typeid)
	buyprice, sellprice = -1, -1
	buyhighestbidderflag = False
	sellhighestbidderflag = False
	for o in toporders[0]:
		if(o.volremaining > variables.minquantity):
			buyhighestbidderflag = any(areOrdersTheSame(o, co) for co in getOrderCache())
			buyprice = o.price
			break
	for o in toporders[0]:
		#if we are highest bidder, but some other order that isnt ours has the same price as ours
		if(buyhighestbidderflag and buyprice == o.price and not any(areOrdersTheSame(o, co) for co in getOrderCache())):
			#we set highestbidder to false so we can overbid people that have the same price as us
			buyhighestbidderflag = False
			break
	#highest bidder checks for sell orders
	for o in toporders[1]:
		if(o.volremaining > variables.minquantity):
			sellhighestbidderflag = any(areOrdersTheSame(o, co) for co in getOrderCache())
			sellprice = o.price
			break
	for o in toporders[1]:
		if(sellhighestbidderflag and sellprice == o.price and not any(areOrdersTheSame(o, co) for co in getOrderCache())):
			sellhighestbidderflag = False
			break
	print("finished getgoodprices")
	returntuple = (buyprice, sellprice, buyhighestbidderflag, sellhighestbidderflag)
	print(returntuple)
	return returntuple

def buyItem(itemhandler, goodprices):
	quantity = itemhandler.volume
	buyprice = goodprices[0]
	if(buyprice == -1):
		print("Warning, not buying item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		return
	buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
	print("itemhandler called: " + api.getNameFromID(itemhandler.typeid) + " is initiating buyorder. price:" + str(buyprice) + ", quantity:" + str(quantity))
	buyorder(itemhandler.typeid, buyprice, quantity)
	itemhandler.buyorder = cm.Order(itemhandler.typeid, -1, True, buyprice, quantity, quantity, cm.getEVETimestamp())
	#this line sets the orderid from -1 to something else
	refreshAllOrders()

def sellItem(itemhandler, goodprices):
	sellprice = goodprices[1]
	if(sellprice == -1):
		print("Warning, not selling item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		return
	sellprice = round(sellprice - random.random() / 7 - 0.01, 2)
	flag = sellitemininventory(itemhandler.typeid, sellprice)
	if(flag == 0):
		print("couldnt sell item from inventory, doesnt exist")
		return
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
	itemhandler.sellorderlist.append(cm.Order(itemhandler.typeid, -1, False, sellprice, quantity, quantity, cm.getEVETimestamp()))
	#this line sets the orderid from -1 to something else
	refreshAllOrders()

def getPriorityItemhandlers():
	priorlist = []
	for ih in variables.itemhandlerlist:
		if ih.buyorder is not None and ih.buyorder.hasbeenoverbid and ih.buyorder.canChange():
			priorlist.append(ih)
			continue
		for so in ih.sellorderlist:
			if(so.hasbeenoverbid and so.canChange()):
				priorlist.append(ih)
				continue
	return priorlist

def refreshUnprofitable(itemhandler, goodprices):
	prices = goodprices
	pricemargin = (prices[1] - prices[0]) / prices[1]
	itemhandler.unprofitable = (pricemargin < variables.minmargin)

def checkAndUnderBid(itemhandler, goodprices):
	prices = goodprices
	#manage buyorder
	if itemhandler.buyorder is not None:
		highestBidder = prices[2]
		curPrice = prices[0]
		if(curPrice == -1):
			print("Warning, not adjusting item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		else:
			print("curprice of item called \"" + api.getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
			if(curPrice > float(itemhandler.buyorder.price) and not highestBidder):
				if itemhandler.buyorder.canChange():
					itemhandler.buyorder.hasbeenoverbid = False
					print("Adjusting buyorder!")
					newprice = round(curPrice + random.random() / 15 + 0.02, 2)
					print("Bidding for newprice: " + str(newprice))
					changeOrder(itemhandler.buyorder, newprice)
				else:
					itemhandler.buyorder.hasbeenoverbid = True
	#manage sellorders
	#this makes all of your sellorders have the same price
	if itemhandler.sellorderlist:
		curPrice = prices[1]
		targetnewprice = round(curPrice - random.random() / 15 - 0.02, 2)
		highestBidder = prices[3]
		if(curPrice == -1):
			print("Warning, not adjusting item: " + api.getNameFromID(itemhandler.typeid) + " because there is no good price.")
		else:
			for sellorder in itemhandler.sellorderlist:
				print("curprice of item called \"" + api.getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
				if(curPrice < float(sellorder.price)):
					if sellorder.canChange():
						sellorder.hasbeenoverbid = False
						if highestBidder:
							continue
						print("Adjusting sellorder!")
						#if we are already top order, make this order the same as that one, so we dont onderbid ourselves
						print("Bidding for newprice: " + str(targetnewprice))
						changeOrder(sellorder, targetnewprice)
					else:
						sellorder.hasbeenoverbid = True

