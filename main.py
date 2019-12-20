import mainwrapper
import multiprocessing
import variables
import time
import common as cm
import pyautogui
import sys

if __name__ == '__main__':
    process = multiprocessing.Process(target=mainwrapper.doTradeBot)
    process.start()
    while True:
        if not process.is_alive():
            sys.exit()
        cl = pyautogui.locateOnScreen("imgs/connectionlost.png", confidence=0.9)
        if(cl is not None):
            process.terminate()

            print("we lost connection, initiating restart procedure")
            point = cm.Point(cl.left + 169, cl.top + 194)
            cm.clickPoint(point, 1)
            #wait 20 minutes for internet to come back or eve to restart
            time.sleep(1200)
            cm.clickPointPNG("imgs/launchgroup.png", 10, 10)
            cm.clickPointPNG("imgs/playnow.png", 10, 10)
            #wait for game to start
            time.sleep(45)
            cm.clickxy(470, 420)
            time.sleep(45)
            
            process = multiprocessing.Process(target=mainwrapper.doTradeBot)
            process.start()
        time.sleep(10)
