################################################################
# jboxadmin.py jukebox application admin functions             #
################################################################
######   Copyright (c) Simon McKenna 11/25  Version 0.1   ######
################################################################
import logging
import logging.handlers

logger=logging.getLogger(__name__)

import config
from config import func_name
import os

from flask import  Blueprint, redirect, request, session, jsonify
from flask_session import Session
from threading import Thread, Lock
from types import SimpleNamespace

import json, uuid
from  jboxdbfunctions import jukeboxdb
from jboxspotifyfunctions import jboxSpotify
from urllib.request import  Request, urlopen
from typing import NamedTuple


admin_connected = False
admin_session_uuid = None

# define the flask blueprint linked to the function admin_page and
# the flask route defined in the bkstgsvc.py file
admin_route = Blueprint('admin_route',__name__)

################################################################
################################################################
@admin_route.route('/admin/admin_sign_out',methods=['GET'])
def admin_sign_out():
    webdata=''
    logger.debug(f"EXEC {func_name()}() - Request [{request}] ")
    if admin_session():
        admin_session_end()
    
    webdata = redirect('/')  

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
def admin_session():
    global admin_connected
    logger.debug(f"EXEC {func_name()}()")
    result = admin_connected
    logger.debug(f"ENDS {func_name()}() HTML- {result}")
    return result

################################################################
################################################################
def admin_session_end():
    global admin_connected
    logger.debug(f"EXEC {func_name()}()")
    admin_connected = False
    result = admin_connected
    logger.debug(f"ENDS {func_name()}() HTML- {result}")
    return result

################################################################
################################################################
def admin_session_start():
    global admin_connected
    logger.debug(f"EXEC {func_name()}()")
    admin_connected = True
    result = admin_connected
    logger.debug(f"ENDS {func_name()}() HTML- {result}")
    return result
################################################################
################################################################


def drawAdminPage(myjboxdb,myjboxSpotify):
    global active_playlist_id

    logger.debug(f"EXEC {func_name()}()")

    if not admin_session():
        username = ""
        playlist_name = ""
        playback_device_name = ""
        credits = 0
    else:
        username = myjboxSpotify.me()["display_name"]
        playlist_name,msg = myjboxdb.ReadValue("jbox_playlist")
        playback_device_name,msg = myjboxdb.ReadValue("jbox_device")
        credits,msg = myjboxdb.ReadValue("jbox_credits")

    webdata = '<head> <meta charset="UTF-8"> <title>SpotBox Jukebox Admin Page</title> '\
              '<link href="/static/jukebox.css" rel="stylesheet"> '\
              '</head><body>'
    
    webdata +=  f'<div class="jukebox"> '\
                f'<div class="screen">'\
                f'<div class="jukebox-title"> Spotbox Admin</div><br>'\
                f'<div class="jukebox-title2"> Spotify User    [{username}] </div> '\
                f'<div class="jukebox-title2"> Spotify Device  [{playback_device_name}] </div>' \
                f'<div class="jukebox-title2"> Spotify Paylist [{playlist_name}] </div>'\
                f'<div class="jukebox-title2"> Jbox Credits    [{credits}]</div>'\
                f'</div>'\
                f'<div class="screen">'
    if not admin_session():
        webdata +=  '<div> <div> <div class="jukebox-title2">Enter Admin Passcode:</div></div>'\
                    '<form id="admin_form" action="/admin/admin_login" method="POST">'\
                    '<div> <div class="center"> '\
                    '<input type="password" inputmode="numeric" class="jukebox-title1b" pattern="[0-9]{1,6}" maxlength="6" name="admin_code" id="admin_code"/> ' \
                    '<input type="submit" class="jukebox-title2b" name="submit" id="submit" value="submit"/>' \
                    '</div></div>'\
                    '</form></div>'
        
        webdata +=  f'<div class="jukebox-title3"> <a href="/">cancel</a></div>' \


    else:
        webdata +=  f'<div class="admin-grid">'                
        webdata +=  f'<div class="card"> <div class="jukebox-title2"><a href="/admin/get_playlists">my playlists</a></div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/admin/get_devices">current devices</a></div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/admin/set_credits">set credits</a></div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/admin/set_admin_code">reset admin_code</a></div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/admin/show_metrics">playback metrics</a></div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/">return to spotbox (admin open)</a></div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/admin/admin_sign_out">return to spotbox (admin closed)<a/> </div></div>' \
                    f'<div class="card"> <div class="jukebox-title2"><a href="/sign_out">[sign out of Spotify]<a/> </div></div>' 
        webdata +=  f'</div>'
    webdata +=  f'</div>'\
                f'</div>'
    
    webdata +=  f'</body>'

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata



