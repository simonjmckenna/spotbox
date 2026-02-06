################################################################
# jboxdbfunctions.py dnb inteface module for jukebox app       #
################################################################
######   Copyright (c) Simon McKenna 11/25  Version 0.1   ######
################################################################
import logging
logger=logging.getLogger(__name__)

import os
import config
import time
from config import func_name
from sqliteDb import sqliteDatabase
from threading import Thread, Lock

value_mutex = Lock()
track_mutex = Lock()


class jukeboxdb:

    sqldbname = None
    sqldb = None

################################################################
#### __init__ constructor
################################################################

    def __init__(self,sqldbname):
        logger.debug(f"EXEC {func_name()}()")
        self.sqldbname = sqldbname
        self.sqldb = sqliteDatabase(sqldbname)
        logger.debug(f"ENDS {func_name()}()")
  
################################################################
#### validate datbase is ok - connect/disconnect from it
#### to do - check number/names of tables as sanity check
################################################################
    def test(self):
        testCount = 0
        # Connect to Database 
        result,msg = self.connect()
        if result == False:
            # Connect failed
            msg = f"Failed to connect to database {self.sqldbname}"
            logger.error(f"ENDS {func_name()}() = {result},{msg}")
            return result,msg
        
        
        # update the start count
        data,msg = self.ReadValue("TestCount")
        if msg is None:
            if data is None:
                # Not found a value create it
                testCount = 0 
                logger.debug(f"---- INFO New testCount {testCount}")
            else:
                # Found an existing value -- query needs to be update
                testCount= int(data) + 1
                logger.debug(f"---- INFO Updated testCount {testCount}")
        else:  # Anything else is wrong 
                msg=f"ERROR have a problem with CONFIG TABLE for key testCount not single or no entries"
                result = False 
                logger.error(f"ENDS {func_name()}() = {result},{msg}")
                return result,msg

        result,msg = self.StoreValue("TestCount",f"{testCount}")
        if msg is not None:
            msg=f"ERROR updating testcount database entry: {msg}"
            result = False 
            logger.error(f"ENDS {func_name()}() = {result},{msg}")
            return result,msg

        
    
        # disconnect from Database 
        result,msg = self.disconnect()
        if result == False:
            # Connect failed
            msg = f"Failed to disconnect from database {self.sqldbname}"    

        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return result,msg

################################################################
#### connect to a sql database 
################################################################
    def connect(self):
        logger.debug(f"EXEC {func_name()}()")
        result,msg = self.sqldb.connect()
        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return result,msg    
    
################################################################
#### disconnect from a sql database 
################################################################
    def disconnect(self,commit=True):
        logger.debug(f"EXEC {func_name()}(commit={commit})")
        result = True
        if commit == True:
            result,msg = self.sqldb.commit()
            logger.debug(f"---- INFO commited transaction {result},{msg}")
        if result == True:
            result,msg = self.sqldb.disconnect()

        logger.debug(f"ENDS {func_name()}() = {result},{msg}")
        return result,msg  

################################################################
#### STore a value in the datbase config table
################################################################
    def StoreValue(self, key: str,valueStr: str):
        result = True
        msg = None 
        query = None
        logger.debug(f"EXEC {func_name()}( {key}, {valueStr})")

        data,msg = self.ReadValue(key)
        if msg is None:
            if data is None:
                # Not found a value query needs to be insert
                #query = f"INSERT INTO CONFIG (Key,Value) VALUES ('{key}','{valueStr}')"
                query = f"INSERT INTO CONFIG (Value,Key) VALUES ( ?,? )"
                logger.debug(f"---- INFO updating existing {key}")
            else:
                # Found an existing value -- query needs to be update
                #query = f"UPDATE CONFIG SET Value = '{valueStr}' WHERE Key = '{key}'"
                query = f"UPDATE CONFIG SET Value = ? WHERE Key = ?"
                logger.debug(f"---- INFO creating new {key}")
        else:  # Anything else is wrong 
                query = None
                msg=f"---- ERROR have a problem with CONFIG TABLE for key {key} not single or no entries"
                result = False 
    
        if query is not None:
            result,msg = self.sqldb.execute(query,(valueStr,key,),)

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg

