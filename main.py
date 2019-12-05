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
from common import *
from variables import itemhandlerlist
import random
import pickle

simpleitems = collectItems()
goodmarginsimpleitems = []
for si in simpleitems:
	if(variables.maxmargin > si.margin() > variables.minmargin):
		if(si.lowestsell - si.highestbuy > 1000):
			goodmarginsimpleitems.append(si)
setItemVolumes(goodmarginsimpleitems)
tradableitems = []
for si in goodmarginsimpleitems:
	#apparently this one doesnt get its volume set
	if(si.volume > 30000):
		print("id: " + str(si.typeid) + ", margin: " + str(si.margin()) + ", volume: " + str(si.volume))
		tradableitems.append(si)

#todo delete this after testing, i only need this so it doesnt buy every item after restarting
with open('itemhandlers.csv', 'rb') as itemhandlersfile:
	itemhandlerlist = pickle.load(itemhandlersfile)

volumesum = 0
for ti in tradableitems:
	volumesum += ti.volume
for ti in tradableitems:
    if(len(itemhandlerlist) == 8):
		break
	if not(any(ti.typeid == ih.typeid for ih in itemhandlerlist)):
		capitalpercentage = ti.volume / volumesum
		investition = variables.capital * capitalpercentage
		buyprice = getGoodPrices(ih.typeid)[0]
		if(buyprice == -1):
			print("Warning, not adding itemhandler: " + getNameFromID(itemhandler.itemid) + " because there is no good price.")
			continue
		volume = math.floor(investition / topbuyorder.price)
		itemhandlerlist.append(ItemHandler(ti.typeid, investition, volume))

#todo delete this after testing, i only need this so it doesnt buy every item after restarting
with open('itemhandlers.csv', 'wb') as itemhandlersfile:
	pickle.dump(itemhandlerlist, itemhandlersfile)

#close undock window
try:
	clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
	print("couldnt close undock window, was probably already closed")

if(len(itemhandlerlist) > 8):
	print("more than 8 item handlers wont work with an alpha account")
	sys.exit()

def connectionLost():
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

#underbid order loop logic
#todo implement an ocr check when changing orders!!! (check if it clicked the right order)

#run for about 9 hours
tradedaystart = getEVETimestamp()
while getEVETimestamp() - tradedaystart < 3600 * 7.5:
	for itemhandler in itemhandlerlist:
		connectionLost()
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
		print("Couldn't finish selling item called: " + getNameFromID(so.typeid))
		cancelOrder(so)
print("ended trading day")
#todo add an earnings report