################################################################
################################################################
@admin_route.route('/admin/admin_login',methods=['POST'])
def admin_login():
    webdata = None
    logger.debug(f"EXEC {func_name()}()")
    
    myjboxdb = jukeboxdb(config.SQLDBNAME)
    # Connect to database
    myjboxdb.connect()

    entered_admin_code=request.form.get('admin_code')
    logger.debug(f"---- {func_name()}() got admin_code as - {entered_admin_code}")

    jbox_admin_code,msg = myjboxdb.ReadValue("jbox_admin_code")

    if msg is not None:
        logger.error(f'---- {func_name()}() FAILED to Retrieve Admin code from DB : {msg}')
        webdata = redirect('/admin')
        logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
        return webdata
    
    logger.debug(f'---- {func_name()}() Entered Admin Code: {entered_admin_code}')
    logger.debug(f'---- {func_name()}() jukebox Admin Code: {jbox_admin_code}')

    if entered_admin_code != jbox_admin_code:
        logger.error(f'---- {func_name()}() Entered Admin Code does not match Stored Admin Code : {msg}')
        webdata = redirect('/admin')
        logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
        return webdata
    
    admin_session_start()
    
    webdata = redirect('/admin')  

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
@admin_route.route('/admin',methods=['GET','POST'])
def admin_page():
    global active_playlist_id
    global playback_device_id
    global request_headers
    global admin_connected
    webdata =""

    logger.debug(f"EXEC {func_name()}()")

    msg = None

    if not admin_session():
        logger.debug(f"---- {func_name()}() - starting admin login")
        webdata += drawAdminPage(None,None)
        logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
        return webdata



    myjboxdb = jukeboxdb(config.SQLDBNAME)
    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name}() HTML- redirect('/')")
        return redirect('/')

    myjboxSpotify.connect()

    # Connect to database
    myjboxdb.connect()
        
    webdata += drawAdminPage(myjboxdb,myjboxSpotify)
    # finished disconnect
    myjboxdb.disconnect()
    
    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata


################################################################
################################################################
@admin_route.route('/admin/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

################################################################
################################################################
@admin_route.route('/admin/get_playlists')
def get_playlists():
    webdata=""

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name}() HTML- redirect('/')")
        return redirect('/')

    myjboxSpotify.connect()

    playlist_data = myjboxSpotify.getPlayLists()

    webdata = '<head> <meta charset="UTF-8"> <title>SpotBox Jukebox Admin Page</title> '\
              '<link href="/static/jukebox.css" rel="stylesheet"> '\
              '</head><body>'
    
    webdata +=  f'<div class="jukebox"> '\
                f'<div class="screen">'\
                f'<div class="jukebox-title"> Spotbox Playlists</div><br>'
        
    if len(playlist_data['items']) != 0 :
        for playlist in playlist_data['items']:
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            webdata = webdata + f'<div class="jukebox-title2"><a href="/admin/set_playlist?id={playlist_id}">{playlist_name}</a></div> '
    else:
        webdata ='<div class="jukebox-title2">No Playlists available.</div>'
    
    webdata +=  f'</div> '\
                f'</body>'f'<div class="jukebox-title2"> <a href="/admin">cancel</a></div>'\
                f'</div>' 

    return webdata

