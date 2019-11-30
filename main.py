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
import random
import pickle

def saveItemHandlers(itemhandlerlist):
    with open('itemhandlers.csv', 'w') as itemhandlersfile:
        pickle.dump(itemhandlerlist, itemhandlersfile)

time.sleep(1)
ih = ItemHandler(17668,1,1)
ih.buyorder = Order(17668,True,1,1,1,0)
ihl = []
ihl.append(ih)
refreshOrderCache(ihl)
print(ih.buyorder)
checkAndUnderBid(ih)
print(ih.buyorder)

sys.exit()

#close undock window
try:
	clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
	print("couldnt close undock window, was probably already closed")
	
#create buy orders for items that havent got one yet
orderlist = []
#50 million, todo keep track of this differently
usercapital = 15 * 10**5

	
#itemhandler for every item in items.csv
itemhandlerlist = []

#buy all the items that havent been bought yet at start of trading day
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
			cancelBuyOrder(itemhandler)
while getEVETimestamp() - tradedaystart < 3600 * 9:
	for idx, ih in enumerate(itemhandlerlist):
		cancelBuyOrder(itemhandler)
		if(not itemhandler.sellorderlist):
			del itemhandlerlist[idx]
		itemhandler.handle()
	
