################################################################
# jboxspotifyfunctions.py dnb inteface module for jukebox app  #
################################################################
######   Copyright (c) Simon McKenna 11/25  Version 0.1   ######
################################################################
import logging
logger=logging.getLogger(__name__)

import os
import config
import time
from config import func_name

import spotipy

class jboxSpotify:

    def __init__(self,session,loggedIn=True):
        self.cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
        if loggedIn == False:
            self.auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing user-read-playback-state streaming playlist-modify-private',
                                               cache_handler=self.cache_handler,
                                               show_dialog=True)
        else:
            self.auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=self.cache_handler)
        
    def getAccessToken(self,token: str):
        return self.auth_manager.get_access_token(token)
    
    def validateAccessToken(self):
        return self.auth_manager.validate_token(self.cache_handler.get_cached_token())
    
    def getAuthorizeUrl(self):
        return self.auth_manager.get_authorize_url()
    
    def connect(self):
        self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)

    ################################################################
    ################################################################
    def findDeviceidByName(self, playback_device_name):
        result = None
        msg = None
        global playback_device_id
        logger.debug(f"EXEC {func_name()}( spotify, {playback_device_name})")

        device_data = self.spotify.devices()
    
        if len(device_data['devices']) != 0 :

            for device in device_data['devices']:
                logger.debug(f"---- CHECKING DEVICE ID={device['id']}")
                if device['name'] == playback_device_name:
                    logger.debug(f"---- DEVICE ID={device['id']} MATCHED {playback_device_name}")
                    result = device['id']
        else:
            msg = "No devices available on Spotify"
            logger.debug(f"---- {msg}")

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg

    ################################################################
    ################################################################
    def findPlaylistIdByName(self, active_playlist_name):
        result = None
        msg = None
        global playback_device_id
        logger.debug(f"EXEC {func_name()}( spotify, {active_playlist_name})")

        playlist_data = self.spotify.current_user_playlists()
    
        if len(playlist_data['items']) != 0 :

            for playlist in playlist_data['items']:
                logger.debug(f"---- CHECKING PLAYLIST ID={playlist['id']}")
                if playlist['name'] == active_playlist_name:
                    logger.debug(f"---- PLAYLIST ID={playlist['id']} MATCHED {active_playlist_name}")
                    result = playlist['id']
        else:
            msg = "No playlist available on Spotify"
            logger.debug(f"---- {msg}")

        logger.debug(f"ENDS {func_name()}() {result},{msg}")
        return result,msg
    
    ################################################################
    ################################################################
    def getPlayLists(self):
        logger.debug(f"EXEC {func_name()}()")

        data = self.spotify.current_user_playlists()
        
        logger.debug(f"ENDS {func_name()}() {data}")
        return data
        
    ################################################################
    ################################################################  
    def getCurrentTrack(self):
        logger.debug(f"EXEC {func_name()}()")

        data = self.spotify.current_user_playing_track()
        
        logger.debug(f"ENDS {func_name()}() {data}")
        return data
    
    ################################################################
    ################################################################
    def getPlayListTracks(self,playListId,offset,count):
        
        logger.debug(f"EXEC {func_name()}({playListId},{offset},{count})")

        data = self.spotify.playlist_items(playListId, fields=None, limit=count, offset=offset, market=None, additional_types=('track'))   
        
        logger.debug(f"ENDS {func_name()}() {data}")
        return data

    ################################################################
    ################################################################  
    def getDevices(self):
        logger.debug(f"EXEC {func_name()}()")

        data = self.spotify.devices()

        logger.debug(f"ENDS {func_name()}() {data}")

        return data
 
    ################################################################
    ################################################################  
    def transferPlayback(self,playback_device_id,forcePlay=False):
        logger.debug(f"EXEC {func_name()}()")

        data = self.spotify.transfer_playback(device_id=playback_device_id,force_play=forcePlay)

        logger.debug(f"ENDS {func_name()}() {data}")

        return data
    
    ################################################################
    ################################################################  
    def me(self):
        logger.debug(f"EXEC {func_name()}()")

        data = self.spotify.me()

        logger.debug(f"ENDS {func_name()}() {data}")

        return data

    ################################################################
    ################################################################  
    def start_playback(self,trackid):
        logger.debug(f"EXEC {func_name()}()")

        data = self.spotify.start_playback(device_id=None, uris=[f"spotify:track:{trackid}"])

        logger.debug(f"ENDS {func_name()}() {data}")

        return data   