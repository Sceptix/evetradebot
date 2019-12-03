import grequests
import requests
import json
import time
import variables

def getItemID(name):
	response = requests.get("https://www.fuzzwork.co.uk/api/typeid.php?typename=" + name.replace(" ", "%20"))
	return int(response.json()['typeID'])

def getNameFromID(id):
	response = requests.get("https://www.fuzzwork.co.uk/api/typeid.php?typeid=" + str(id))
	return str(response.json()['typeName'])

#returns the highest buy and lowest sell price of an item with a given id
def getItemPrices(itemid):
	#todo add try catch
	response = requests.get("https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&type_id=" + str(itemid))
	if response.status_code != 200 or isinstance(response.json(), str):
		time.sleep(30)
		response = requests.get("https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&type_id=" + str(itemid))

	buyorders = []
	sellorders = []
	
	for order in response.json():
		if order['location_id'] == 60003760:
			if order['is_buy_order']:
				buyorders.append(float(order['price']))
			else:
				sellorders.append(float(order['price']))
	try:
		return (sorted(buyorders, reverse=True)[0], sorted(sellorders)[0])
	except IndexError:
		print("itemid: " + str(itemid) + " had no buy or no sell orders, returning none")
		return None

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

	def ratio(self):
		if self.highestbuy == -1 or self.lowestsell == -1:
			return 0
		return self.lowestsell / self.highestbuy

def collectItems():
	page = 1
	pagemultiple = 30
	allorders = []
	running = True
	while running:
		urls = []
		for i in range(page, page + pagemultiple):
			urls.append("https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&page=" + str(i))
		rs = (grequests.get(u) for u in urls)
		allresponses = grequests.map(rs)
		for response in allresponses:
			try:
				rsjson = response.json()
			except:
				print("json decode wasn't perfect")
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

#todo make this faster with threading or async or using the order pages idk
def setItemsWeeklyVolumes(simpleitemlist):
	seperatedlist = [simpleitemlist[x:x+10] for x in range(0, len(simpleitemlist),10)]
	for itempackage in seperatedlist:
		urls = []
		for item in itempackage:
			urls.append("https://esi.evetech.net/latest/markets/10000002/history/?datasource=tranquility&type_id=" + str(item.typeid))
		rs = (grequests.get(u) for u in urls)
		allresponses = grequests.map(rs)
		while (any(r.status_code != 200 for r in allresponses)):
			time.sleep(5)
			rs = (grequests.get(u) for u in urls)
			allresponses = grequests.map(rs)
		for response in allresponses:
			try:
				rsjson = response.json()
			except:
				print("json decode wasn't perfect")
			if not rsjson:
				return 0
			vol = 0
			for idx in range(0,8):
				try:
					vol += int(rsjson[idx]['volume'])
				except:
					pass
			item.volume = vol

	return simpleitemlist

# station trading api routine:
#     get all order pages
#     in there are orders with itemtypes
#     collect for all item types
#     then get volume for all item types where margin is big enough