################################################################
# config.py parameters for jukebox                             #
################################################################
######   Copyright (c) Simon McKenna 11/325  Version 0.1  ######
################################################################
import logging
import os


################################################################
# Logging configuration
################################################################


# Log File debug levels
# logging.DEBUG     10
# logging.INFO      20
# logging.WARNING   30
# logging.ERROR     40
JBOX_PROD_LOGFILE = "/var/log/jbox/jbox.log"
JBOX_PROD_LOGLEVEL = logging.INFO
JBOX_PROD_LOGMODE = "PROD"
# How many Days to retain the logfile for 
LOG_FILE_RETENTION = 7   # Updatable in postgres Parameters

JBOX_DEV_LOGFILE = "logfile/bkstgsvc.log"
JBOX_DEV_LOGLEVEL  = logging.DEBUG

JBOX_LOGLEVEL      = JBOX_DEV_LOGLEVEL # Updatable in postgres Parameter
JBOX_LOGFILE       = JBOX_DEV_LOGFILE

# Jukebox Listener spotify expects to see either 7777 or 8888
JBOX_LISTENER_PORT = 8888
# JBOX_LISTENER_PORT = 7777
JBOX_LISTENER_ADDR = "127.0.0.1"
JBOX_CALLBACK_INTF = "/callback/"
JBOX_CLIENT_ID = "1001290845224629a9940fbc23bdec16"
JBOX_CLIENT_SECRET = "SET IN ENVIRONMENT VARIABLE"
JBOX_CALLBACK_URI=f"http://{JBOX_LISTENER_ADDR}:{JBOX_LISTENER_PORT}/{JBOX_CALLBACK_INTF}"

# CA BUNDLE for outbound web service https calls
REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

# Incoming IP ADDRESSES
VALIDATE_CLIENT_IP=1
ALLOWED_IP="127.0.0.0/24" 

# Authentication Token
JBOX_TOKEN = "DUMMY-VALUE"
JBOX_TOKEN_NAME = "X-JBOX-AUTH-TOKEN"

# Delay for the background scheduler
JBOX_SCHEDULER_DELAY = 2

# Global variable to hold the database filename
SQLDBNAME= "/home/jbox/jukebox.db"
# Global variable to hold the homepage filename
JBOX_HOME = 'static/jukebox.html'

def func_name():
    if 'JBOX_DEBUG' in os.environ:
        import traceback
        return traceback.extract_stack(None, 2)[0][2]
    else:
        return ""