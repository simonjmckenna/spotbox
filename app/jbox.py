################################################################
# jbox.py main jukebox application                             #
################################################################
######   Copyright (c) Simon McKenna 11/25  Version 0.1   ######
################################################################
import logging
import logging.handlers

logger=logging.getLogger(__name__)

import config
from config import func_name
import os

# Are we in Debug 
if 'JBOX_DEBUG' in os.environ :
    # This is developement set the logfile and log level
    config.JBOX_LOGLEVEL      = config.JBOX_DBG_LOGLEVEL 
else:
    config.JBOX_LOGLEVEL      = config.JBOX_PROD_LOGLEVEL 

if 'FLASK_ENV' in os.environ :
    config.JBOX_LOGFILE       = config.JBOX_DEV_LOGFILE
else:
    config.JBOX_LOGFILE       = config.JBOX_PROD_LOGFILE 

# instantiate the logger, use the watched filehandler so logrotate works
logging.basicConfig( level=config.JBOX_LOGLEVEL,
                     format='%(asctime)s %(levelname)s LOG: %(message)s',
                     handlers=[ logging.handlers.TimedRotatingFileHandler(config.JBOX_LOGFILE, when='midnight', interval=1,backupCount=config.LOG_FILE_RETENTION ), logging.StreamHandler() ])
print("log init complete")


from flask import Flask, redirect, request, session, jsonify
from flask_session import Session
from threading import Thread, Lock
from types import SimpleNamespace

import json, requests
from  jboxdbfunctions import jukeboxdb
from jboxspotifyfunctions import jboxSpotify
from urllib.request import  Request, urlopen
from typing import NamedTuple

from jboxadmin import admin_route



app = Flask(__name__)
# add the Url paths this application supports 
app.register_blueprint(admin_route)

queue_wake_time = 0 
queue_mutex = Lock()

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


# Global Variable to hold the website URL
weburl = None
webport = None
# Global Variables caching data from database
playback_device_id=None
active_playlist_id=None
request_headers=[]



class urlHeader(NamedTuple):
    key: str
    value: str

################################################################
################################################################
@app.route('/')
def root_page():
    global active_playlist_id
    global playback_device_id
    global request_headers
    webdata = ""
    msg = None

    logger.debug(f"EXEC {func_name()}()")

    myjboxdb = jukeboxdb(config.SQLDBNAME)
    myjboxSpotify = jboxSpotify(session,False)

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        myjboxSpotify.getAccessToken(request.args.get("code"))
        return redirect('/')

    if not myjboxSpotify.validateAccessToken():
        # Step 1. Display sign in link when no token
        auth_url = myjboxSpotify.getAuthorizeUrl()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

     # Step 3. Signed in, display data
    myjboxSpotify.connect()

    # Connect to database
    myjboxdb.connect()
    
    # If there is no device assigned - try to read the name from the database
    if playback_device_id is None:
        logger.debug(f"---- {func_name()}() playback_device_id is None ")
        msg = getPlaybackDevice(myjboxdb,myjboxSpotify)

    # if there is no playlist assigned - try to read the name from the database
    if active_playlist_id is None:
        logger.debug(f"---- {func_name()}() active_playlist_id is None ")
        msg = getActivePlaylistName(myjboxdb,myjboxSpotify)

    # finished disconnect
    myjboxdb.disconnect()

    if msg is not None:
        webdata += f'<h2> Configuration Error </h2><br> {msg} <br>'
    else:
        # save the request headers so we can use them in the triggered workflows
        
        for header in request.headers:
            logger.debug(f"EXEC {func_name()}() Header is - {header}") 
            key, value = header
            request_headers.append(urlHeader(key,value))
            logger.debug(f"---- HEADERS SAVED - {request_headers}")

    logger.debug(f"ENDS {func_name()}() REDIRECT {config.JBOX_HOME}")
    return redirect(config.JBOX_HOME)
        


################################################################
################################################################
def getActivePlaylistName(myjboxdb,myjboxSpotify):
    global active_playlist_id
    global playback_device_id
    msg = None
    active_playlist_name= None

    logger.debug(f"EXEC {func_name()}()")

    # load the target playlist name
    active_playlist_name,msg = myjboxdb.ReadValue("jbox_playlist")
    if msg is None: 
        # did we find an entry in the database
        if active_playlist_name is not None:
            # Take the name and find the playlist id
           active_playlist_id,msg = myjboxSpotify.findPlaylistIdByName(active_playlist_name)
        else:
            logger.debug(f"---- No database entry for jbox_playlist {active_playlist_name}")
        
    # Something went wrong 
    if msg is not None:
        msg = f"ERROR: system error trying to get a target playlist: {msg}"
        logger.error(f"---- {msg}")

    logger.debug(f"ENDS {func_name()}() MSG- {msg}")
    return msg


