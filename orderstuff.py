import time
import sys

class Order:
    def __init__(self, name, price, isbuy, boughtat):
        self.name = name
        self.price = price
        self.isbuy = isbuy
        self.boughtat = boughtat
    def __str__(self):
        return "Order: " + str(self.__dict__)    
    def __repr__(self):
        return "Order: " + str(self.__dict__) + "\n" 
    def canChange(self):
        return (time.time() - self.boughtat) > 300
    def change(self, newprice):
        if not canChange(self):
            print("tried changing order before possible")
            sys.exit()
        self.boughtat = time.time()
        self.price = newprice
    def csvdump(self):
        return str(self.name) + ', ' + str(self.price) + ', ' + str(self.isbuy) + ', ' + str(self.boughtat)