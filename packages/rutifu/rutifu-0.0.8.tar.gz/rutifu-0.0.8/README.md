# RUTIFU - Random Utilities That I Find Useful

This is a set of Python routines that perform various functions that I find useful for multiple projects.

## Logging and debugging
#### Log a message to syslog or stdout
    log(*args)
#### Log the traceback for an exception
    logException(name, ex)
#### Log a debug message conditioned on a specified global variable
    debug(*args)

## Threads and processes
#### Thread object that logs a stack trace if there is an uncaught exception
    class LogThread(threading.Thread)
#### Convenience function to create and start a thread
    startThread(name, target, **kwargs)
#### Block a thread indefinitely
    block()
#### Wait until the network is available
    waitForDns(host)

## Manipulation of strings and lists
#### Transform a string of words into a camel case name
    camelize(words)
#### Create a string of words from a camel case name
    labelize(name)
#### Get the value of a json item from a file
    getValue(fileName, item)
#### Turn an item into a list if it is not already
    listize(x)
#### Truncate or pad a list into a fixed number of items
    fixedList(items, nItems, pad=None)
#### Format an E.164 phone number for display
    displayNumber(number)
#### Format a phone number as E.164
    e164number(number, defaultAreaCode="", defaultCountryCode="1")
