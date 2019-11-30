import time
import sys
import pyautogui
from dateutil.parser import parse as DateUtilParser
from apistuff import *
import uuid
import pickle
from PIL import Image, ImageGrab, ImageFilter, ImageEnhance, ImageOps
import pytesseract
import os
import csv
import math
import random
from pytz import timezone
from datetime import datetime

def getEVETimestamp():
	return datetime.now(timezone('GMT')).replace(tzinfo=None).timestamp()

def clickPoint(point, clicks=1, right=False):
	pyautogui.moveTo(point.x, point.y)
	pyautogui.sleep(0.2)
	if right:
		pyautogui.click(button='right', clicks=clicks)
	else:
		pyautogui.click(clicks=clicks)

def clickPointPNG(pngname, leftoffset, topoffset, clicks=1, right=False):
	thing = pyautogui.locateOnScreen(pngname, confidence=0.9)
	point = Point(thing.left + leftoffset, thing.top + topoffset)
	clickPoint(point, clicks, right)

def clickxy(x, y, clicks=1, right=False):
	pyautogui.moveTo(x, y)
	pyautogui.sleep(0.2)
	if right:
		pyautogui.click(button='right', clicks=clicks)
	else:
		pyautogui.click(clicks=clicks)

def clickDetails():
	clickPointPNG('imgs/multibuy.png', 60, 3)

def clickMyOrders():
	clickPointPNG('imgs/multibuy.png', 160, 3)

def getAPandLH(bid):
	if bid:
		actingpointthing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		buylisttopleft = Point(thing.left + 74, thing.top + 16)
		thing = pyautogui.locateOnScreen('imgs/myordersexport.png', confidence=0.9)
		buylistbottomleft = Point(thing.left + 79, thing.top - 85)
		listheight = buylistbottomleft.y - buylisttopleft.y	+ 2
	else:
		actingpointthing = pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9)
		thing = pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9)
		selllisttopleft = Point(thing.left + 74, thing.top + 16)
		thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		selllistbottomleft = Point(thing.left + 74, thing.top - 7)
		listheight = selllistbottomleft.y - selllisttopleft.y + 2
	actingPoint = Point(actingpointthing.left + 100, actingpointthing.top + 17)
	return actingPoint, listheight

def changeOrder(order, newprice, position, itemsinlist):
	print("changing order of item: " + getNameFromID(order.typeid))
	clickMyOrders()
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
	order.issuedate = getEVETimestamp()

#todo implement check that we actually clicked the right order, ocr
def cancelBuyOrder(itemhandler):
	if(itemhandler.buyorder is None):
		print("tried to cancel a none buyorder in itemhandler: " + getNameFromID(itemhandler.id))
		return
	position, itemsinlist = getOrderPosition(itemhandler.buyorder)
	print("cancelling buyorder: " + getNameFromID(itemhandler.typeid))
	clickMyOrders()

	actingPoint, listheight = getAPandLH(True)
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
	itemhandler.buyorder = None

#todo change this to work on single itemhandler
def refreshOrders(itemhandler):
	oldorders = []
	if itemhandler.buyorder is not None:
		oldorders.append(itemhandler.buyorder)
	if itemhandler.sellorderlist:
		oldorders += itemhandler.sellorderlist
	clickMyOrders()
	pyautogui.sleep(0.3)
	clickPointPNG('imgs/myordersexport.png', 10, 10)
	pyautogui.sleep(1)
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	neworders = []
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			#todo check if indexes are right
			neworders.append(Order(int(l['typeID']), str2bool(l['bid']), float(l['price']),
							int(l['volentered']), int(l['volremaining']), DateUtilParser(l['issuedate']).timestamp()))
	os.remove(logfile)
	#the neworder list will contain every order even finished ones, the itemhandler will remove those in its handle func
	for oo in oldorders:
		if not any(oo.typeid == no.typeid for no in neworders):
			oo.finished = True
			neworders.append(oo)
	#sort each neworder back into their itemhandler
	for no in neworders:
		if(itemhandler.typeid == no.typeid):
			if no.bid:
				itemhandler.buyorder = no
			else:
				itemhandler.sellorderlist = []
				itemhandler.sellorderlist.append(no)