################################################################
#### read a value from the databsae config table
################################################################
    def ReadValue(self, key: str):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}({key})")

        result,msg = self.sqldb.execute(f"SELECT Value FROM CONFIG WHERE Key = ? ",(key,),)

        # if we didn't have an error - fecth the data
        if result == True:
            data,msg = self.sqldb.fetchall()

            if msg is None:
                match (len(data)):
                    case 0:  # Not found
                        msg = None
                        result = None
                    case 1:  # exactly what we want
                        msg = None
                        result,*rest = data[0] 
                    case _:  # something not right
                        msg = f'ERROR found {len(data)} entries for key {key} in config store'
                        result = -2
                    
        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
################################################################
#### delete a value from the databsae config table
################################################################
    def deleteValue(self, key: str):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}({key})")

        result,msg = self.sqldb.execute(f"DELETE FROM CONFIG WHERE Key = ? ",(key,),)
                    
        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
################################################################
#### Queue a track 
################################################################
    def queueTrack(self,trackId,duration):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}()")

        # Have Track ID
        # Get STATUS
        status = "QUEUED"
        # Get the time we are queing this
        timeQueued = int(time.time())
        logger.debug(f"---- Queue Entry {trackId},{status},{duration},{timeQueued}")
        self.sqldb.execute("INSERT INTO CURRENTQUEUE (trackId,status,actiontime,Duration,QueueNumber) VALUES (? , ? , ? , ? ,NULL)",(trackId,status,timeQueued,duration,),)

        self.sqldb.commit()

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg


################################################################
#### Queue a track 
################################################################
    def getQueueLength(self):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}()")

        # find the queued rows         
        data,msg = self.sqldb.execute("SELECT QueueNumber FROM CURRENTQUEUE WHERE status ='QUEUED'")

        if msg is not None:
            logger.error(f"{func_name()}() SQL Query returned {msg} and {data} ")
            return None,msg
        
        data,msg = self.sqldb.fetchall()
        
        if msg is not None:
            logger.error(f"{func_name()}() SQL data fetch returned {msg} and {data} ")
            return None,msg
        
        queueLen = len (data)

        logger.debug(f"---- QueueLen ,{queueLen}")
        self.sqldb.commit()

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return queueLen,msg
    
################################################################
#### Read First track from Queue 
################################################################
    def pullFirstQueuedTrack(self):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}()")

        result,msg = self.sqldb.execute("SELECT trackId,status,actiontime,QueueNumber,duration FROM CURRENTQUEUE WHERE status = 'QUEUED' ORDER BY QueueNumber ASC LIMIT 1")

        if msg is None:
            data,msg = self.sqldb.fetchall()
            if msg is None:
                result = data
            else:
                result = False

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg

################################################################
#### Set identified track as finished
################################################################    
    def setTrackFinished(self,track_db):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}()")

        if track_db is None:
            # No current track playing in Database
            return result

        actiontime = int(time.time())
        Queuenumber = track_db['QueueNumber']

        result,msg = self.sqldb.execute("UPDATE CURRENTQUEUE SET status=?,actiontime=?  WHERE QueueNumber = ?",('FINISHED',actiontime,Queuenumber,),)
        if msg is None:
            data,msg = self.sqldb.fetchall()
            if msg is None:
                result = data
            else:
                result = False

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg      

