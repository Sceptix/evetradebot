import orderstuff
import pyautogui
import sys
import math
import apistuff as api
from PIL import ImageGrab, ImageFilter, ImageOps
import pytesseract
from difflib import SequenceMatcher
from pytz import timezone
from datetime import datetime
import variables
import pyperclip


def getEVETimestamp():
	return datetime.now(timezone('GMT')).replace(tzinfo=None).timestamp()

def sleep(time):
	pyautogui.sleep(variables.sleepmultiplier * time)

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
	def __init__(self, typeid: int, orderid: int, bid: bool, price: float, volentered: int, volremaining: int, issuedate: int):
		self.typeid = typeid
		self.orderid = orderid
		self.bid = bid
		self.price = price
		self.volentered = volentered
		self.volremaining = volremaining
		self.issuedate = issuedate
		self.finished = False
		self.hasbeenoverbid = False
	def __str__(self):
		return str(self.__dict__)
	def __repr__(self):
		return str(self.__dict__)
	def canChange(self):
		return (getEVETimestamp() - self.issuedate) > 296

#general rule: every item can only ever have 2 orders belonging to it

#TODO! dynamic itemhandler amount, because there are rarely 16 orders

class ItemHandler:
	def __init__(self, typeid: int, investition: float, volume: int):
		self.typeid = typeid
		self.investition = investition
		self.volume = volume
		self.unprofitable = False
		self.buyorder = None
		self.sellorderlist = []
		self.unprofitabledate = -1

	def clearOrders(self):
		self.buyorder = None
		self.sellorderlist = []

	def handle(self, nomorebuy=False):
		orderstuff.refreshAllOrders()

		goodprices = orderstuff.getGoodPrices(self.typeid)
		#check unprofitable, cancel buyorder if it is
		orderstuff.refreshUnprofitable(self, goodprices)
		if self.unprofitable and self.unprofitabledate == -1:
			self.unprofitabledate = getEVETimestamp()
		else:
			self.unprofitabledate = -1
		#we can only cancel if it has been unprofitable for 20 minutes
		if(self.unprofitable and self.buyorder is not None and (getEVETimestamp() - self.unprofitabledate > 1200)):
			print("cancelling itemhandler: " + api.getNameFromID(self.typeid) + "'s buyorder due to unprofitability")
			orderstuff.cancelOrder(self.buyorder)
			print("trying to sell itemhandler: " + api.getNameFromID(self.typeid) + "'s purchases")
			orderstuff.sellItem(self, goodprices)
			if len(self.sellorderlist) == 0:
				print("didn't have any purchases, fetching new itemhandlers from api...")
				api.fetchItemHandlers()
			return
		#we only sell half of bought once per item cycle
		if self.buyorder is not None and not self.unprofitable:
			if (self.buyorder.volremaining < (self.buyorder.volentered / 2) and not self.sellorderlist) or self.buyorder.finished:
				orderstuff.sellItem(self, goodprices)
				if self.buyorder.finished:
					self.buyorder = None
		#we place buyorder when there are no orders
		if not nomorebuy:
			if not self.buyorder and not self.sellorderlist and not self.unprofitable:
				orderstuff.buyItem(self, goodprices)
				return
		#check if all sellorders are done
		#finished is false if its not finished
		if len(self.sellorderlist) > 0 and all(order.finished == True for order in self.sellorderlist) and self.buyorder is None:
			self.sellorderlist = []
			print("itemhandler went through full trade cycle")
			if self.unprofitable and (getEVETimestamp() - self.unprofitabledate > 3600):
				print("fetching new itemhandlers from api...")
				api.fetchItemHandlers()
				return
			else:
				print("increasing volume by 5%...")
				self.volume = math.ceil(self.volume * 1.05)
		
		#update prices
		orderstuff.checkAndUnderBid(self, goodprices)

def clickPoint(point, clicks=1, right=False):
	pyautogui.moveTo(point.x, point.y)
	sleep(0.2)
	if right:
		pyautogui.click(button='right', clicks=clicks)
	else:
		pyautogui.click(clicks=clicks)