################################################################
################################################################
@admin_route.route('/admin/set_playlist')
def set_playlists():
    global active_playlist_id
    jbox_playlist_name = None
    webdata=""

    logger.debug(f"EXEC {func_name()}()")

    if admin_session() is not True:
        logger.debug(f"ENDS {func_name}() admin function and not admin")
        return redirect('/')

    myjboxdb = jukeboxdb(config.SQLDBNAME)

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name}() HTML- redirect('/admin')")
        return redirect('/')

    myjboxSpotify.connect()
    active_playlist_id =  request.args.get("id")

    playlist_data = myjboxSpotify.getPlayLists()

    if len(playlist_data['items']) != 0 :
        for playlist in playlist_data['items']:
            if playlist['id'] == active_playlist_id:
               jbox_playlist_name = playlist['name']
    
    if jbox_playlist_name is None:
        logger.error(f"---- ERROR saved playlist is not in list of playlists: {msg}")
        webdata += f"<br><b>ERROR saved playlist is not in list of playlist: {msg} </b><br>"
    else:    
        # Connect to database
        myjboxdb.connect()

        # Save the Playback device name to the configuration
        result,msg = myjboxdb.StoreValue("jbox_playlist",jbox_playlist_name)
        if msg is not None:
            # log and report the error
            logger.error(f"---- ERROR Storing playlist_name: {msg}")
            webdata += f"<br><b>ERROR Storing playlist name to database failed: msg </b><br>"
        else:
            # report on new playback device
            webdata = redirect('/admin')
    
        myjboxdb.disconnect()
    
    logger.debug(f"ENDS {func_name}() HTML- {webdata}")
    return webdata

################################################################
################################################################
@admin_route.route('/admin/get_devices')
def current_devices():
    webdata=""
    logger.debug(f"EXEC {func_name()}() - {request.headers}")

    if admin_session() is not True:
        logger.debug(f"ENDS {func_name}() admin function and not admin")
        return redirect('/')

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name}() HTML- redirect('/')")
        # return jsonify( errstr="Not Authorised"  , errno=1  )
        return redirect('/')

    # complete signin
    myjboxSpotify.connect()

    device_data = myjboxSpotify.getDevices()

    webdata = '<head> <meta charset="UTF-8"> <title>SpotBox Jukebox Admin Page</title> '\
              '<link href="/static/jukebox.css" rel="stylesheet"> '\
              '</head><body>'
    
    webdata +=  f'<div class="jukebox"> '\
                f'<div class="screen">'\
                f'<div class="jukebox-title"> Spotbox Devices</div><br>'
    
    if len(device_data['devices']) != 0 :
        for device in device_data['devices']:
            print(f"DEVICE = {device} \n")
            device_id = device['id']
            device_name = device['name']
            webdata = webdata + f'<div class="jukebox-title2"><a href="/admin/set_device?id={device_id}">{device_name}</a></div>'
    else:
        webdata += '<div class="jukebox-title2">No devices currently connected.</div>'
    
    webdata +=  f'</div> '\
                f'</body>'f'<div class="jukebox-title2"> <a href="/admin">cancel</a></div>'\
                f'</div>' 
    
    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
def getActiveDevice(myjboxSpotify):
    result = None
    logger.debug(f"EXEC {func_name()}() ")

    device_data = myjboxSpotify.getDevices()

    for device in device_data['devices']:
        if device['is_active'] == False:
            print(f"\nACTIVE DEVICE ={device} \n")
            result = device
            break
        
    logger.debug(f"ENDS {func_name()}() RESULT- {result}")
    return result

################################################################
################################################################
@admin_route.route('/admin/set_device')
def set_device():
    global playback_device_id
    playback_device_name = None

    logger.debug(f"EXEC {func_name()}() - ")

    if admin_session() is not True:
        logger.debug(f"ENDS {func_name}() admin function and not admin")
        return redirect('/')
    
    myjboxdb = jukeboxdb(config.SQLDBNAME)

    webdata=""

    myjboxSpotify = jboxSpotify(session,loggedIn=True)

    if not myjboxSpotify.validateAccessToken():
        logger.debug(f"ENDS {func_name}() HTML- redirect('/')")
        # return jsonify( errstr="Not Authorised"  , errno=1  )
        return redirect('/')

    # complete signin
    myjboxSpotify.connect()

    playback_device_id = request.args.get("id")
    print(f"Got new id {playback_device_id}\n")

    device_data = myjboxSpotify.getDevices()
    
    if len(device_data['devices']) != 0 :

        for device in device_data['devices']:
            print(f"DEVICE ID={device['id']} \n")
            if device['id'] == playback_device_id:
                playback_device_name = device['name']
                myjboxSpotify.transferPlayback(playback_device_id=playback_device_id,forcePlay=False)
    
    if playback_device_name is None:
        logger.error(f"---- ERROR saved playback_device is not in list of devices: {msg}")
        webdata += f"<br><b>ERROR saved playback_device is not in list of devices: {msg} </b><br>"
    else:    
        # Connect to database
        myjboxdb.connect()


        # Save the Playback device name to the configuration
        result,msg = myjboxdb.StoreValue("jbox_device",playback_device_name)
        if msg is not None:
           # log and report the error
           logger.error(f"---- ERROR Storing playback_device_name: {msg}")
           webdata += f"<br><b>ERROR Storing device name to database failed: {msg} </b><br>"
        else:
           # report on new playback device
           webdata =redirect('/admin')
    
        myjboxdb.disconnect()

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}") 
    return webdata

