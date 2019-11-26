import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
from MyUtils import *
from apistuff import *
from orderstuff import *
import random
import pickle

def saveItemHandlers(itemhandlerlist):
    with open('itemhandlers.csv', 'w') as itemhandlersfile:
        pickle.dump(itemhandlerlist, itemhandlersfile)

#changeOrder(Order(69, True, 1.53, 1, 1, 1), 2, 13)

thing = pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9)
selllisttopleft = Point(thing.left + 74, thing.top + 16)
thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
selllistbottomleft = Point(thing.left + 74, thing.top - 7)
sellinglistheight = selllistbottomleft.y - selllisttopleft.y

thing = pyautogui.locateOnScreen('imgs/myordersbuying.png', confidence=0.9)
print(thing)
buylisttopleft = Point(thing.left + 74, thing.top + 16)
thing = pyautogui.locateOnScreen('imgs/myordersexport.png', confidence=0.9)
print(thing)
buylistbottomleft = Point(thing.left + 79, thing.top - 85)
buylistheight = buylistbottomleft.y - buylisttopleft.y
print(buylistheight)
print(sellinglistheight)


sys.exit()

#close undock window

try:
	clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
	print("couldnt close undock window, was pr7obably already closed")
	
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

#todo implement rebuying earlier, having sell and buy orders of the same type
#todo implement scrolling in myorders!!!! we may reach points where all 16 orders are sellorders
#rebuying items that sold out quickly more, not proportional to volume in items.csv
#todo make it only sell everything, no rebuying in the laste two or three hours, and delete the orders that didnt make it
#todo automatic loading from evetrade.space
#todo implement an ocr check when changing orders!!! (check if it clicked the right order)
#todo restart game when disconnect

#run for about 9 hours
tradedaystart = getEVETimestamp()
while getEVETimestamp() - tradedaystart < 3600 * 9:
	for itemhandler in itemhandlerlist:
		refreshOrderCache(itemhandlerlist)
		print("handling itemhandler: " + getNameFromID(itemhandler.typeid))
		time.sleep(random.random() * 7)
		itemhandler.handle()
		if(itemhandler.unprofitable):
			#cancel unprofitable buyorder
			cancelBuyOrder(itemhandler)
		