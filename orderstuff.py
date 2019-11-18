import time
import sys

class Order:
    def __init__(self, name, price, isbuy):
        self.name = name
        self.price = price
        self.boughtat = time.time() 
        self.isbuy = isbuy
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