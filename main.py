import pyautogui
import pytesseract
import csv
import os
from PIL import Image, ImageGrab, ImageFilter, ImageOps
from MyUtils import *
from apistuff import *
from orderstuff import *
#ideas
#random time differences for not getting banned
#internal clock, orders are renewable every 5 minutes each
orderlist = []

#start the trading day

#close undock window

try:
    clickPointPNG('imgs/undock.png', 173, 3)
except AttributeError:
    print("who cares")



with open('openorders.csv') as orders:
    data = list(csv.reader(orders, delimiter=','))
    for x in data:
        orderlist.append(Order(x[0], x[1], x[2], x[3]))

with open('items.csv') as items:
    data = list(csv.reader(items, delimiter=','))
    totalvolume = 0
    totalvolume += sum(int(x[1]) for x in data)
    print(totalvolume)
    for row in data:
        print(row)
        itemname = row[0]
        itempercentage = int(row[1]) / totalvolume
        print(itemname)
        print(itempercentage)
        #bla bla if order exists go skip, but dont change the eprcenratages

def clickDetails():
    clickPointPNG('imgs/multibuy.png', 60, 3)

def clickMyOrders():
    clickPointPNG('imgs/multibuy.png', 160, 3)

def refreshOrders():
    clickMyOrders()
    clickPointPNG('imgs/myordersexport.png', 10, 10)
    pyautogui.sleep(1)
    marketlogsfolder = os.path.expanduser('~\\Documents\\EVE\\logs\\Marketlogs')
    logfile = marketlogsfolder + "\\" + os.listdir(marketlogsfolder)[-1]
    neworderlist = []
    with open(logfile) as export:
        reader = csv.DictReader(export)
        
        for line in reader:
            print("LINE: " + str(line))
            name = getNameFromID(line['typeID'])
            for x in orderlist:
                if x.name == name:
                    neworderlist.append(x)
    os.remove(logfile)
    #change the durations i guess?
    return neworderlist


refreshOrders()



#print(getItemPrices("amarr Titan"))


def changeBuyOrder(name, newprice):
    clickMyOrders()
    position = 5
    clickPointPNG('imgs/myordersbuying.png', 100, 22 + (20 * position), clicks=1, right=True)
    pyautogui.sleep(0.2)
    pyautogui.move(35, 10)
    pyautogui.click()
    pyautogui.sleep(0.2)
    pyautogui.typewrite(['backspace'])
    pyautogui.typewrite(str(newprice), interval=0.1)
    return
    pyautogui.typewrite(['enter'])

def changeSellOrder(name, newprice):
    clickMyOrders()
    position = 0
    clickPointPNG('imgs/myordersselling.png', 100, 22 + (20 * position), clicks=1, right=True)
    pyautogui.sleep(0.2)
    pyautogui.move(35, 10)
    pyautogui.click()
    pyautogui.sleep(0.2)
    pyautogui.typewrite(['backspace'])
    pyautogui.typewrite(str(newprice), interval=0.1)
    return
    pyautogui.typewrite(['enter'])

#changeSellOrder("Spirits", 407.02)


#sellitemininventory("proteins", 1235.29)



#implement internal bookkeeping in buyorder function
#buyorder("yan jung glass scale", 1, 1)


#search_market("occult s", screenpositions[0])