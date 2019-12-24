import common as cm
import apistuff as api
import pyautogui
from logging import info as print

itemlist = []

def show():
	cm.clickPointPNG('imgs/regionalmarkettopleft.png', 76, 58, cache=True)
	cm.sleep(0.5)

def dontShow():
	cm.clickPointPNG('imgs/regionalmarkettopleft.png', 25, 58, cache=True)
	cm.sleep(0.5)

def clear():
	show()
	cm.sleep(0.2)
	cm.clickPointPNG('imgs/resetquickbar.png', 5, 5)
	cm.sleep(0.5)
	cm.clickPointPNG('imgs/yesno.png', 5, 5)
	itemlist = []

def search_market(item):
	pos = pyautogui.locateOnScreen('imgs/search.png')
	pyautogui.moveTo(pos.left - 70, pos.top + pos.height / 2)
	pyautogui.doubleClick(pos.left - 70, pos.top + pos.height / 2)
	cm.safetypewrite(item)
	cm.sleep(0.3)
	pyautogui.moveTo(pos.left + pos.width / 2, pos.top + pos.height / 2)
	pyautogui.click(pos.left + pos.width / 2, pos.top + pos.height / 2)
	pyautogui.moveTo(200,10)

def addItemToQuickbar(typeid):
	dontShow()
	itemname = api.getNameFromID(typeid)
	pyautogui.moveTo(200,10)
	pyautogui.sleep(0.3)
	thing = pyautogui.locateOnScreen('imgs/regionalmarkettopleft.png', confidence=0.9)
	thing2 = pyautogui.locateOnScreen('imgs/search.png', confidence=0.9)
	if thing is None or thing2 is None:
		print("im blind")
		return addItemToQuickbar(typeid)
	search_market(itemname)
	cm.sleep(4)
	searchareacapturepos = cm.Area(thing.left, thing.top + 100, thing2.left - thing.left + 50, 400)

	for loopidx in range(20):
		ocr = cm.grabandocr(searchareacapturepos)
		ocrlines = ocr.splitlines()
		if loopidx == 10:
			search_market(itemname)
			cm.sleep(0.5)
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
			cursim = cm.similar(itemname.lower(), s)
			if cursim > highestsim:
				highestsim = cursim
				bestidx = stringdict[s]
		if (highestsim > 0.8):
			s = ocrlines[bestidx]
			print("found item in search results: " + s)
			offsetpos = searchareacapturepos
			mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
			mousey = offsetpos.y + int(s.split()[7]) / 4 + 5

			cm.clickxy(mousex, mousey)
			cm.sleep(1.5)

			thing = pyautogui.locateOnScreen('imgs/search.png', confidence=0.9)
			marketnamearea = cm.Area(thing.left + 158, thing.top + 14, 375, 30)
			ocr = cm.grabandocr(marketnamearea)
			marketname = ""
			for line in ocr.splitlines():
				if len(line.split()) > 11:
					marketname += line.split()[-1] + ' '
			marketname = marketname.strip()
			print("read marketname while adding item: " + marketname)
			if(cm.similar(marketname.lower(), itemname.lower()) < 0.8):
				print("clicked wrong item while adding, retrying")
				return addItemToQuickbar(typeid)

			cm.clickxy(mousex, mousey, right=True)
			cm.sleep(0.2)
			cm.clickxy(mousex + 52, mousey + 29)
			itemlist.append(itemname)
			itemlist.sort(key=str.lower)
			return

		if loopidx > 12:
			#we only get here if it didnt find an item: the item must have been in a collapsed category
			for s in ocr.splitlines():
				if(len(s.split()) > 11 and len(s.split()[-1]) > 3):
					#we do NOT want to open the blueprint category
					if not "prints" in s and not "react" in s:
						offsetpos = searchareacapturepos
						mousex = offsetpos.x + int(s.split()[6]) / 4 + 5
						mousey = offsetpos.y + int(s.split()[7]) / 4 + 5
						cm.clickxy(mousex, mousey)
						break
		cm.sleep(0.5)

	print("looped through item adding a lot without success, aborting")
	sys.exit()

def openItem(typeid):
	show()
	for idx, item in enumerate(itemlist):
		if api.getNameFromID(typeid) == item:
			print(idx * 20)
			cm.clickPointPNG('imgs/regionalmarkettopleft.png', 35, 81 + idx * 20, cache=True)
			return