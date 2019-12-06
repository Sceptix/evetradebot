#todo make a readme with needed setup config
#disable agency and daily gifts show up on login
#make sure regional manager and inventory are big

import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
import apistuff as api
from orderstuff import *
import common
import variables
import random
import pickle

variables.init()

print("collecting tradable items...")
simpleitems = api.collectItems()
goodmarginsimpleitems = []
for si in simpleitems:
	if(variables.maxmargin > si.margin() > variables.minmargin):
		if(si.lowestsell - si.highestbuy > 1000):
			goodmarginsimpleitems.append(si)
api.setItemVolumes(goodmarginsimpleitems)
tradableitems = []
for si in goodmarginsimpleitems:
	#apparently this one doesnt get its volume set
	if(si.volume > 30000):
		print("id: " + str(si.typeid) + ", margin: " + str(si.margin()) + ", volume: " + str(si.volume))
		tradableitems.append(si)

#close undock window
cm.clickPointPNG('imgs/undock.png', 173, 3)

cm.clickMyOrders()
variables.bidaplh = cm.getAPandLH(True)
variables.sellaplh = cm.getAPandLH(False)

#todo delete this after testing, i only need this so it doesnt buy every item after restarting
with open('itemhandlers.csv', 'rb') as itemhandlersfile:
	try:
		variables.itemhandlerlist = pickle.load(itemhandlersfile)
	except EOFError:
		pass

print("initiating itemhandlers...")
volumesum = 0
for ti in tradableitems:
	volumesum += ti.volume
for ti in tradableitems:
	if(len(variables.itemhandlerlist) == 8):
		break
	print("initiating itemhandler: " + api.getNameFromID(ti.typeid))
	if not(any(ti.typeid == ih.typeid for ih in variables.itemhandlerlist)):
		variables.capitalpercentage = ti.volume / volumesum
		investition = variables.capital * variables.capitalpercentage
		buyprice = getGoodPrices(ti.typeid)[0]
		if(buyprice == -1):
			print("Warning, not adding itemhandler: " + api.getNameFromID(ti.typeid) + " because there is no good price.")
			continue
		volume = math.ceil(investition / buyprice)
		variables.itemhandlerlist.append(cm.ItemHandler(ti.typeid, investition, volume))

#todo delete this after testing, i only need this so it doesnt buy every item after restarting
with open('itemhandlers.csv', 'wb') as itemhandlersfile:
	pickle.dump(variables.itemhandlerlist, itemhandlersfile)


if(len(variables.itemhandlerlist) > 8):
	print("more than 8 item handlers wont work with an alpha account")
	sys.exit()

def connectionLost():
	cl = pyautogui.locateOnScreen("imgs/connectionlost.png", confidence=0.9)
	if(cl is not None):
		#we lost connection, click quit
		point = cm.Point(cl.left + 169, cl.top + 194)
		cm.clickPoint(point, 1)
		#wait six minutes for internet to come back
		pyautogui.sleep(360)
		cm.clickPointPNG("imgs/launchgroup.png", 10, 10)
		cm.clickPointPNG("imgs/playnow.png", 10, 10)
		#wait for game to start
		pyautogui.sleep(45)
		cm.clickxy(470, 420)
		pyautogui.sleep(45)
		#close undock window
		cm.clickPointPNG('imgs/undock.png', 173, 3)

#underbid order loop logic
#todo implement an ocr check when changing orders!!! (check if it clicked the right order)

#run for about 9 hours
tradedaystart = cm.getEVETimestamp()
while cm.getEVETimestamp() - tradedaystart < 3600 * 7.5:
	for itemhandler in variables.itemhandlerlist:
		connectionLost()
		refreshOrderCache(variables.itemhandlerlist)
		print("handling itemhandler: " + api.getNameFromID(itemhandler.typeid))
		time.sleep(random.random() * 3)
		itemhandler.handle()
		if(itemhandler.unprofitable):
			#cancel unprofitable buyorder
			print("cancelling itemhandler: " + api.getNameFromID(itemhandler.typeid) + "'s buyorder")
			cancelOrder(itemhandler.buyorder)
while cm.getEVETimestamp() - tradedaystart < 3600 * 9:
	print("cancelling all buyorders")
	for idx, ih in enumerate(variables.itemhandlerlist):
		cancelOrder(itemhandler.buyorder)
		if(not itemhandler.sellorderlist):
			#stop trading items that have sold out at this point
			del variables.itemhandlerlist[idx]
		connectionLost()
		itemhandler.handle()
print("cancelling all sellorders")
for idx, ih in enumerate(variables.itemhandlerlist):
	for so in ih.sellorderlist:
		print("Couldn't finish selling item called: " + api.getNameFromID(so.typeid))
		cancelOrder(so)
#clear these files
open('ordercache.csv', 'w').close()
open('itemhandlers.csv', 'w').close()
print("ended trading day")
#todo add an earnings report