################################################################
################################################################
@app.route('/webapi/get_playlist')
def api_get_playlist():
    data = {}
    jbox_playlist = None
    logger.debug(f"EXEC {func_name()}()")

    myjboxdb = jukeboxdb(config.SQLDBNAME)

    # Connect to database
    myjboxdb.connect()

    jbox_playlist,msg = myjboxdb.ReadValue("jbox_playlist")

    if msg is None:
        # we got something back
        msg = ""
    if jbox_playlist is None:
        jbox_playlist = "Missing Counter"

    data = { "name": jbox_playlist, "error" : msg}
    
    # disonnect from database
    myjboxdb.disconnect()


    logger.debug(f"ENDS {func_name()}() JSON {data}")
    return jsonify(data), 200
################################################################
################################################################
@app.route('/webapi/get_trackList')
def get_tracks():
    data = None
    global active_playlist_id
    playlist_index = 0 
    myjboxdb = jukeboxdb(config.SQLDBNAME)
    webdata=None

    logger.debug(f"EXEC {func_name()}()")

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name()}() HTML- redirect('/')")
        return redirect('/')

    myjboxSpotify.connect()

    webdata =  request.args.get("id")
    if webdata is not None:
            playlistId = webdata

    webdata = request.args.get("index")
    if webdata is not None:
        playlist_index = int(webdata)
    
    playlist_data = myjboxSpotify.getPlayLists()

    # If the list of playlists is not empty
    if len(playlist_data['items']) != 0 :
        logger.debug(f"---- {func_name()}() found {len(playlist_data['items'])} playlists ")
        # iterate the list of playlists
        for playlist in playlist_data['items']:
            # if this is the playlist we are interested in 
            if playlist['id'] == active_playlist_id:
                # call spotify to get the track list
                logger.debug(f"---- {func_name()}() matched {active_playlist_id} ")
                playlistTracks = myjboxSpotify.getPlayListTracks(active_playlist_id,0,100)
                # Connect to database
                myjboxdb.connect()
                # Build the track table for the playlist
                data = build_tracktable(myjboxdb,playlistTracks)
                #Finish disconnect from database
                commit = True
                result,msg = myjboxdb.disconnect(commit)
                break

            else:
                logger.debug(f"---- {func_name()}() did not match {active_playlist_id} ")
    else:
        #build an empty data structure with a message
        logger.debug(f"---- {func_name()}() did not find any playlists")
        data = { "artist": "No Artist", "title": "No Title", "image": "/static/NoMusicIcon.png", "trackid": "0", "message" : "No Playlist Selected" }
    
    logger.debug(f"ENDS {func_name()}() JSON- {data}")
    return jsonify(data)



################################################################
################################################################
def build_tracktable(myjboxdb,tracks):
    logger.debug(f"EXEC {func_name()}()")
    data=[]
    msg=""
    mytrack={}

    if len(tracks) == 0:
        logger.debug(f"---- {func_name()}() Empty Playlist")
        data = { "artist": "No Artist", "title": "No Title", "image": "/static/NoMusicIcon.png", "trackid": "0", "message" : "Empty Playlist Selected" }
        logger.debug(f"ENDS {func_name()}() JSON {data}")
        return data       

    for track in tracks['items']:
        # Grab the data for this track....
        logger.debug(f"---- {func_name()} - got track {track['track']['id']} - track['track']['name'] from spotify ")
        track_artist = track['track']['artists'][0]['name']
        track_title  = track['track']['name']
        track_image  = track['track']['album']['images'][2]['url']
        trackid      = track['track']['id']
        image_width  = track['track']['album']['images'][2]['width']
        image_height = track['track']['album']['images'][2]['height']
        track_time   = int(track['track']['duration_ms'] /1000)
       
        
        mytrack = { "artist": track_artist, "title": track_title, "length": track_time, "image": track_image, "image_height": image_height, "image_width": image_width, "trackid": trackid, "message" : msg }
        data.append(mytrack)
        myjboxdb.initialiseTrackMetrics(mytrack)

    logger.debug(f"ENDS {func_name()}() JSON {data}")
    return data


