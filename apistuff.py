import grequests
import json
import time
import asyncio
import common as cm
from aiohttp import ClientSession

async def agetNameFromID(typeid):
	async with ClientSession() as session:
		async with session.get("https://www.fuzzwork.co.uk/api/typeid.php?typeid=" + str(typeid)) as response:
			repo = await response.read()
			rsjson = json.loads(repo)
			return str(rsjson['typeName'])

def getNameFromID(typeid):
	loop = asyncio.get_event_loop()
	future = asyncio.ensure_future(agetNameFromID(typeid))
	typename = loop.run_until_complete(future)
	loop.close
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
	simpleorderlist = []
	#have fun understanding this
	for i in range(0,60000):
		simpleorderlist.append(SimpleItem(i,-1,-1))
	for order in allorders:
		si = simpleorderlist[order.typeid]
		if order.is_buy_order and (si.highestbuy < order.price or si.highestbuy == -1):
			si.highestbuy = order.price
		if not order.is_buy_order and (si.lowestsell > order.price or si.lowestsell == -1):
			si.lowestsell = order.price
	return simpleorderlist

async def fetch(item, session):
	async with session.get("https://esi.evetech.net/latest/markets/10000002/history/?datasource=tranquility&type_id=" + str(item.typeid)) as response:
		repo = await response.read()
		try:
			rsjson = json.loads(repo)
		except:
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