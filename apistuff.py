import grequests
import json
import asyncio
import common as cm
from aiohttp import ClientSession
import variables
import orderstuff
import math
import quickbar
import pyautogui
from logging import info as print

async def agetNameFromID(typeid):
	async with ClientSession() as session:
		async with session.get("https://www.fuzzwork.co.uk/api/typeid.php?typeid=" + str(typeid)) as response:
			repo = await response.read()
			rsjson = json.loads(repo)
			return str(rsjson['typeName'])

def getNameFromID(typeid):
	try:
		loop = asyncio.get_event_loop()
		future = asyncio.ensure_future(agetNameFromID(typeid))
		typename = loop.run_until_complete(future)
		loop.close
	except:
		print("failed to get info from fuzzwork, retrying in 15s")
		pyautogui.sleep(15)
		return getNameFromID(typeid)
	return typename

class SimpleOrder:
	def __init__(self, typeid: int, is_buy_order: bool, price: float):
		self.typeid = typeid
		self.is_buy_order = is_buy_order
		self.price = price

class SimpleItem:
	def __init__(self, typeid: int, highestbuy: float, lowestsell: float):
		self.typeid = typeid
		self.highestbuy = highestbuy
		self.lowestsell = lowestsell
		self.volume = 0
		self.buycount = 0
		self.sellcount = 0

	def margin(self):
		if self.highestbuy == -1 or self.lowestsell == -1:
			return 0
		return (self.lowestsell - self.highestbuy) / self.lowestsell

def collectItems():
	page = 1
	pagemultiple = 50
	allorders = []
	running = True
	while running:
		urls = []
		for i in range(page, page + pagemultiple):
			urls.append("https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&page=" + str(i))
		rs = (grequests.get(u) for u in urls)
		allresponses = grequests.map(rs)
		while (any(r.status_code != 200 for r in allresponses)):
			print("received non 200 status code")
			rs = (grequests.get(u) for u in urls)
			allresponses = grequests.map(rs)
		for response in allresponses:
			rsjson = None
			try:
				rsjson = response.json()
			except:
				print("json decode in collectitems wasn't perfect")
				print(response.text)
			if not rsjson:
				running = False
				break
			for order in rsjson:
				#todo only jita
				if(order['location_id'] == 60003760):
					allorders.append(SimpleOrder(int(order['type_id']), str(order['is_buy_order']) == "True", float(order['price'])))
		page += pagemultiple
	simpleitemlist = []
	#have fun understanding this
	for i in range(0,60000):
		simpleitemlist.append(SimpleItem(i,-1,-1))
	for order in allorders:
		si = simpleitemlist[order.typeid]
		if order.is_buy_order:
			si.buycount += 1
			if (si.highestbuy < order.price or si.highestbuy == -1):
				si.highestbuy = order.price
		if not order.is_buy_order:
			si.sellcount += 1
			if (si.lowestsell > order.price or si.lowestsell == -1):
				si.lowestsell = order.price
			
	return simpleitemlist

async def fetch(item, session):
	async with session.get("https://esi.evetech.net/latest/markets/10000002/history/?datasource=tranquility&type_id=" + str(item.typeid)) as response:
		repo = await response.read()
		try:
			rsjson = json.loads(repo)
		except:
			print("failed to load volume for item: " + str(item.__dict__))
			return item
		vol = 0
		for day in range(len(rsjson) - 14, len(rsjson)):
			try:
				vol += rsjson[day]['volume']
			except:
				break
		item.volume = int(vol / 14)
		return item


async def getResponses(simpleitemlist):
	tasks = []

	#keep connection alive for all requests
	async with ClientSession() as session:
		for i in simpleitemlist:
			task = asyncio.ensure_future(fetch(i, session))
			tasks.append(task)

		items = await asyncio.gather(*tasks)
		simpleitemlist.sort(key=lambda x: x.volume, reverse=True)
		return items

def setItemVolumes(simpleitemslist):
	loop = asyncio.get_event_loop()
	future = asyncio.ensure_future(getResponses(simpleitemslist))
	simpleitemslist = loop.run_until_complete(future)
	loop.close

def fetchItemHandlers():
	quickbar.clear()
	itemhandlerlist = variables.itemhandlerlist

	print("old ihl:")
	print(itemhandlerlist)

	for idx, ih in enumerate(itemhandlerlist):
		if(isinstance(ih, cm.ItemHandler)):
			if(ih.unprofitable):
				itemhandlerlist[idx] = cm.ItemHandler(-1,-1,-1);

	print("new ihl:")
	print(itemhandlerlist)

	leftoveritemhandlerlist = [ih for ih in itemhandlerlist if isinstance(ih, cm.LeftoverItemHandler)]

	while ( len(itemhandlerlist) - len(leftoveritemhandlerlist) ) < 8:
		itemhandlerlist.append(cm.ItemHandler(-1,-1,-1))

	print("fetching tradable items...")
	simpleitems = collectItems()
	gooditems = []
	for si in simpleitems:
		#multiply minmargin by 1.15 so items that are close to minmargin don't get cut off due to unprofitability very fast
		#todo make setting for 1.15
		if(variables.maxmargin > si.margin() > variables.minmargin * 1.15):
			if(si.lowestsell - si.highestbuy > variables.minpricediff):
				#we dont want items which aren't populated with orders
				if(si.buycount > variables.minordercount and si.sellcount > variables.minordercount):
					gooditems.append(si)
	setItemVolumes(gooditems)
	tradableitems = []
	for si in gooditems:
		if(si.volume > 30000):
			namefromid = getNameFromID(si.typeid)
			if(namefromid == "bad item"):
				print("got a bad item with id: " + str(si.typeid))
				continue
			print("name: " + namefromid + ", margin: " + str(si.margin()) + ", volume: " + str(si.volume))
			#todo
			#there are some items like tungsten which will generate a lot of search results and the ocr cant deal with that
			if(namefromid == "Tungsten"):
				continue
			tradableitems.append(si)

	realitems = []
	for ti in tradableitems:
		print("checking tradable item: " + getNameFromID(ti.typeid))
		quickbar.addItemToQuickbar(ti.typeid)
		goodprices = orderstuff.getGoodPrices(ti.typeid)
		buyprice = goodprices[0]
		ti.highestbuy = goodprices[0]
		ti.lowestsell = goodprices[1]
		if(buyprice == -1):
			print("no good prices")
			continue
		pricemargin = (goodprices[1] - goodprices[0]) / goodprices[1]
		#the api isn't fresh all the time so it can happen that items get into this list that arent profitable
		if (pricemargin < variables.minmargin * 1.15):
			continue
		#we dont wan't items that are already in ihl
		if any(ih.typeid == ti.typeid for ih in itemhandlerlist):
			continue
		realitems.append(ti)
		if(len(realitems) > 10):
			break
	print("adding itemhandlers...")
	importancesum = 0
	idx = 0
	for ti in realitems[:variables.maxhandlers]:
		#items that have high volume and high margin will get get traded more
		importancesum += ti.volume * ti.margin()
	print(importancesum)
	for ri in realitems:
		if(all(ih.typeid != -1 for ih in itemhandlerlist)):
			break
		if itemhandlerlist[idx].typeid == -1:
			print("initiating itemhandler: " + getNameFromID(ri.typeid))
			capitalpercentage = (ri.volume * ri.margin()) / importancesum
			investition = variables.capital * capitalpercentage
			volume = math.ceil(investition / ri.highestbuy)
			itemhandlerlist[idx] = cm.ItemHandler(ri.typeid, investition, volume)
		idx += 1