#todo make a readme with needed setup config
#disable agency and daily gifts show up on login
#make sure regional manager and inventory are big
#make sure "Cancel Order", "Market Export Information" and "Personal Market Export Information"
#are in Reset Settings -> Reset Supress Message settings
#quadruple check that expires in is sorted so the arrow points upwards
#make sure that the market window is spaced so "the forge" and "regional market" are on two different lines
#make tooltips delay very long, reject all chat requests, leave help channel

import pyautogui
import os
import apistuff as api
from orderstuff import *
import common as cm
import variables
import quickbar
import sys
from logging import info as print
import logging

def guiinit():
	#close undock window
	cm.clickPointPNG('imgs/undock.png', 173, 3)
	if pyautogui.locateOnScreen('imgs/myordersselling.png', confidence=0.9) is None:
		cm.clickPointPNG('imgs/marketordersbutton.png', 10, 10, cache=True)
	#make regional market search results big so ocr can read better
	thing = pyautogui.locateOnScreen('imgs/search.png', confidence=0.9)
	pyautogui.moveTo(thing.left + 75, thing.top + 27)
	cm.sleep(1)
	pyautogui.dragRel(300, 0, 1, button='left')
	cm.sleep(1)
	variables.bidaplh = cm.getAPandLH(True)
	variables.sellaplh = cm.getAPandLH(False)

def doTradeBot(tradedaystart):
	logging.basicConfig(level=logging.DEBUG, filename="logfile.txt", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
	variables.init()
	pyautogui.sleep(5)

	#todo implement check to look if "expires in" is sorted in the correct direction (lowest timestamp first)
	""" stuff = (a for a in pyautogui.locateAllOnScreen('imgs/expiresin.png') if a.left < 500)
	for a in stuff:
		print(a)"""

	quickbar.clear()
	quickbar.dontShow()
	pyautogui.sleep(1)
	guiinit()
	api.fetchItemHandlers()
	loadOrders()

	for ih in variables.itemhandlerlist:
		print(ih.__dict__)

	#underbid order loop logic

	#run for about 9 hours
	while cm.getEVETimestamp() - tradedaystart < 3600 * 7.5:
		for ih in variables.itemhandlerlist:
			priorlist = getPriorityItemhandlers()
			if priorlist:
				print("handling prioritised itemhandler: " + api.getNameFromID(priorlist[0]))
				priorlist[0].handle()
			print("handling itemhandler: " + api.getNameFromID(ih.typeid))
			ih.handle()

	print("cancelling all buyorders")
	for ih in variables.itemhandlerlist:
		if ih.buyorder is not None:
			cancelOrder(ih.buyorder)
			goodprices = getGoodPrices(ih.typeid)
			sellItem(ih, goodprices)

	while cm.getEVETimestamp() - tradedaystart < 3600 * 9:
		for ih in variables.itemhandlerlist:
			priorlist = getPriorityItemhandlers()
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
