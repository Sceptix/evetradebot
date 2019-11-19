import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
from MyUtils import *
from apistuff import *
from orderstuff import *
import random
#ideas
#random time differences for not getting banned
#internal clock, orders are renewable every 5 minutes each


#start the trading day

#close undock window

try:
    clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
    print("who cares")
    
#create buy orders for items that havent got one yet
orderlist = []
#150 million, todo keep track of this differently
usercapital = 1 * 10**4

with open('openorders.csv') as orders:
    data = list(csv.reader(orders, delimiter=','))
    for x in data:
        orderlist.append(Order(x[0], x[1], x[2], x[3]))

#todo implement saving the refreshed order list
print(orderlist)
orderlist, soldorders = refreshOrders(orderlist)
print(soldorders)
print(orderlist)

def saveOrderList():
    f = open('openorders.csv', "w")
    for order in orderlist:
        f.write(order.csvdump() + "\n")
    f.close()
    
#every item in items.csv
tradinglist = []

with open('items.csv') as items:
    data = list(csv.reader(items, delimiter=','))
    totalvolume = 0
    totalvolume += sum(int(x[1]) for x in data)
    for row in data:
        itemname = row[0]
        tradinglist.append(itemname)
        if(any(x for x in orderlist if x.name == itemname)):
            print("item " + itemname + " already in orders, skipping")
            continue
        itempercentage = int(row[1]) / totalvolume
        print(itemname)
        print(itempercentage)
        unordereditems = []
        #we only get here if we dont have a buy order with that item name yet
        purchasetotal = usercapital * itempercentage
        buyprice = getItemPrices(itemname)[0]
        buyprice = round(buyprice + random.random() / 7 + 0.01, 2)
        quantity = int(purchasetotal / buyprice)
        print(str(itemname) + " , " + str(buyprice) + " , " + str(quantity))
        buyorder(itemname, buyprice, quantity)
        orderlist.append(Order(itemname, buyprice, True, time.time()))
        saveOrderList()
        
#make sure every order is renewable
sleep(300)

#todo remember not to overbid yourself

#underbid order loop logic


    
def doSoldOrders(curitem, soldorders):
    for x in soldorders:
        if(curitem == x.name):
            lowestSellPrice = getItemPrices(curitem)[1]
            lowestSellPrice  = round(lowestSellPrice - random.random() / 7 - 0.01, 2)
            sellitemininventory(curitem, lowestSellPrice)
            sleep(random.randint(4,6))
            return True
    return False

def getOrderPosition(itemname, orderlist, isItemBuy):
    #sort by bought at, which is also the standard sorting in eve's my orders
    buylist, selllist = []
    #todo check if i dont have to sort buylist and sellist seperately after
    #splitting the orderlist into buy and sellorders
    orderlist.sort(key=lambda x: x.boughtat, reverse=False)
    for order in orderlist:
        if(buyorder.isbuy()):
            buylist.append(order)
        else:
            selllist.append(order)
    if (isItemBuy):
        for x in range(len(buylist)):
            if(buylist[x].name == itemname):
                return x
    else:
        for x in range(len(selllist)):
            if(selllist[x].name == itemname):
                return x
    print("couldnt find item in getorderposition, aborting")
    sys.exit()

def checkAndUnderBid(item, orderlist):
    for x in orderlist:
        if x.isbuy:
            curPrice = getItemPrices(x.name)[0]
            if(curPrice > x.price):
                position = getOrderPosition(item, orderlist, True)
                newprice = round(curPrice + random.random() / 7 + 0.01, 2)
                changeOrder(True, newprice, position)
        else:
            curPrice = getItemPrices(x.name)[1]
            if(curPrice < x.price):
                position = getOrderPosition(item, orderlist, False)
                newprice = round(curPrice - random.random() / 7 +- 0.01, 2)
                changeOrder(False, newprice, position)

#i need a function that goes through every order
#looking at the saved order price and comparing it with the api order price
#if the api order price is higher, that means somebody else overbid me
#so i have to update the order

for i in range(1000 + random.randint(-21, 25)):
    for item in tradinglist:
        startticktime = time.time()
        time.sleep(12)
        orderlist, soldorders = refreshOrders(orderlist)
        #if the current items buy order was fulfilled, we make a sell order and
        #go to the next item in the tradinglist
        if(doSoldOrders(item, soldorders)):
            continue
        checkAndUnderBid(item, orderlist)
        
        
                

    time.sleep(12)
    orderlist, soldorders = refreshOrders(orderlist)

start = time.time()
#changeOrder(orderlist[0], 7347.5, 0)
#sellitemininventory("proteins", 1235.29)
#buyorder("occult s", 15, 5)
#orderlist.append(Order("occult s", 15, True, time.time()))
#saveOrderList()
orderlist = refreshOrders(orderlist)
end = time.time()
print(end-start)


#print(getItemPrices("amarr Titan"))



#changeSellOrder("Spirits", 407.02)






#implement internal bookkeeping in buyorder function
#buyorder("yan jung glass scale", 1, 1)


#search_market("occult s", screenpositions[0])