def search_market(item):
	pos = pyautogui.locateOnScreen('imgs/search.png')
	pyautogui.moveTo(pos.left - 70, pos.top + pos.height / 2)
	pyautogui.doubleClick(pos.left - 70, pos.top + pos.height / 2)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(item, interval=0.1)
	pyautogui.moveTo(pos.left + pos.width / 2, pos.top + pos.height / 2)
	pyautogui.click(pos.left + pos.width / 2, pos.top + pos.height / 2)

def grabandocr(box, pricesonly=False, treshfilter=False):
	if isinstance(box, Area):
		box = box.toAbsTuple()

	config = """ --tessdata-dir "C:\\Users\\timon\\Desktop\\tesseract\\tessdata" --psm 4 """
	if pricesonly:
		config += "-c tessedit_char_whitelist=\\'iskISK0123456789. "

	processedimg = ImageGrab.grab(box).convert('L')
	if treshfilter:
		thresh = 125
		fn = lambda x : 255 if x > thresh else 0
		processedimg = processedimg.convert('L').point(fn, mode='1')
	processedimg = processedimg.resize((processedimg.width * 4, processedimg.height * 4))
	processedimg = ImageOps.invert(processedimg)
	processedimg = processedimg.filter(ImageFilter.GaussianBlur(1.8))
	processedimg = processedimg.filter(ImageFilter.UnsharpMask(5.7, 340, 10))
	processedimg = processedimg.filter(ImageFilter.GaussianBlur(0.9))
	processedimg.save('imgs/screencapture.png')

	pytesseract.pytesseract.tesseract_cmd = 'C:\\Users\\timon\\Desktop\\tesseract\\tesseract.exe'
	ocr = pytesseract.image_to_data(Image.open('imgs/screencapture.png'), config=config)
	ocr = ocr.lower().split("\n",1)[1]
	return ocr

def buyorder(itemid, price, quantity):
	clickDetails()
	openItem(itemid)
	pyautogui.sleep(3)
	thing = pyautogui.locateOnScreen('imgs/placebuyorder.png')
	buyorderpos = Point( thing.left + thing.width / 2 , thing.top + thing.height / 2)
	clickPoint(buyorderpos)
	pyautogui.sleep(2)
	thing = pyautogui.locateOnScreen('imgs/buyorderadvanced.png')
	if thing != None:
		advanced = Point( thing.left + thing.width / 2 , thing.top + thing.height / 2)
		clickPoint(advanced)
		pyautogui.sleep(1)
	#make sure buy order is set to advanced
	#TODO implement advanced check
	thing = pyautogui.locateOnScreen('imgs/buyorderoriginpoint.png')
	bidpricefield = Point( thing.left + 143 , thing.top + 33)
	quantityfield = Point( thing.left + 143 , thing.top + 169)
	duration = Point( thing.left + 143 , thing.top + 190)
	threemonths = Point( thing.left + 143 , thing.top + 332)
	buything = pyautogui.locateOnScreen('imgs/buyandcancel.png')
	buybutton = Point( buything.left + 25 , buything.top + 7)
	clickPoint(bidpricefield, 2)
	pyautogui.sleep(0.1)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(str(price), interval=0.1)
	clickPoint(quantityfield, 2)
	pyautogui.sleep(0.1)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(str(quantity), interval=0.1)
	clickPoint(duration)
	clickPoint(threemonths)
	clickPoint(buybutton, 1)
	pyautogui.sleep(0.6)
	thing = pyautogui.locateOnScreen('imgs/confirmorder.png')
	confirmyes = Point( thing.left + 149 , thing.top + 197)
	clickPoint(confirmyes)

def openItem(itemid):
	itemname = getNameFromID(itemid)
	clickDetails()
	thing = pyautogui.locateOnScreen('imgs/browselistleft.png', 0.6)
	thing2 = pyautogui.locateOnScreen('imgs/search.png')
	search_market(itemname)
	pyautogui.sleep(0.3)
	searchareacapturepos = Area(thing.left, thing.top + 118, thing2.left - thing.left + 58, 400)

	pyautogui.sleep(1)

	for _ in range(5):

		ocr = grabandocr(searchareacapturepos)

		for s in ocr.splitlines()[1:]:
			if len(s.split()[-1]) > 1:
				if(s.split()[-1][:5] in itemname.lower()):
					offsetpos = searchareacapturepos
					mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
					mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
					clickxy(mousex, mousey)
					return

		#we only get here if it didnt find an item: the item must have been in a collapsed category
		for s in ocr.splitlines()[1:]:
			if len(s.split()[-1]) > 3:
				#we do NOT want to open the blueprint category
				if not "prints" in s and not "react" in s:
					offsetpos = searchareacapturepos
					mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
					mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
					clickxy(mousex, mousey)
					break
	print("looped through item opening 5 times without success, aborting")
	sys.exit()