################################################################
################################################################
@app.route('/webapi/queue_track', methods = ['POST'])
def queue_track():
    trackId = None
    commit = False
    myjboxdb = jukeboxdb(config.SQLDBNAME)
    result = None

    logger.debug(f"EXEC {func_name()}()")

    # get the track info from the json data
    json_data = json.loads(request.data)

    if json_data is None: 
        msg = "no data found in queue_track request"
        logger.debug(f"ENDS {func_name()}() - {msg} ")
        return jsonify({ "status": "error", "message": msg}), 500

    logger.debug(f"---- IN queue_track json_data is = {json_data}")

    trackId = json_data.get("trackid",None)
    duration = json_data.get("tracktime",None)

    if trackId is None:
        msg = "trackid not found in queue_track request"
        logger.debug(f"ENDS {func_name()}() - {msg} ")
        return jsonify({ "status": "error", "message": msg}), 500
    
    if duration is None:
        msg = "tracktime not found in queue_track request"
        logger.debug(f"ENDS {func_name()}() - {msg} ")
        return jsonify({ "status": "error", "message": msg}), 500

    # Connect to database
    myjboxdb.connect()

    # are there enough credits
    jbox_credits,msg = myjboxdb.ReadValue("jbox_credits")
    jbox_credits = int(jbox_credits)

    if jbox_credits <= 0 :
        myjboxdb.disconnect(commit)
        msg = "Not enough credits to Queue a Track"
        logger.debug(f"ENDS {func_name()}() - {msg} ")
        return jsonify({ "status": "error", "message": msg}), 500

    result,msg = myjboxdb.queueTrack(trackId,duration)

    if msg is not None:
        myjboxdb.disconnect(commit)
        msg = f"ERROR Queuing trackID: {trackId}: {msg}"
        logger.error(f"---- {msg}")
        return jsonify({ "status": "error", "message":msg}), 500
    
    # reduce the number of credits 
    result,msg = myjboxdb.StoreValue("jbox_credits",f"{jbox_credits-1}")

    if msg is not None:
        myjboxdb.disconnect(commit)
        msg = f"ERROR Reducing jukebox Credits for {trackId}: {msg}"
        logger.error(f"---- {msg}")
        return jsonify({ "status": "error", "message":msg}), 500

    #Finish disconnect from database
    commit = True
    result,msg = myjboxdb.disconnect(commit)

    return jsonify({"status":"ok"}), 200

################################################################
################################################################
@app.route('/webapi/getNowPlayingTrack')
def api_playing_track():
    msg = ""
    
    logger.debug(f"EXEC {func_name()}()")

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    myjboxdb = jukeboxdb(config.SQLDBNAME)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name()}() Not Signed in")
        data = {"error": "Application Not Signed In" }
        return jsonify(data), 500

    # complete signin
    myjboxSpotify.connect()
    
    track = myjboxSpotify.getCurrentTrack()

    # Connect to database
    myjboxdb.connect()

    logger.debug(f"---- {func_name()}() - **************************************")
    # how many tracks are waiting
    queueLength,msg = myjboxdb.getQueueLength()
    queueLen = int(queueLength)

    logger.debug(f"---- {func_name()}() - QueueLength = {queueLen}")

    logger.debug(f"---- {func_name()}() - **************************************")

    # Connect to database
    myjboxdb.disconnect()

    if track is not None :
        # Got a track from the jbox - pull out what we need
        logger.debug(f"---- {func_name()}() - got a current track from spotify {track}")

        #
        if track['is_playing'] == False:
            logger.debug(f"---- {func_name()}() - Track is not playing")
            data = setTrackData("No Artist","No Track","/static/NoMusicIcon.png","",1,None,queueLen)
            logger.debug(f"ENDS {func_name()}() JSON {data}")
            return jsonify(data), 200
        
        if track['currently_playing_type'] == 'track':
            logger.debug(f"---- {func_name()}() - Track is a music track")
            data = setTrackData(track['item']['artists'][0]['name'],
                                track['item']['name'],
                                track['item']['album']['images'][1]['url'],
                                "",
                                0,
                                track['item']['id'],
                                queueLen )
        else:
            logger.debug(f"---- {func_name()}() - Track is not music")
            data = setTrackData("No Artist","No Track","/static/NoMusicIcon.png","",1,None,queueLen)
    else:
        # Nothing going on - say so 
        logger.debug(f"---- {func_name()}() - did not get a track return from spotify ")
        data = setTrackData("No Artist","No Track","/static/NoMusicIcon.png","",1,None,queueLen)

    logger.debug(f"ENDS {func_name()}() JSON {data}")
    return jsonify(data), 200

################################################################
################################################################
def setTrackData(track_artist,track_title,track_image,msg,track_status,trackid,queueLen):
    logger.debug(f"EXEC {func_name()}({track_artist},{track_title},{track_image},{msg},{track_status},{trackid},{queueLen})")

    data = { "artist": track_artist, "title": track_title, "image": track_image,  "error" : msg, "state": track_status, "trackid": trackid, "queueLen": queueLen, }

    logger.debug(f"ENDS {func_name()}() JSON {data}")

    return data

