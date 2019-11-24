import time
import sys
import pyautogui
import MyUtils

class Order:
	def __init__(self, typeid: int, bid: bool, price: float, volentered: int, volremaining: int, issuedate: int):
		self.typeid = typeid
		self.bid = bid
		self.price = price
		self.volentered = volentered
		self.volremaining = volremaining
		self.issuedate = issuedate
		self.finished = False
	def __str__(self):
		return "Order: " + str(self.__dict__)    
	def __repr__(self):
		return "Order: " + str(self.__dict__) + "\n" 
	def canChange(self):
		return (getEVETimestamp() - self.issuedate) > 300

def refreshOrders(itemhandlerlist):
	clickMyOrders()
	pyautogui.sleep(0.3)
	clickPointPNG('imgs/myordersexport.png', 10, 10)
	pyautogui.sleep(1)
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for line in reader:
			name = getNameFromID(line['typeID'])

	os.remove(logfile)

def buyItem(itemhandler):
	buyprice = getItemPrices(itemhandler.typeid)[0]
	buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
	quantity = itemhandler.volume
	print("itemhandler initiating initialbuyorder: " + str(itemhandler.typeid) + " , " + str(buyprice) + " , " + str(quantity))
	buyorder(itemhandler.typeid, buyprice, quantity)
	itemhandler.buyorder = Order(itemhandler.typeid, True, buyprice, quantity, quantity, getEVETimestamp())
	#todo replace this saveOrderList()

def sellItem(itemhandler):
	sellPrice = getItemPrices(itemhandler.typeid)[1]
	sellPrice  = round(sellPrice - random.random() / 7 - 0.01, 2)
	sellitemininventory(itemhandler.typeid, sellPrice)
	quantity = 0
	if itemhandler.buyorder.finished:
		quantity = itemhandler.buyorder.quantity
	else:
		quantity = itemhandler.buyorder.volentered - itemhandler.buyorder.volremaining
	itemhandler.sellorderlist.append(Order(itemhandler.typeid, False, sellPrice, quantity, quantity, getEVETimestamp()))
	#todo replace this saveOrderList()

def refreshUnprofitable(itemhandler):
    prices = getItemPrices(itemhandler.typeid)
	priceratio = prices[1] / prices[0]
	#todo maybe make a settings file for this
	if(priceratio < 1.2):
		#not profitable anymore because of taxes
		itemhandler.unprofitable = True

def checkAndUnderBid(itemhandler):
    prices = getItemPrices(itemhandler.typeid)
	#manage buyorders
	curPrice = prices[0]
	print("curprice of item called \"" + itemhandler. + "\" is: " + str(curPrice))
	if(curPrice > float(x.price)):
		print("weve been overbid!")
		position = getOrderPosition(item, orderlist.copy(), True)
		newprice = round(curPrice + random.random() / 7 + 0.01, 2)
		print("bidding for newprice: " + str(newprice))
		neworder = changeOrder(x, newprice, position)
		orderlist[idx] = neworder
	#manage sellorders
	curPrice = prices[1]
	print("curprice of item called \"" + item + "\" is: " + str(curPrice))
	if(curPrice < float(x.price)):
		print("weve been overbid!")
		position = getOrderPosition(item, orderlist.copy(), False)
		newprice = round(curPrice - random.random() / 7 +- 0.01, 2)
		print("bidding for newprice: " + str(newprice))
		neworder = changeOrder(x, newprice, position)
		orderlist[idx] = neworder

#todo implement rebuying items, that have been bought and sold faster, more often than other items
#general rule: every item can only ever have 2 orders belonging to it
class ItemHandler:
	def __init__(self, typeid: str, investition: float, volume: int):
		self.typeid = typeid
		self.investition = investition
		self.volume = volume
		self.unprofitable = False
		self.buyorder = None
		self.sellorderlist = []

	def handle(self):
		#check unprofitable
		
		#we place buyorder when there are no orders
		if not self.buyorder and not sellorderlist:
			buyItem(self)
			return
		#we only sell half of bought once per item cycle
		if self.buyorder is not None:
			if (self.buyorder.volremaining < (self.buyorder.volentered / 2) and not sellorderlist) or self.buyorder.finished:
				sellItem(self)
				if self.buyorder.finished:
					self.buyorder = None
		#check if all sellorders are done
		if all(order.finished for order in self.sellorderlist):
			sellorderlist = []
		#update prices

			
			


