import datetime

"""
    Class for making a log for REST requests.

    Author: Michael de Winter
"""
def append_message(message):
      print(str(datetime.datetime.now())+": "+str(message))
      with open("log.txt", "a") as myfile:
                myfile.write(str(datetime.datetime.now())+": "+str(message)+"\n")
import sys
import logging


"""
Logger settings init.

Author: Michael de Winter
"""

def init_logger():

    debug = logging.DEBUG
    logger = logging.getLogger('NSO-logger')

    #logging.basicConfig(format='%(asctime)s;%(levelname)s;%(module)s;%(message)s', stream=sys.stdout, level=debug)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('NSO-logger.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
   
    return logger