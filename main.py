#todo make a readme with needed setup config
#disable agency and daily gifts show up on login
#make sure regional manager and inventory are big
#make sure "Cancel Order", "Market Export Information" and "Personal Market Export Information"
#are in Reset Settings -> Reset Supress Message settings
#quadruple check that expires in is sorted so the arrow points upwards
#make sure that the market window is spaced so "the forge" and "regional market" are on two different lines

import pyautogui
import os
import apistuff as api
from orderstuff import *
import common as cm
import variables

variables.init()

def guiinit():
	#close undock window
	cm.clickPointPNG('imgs/undock.png', 173, 3)
	if pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9) is None:
		cm.clickPointPNG('imgs/marketordersbutton.png', 10, 10, cache=True)
	#make regional market search results big so ocr can read better
	thing = pyautogui.locateOnScreen('imgs/search.png', confidence=0.9)
	pyautogui.moveTo(thing.left + 76, thing.top + 27)
	cm.sleep(0.3)
	pyautogui.dragRel(300, 0, 1, button='left')
	cm.sleep(1)
	variables.bidaplh = cm.getAPandLH(True)
	variables.sellaplh = cm.getAPandLH(False)

guiinit()

api.fetchItemHandlers()

loadOrders()

for ih in variables.itemhandlerlist:
	print(ih.__dict__)

def connectionLost():
	cl = pyautogui.locateOnScreen("imgs/connectionlost.png", confidence=0.9)
	if(cl is not None):
		#we lost connection, click quit
		point = cm.Point(cl.left + 169, cl.top + 194)
		cm.clickPoint(point, 1)
		#wait 20 minutes for internet to come back or eve to restart
		cm.sleep(1200)
		cm.clickPointPNG("imgs/launchgroup.png", 10, 10)
		cm.clickPointPNG("imgs/playnow.png", 10, 10)
		#wait for game to start
		cm.sleep(45)
		cm.clickxy(470, 420)
		cm.sleep(45)
		guiinit()

#underbid order loop logic

#run for about 9 hours
tradedaystart = cm.getEVETimestamp()
while cm.getEVETimestamp() - tradedaystart < 3600 * 7.5:
	for ih in variables.itemhandlerlist:
		priorlist = getPriorityItemhandlers()
		connectionLost()
		if priorlist:
			print("handling prioritised itemhandler: " + api.getNameFromID(priorlist[0]))
			priorlist[0].handle()
		print("handling itemhandler: " + api.getNameFromID(ih.typeid))
		ih.handle()

print("cancelling all buyorders")
for ih in variables.itemhandlerlist:
	if itemhandler.buyorder is not None:
		cancelOrder(itemhandler.buyorder)

while cm.getEVETimestamp() - tradedaystart < 3600 * 9:
	for ih in variables.itemhandlerlist:
		priorlist = getPriorityItemhandlers()
		connectionLost()
		if priorlist:
			print("handling prioritised itemhandler: " + api.getNameFromID(priorlist[0]))
			priorlist[0].handle()
		print("handling itemhandler: " + api.getNameFromID(ih.typeid))
		if ih.sellorderlist:
			ih.handle(nomorebuy=True)
print("cancelling all sellorders")
for idx, ih in enumerate(variables.itemhandlerlist):
	for so in ih.sellorderlist:
		print("Couldn't finish selling item called: " + api.getNameFromID(so.typeid))
		cancelOrder(so)
print("ended trading day")
#todo add an earnings report
