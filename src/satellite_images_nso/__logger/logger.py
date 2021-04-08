import datetime

"""
    Class for making a log for REST requests.

    Author: Michael de Winter
"""
def append_message(message):
      print(str(datetime.datetime.now())+": "+str(message))
      with open("log.txt", "a") as myfile:
                myfile.write(str(datetime.datetime.now())+": "+str(message)+"\n")