################################################################
##### Set Track from QUeue's status. 
################################################################
    def setQueuedTrackStatus(self, Queuenumber, status):
        result = True
        msg = None
        logger.debug(f"EXEC {func_name()}()")

        actiontime = int(time.time())

        result,msg = self.sqldb.execute("UPDATE CURRENTQUEUE SET status=?,actiontime=?  WHERE QueueNumber = ?",(status,actiontime,Queuenumber,),)

        if msg is None:
            result = True
        else:
            result = False

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
################################################################
#### Get Playing Track
################################################################    
    def getPlayingTrack(self):
        result = 0
        msg = None
        data = None
        track = {}
        result = None
        logger.debug(f"EXEC {func_name()}()")

        result,msg = self.sqldb.execute("SELECT trackId,QueueNumber,duration,actiontime FROM CURRENTQUEUE WHERE status = 'PLAYING' ")

        if msg is not None:
            logger.debug("SQL QUERY Failed: {msg}")
            result = None
            logger.debug(f"ENDS {func_name()}() {result},{msg}")
            return result,msg            
        
        data,msg = self.sqldb.fetchall()

        if msg is not None:
            logger.debug("SQL RETRIEVAL Failed: {msg}")
            result = None
            logger.debug(f"ENDS {func_name()}() {result},{msg}")
            return result,msg            
                

        match (len(data)):
            case 0:  # Not found
                msg = None
                result = None
            case 1:  # exactly what we want
                msg = None
                track['trackid'],track['QueueNumber'],track['duration'],track['actiontime'],*rest = data[0] 
                result = track
            case _:  # something not right
                msg = f'ERROR found {len(data)} entries for PLAYING tracks in queue store'
                result = None

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
################################################################
####  initialiseTrackMetrics - add tracking for a played track
################################################################# 
    def initialiseTrackMetrics(self,track):
    # track = { "artist": track_artist, "title": track_title, "length": track_time, "image": track_image, "image_height": image_height, "image_width": image_width, "trackid": trackid, "message" : msg }
        result = None
        msg = None  
        logger.debug(f"EXEC {func_name()}({track})")

        with track_mutex:

            result,msg = self.sqldb.execute("SELECT trackid FROM TRACK WHERE trackid = ? ",(track['trackid'],),)
            
            if msg is not None:
                logger.error(f'ENDS {func_name()}() - TRACK DB access query failed: {msg}')
                return False
            
            result,msg = self.sqldb.fetchall()

            if msg is not None:
                logger.error(f'ENDS {func_name()}() - TRACK DB fetchall failed: {msg}')
                return False

            # the number of records we get back is what we need to look at.
            match (len(result)):
                case 0:
                    # Entry doesnt exist - add it
                    logger.debug(f"---- {func_name()}(){track['trackid']} - did not find track in database - adding")
                    result,msg = self.sqldb.execute("INSERT INTO TRACK (artist,title,duration,imageurl,trackid) VALUES ( ?,?,?,?,? )",(track['artist'],track['title'],track['length'],track['image'],track['trackid']),)
                case 1:
                    # entry already exists - update it 
                    logger.debug(f"---- {func_name()}(){track['trackid']}) - found track in database updating")
                    result,msg = self.sqldb.execute("UPDATE TRACK SET artist=?,title=?,duration=?,imageurl=? WHERE trackid = ? ",(track['artist'],track['title'],track['length'],track['image'],track['trackid']),)
                case _:
                    logger.error(f"ENDS {func_name()}() - unexpected in tracks returned with trackid {track['trackid']}")
                    return False
        
            if msg is not None:
                logger.error(f'---- {func_name()}() - updating TRACK DB: {msg}')
                return False

        logger.debug(f"ENDS {func_name()}() initialised track metrics for {track['trackid']}")
        return True

################################################################
####  updateTrackMetrics - add tracking for a played track
################################################################# 
    def updateTrackMetrics(self,trackid,actiontime):
        result = None
        msg = None  
        logger.debug(f"EXEC {func_name()}({trackid},{actiontime})")

        with track_mutex:
            result,msg = self.sqldb.execute("UPDATE TRACK SET playCount = playCount + 1 WHERE trackid = ? ",(trackid,),)

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg 
                      
################################################################
#### AddJBCredits - add a number of credits to the jukebox
#################################################################    
    def addJBCredits(self, numberofCredits):
        result = True
        msg = None
        data = ""
        credits =0
        logger.debug(f"EXEC {func_name()}()")

        with value_mutex:
            data,msg = self.readValue("jukeBoxCredits")

            if msg is None:
                result = True
            else:
                result = False

            credits = int(data)

            if numberofCredits > 0 :
                credits += numberofCredits 

            result,msg = self.StoreValue("jukeBoxCredits",f"{credits}")

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
################################################################
#### subJBCredits - - subtract a credit from the jukebox
#################################################################        
    def subJBCredit(self):
        result = True
        data = ""
        credits =0
        msg = None
        logger.debug(f"EXEC {func_name()}()")

        with value_mutex:
            data,msg = self.readValue("jukeBoxCredits")

            if msg is None:
                result = True
            else:
                result = False

            credits = int(data)

            if credits < 0 :
                credits = 0 
                result = False 
                msg = "Not Enough Credits"

            result,msg = self.StoreValue("jukeBoxCredits",f"{credits}")

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
################################################################# 
#### getJBCredits - get the julkebox credits
################################################################# 
    def getJBCredits(self):
        result = 0
        msg = None
        data = ""
        logger.debug(f"EXEC {func_name()}()")

        with value_mutex:
            data,msg = self.readValue("jukeBoxCredits")

        if msg is None:
            result = int(data)
        else:
            result = -1

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg