#todo make a readme with needed setup config
#disable agency and daily gifts show up on login
#make sure regional manager and inventory are big

import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
from apistuff import *
from orderstuff import *
from variables import itemhandlerlist
import random
import pickle

def saveItemHandlers(itemhandlerlist):
    with open('itemhandlers.csv', 'w') as itemhandlersfile:
        pickle.dump(itemhandlerlist, itemhandlersfile)

simpleitems = collectItems()
print(simpleitems[47930].__dict__)
goodratiosimpleitems = []
for si in simpleitems:
	if(4 > si.ratio() > variables.profitableratio):
		goodratiosimpleitems.append(si)
setItemsWeeklyVolumes(goodratiosimpleitems)
time.sleep(5)
for si in goodratiosimpleitems:
	#apparently this one doesnt get its volume set
	if(si.typeid == 47930):
		print(si.__dict__)
	if(si.volume > 10000):
		print("id: " + str(si.typeid) + ", ratio: " + str(si.ratio()) + ", volume: " + str(si.volume))
sys.exit()

time.sleep(1)
ih = ItemHandler(17668,1,1)
ih.buyorder = Order(17668,True,1,1,1,0)
print(ih.buyorder)
sys.exit()
ihl = []
ihl.append(ih)
refreshOrderCache(ihl)
print(ih.buyorder)
checkAndUnderBid(ih)
print(ih.buyorder)



#close undock window
try:
	clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
	print("couldnt close undock window, was probably already closed")


#todo delete this after testing, i only need this so it doesnt buy every item after restarting
with open('itemhandlers.csv', 'r') as itemhandlersfile:
    itemhandlerlist = pickle.load(itemhandlersfile)

if(len(itemhandlerlist) > 8):
    print("more than 8 item handlers wont work with an alpha account")
    sys.exit()

#underbid order loop logic
#todo make it cancel the sell orders at the very end of day maybe?
#todo automatic loading from evetrade.space
#todo implement an ocr check when changing orders!!! (check if it clicked the right order)

#run for about 9 hours
tradedaystart = getEVETimestamp()
while getEVETimestamp() - tradedaystart < 3600 * 7.5:
	for itemhandler in itemhandlerlist:
		cl = pyautogui.locateOnScreen("imgs/connectionlost.png", confidence=0.9)
		if(cl is not None):
			#we lost connection, click quit
			point = Point(cl.left + 169, cl.top + 194)
			clickPoint(point, 1)
			#wait six minutes for internet to come back
			pyautogui.sleep(360)
			clickPointPNG("imgs/launchgroup.png", 10, 10)
			clickPointPNG("imgs/playnow.png", 10, 10)
			#wait for game to start
			pyautogui.sleep(45)
			clickxy(470, 420)
			pyautogui.sleep(45)
			#close undock window
			try:
				clickPointPNG('imgs/undock.png', 173, 3)
			except AttributeError:
				print("couldnt close undock window, was probably already closed")
		refreshOrderCache(itemhandlerlist)
		print("handling itemhandler: " + getNameFromID(itemhandler.typeid))
		time.sleep(random.random() * 3)
		itemhandler.handle()
		if(itemhandler.unprofitable):
			#cancel unprofitable buyorder
			print("cancelling itemhandler: " + getNameFromID(itemhandler.typeid) + "'s buyorder")
			cancelOrder(itemhandler.buyorder)
while getEVETimestamp() - tradedaystart < 3600 * 9:
	print("cancelling all buyorders")
	for idx, ih in enumerate(itemhandlerlist):
		cancelOrder(itemhandler.buyorder)
		if(not itemhandler.sellorderlist):
			#stop trading items that have sold out at this point
			del itemhandlerlist[idx]
		itemhandler.handle()
print("cancelling all sellorders")
for idx, ih in enumerate(itemhandlerlist):
	for so in ih.sellorderlist:
		cancelOrder(so)
print("ended trading day")
#todo add an earnings report