def sellitemininventory(itemid, price):
	item = getNameFromID(itemid)
	clickPointPNG('imgs/inventorytopright.png', 0, 25, 2)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(item, interval=0.1)

	thing = pyautogui.locateOnScreen('imgs/inventoryitemhangar.png')
	inventorylist = Area(thing.left + 25, thing.top + 70, 1000, 250)

	pyautogui.sleep(1)

	box = inventorylist.toAbsTuple()
	ocr = grabandocr(box)

	for s in ocr.splitlines()[1:]:
		if(s.split()[-1][:5] in item.lower()):
			offsetpos = inventorylist
			mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
			mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
			clickxy(mousex, mousey, clicks=1, right=True)
			pyautogui.sleep(0.2)

			box = (mousex + 15,mousey + 2 ,mousex + 15 + 135, mousey + 3 + 200)
			ocr = grabandocr(box)

			for s in ocr.splitlines()[1:]:
				if(s.split()[-1] == "sell"):
					mousex = mousex + 18 + int(s.split()[6]) / 4 + 5
					mousey = mousey + 3 + int(s.split()[7]) / 4 + 5
					clickxy(mousex, mousey)
					pyautogui.sleep(5)
					thing = pyautogui.locateOnScreen('imgs/sellitems.png')
					#quantityfield = Point( thing.left + thing.width / 2 , thing.top + 60) we dont need quantity, we always sell all items, todo maybe change this when you want multiple orders
					pricefield = Point( thing.left + thing.width / 2 , thing.top + 80)
					thing = pyautogui.locateOnScreen('imgs/sellitemsellcancel.png')
					sellbutton = Point( thing.left + 25, thing.top + 12)
					thing = pyautogui.locateOnScreen('imgs/sellitemduration.png')
					durationfield = Point( thing.left - 50 , thing.top + 28)

					#set duration to 3 months
					clickPoint(durationfield)
					clickxy(durationfield.x, durationfield.y + 145)

					#set price
					pyautogui.moveTo(pricefield.x, pricefield.y)
					pyautogui.sleep(0.1)
					pyautogui.doubleClick(pricefield.x, pricefield.y)
					pyautogui.typewrite(['backspace'])
					pyautogui.typewrite(str(price), interval=0.1)

					clickPoint(sellbutton)
					pyautogui.sleep(0.5)
					thing = pyautogui.locateOnScreen('imgs/sellitemconfirm.png')
					confirmbutton = Point( thing.left +145 , thing.top + 193)
					clickPoint(confirmbutton)

					return

class Point:
	def __init__(self, xin, yin):
		self.x = xin
		self.y = yin
	def toTuple(self):
		return (self.x, self.y)

class Area:
	def __init__(self, xin, yin, win, hin):
		self.x = xin
		self.y = yin
		self.width = win
		self.height = hin
	def toTuple(self):
		return (self.x, self.y, self.width, self.height)
	def toAbsTuple(self):
		return (self.x, self.y, self.x + self.width, self.y + self.height)

class Order:
	def __init__(self, typeid: int, bid: bool, price: float, volentered: int, volremaining: int, issuedate: int):
		self.typeid = typeid
		self.bid = bid
		self.price = price
		self.volentered = volentered
		self.volremaining = volremaining
		self.issuedate = issuedate
		#i only need to uuid for getting order position, maybe this has more use?
		self.uuid = uuid.uuid4().hex
		self.finished = False
	def __str__(self):
		return "Order: " + str(self.__dict__)    
	def __repr__(self):
		return "Order: " + str(self.__dict__) + "\n" 
	def canChange(self):
		return (getEVETimestamp() - self.issuedate) > 300