pointcache = {}


#todo this just looks awful
def clickPointPNG(pngname, leftoffset, topoffset, clicks=1, right=False, cache=False):
	if cache:
		point = None
		if pngname in pointcache:
			point = pointcache[pngname]
			point = Point(point.x + leftoffset, point.y + topoffset)
		else:
			thing = pyautogui.locateOnScreen(pngname, confidence=0.9)
			if thing is not None:
				point = Point(thing.left, thing.top)
				pointcache[pngname] = point
				point = Point(thing.left + leftoffset, thing.top + topoffset)
		if point is not None:
			clickPoint(point, clicks, right)
	else:
		thing = pyautogui.locateOnScreen(pngname, confidence=0.9)
		if thing is not None:
			clickPoint(Point(thing.left + leftoffset, thing.top + topoffset), clicks, right)

def clickxy(x, y, clicks=1, right=False):
	pyautogui.moveTo(x, y)
	sleep(0.1)
	if right:
		pyautogui.click(button='right', clicks=clicks)
	else:
		pyautogui.click(clicks=clicks)

def getAPandLH(bid):
	if bid:
		thing = actingpointthing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		buylisttopleft = Point(thing.left - 6969, thing.top + 39)
		thing = pyautogui.locateOnScreen('imgs/myordersbuyingbottomleft.png', confidence=0.9)
		buylistbottomleft = Point(thing.left - 6969, thing.top - 8)
		listheight = buylistbottomleft.y - buylisttopleft.y	+ 3
	else:
		thing = actingpointthing = pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9)
		selllisttopleft = Point(thing.left - 6969, thing.top + 39)
		thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
		selllistbottomleft = Point(thing.left - 6969, thing.top - 10)
		listheight = selllistbottomleft.y - selllisttopleft.y + 3
	actingPoint = Point(actingpointthing.left + 26, actingpointthing.top + 40)
	return (actingPoint, listheight)

def safetypewrite(text):
	while True:
		pyautogui.keyDown('ctrl')
		pyautogui.keyDown('a')
		sleep(0.3)
		pyautogui.keyUp('a')
		pyautogui.keyUp('ctrl')
		pyautogui.typewrite(['backspace'])
		pyautogui.typewrite(str(text), interval=0.04)
		sleep(0.1)
		pyautogui.keyDown('ctrl')
		pyautogui.keyDown('a')
		sleep(0.3)
		pyautogui.keyUp('a')
		pyautogui.keyUp('ctrl')
		sleep(0.1)
		pyautogui.keyDown('ctrl')
		pyautogui.keyDown('c')
		sleep(0.5)
		pyautogui.keyUp('c')
		pyautogui.keyUp('ctrl')
		sleep(0.5)
		realtext = pyperclip.paste()
		print(realtext)
		if(str(text) == str(realtext)):
			return

def exportMyOrders():
	clickPointPNG('imgs/marketorders.png', 6, 6, cache=True)
	sleep(0.2)
	pyautogui.move(10, 22)
	pyautogui.click()

def similar(a, b):
	return SequenceMatcher(None, a, b).ratio()

def grabandocr(box):
	if isinstance(box, Area):
		box = box.toAbsTuple()
	config = " --tessdata-dir "
	config += '"' + variables.tesseractpath + "tessdata" + '"' + " --psm 4"

	processedimg = ImageGrab.grab(box).convert('L')
	processedimg = processedimg.resize((processedimg.width * 4, processedimg.height * 4))
	processedimg = ImageOps.invert(processedimg)
	processedimg = processedimg.filter(ImageFilter.GaussianBlur(1.8))
	processedimg = processedimg.filter(ImageFilter.UnsharpMask(5.7, 340, 10))
	processedimg = processedimg.filter(ImageFilter.GaussianBlur(0.9))

	pytesseract.pytesseract.tesseract_cmd = variables.tesseractpath + "tesseract.exe"
	ocr = pytesseract.image_to_data(processedimg, config=config)
	ocr = ocr.lower().split("\n",1)[1]
	return ocr

