################################################################
# db.py database module for jukebox application                #
################################################################
######   Copyright (c) Simon McKenna 11/25  Version 0.1   ######
################################################################
import logging
logger=logging.getLogger(__name__)

import os
import sqlite3
import config 
from config import func_name


class sqliteDatabase:

#### Class constructor 

    def __init__(self, dbfilename: str):
        logger.debug(f"EXEC {func_name()}({dbfilename})")
        self.dbfilename = dbfilename

        self._resetVars()
        logger.debug(f"ENDS {func_name()}() ")

    def _resetVars(self):
        self.connected = False
        self.connection = None
        self.cursor = None

    #### connect to the database 
    def connect(self):
        msg = None
        result = True
        logger.debug(f"EXEC {func_name()}()")
        try:
            self.connection = sqlite3.connect(self.dbfilename)
            self.connected = True
            self.cursor = self.connection.cursor()

        except sqlite3.Error as error:
            msg = f'SQL Error occurred -{error}'
            result = False

        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return  result,msg

    ####  execute a sql query against a connected database 
    def execute(self,sqlCommand,sqlArgs=None):
        msg = None
        result = True
        logger.debug(f"EXEC {func_name()}({sqlCommand},{sqlArgs})")
        if not self.connected:
            msg = f"SQL Database {self.dbfilename} not connected"
        else:
            try:
                if sqlArgs is None:
                    self.cursor.execute(sqlCommand)
                else:
                    self.cursor.execute(sqlCommand,sqlArgs)
                    
            except sqlite3.Error as error:
                msg = f'SQL Error occurred -{error}'
                result = False

        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return  result,msg

    ####  fetch the results of a query against the connected database 
    def fetchall(self):
        msg = None
        result = True
        logger.debug(f"EXEC {func_name()}()")
        if not self.connected:
            msg = f"SQL Database {self.dbfilename} not connected"
        else:
            try:
                result = self.cursor.fetchall()
    
            except sqlite3.Error as error:
                msg = f'SQL Error occurred -{error}'
                result = False
            
        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return  result,msg
    

    #### commit changes to the database
    def commit(self):
        msg = None
        result = True
        logger.debug(f"EXEC {func_name()}()")
        if not self.connected:
            msg = f"SQL Database {self.dbfilename} not connected"
        else:
        
            try:
                self.connection.commit()

            except sqlite3.Error as error:
                msg = f'SQL Error occurred -{error}'
                result = False

        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return  result,msg
    
    #### commit changes to the database
    def rollack(self):
        msg = None
        result = True
        logger.debug(f"EXEC {func_name()}()")
        if not self.connected:
            msg = f"SQL Database {self.dbfilename} not connected"
        else:
        
            try:
                self.connection.rollbackmit()

            except sqlite3.Error as error:
                msg = f'SQL Error occurred -{error}'
                result = False

        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return  result,msg
          

    #### disconnect from the database
    def disconnect(self):
        msg = None
        result = True
        logger.debug(f"EXEC {func_name()}()")
        if not self.connected:
            msg = f"SQL Database {self.dbfilename} not connected"
            return False,msg
        
        try:
            self.connection.close()

        except sqlite3.Error as error:
            msg = f'SQL Error occurred -{error}'
            result = False

        self._resetVars()
        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return  result,msg