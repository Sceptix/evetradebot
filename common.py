import orderstuff
import pyautogui
import sys
import apistuff as api
from PIL import Image, ImageGrab, ImageFilter, ImageEnhance, ImageOps
import pytesseract
from difflib import SequenceMatcher
from pytz import timezone
from datetime import datetime
import variables
import pickle


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
		return (getEVETimestamp() - self.issuedate) > 300

#general rule: every item can only ever have 2 orders belonging to it
class ItemHandler:
	def __init__(self, typeid: int, investition: float, volume: int):
		self.typeid = typeid
		self.investition = investition
		self.volume = volume
		self.unprofitable = False
		self.buyorder = None
		self.sellorderlist = []

	def clearOrders(self):
		self.buyorder = None
		self.sellorderlist = []

	def handle(self, nomorebuy=False):
		print("handler: " + api.getNameFromID(self.typeid))
		allorders = []
		allorders += self.sellorderlist
		allorders.append(self.buyorder)
		print(allorders)
		orderstuff.refreshAllOrders()
		print("handler: " + api.getNameFromID(self.typeid))
		allorders = []
		allorders += self.sellorderlist
		allorders.append(self.buyorder)
		print(allorders)

		goodprices = orderstuff.getGoodPrices(self.typeid)
		#check unprofitable, cancel buyorder if it is
		orderstuff.refreshUnprofitable(self, goodprices)
		if(self.unprofitable and self.buyorder is not None and not self.sellorderlist):
			print("cancelling itemhandler: " + api.getNameFromID(self.typeid) + "'s buyorder due to unprofitability")
			orderstuff.cancelOrder(self.buyorder)
			print("selling itemhandler: " + api.getNameFromID(self.typeid) + "'s purchases")
			orderstuff.sellItem(self, goodprices)
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
		if len(self.sellorderlist) > 0 and all(order.finished == True for order in self.sellorderlist):
			sellorderlist = []
			print("itemhandler went through full trade cycle")
			if self.unprofitable:
				print("fetching new itemhandlers from api...")
				api.fetchItemHandlers()
				return
			else:
				print("increasing volume by 5%...")
				self.volume *= 1.05
		
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
		else:
			thing = pyautogui.locateOnScreen(pngname, confidence=0.9)
			if thing is not None:
				point = Point(thing.left + leftoffset, thing.top + topoffset)
				pointcache[pngname] = point
		if point is not None:
			clickPoint(point, clicks, right)
	else:
		thing = pyautogui.locateOnScreen(pngname, confidence=0.9)
		if thing is not None:
			clickPoint(Point(thing.left + leftoffset, thing.top + topoffset), clicks, right)

def clickxy(x, y, clicks=1, right=False):
	pyautogui.moveTo(x, y)
	sleep(0.2)
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

def exportMyOrders():
	clickPointPNG('imgs/marketorders.png', 6, 6)
	sleep(0.2)
	pyautogui.move(10, 22)
	pyautogui.click()

def search_market(item):
	pos = pyautogui.locateOnScreen('imgs/search.png')
	pyautogui.moveTo(pos.left - 70, pos.top + pos.height / 2)
	pyautogui.doubleClick(pos.left - 70, pos.top + pos.height / 2)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(item, interval=0.03)
	sleep(0.3)
	pyautogui.moveTo(pos.left + pos.width / 2, pos.top + pos.height / 2)
	pyautogui.click(pos.left + pos.width / 2, pos.top + pos.height / 2)

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

def openItem(typeid):
	itemname = api.getNameFromID(typeid)
	thing = pyautogui.locateOnScreen('imgs/regionalmarkettopleft.png', 0.6)
	thing2 = pyautogui.locateOnScreen('imgs/search.png')
	search_market(itemname)
	sleep(0.3)
	searchareacapturepos = Area(thing.left, thing.top + 100, thing2.left - thing.left + 50, 400)

	for loopidx in range(10):
		if loopidx > 5:
			search_market(itemname)
			sleep(0.3)
		sleep(1.2)
		ocr = grabandocr(searchareacapturepos)
		ocrlines = ocr.splitlines()[1:]
		if(len(ocrlines) == 0):
			#todo make this loop
			print("ocr detected nothing, returning")
			sys.exit()
		stringdict = {}
		curstring = ""
		for idx, s in enumerate(ocrlines):
			s = s.lower()
			if(len(s.split()) <= 11 or len(s.split()[-1]) < 2):
				if curstring:
					stringdict[curstring.strip()] = idx - 1
				curstring = ""
			else:
				curstring += s.split()[-1] + " "
			if (idx == len(ocrlines) - 1):
				stringdict[curstring.strip()] = idx - 1
		highestsim = -1
		bestidx = 0
		for s in stringdict:
			cursim = similar(itemname.lower(), s)
			if cursim > highestsim:
				highestsim = cursim
				bestidx = stringdict[s]
		if (highestsim > 0.5):
			s = ocrlines[bestidx]
			print("clicking s because similarity is over 0.5: " + s)
			offsetpos = searchareacapturepos
			mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
			mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
			clickxy(mousex, mousey)
			return

		#we only get here if it didnt find an item: the item must have been in a collapsed category
		for s in ocr.splitlines()[1:]:
			if(len(s.split()) > 11 and len(s.split()[-1]) > 3):
				#we do NOT want to open the blueprint category
				if not "prints" in s and not "react" in s:
					offsetpos = searchareacapturepos
					mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
					mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
					clickxy(mousex, mousey)
					break
	#todo find a better way to handle this
	print("looped through item opening ten times without success, aborting")
	sys.exit()