################################################################
################################################################
@admin_route.route('/admin/set_admin_code',methods=['GET','POST'])
def set_admin_code():

    webdata=""
    
    logger.debug(f"EXEC {func_name()}() - ")

    if admin_session() is not True:
        logger.debug(f"ENDS {func_name}() admin function and not admin")
        return redirect('/')
    
    myjboxdb = jukeboxdb(config.SQLDBNAME)

    # Connect to database
    myjboxdb.connect()

    if request.method == 'GET':
        # Empty call display the form
        logger.debug(f"---- {func_name()}() - Display set jbox_admin_code Form")
        webdata = setCodeFormDisplay(None)
        
    else:
        # we got a number of credits to add method is a POST
        logger.debug(f"---- {func_name()}() - setting new jbox_admin_code ")
        webdata = setCodeFormSubmit(myjboxdb,request)

    # finished disconnect
    myjboxdb.disconnect()

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
def setCodeFormDisplay(error_message):
    logger.debug(f"EXEC {func_name()}() ")

    webdata = '<head> <meta charset="UTF-8"> <title>SpotBox Jukebox Set Admin Code Page</title> '\
              '<link href="/static/jukebox.css" rel="stylesheet"> '\
              '</head><body>'
    webdata +=  f'<div class="jukebox"> '\
                f'<div class="screen">'\
                f'<div class="jukebox-title"> Spotbox Admin Code</div>'
    
    if error_message is not None:
        webdata +=  f'<div class="jukebox-title2r">  Error Setting Admin Code: {error_message} </div>'
    else:
        webdata +=  f'<div class="jukebox-title2r">   </div>'
        
    webdata +=  f'<div> <div class="center"> <form id="admin_code_form" action="set_admin_code" method="POST"> '

    webdata +=  f'<div class="jukebox-title2">  Enter Current Code: '\
                 '<input type="password" class="jukebox-title2b" inputmode="numeric" pattern="[0-9]{1,6}" maxlength="6" name="cur_admin_code" id="cur_admin_code"/>' \
                f'</div> '

    webdata +=  f'<div class="jukebox-title2">  Enter New Code:  '\
                 '<input type="password" class="jukebox-title2b" inputmode="numeric" pattern="[0-9]{1,6}" maxlength="6" name="new_admin_code1" id="new_admin_code1"/>' \
                f'</div> '

    webdata +=  f'<div class="jukebox-title2"> ReEnter New Code: '\
                 '<input type="password" class="jukebox-title2b" inputmode="numeric" pattern="[0-9]{1,6}" maxlength="6" name="new_admin_code2" id="new_admin_code2"/>' \
                f'</div> '
         
    webdata +=  f'<div class="center"> <input type="submit" class="jukebox-title2b" name="submit" id="submit" value="submit"/> </div>' \
                f'</form>'\
                f'</div>' \
                f'</div> </div>'
    webdata +=  f'<div class="jukebox-title3"> <a href="/admin">cancel</a></div>' \
                f'</div>' \
                f'</body>'
    

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
def setCodeFormSubmit(myjboxdb,request):
    webdata=''
    logger.debug(f"EXEC {func_name()}() - Request [{request}] ")

    jbox_admin_code,msg = myjboxdb.ReadValue("jbox_admin_code")
    if msg is not None:
        logger.debug(f"---- {func_name()}() - ReadValue(jbox_admin_code) got error: {msg}")
        webdata = setCodeFormDisplay(msg)
        logger.debug(f"ENDS {func_name()}() {msg}")
        return webdata  

    cur_admin_code=request.form.get('cur_admin_code')
    new_admin_code1=request.form.get('new_admin_code1')
    new_admin_code2=request.form.get('new_admin_code2')

    logger.debug(f"---- {func_name()}() got cur_admin_code  - {cur_admin_code}")
    logger.debug(f"---- {func_name()}() got new_admin_code1 - {new_admin_code1}")
    logger.debug(f"---- {func_name()}() got new_admin_code2 - {new_admin_code2}")

    jbox_admin_code,msg = myjboxdb.ReadValue("jbox_admin_code")

    if cur_admin_code != jbox_admin_code:
        webdata = setCodeFormDisplay("Incorrect Current Admin Code")
        logger.debug(f"ENDS {func_name()}() Incorrect Current Admin Code")
        return webdata        

    if new_admin_code1 != new_admin_code2:
        webdata = setCodeFormDisplay("New Admin Codes Do Not Match")       
        logger.debug(f"ENDS {func_name()}() New Admin Codes Do Not Match") 
        return webdata
    
    jbox_admin_code,msg = myjboxdb.StoreValue("jbox_admin_code",f"{new_admin_code1}")
    
    webdata = redirect('/admin')  

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
@admin_route.route('/admin/set_credits',methods=['GET','POST'])
def set_credits():

    webdata=""
    
    logger.debug(f"EXEC {func_name()}() - ")

    if admin_session() is not True:
        logger.debug(f"ENDS {func_name}() admin function and not admin")
        return redirect('/')
    
    myjboxdb = jukeboxdb(config.SQLDBNAME)


    # Connect to database
    myjboxdb.connect()

    jbox_credits,msg = myjboxdb.ReadValue("jbox_credits")
    if msg is not None:
        logger.debug(f"---- {func_name()}() - ReadValue(jbox_credits) got error: {msg}")
        return redirect('/admin')

    if request.method == 'GET':
        # Empty call display the form
        logger.debug(f"---- {func_name()}() - Display newcredits Form")
        webdata = creditFormDisplay(jbox_credits)
        
    else:
        # we got a number of credits to add method is a POST
        logger.debug(f"---- {func_name()}() - setting new credits ")
        webdata = creditFormSubmit(myjboxdb,request)

    # finished disconnect
    myjboxdb.disconnect()

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
def creditFormDisplay(current_credits):
    logger.debug(f"EXEC {func_name()}() - Current Credits {current_credits} ")

    webdata = '<head> <meta charset="UTF-8"> <title>SpotBox Jukebox Credit Management Page</title> '\
              '<link href="/static/jukebox.css" rel="stylesheet"> '\
              '</head><body>'
    webdata +=  f'<div class="jukebox"> '\
                f'<div class="screen">'\
                f'<div class="jukebox-title"> Spotbox Credits</div>'

    webdata+=   f'<div class="jukebox-title2"> Current Credits value is {current_credits}</div>' \
                f'<div class="jukebox-title2">  Enter required new credits value: </div>'
    webdata+=   f'<div> <div class="center"> <form id="credit_form" action="set_credits" method="POST"> '\
                 '<div> <div class="center"> <input type="text" class="jukebox-title2b" inputmode="numeric" pattern="[0-9]{1,5}" maxlength="5" name="new_credits" id="new_credits"/>  ' \
                f'<input type="submit" class="jukebox-title2b" name="submit" id="submit" value="submit"/> </div> </div>' \
                f'</form>'\
                f'</div>' \
                f'</div> '
    webdata +=  f'<div class="jukebox-title3"> <a href="/admin">cancel</a></div>' \
                f'</div>' \
                f'</body>'
    

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata

################################################################
################################################################
def creditFormSubmit(myjboxdb,request):
    webdata=''
    logger.debug(f"EXEC {func_name()}() - Request [{request}] ")

    new_credits=request.form.get('new_credits')
    logger.debug(f"---- {func_name()}() got new_credits as - {new_credits}")

    result,msg = myjboxdb.StoreValue("jbox_credits",f"{new_credits}")
    webdata = redirect('/admin')  

    logger.debug(f"ENDS {func_name()}() HTML- {webdata}")
    return webdata
