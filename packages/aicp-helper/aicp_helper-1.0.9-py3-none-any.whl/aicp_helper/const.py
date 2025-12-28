import time

LOG_TAG = "[aicp-helper]"

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())