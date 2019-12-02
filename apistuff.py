import requests
import json
import time
import settings

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

class ProfitableType:
	def __init__(self, typeid: int, buyprice: float, sellprice: float, ppi: float, ratio: float):
		self.typeid = typeid
		self.buyprice = buyprice
		self.sellprice = sellprice
		self.ppi = ppi
		self.ratio = ratio
	def __str__(self):
		return "ProfitableType: " + str(self.__dict__)    
	def __repr__(self):
		return __str__(self)

def getAllTypeIDs():
	page = 1
	typeids = []
	running = True
	while running:
		response = requests.get("https://esi.evetech.net/latest/markets/10000002/types/?datasource=tranquility&page=" + str(page))
		if not response.json():
			running = False
		else:
			typeids += response.json()
			page += 1
	return typeids

#todo make this faster with threading or async or using the order pages idk
def getAllProfitableTypes(typeids):
	profitabletypelist = []
	for typeid in typeids:
		prices = getItemPrices(typeid)
		if prices is not None:
			ratio = prices[1] / prices[0]
			if ratio > settings.profitableratio:
				pt = ProfitableType(typeid, prices[0], prices[1], prices[1] - prices[0], ratio)
				profitabletypelist.append(pt)
	return profitabletypelist

# station trading api routine:
#     get all order pages
#     in there are orders with itemtypes
#     collect for all item types
#     then get volume for all item types where margin is big enough