# RUTIFU - Random Utilities That I Find Useful

import syslog
import os
import time
import threading
import traceback
import json
import socket
import inspect

################################################################################
# Logging and debugging
################################################################################
sysLogging = True
# Optionally import app specific configuration
try:
    from debugConf import *
except ImportError:
    pass
# Log a message to syslog or stdout
def log(*args):
    message = ""
    for arg in args:
        message += arg.__str__()+" "
    if sysLogging:
        syslog.syslog(message)
    else:
        print(time.strftime("%b %d %H:%M:%S")+" "+message)
# Log the traceback for an exception
def logException(name, exception):
    tracebackLines = traceback.format_exception(None, exception, exception.__traceback__)
    log(name+":")
    for tracebackLine in tracebackLines:
        log(tracebackLine)
# Log a debug message conditioned on a specified global variable
def debug(*args):
    if (args[0] in globals()) and globals()[args[0]]:  # only log if the specified debug variable is True
        log(*args[1:])
# Log a stack trace conditioned on a specified global variable
def debugTraceback(debugType, debugName):
    try:
        if (debugType in globals()) and globals()[debugType]:  # only log if the specified debug variable is True
            s = inspect.stack()
            for f in s:
                log(debugName, f[1], f[2], f[3], f[4])
    except KeyError:
        pass

################################################################################
# Thread and process
################################################################################
# Thread object that logs a stack trace if there is an uncaught exception
class LogThread(threading.Thread):
    def __init__(self, name, target, notify=None, **kwargs):
        super().__init__(name=name, target=target, **kwargs)
        self.runTarget = self.run   # save the target that was specified
        self.run = self.logTarget   # set the target to the wrapper target
        self.notify = notify
    # wrapper to catch exceptions in the target
    def logTarget(self, *args, **kwargs):
        try:
            self.runTarget(*args, **kwargs)        # run the specified target
        except Exception as exception:
            logException("exception in thread "+self.name, exception)
            if self.notify:         # optional callback for notification
                self.notify(self.name, str(exception))
# Convenience function to create and start a thread
def startThread(name, target, notify=None, **kwargs):
    thread = LogThread(name, target, notify, **kwargs)
    thread.start()
    return thread
# Block a thread indefinitely
def block():
    while True:
        time.sleep(1)
# Wait until the network is available
def waitForNetwork(host):
    networkUp = False
    wasWaiting = False
    while not networkUp:
        try:
            hostAddr = socket.gethostbyname(host)
            status = os.system("ping "+hostAddr+" -c1")
            if status == 0:
                networkUp = True
                break
            else:
                log("Waiting for network", status)
        except Exception as exception:
            log("Waiting for network", str(exception))
        wasWaiting = True
        time.sleep(1)
    if wasWaiting:
        log("Network is up")
    return

################################################################################
# Manipulation of strings and lists
################################################################################
# Transform a string of words into a camel case name
def camelize(words):
    return "".join([words.split()[0].lower()]+[part.capitalize() for part in (words.split()[1:])])
# Create a string of words from a camel case name
def labelize(name):
    words = ""
    for char in name:
        if words:
            if words[-1].islower() and (char.isupper() or char.isnumeric()):
                words += " "
        words += char.lower()
    return words.capitalize()
# Get the value of a json item from a file
def getValue(fileName, item):
    return json.load(open(fileName))[item]
# Turn an item into a list if it is not already
def listize(x):
    return x if isinstance(x, list) else [x]
# Truncate or pad a list into a fixed number of items
def fixedList(items, nItems, pad=None):
    return (items+nItems*[pad])[0:nItems]
# Format an E.164 phone number for display
def displayNumber(number):
    if number != "":
        return "%s %s-%s" % (number[2:5], number[5:8], number[8:])
    else:
        return ""
# Format a phone number as E.164
def e164number(number, defaultAreaCode="", defaultCountryCode="1"):
    number = ''.join(ch for ch in number if ch.isdigit())
    if len(number) == 7:
        number = defaultAreaCode+number
    if len(number) == 10:
        number = defaultCountryCode+number
    if len(number) == 11:
        number = "+"+number
    return number