################################################################
################################################################
@app.route('/webapi/play_track',methods=['POST'])
def api_play_track():
    logger.debug(f"EXEC {func_name()}()")

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name}() Not Signed in")
        data = {"error": "Application Not Signed In" }
        return jsonify(data), 500

    # complete signin
    myjboxSpotify.connect()

    # get the track info from the json data
    json_data = json.loads(request.data)

    if json_data is None: 
        msg = "no data found in queue_track request"
        logger.debug(f"ENDS {func_name()}() - {msg} ")
        return jsonify({ "status": "error", "message": msg}), 500

    logger.debug(f"---- IN play_track json_data is = {json_data}")

    trackid = json_data.get("trackid",None)

    if trackid is None:
        data = jsonify( { "errstr": "No Track to Play", "errno": 3, "trackid": "", } )
        logger.debug(f"ENDS {func_name()}() JSON {data}")
        return data

    logger.debug(f"---- IN play_track calling spotify start_playback({trackid})")    
    myjboxSpotify.start_playback(trackid)
    
    data = jsonify({ "errstr" :"", "trackid": trackid, "errno": 0, } )
    logger.debug(f"ENDS {func_name()}() JSON {data}")
    return data


################################################################
################################################################
def getPlaybackDevice(myjboxdb,myjboxSpotify):
    global active_playlist_id
    global playback_device_id
    msg = None
    playback_device_name= None

    # Load the playback device name
    playback_device_name,msg = myjboxdb.ReadValue("jbox_device")
    
    # check for an error
    if msg is None: 
        # did we find an entry in the database
        if playback_device_name is not None:
            # Take the name and find the device id
            playback_device_id,msg = myjboxSpotify.findDeviceidByName(playback_device_name)
        else:
            logger.debug(f"---- No database entry for jbox_device")
    # Something went wrong 
    if msg is not None:
        msg = f"ERROR: system error trying to get a playback device: {msg}"
        logger.error(f"---- {msg}")

    logger.debug(f"ENDS {func_name()}() MSG- {msg}")
    return msg


################################################################
################################################################
@app.route('/webapi/get_credits')
def api_get_credits():
    data = {}
    jbox_credits = None
    logger.debug(f"EXEC {func_name()}()")

    myjboxdb = jukeboxdb(config.SQLDBNAME)

    # Connect to database
    myjboxdb.connect()

    jbox_credits,msg = myjboxdb.ReadValue("jbox_credits")

    if msg is None:
        # we got something back
        msg = ""
    if jbox_credits is None:
        jbox_credits = "Missing Counter"

    data = { "credits": jbox_credits, "error" : msg}
    
    # disonnect from database
    myjboxdb.disconnect()


    logger.debug(f"ENDS {func_name()}() JSON {data}")
    return jsonify(data), 200

################################################################
################################################################
def bgSendApprequest(url:str,method : str,payload=None):
    logger.debug(f"EXEC {func_name()}() url=[{url}], method=[{method}],payload=[{payload}]") 
    headers = {}

    if len(request_headers) == 0:
        logger.debug(f"ENDS {func_name()}() = No Saved Headers")
        return None
    
    #for h in request_headers:
    #    logger.debug(f"---- {func_name()}() - header key = {h[0]}: {h[1]} ")
    #    headers.update({h[0]: h[1]})
    headers.update(request_headers)

    match (method):

        case 'GET':
            response = requests.get(url,headers=headers)
        case 'POST':
            headers.update({'content-type': 'application/json'})
            response = requests.post(url,headers=headers,data=json.dumps(payload))
        case _:
            logger.error(f"---- {func_name()}() bad HTTP Method: {method}")
            return None
    
    #logger.debug(f"---- {func_name()}() - Request was: {response.request}")

    if response:
        logger.debug(f"---- Response status= {response.status_code}")
    else:
        logger.debug(f"---- Response returned as None") 

    logger.debug(f"ENDS {func_name()}() = {response}")

    return response

