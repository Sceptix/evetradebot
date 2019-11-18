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

with open('items.csv') as items:
    data = list(csv.reader(items, delimiter=','))
    totalvolume = 0
    totalvolume += sum(int(x[1]) for x in data)
    for row in data:
        itemname = row[0]
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

#todo remember not to overbid yourself

#underbid order loop logic

#i need a function that goes through every order
#looking at the saved order price and comparing it with the api order price
#if the api order price is higher, that means somebody else overbid me
#so i have to update the order

#for i in range(1000 + random.randint(-51, 55)):
#    time.sleep()

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