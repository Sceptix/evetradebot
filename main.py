import mainwrapper
import multiprocessing
import variables
import time
import common as cm
import pyautogui
import sys
from logging import info as print
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename="logfile.txt", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    #need this for the sleep calls in cm.clickpoint
    variables.init()
    tradedaystart = cm.getEVETimestamp()
    process = multiprocessing.Process(target=mainwrapper.doTradeBot, args=(tradedaystart,))
    process.start()
    while True:
        try:
            if not process.is_alive():
                sys.exit()
            cl = pyautogui.locateOnScreen("imgs/connectionlost.png", confidence=0.9)
            if(cl is not None):
                process.terminate()
                print("we lost connection, initiating restart procedure")
                point = cm.Point(cl.left + 169, cl.top + 194)
                cm.clickPoint(point)
                #wait 20 minutes for internet to come back or eve to restart
                time.sleep(10)
                lg = pyautogui.locateOnScreen("imgs/launchgroup.png")
                pn = pyautogui.locateOnScreen("imgs/playnow.png")
                while (lg is None and pn is None):
                    cm.clickPointPNG("imgs/evetaskbar.png", 5, 5)
                    lg = pyautogui.locateOnScreen("imgs/launchgroup.png")
                    pn = pyautogui.locateOnScreen("imgs/playnow.png")
                    time.sleep(5)
                print("starting eve client")
                cm.clickPointPNG("imgs/launchgroup.png", 10, 10)
                cm.clickPointPNG("imgs/playnow.png", 10, 10)
                #wait for game to start
                time.sleep(45)
                print("clicking character")
                cm.clickxy(470, 420)
                time.sleep(45)
                print("starting bot")
                process = multiprocessing.Process(target=mainwrapper.doTradeBot, args=(tradedaystart,))
                process.start()
            time.sleep(5)
        except KeyboardInterrupt:
            sys.exit()
