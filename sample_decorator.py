def hello_goodbye(func):

    def wrapper(*args):
        print "Entering {0} with args {1}".format(func.__name__, args)
        return_value = func(*args)
        print "Exiting {0}".format(func.__name__)

        return return_value

    return wrapper
