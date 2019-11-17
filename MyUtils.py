import pyautogui
from PIL import Image, ImageGrab, ImageFilter, ImageEnhance, ImageOps
import pytesseract



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

def buyorder(name, price, quantity):
	clickDetails()
	openItem(name)
	pyautogui.sleep(0.3)
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
	clickPoint(buybutton, 2)
	pyautogui.sleep(0.6)
	thing = pyautogui.locateOnScreen('imgs/confirmorder.png')
	confirmyes = Point( thing.left + 149 , thing.top + 197)
	clickPoint(confirmyes)

def openItem(itemname):
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
			print("first loop s: " + s)
			if(s.split()[-1] in itemname.lower()):
				offsetpos = searchareacapturepos
				mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
				mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
				clickxy(mousex, mousey)
				return

		#we only get here if it didnt find an item: the item must have been in a collapsed category
		for s in ocr.splitlines()[1:]:
			print("second loop s: " + s)
			if len(s.split()[-1]) > 3:
				#we do NOT want to open the blueprint category
				if not "prints" in s and not "react" in s:
					print("got here")
					offsetpos = searchareacapturepos
					mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
					mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
					clickxy(mousex, mousey)
					break
	print("looped through item opening 5 times without success, aborting")
	sys.exit()

def sellitemininventory(item, price):
	clickPointPNG('imgs/inventorytopright.png', 0, 25, 2)
	pyautogui.typewrite(['backspace'])
	pyautogui.typewrite(item, interval=0.1)

	thing = pyautogui.locateOnScreen('imgs/inventoryitemhangar.png')
	inventorylist = Area(thing.left + 25, thing.top + 70, 1000, 250)

	pyautogui.sleep(1)

	box = inventorylist.toAbsTuple()
	ocr = grabandocr(box)

	for s in ocr.splitlines()[1:]:
		print("first loop s: " + s)
		if(s.split()[-1] in item.lower()):
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
					pyautogui.sleep(1)
					thing = pyautogui.locateOnScreen('imgs/sellitems.png')
					#quantityfield = Point( thing.left + thing.width / 2 , thing.top + 60) we dont need quantity, we always sell all items, maybe change this when you want multiple orders
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