def str2bool(string):
	string = string.strip().lower()
	if(isinstance(string, bool)):
		return string
	if(string == "True"):
		return True
	elif(string == "False"):
		return False
	else:
		print("wrong type for str2bool, got: " + str(type(string)) + ", aborting")
		sys.exit()

#call this every time you handle an itemhandler
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
			if(x.uuid == wantedorder.uuid):
				return (idx, len(buylist))
	else:
		for idx, x in enumerate(selllist):
			if(x.uuid == wantedorder.uuid):
				return (idx, len(selllist))
	print("couldnt find order: " + getNameFromID(wantedorder.typeid) + "  in getorderposition, aborting")
	sys.exit()
	



def buyItem(itemhandler):
	buyprice = getItemPrices(itemhandler.typeid)[0]
	buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
	quantity = itemhandler.volume
	print("itemhandler initiating initialbuyorder: " + str(itemhandler.typeid) + " , " + str(buyprice) + " , " + str(quantity))
	buyorder(itemhandler.typeid, buyprice, quantity)
	itemhandler.buyorder = Order(itemhandler.typeid, True, buyprice, quantity, quantity, getEVETimestamp())
	#todo check if we need refreshordercache here

def sellItem(itemhandler):
	sellPrice = getItemPrices(itemhandler.typeid)[1]
	sellPrice  = round(sellPrice - random.random() / 7 - 0.01, 2)
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
	itemhandler.sellorderlist.append(Order(itemhandler.typeid, False, sellPrice, quantity, quantity, getEVETimestamp()))
	#todo check if we need refreshordercache here

def refreshUnprofitable(itemhandler):
	prices = getItemPrices(itemhandler.typeid)
	priceratio = prices[1] / prices[0]
	#todo maybe make a settings file for this
	itemhandler.unprofitable = (priceratio < 1.2)

def checkAndUnderBid(itemhandler):
	prices = getItemPrices(itemhandler.typeid)
	#manage buyorders
	if itemhandler.buyorder is not None and itemhandler.buyorder.canChange():
		curPrice = prices[0]
		print("curprice of item called \"" + getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
		if(curPrice > float(itemhandler.buyorder.price)):
			print("weve been overbid!")
			position, itemsinlist = getOrderPosition(itemhandler.buyorder)
			newprice = round(curPrice + random.random() / 7 + 0.01, 2)
			print("bidding for newprice: " + str(newprice))
			changeOrder(itemhandler.buyorder, newprice, position, itemsinlist)
	#manage sellorders
	#TODO! implement not overbidding yourself when you have 2 sell orders
	if itemhandler.sellorderlist:
		for sellorder, idx in enumerate(itemhandler.sellorderlist):
			if sellorder.canChange():
				curPrice = prices[1]
				print("curprice of item called \"" + getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
				if(curPrice < float(sellorder.price)):
					print("weve been overbid!")
					position, itemsinlist = getOrderPosition(sellorder)
					newprice = round(curPrice - random.random() / 7 - 0.01, 2)
					print("bidding for newprice: " + str(newprice))
					changeOrder(sellorder, newprice, position, itemsinlist)
					itemhandler.sellorderlist[idx] = neworder

#todo implement rebuying items, that have been bought and sold faster, more often than other items
#general rule: every item can only ever have 2 orders belonging to it
class ItemHandler:
	def __init__(self, typeid: int, investition: float, volume: int):
		self.typeid = typeid
		self.investition = investition
		#todo check for rounding errors in volume
		self.volume = volume
		self.unprofitable = False
		self.buyorder = None
		self.sellorderlist = []

	def handle(self):
		refreshOrders(self)
		#check unprofitable, cancel buyorder if it is
		refreshUnprofitable(self)
		if(self.unprofitable):
			return
		#we place buyorder when there are no orders
		if not self.buyorder and not self.sellorderlist:
			buyItem(self)
			return
		#we only sell half of bought once per item cycle
		if self.buyorder is not None:
			if (self.buyorder.volremaining < (self.buyorder.volentered / 2) and not self.sellorderlist) or self.buyorder.finished:
				sellItem(self)
				if self.buyorder.finished:
					self.buyorder = None
		#check if all sellorders are done
		if all(order.finished for order in self.sellorderlist):
			sellorderlist = []
		#update prices
		checkAndUnderBid(self)



			
			


