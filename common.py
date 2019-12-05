import orderstuff
import pyautogui

def getEVETimestamp():
    return datetime.now(timezone('GMT')).replace(tzinfo=None).timestamp()

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
	def __str__(self):
		return "Order: " + str(self.__dict__)    
	def __repr__(self):
		return self.__str__(self)
	def canChange(self):
		return (getEVETimestamp() - self.issuedate) > 300

#todo implement rebuying items, that have been bought and sold faster, more often than other items
#general rule: every item can only ever have 2 orders belonging to it
class ItemHandler:
	def __init__(self, typeid: int, investition: float, volume: int):
		self.typeid = typeid
		self.investition = investition
		self.volume = volume
		self.unprofitable = False
		self.buyorder = None
		self.sellorderlist = []

	def handle(self):
		orderstuff.refreshOrders(self)
		#check unprofitable, cancel buyorder if it is
		orderstuff.refreshUnprofitable(self)
		if(self.unprofitable):
			return
		#we place buyorder when there are no orders
		if not self.buyorder and not self.sellorderlist:
			buyItem(self)
			return
		#we only sell half of bought once per item cycle
		if self.buyorder is not None:
			if (self.buyorder.volremaining < (self.buyorder.volentered / 2) and not self.sellorderlist) or self.buyorder.finished:
				orderstuff.sellItem(self)
				if self.buyorder.finished:
					self.buyorder = None
		#check if all sellorders are done
		#finished is false if its not finished
		if all(order.finished for order in self.sellorderlist):
			sellorderlist = []
		#update prices
		orderstuff.checkAndUnderBid(self)


def clickPoint(point, clicks=1, right=False):
	pyautogui.moveTo(point.x, point.y)
	pyautogui.sleep(0.2)
	if right:
		pyautogui.click(button='right', clicks=clicks)
	else:
		pyautogui.click(clicks=clicks)

def clickPointPNG(pngname, leftoffset, topoffset, clicks=1, right=False):
	thing = pyautogui.locateOnScreen(pngname, confidence=0.9)
	if thing is None:
		print("couldnt click png: " + pngname)
		return
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
	#todo find a better way to handle this
	print("looped through item opening 5 times without success, aborting")
	sys.exit()