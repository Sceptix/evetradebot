import time
import sys
import pyautogui
from MyUtils import *
import apistuff
from dateutil.parser import parse as DateUtilParser
from apistuff import *
import uuid

class Order:
	def __init__(self, typeid: int, bid: bool, price: float, volentered: int, volremaining: int, issuedate: int):
		self.typeid = typeid
		self.bid = bid
		self.price = price
		self.volentered = volentered
		self.volremaining = volremaining
		self.issuedate = issuedate
		#i only need to uuid for getting order position, maybe this has more use?
		self.uuid = uuid.uuid4().hex
		self.finished = False
	def __str__(self):
		return "Order: " + str(self.__dict__)    
	def __repr__(self):
		return "Order: " + str(self.__dict__) + "\n" 
	def canChange(self):
		return (getEVETimestamp() - self.issuedate) > 300

def getOrderPosition(itemhandlerlist, wantedorder):
	orderlist = []
	#collect all orders which arent finished
	for ih in itemhandlerlist:
		if ih.buyorder is not None and not ih.buyorder.finished:
			orderlist.append(ih.buyor)
		if ih.sellorderlist:
			for so in ih.sellorderlist:
				if not so.finished:
					orderlist.append(so)
	#splitting the orderlist into buy and sellorders
	buylist = []
	selllist = []
	#sort by boughtat, which is also the standard sorting in eve's my orders
	#todo implement check to look if "expires in" is sorted in the correct direction (oldest first)
	orderlist.sort(key=lambda x: x.issuedate, reverse=False)
	for order in orderlist:
		if(order.isbuy):
			buylist.append(order)
		else:
			selllist.append(order)
	if (wantedorder.bid):
		#todo replace this for x shit with enumerate
		for x in range(len(buylist)):
			if(buylist[x].uuid == wantedorder.uuid):
				return x
	else:
		for x in range(len(selllist)):
			if(selllist[x].uuid == wantedorder.uuid):
				return x
	print("couldnt find order: " + getNameFromID(order.typeid) + "  in getorderposition, aborting")
	sys.exit()
		
def cancelBuyOrder(itemhandler, itemhandlerlist):
	buyorderpos = getOrderPosition(itemhandlerlist, itemhandler.buyorder)
	print("cancelling buyorder: " + getNameFromID(itemhandler.typeid))
	clickMyOrders()
	clickPointPNG('imgs/myordersbuying.png', 100, 22 + (20 * buyorderpos), clicks=1, right=True)
	pyautogui.sleep(0.2)
	pyautogui.move(40, 115)
	pyautogui.click()

def str2bool(string):
	string = string.strip().lower()
	if(isinstance(string, bool)):
		return string
	if(string == "True"):
		return True
	elif(string == "False"):
		return False
	else:
		print("wrong type for str2bool, got: " + str(type(string)) + ", aborting")
		sys.exit()

def refreshOrders(itemhandlerlist):
	oldorders = []
	for ih in itemhandlerlist:
		if ih.buyorder is not None:
			oldorders.append(ih.buyor)
		if ih.sellorderlist:
			oldorders += ih.sellorderlist
	clickMyOrders()
	pyautogui.sleep(0.3)
	clickPointPNG('imgs/myordersexport.png', 10, 10)
	pyautogui.sleep(1)
	marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
	logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
	neworders = []
	with open(logfile) as export:
		reader = csv.DictReader(export)
		for l in reader:
			#todo check if indexes are right
			neworders.append(Order(int(l['typeID']), str2bool(l['bid']), float(l['price']),
						   int(l['volentered']), int(l['volremaining']), DateUtilParser(l['issuedate']).timestamp()))
	os.remove(logfile)
 	#the neworder list will contain every order even finished ones, the itemhandler will remove those in its handle func
 	for oo in oldorders:
		if not any(oo.typeid == no.typeid for no in neworders):
			oo.finished = True
			neworders.append(oo)
	#sort each neworder back into their itemhandler
	for no in neworders:
		for ih in itemhandlerlist:
			if(ih.typeid == no.typeid):
				if no.bid:
					ih.buyorder = no
				else:
					ih.sellorderlist = []
					ih.sellorderlist.append(no)

	

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
	itemhandler.unprofitable = (priceratio < 1.2)

def checkAndUnderBid(itemhandler):
	prices = getItemPrices(itemhandler.typeid)
	#manage buyorders
	curPrice = prices[0]
	print("curprice of item called \"" + getNameFromID(itemhandler.typeid) + "\" is: " + str(curPrice))
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
	def __init__(self, typeid: int, investition: float, volume: int):
		self.typeid = typeid
		self.investition = investition
		self.volume = volume
		self.unprofitable = False
		self.buyorder = None
		self.sellorderlist = []

	def handle(self):
		#check unprofitable, cancel buyorder if it is
		refreshUnprofitable(self)
		if(self.unprofitable and self.buyorder is not None and self.buyorder.canChange()):
			cancelBuyOrder(self, #TODO GET ITEMHANDLERLIST HERE SOMEHOW)
			return
		#we place buyorder when there are no orders
		if not self.buyorder and not self.sellorderlist:
			buyItem(self)
			return
		#we only sell half of bought once per item cycle
		if self.buyorder is not None:
			if (self.buyorder.volremaining < (self.buyorder.volentered / 2) and not self.sellorderlist) or self.buyorder.finished:
				sellItem(self)
				if self.buyorder.finished:
					self.buyorder = None
		#check if all sellorders are done
		if all(order.finished for order in self.sellorderlist):
			sellorderlist = []
		#update prices

			
			


