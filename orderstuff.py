class Order:
    def __init__(self, name, price, duration, isbuy):
        self.name = name
        self.price = price
        self.duration = duration
        self.isbuy = isbuy
    def __str__(self):
        return "Order: " + str(self.__dict__)    
    def __repr__(self):
        return "Order: " + str(self.__dict__) + "\n" 
    