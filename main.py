#todo make a readme with needed setup config
#disable agency and daily gifts show up on login
#make sure regional manager and inventory are big
#make sure "Cancel Order", "Market Export Information" and "Personal Market Export Information"
#are in Reset Settings -> Reset Supress Message settings
#quadruple check that expires in is sorted so the arrow points upwards

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

api.fetchItemHandlers()

for ih in variables.itemhandlerlist:
	print(ih.__dict__)

#close undock window
cm.clickPointPNG('imgs/undock.png', 173, 3)
pyautogui.sleep(1)
cm.clickMyOrders()
variables.bidaplh = cm.getAPandLH(True)
variables.sellaplh = cm.getAPandLH(False)

loadOrders()

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

#run for about 9 hours
tradedaystart = cm.getEVETimestamp()
while cm.getEVETimestamp() - tradedaystart < 3600 * 7.5:
	for itemhandler in variables.itemhandlerlist:
		connectionLost()
		print("handling itemhandler: " + api.getNameFromID(itemhandler.typeid))
		itemhandler.handle()

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
print("ended trading day")
#todo add an earnings report