################################################################
################################################################
def bgPlayNextTrack(myjboxdb):
    msg = None
    response = None
    result = None

    logger.debug(f"EXEC {func_name()}({myjboxdb})") 
    # nothing is playing pull the first item from the queue 
    track_db,msg = myjboxdb.pullFirstQueuedTrack()    

    if msg is None and len(track_db) != 0:
        trackid,status,actiontime,QueueNumber,duration = track_db[0]

        logger.debug(f"Asking for playing track")

        response = bgSendApprequest(f"{weburl}/webapi/play_track","POST",{"trackid": trackid,})

        # Check return code in response

        # Update track status
        myjboxdb.setQueuedTrackStatus(QueueNumber,"PLAYING")
        #retrieve saved status
        track_db= myjboxdb.getPlayingTrack()
        # update track metrics
        myjboxdb.updateTrackMetrics(trackid,actiontime)
        result = True
    
    logger.debug(f"ENDS {func_name()}() = {result},{msg}")
    
    return result,msg

################################################################
################################################################
def bgGetSPCurrentTrack(myjboxdb):
    msg = None
    result = None
    response = None

    logger.debug(f"EXEC {func_name()}({myjboxdb})") 

    logger.debug(f"Asking to get Now playing track ")

    response = bgSendApprequest(f"{weburl}/webapi/getNowPlayingTrack","GET")

    if response:
        result = response.json()

        if result['error'] != "":
            logger.error(f"---- {func_name()}() Got Json error: {result['error']}")
            msg = result['error']
            result = None
    else:
        msg = "Empty return from server"
    logger.debug(f"ENDS {func_name()}() = {result},{msg}")
    return result,msg


################################################################
################################################################
def app_init()->int :
    logger.debug(f"EXEC {func_name()}() ")
    global weburl
    global webport
    redirect_uri=None
    result = 0
    webhost=None
    webpath=None

    # Get the listening port from the environment
    if 'JBOX_USE_PROD_PORT' in os.environ:
        # Using production port 
        webport_name= 'JBOX_PROD_PORT'
    else:
        # using debug Port
        webport_name= 'JBOX_DBG_PORT'

    # Get the port from the environment and check it. 
    webport = os.environ.get(webport_name)
    if webport is None:
        result =1
        logger.error(f"ENDS {func_name()}() error {result}:Missing Environment Variable  {webport_name}") 
        return result
          
    webhost = os.environ.get("JBOX_HOST")
    if webhost is None:
        result =2
        logger.error(f"ENDS {func_name()}() error {result}:Missing Environment Variable JBOX_HOST")
        return result

    webpath = os.environ.get("SPOTIFY_REDIRECT_PATH")

    if webpath is None:
        result =3
        logger.error(f"ENDS {func_name()}() error {result}:Missing Environment Variable SPOTIFY_REDIRECT_PATH")
        return result
    
    redirect_uri = f"{webhost}:{webport}{webpath}"
    os.environ['SPOTIPY_REDIRECT_URI'] = redirect_uri
    logger.debug(f"    {func_name()}()  SPOTIPY_REDIRECT_URI set to {redirect_uri}")
    
    # This needs to be set for the SPOTIPY library to use 
    if "SPOTIPY_CLIENT_ID" not in os.environ:
        result =4
        logger.error(f"ENDS {func_name()}() error {result}:Missing Environment Variable SPOTIPY_CLIENT_ID")
        return result

    # This needs to be set for the SPOTIPY library to use 
    if "SPOTIPY_CLIENT_SECRET" not in os.environ:
        result =5
        logger.error(f"ENDS {func_name()}() error {result}:Missing Environment Variable SPOTIPY_CLIENT_SECRET")
        return result


    # Get the path to the database file from the environment
    sqldbpath = os.environ.get("JBOX_DBPATH")
    if sqldbpath is None:
        sqldbpath=config.SQLDBNAME
    else:
        config.SQLDBNAME = sqldbpath

    logger.debug(f"     {func_name()}() sqldbpath  config.SQLDBNAME is {sqldbpath}")
    
    # Create a database Instance
    myjboxdb = jukeboxdb(sqldbpath)

    # Test the database using a test value read/write
    dbtest,msg = myjboxdb.test()
    if dbtest == False:
        result =  8
        logger.errror(f"ENDS {func_name()}() error{result}: Failed to initialise jukebox database: {msg}")
        return result


    logger.debug(f"ENDS {func_name()}() = SUCCESS {result}")
    return result

################################################################
################################################################

# initialise the application
result = app_init()
if result != 0 :
    # Failed app__init() 
    logger.error(f"function app_init returned nn zero code {result}")
    exit(result)
    
# If we are in development, this modules will be main so run the app
# production uses uwsgi which will startthe app under it's own control
if __name__ == '__main__':
    # Following lines allow application to be run more conveniently with
    # `python app.py` (Make sure you're using python3)
    # (Also includes directive to leverage pythons threading capacity.
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run( threaded=True, debug=True, port=int(webport))
    # We should never get here 
    logger.error(f"Unexpected return from Flask Application")
