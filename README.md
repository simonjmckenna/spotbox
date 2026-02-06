# spotbox
Python flask web app for a simple jukebox using a spotify playlist

written using the spotipy library (https://spotipy.readthedocs.io/en/2.25.2/) 

It has a SQL Lite back end to keep track of queued tracks and track played metrics 

It has an admin interface to manage the selection of the playlist and the number of credits available. 

Future releases will allow credits to be added via an rfid reader.

The Jukebox hsa two screen areas  - one containing a vertically scrollable 4 wide list of tracks with thumbnails, artist and title
                                  - the other containing a larger image, title and artist of the currently playing track.

Between the two areas is the title section that also displays the number of credits, and hw long the currently playing queue is.

The program does not queue multiple tracks to spotify but instead plays each track individually managing the queue itself. 

Initial configuration is carried out by editing the jbox.env file. 

The application must be registered with spotify and this requires a spotify premium account. 

See https://developer.spotify.com/documentation/web-api/concepts/apps for details and also the spotipy docs (link above).

The application is intended to be deployed in /srv/jukebox  with the following directory structure

/srv/jukebox/ -+
               + README.md           - This File
               + app/  -+            - The Python application directory 
                        + venv       - The virtual environment directory
               + db/                 - holds the sqlite database
               + docs/	             - holds documents
               + log/	             - application log files
               + socket/             - holds the nginx <-> jukebox uwsgi socket
               + static/             - holds static files for the web front end
               + wsgi/               - holds uwsgi configuration


All folders are owned by Jukebox:jukebox apart from /srv/jukebox & /srv/jukebox/socket which are owned by jukebox:www-data (to allow nginx to access the socket)  all folders have permissions 0750

The socket that links nginx to uwsgi is located in /srv/jukebox/socket/uwsgi.sock. It should have permissions 0660 and user jukebox and group www-data to allow nginx to write and the jukebox app to read

The jukebox service file is installed in /etc/systemd/system/jukebox.service by the root user.
it is delivered in the wsgi directory andshoudl be copied to the above folder, then instanatiated with 

$ sudo systemctl daemon-reload

The virtual environment shoudl eb created by the jukebox user in the /srv/jukebox/app folder

$ python3 -m venv venv

The activate:

$ . ./venv/bin/activate

Install the requirements (in requirements.txt)

$ pip3 install  uwsgi flask flask_session requests 

The sqlite database has three primary tables 

CONFIG - where configuration data and variables are stored (in key/value pairs) 

TRACKS - A table continaing data for each track in the playlist - including metrics for how often the track is played, 

CURRENTQUEUE the current track queue 

The client web page polls the application every couple of seconds, to retrive information on the currenly playing track, the number of credits and the length of the queue. At this point it also checks to see if there is actually music playing and if not - moves the jukebox on to the next track in the CURRENTQUEUE and requests spotify to polay it. 

There is an admin set of pages that do thing such as select the spotify playlist,   set the playback device, set the number of credits and allows you to change the stored admin code (stored in the database) required to log into the admin page. 1


Databsae Tables: 

CONFIG 

CREATE TABLE "CONFIG" (
	"Key"	TEXT NOT NULL UNIQUE,
	"Value"	TEXT,
	PRIMARY KEY("Key")
)

CURRENTQUEUE

CREATE TABLE "CURRENTQUEUE" (
	"QueueNumber"	INTEGER NOT NULL UNIQUE,
	"trackID"	TEXT NOT NULL,
	"status"	TEXT DEFAULT 'QUEUED',
	"actiontime"	INTEGER NOT NULL,
	"Duration"	INTEGER,
	PRIMARY KEY("QueueNumber")
)

TRACK

CREATE TABLE "TRACK" (
	"trackID"	TEXT NOT NULL UNIQUE,
	"title"	TEXT NOT NULL UNIQUE,
	"artist"	TEXT NOT NULL,
	"imageurl"	TEXT,
	"duration"	INTEGER NOT NULL,
	"lastPlayed"	INTEGER DEFAULT 0,
	"playCount"	INTEGER DEFAULT 0,
	PRIMARY KEY("trackID")
)

INDEXES:

CREATE UNIQUE INDEX "trackName_index" ON "TRACK" (
	"title"	DESC
)





