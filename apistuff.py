import requests
import json
import time

def getItemID(name):
	response = requests.get("https://www.fuzzwork.co.uk/api/typeid.php?typename=" + name.replace(" ", "%20"))
	return int(response.json()['typeID'])

def getNameFromID(id):
	response = requests.get("https://www.fuzzwork.co.uk/api/typeid.php?typeid=" + str(id))
	return str(response.json()['typeName'])

#returns the highest buy and lowest sell price of an item with a given name
def getItemPrices(itemid):
	
	response = requests.get("https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&type_id=" + str(itemid))
	tries = 0

	while(isinstance(response.json(), str)):
		tries += 1
		response = requests.get("https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&type_id=" + str(itemid))
		time.sleep(5)
		if(tries > 5):
			print("eve api responding gibberish: " + response.json())

	buyorders = []
	sellorders = []
	
	for order in response.json():
		if order['location_id'] == 60003760:
			if order['is_buy_order'] == True:
				buyorders.append(float(order['price']))
			else:
				sellorders.append(float(order['price']))
	try:
		return (sorted(buyorders, reverse=True)[0], sorted(sellorders)[0])
	except IndexError:
		print("soo there either arent any buyorders or sellorders for this given item, thats kinda weird because we don't trade items with 0 volume")
		sys.exit()