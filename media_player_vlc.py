#-*- coding:utf-8 -*-

"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Daniel Schreij"
__license__ = "GPLv3"

from libopensesame import item, exceptions, debug, generic_response
from libqtopensesame import qtplugin, pool_widget
import pygame
from pygame.locals import *
import os
import sys

# Check if vlc is available in the python site-packages library, or otherwise in
# the local dir
try:
	import vlc
	debug.msg("simple import vlc")
except:
	import imp
	path = os.path.join(os.path.dirname(__file__), "vlc.py")
	try:
		vlc = imp.load_source("vlc", path)
	except Exception as e:
		raise Exception( \
			"This plug-in requires that VLC player 1.X is installed in the default location. You can download VLC player for free from http://www.videolan.org/. Error: %s"
			% e)
	debug.msg("loading vlc from plugin folder")
	
	
# Try to import Mediainfo for obtaining statistics about the media file (like
# framerate and such).
# Download and install from: http://mediainfo.sourceforge.net/en/Download
# Python wrapper from: https://github.com/paltman/pymediainfo
try:
	from pymediainfo import MediaInfo
	try:
		# Check if MediaInfo CLI (+ DLLs) is already in the system's path and
		# callable
		MediaInfo.parse("")
	except:
		#If not fall back to version included in plugin dir by including this dir
		# to the path
		os.environ['PATH'] = os.path.dirname(__file__) + ';' + os.environ['PATH']					
except:
	debug.msg( \
		"MediaInfo module not found. This plug-in runs better with pymediainfo installed (http://paltman.github.com/pymediainfo/).", \
		reason="warning")

class media_player_vlc(item.item, generic_response.generic_response):

	"""
	The media_player plug-in offers advanced video playback functionality in
	OpenSesame, using vlc
	"""

	def __init__(self, name, experiment, string=None):

		"""
		Constructor. Link to the video can already be specified but this is
		optional

		Arguments:
		name -- the name of the item
		experiment -- the opensesame experiment

		Keyword arguments:
		string -- a definition string for the item (Default=None)
		"""

		# The version of the plug-in
		self.version = 0.10

		self.file_loaded = False
		self.paused = False

		self.item_type = "media_player_vlc"
		self.description = "Plays a video from file"
		self.duration = "keypress"
		self.playaudio = "yes"
		self.sendInfoToEyelink = "no"
		self.event_handler = ""
		self.event_handler_trigger = "on keypress"
		self.vlc_event_handler = None

		self.vlcInstance = vlc.Instance("--no-video-title-show")
		self.player = self.vlcInstance.media_player_new()
		self.media = None
		self.framerate = 0
		self.frame_duration = 0
		self.startPlaybackTime = 0
		self.playbackStarted = False
		self.hasMediaInfo = False
		
		#See if MediaInfo functions are available
		try:
			MediaInfo.parse("")
			self.hasMediaInfo = True
		except:
			debug.msg( \
				"MediaInfo CLI not found. Frame info might be unavailable.",
				reason="warning")
			self.hasMediaInfo = False
			
		# The parent handles the rest of the construction
		item.item.__init__(self, name, experiment, string)

	def _set_display_window(self):
		
		"""
		Routes vlc output to correct experiment window dependig on the opensesame
		backend used
		"""
		
		if self.has("canvas_backend"):
			backend = self.get("canvas_backend")
			if backend in ["legacy", "xpyriment"]:
				win_id = pygame.display.get_wm_info()['window']
			else:
				raise exceptions.runtime_error( \
					"Only the legacy and xpyriment back-ends are supported. Sorry!")
					
		debug.msg("Rendering video to window: {0}".format(win_id))
					
		if sys.platform == "linux2": # for Linux using the X Server
			self.player.set_xwindow(win_id)
		elif sys.platform == "win32": # for Windows
			self.player.set_hwnd(win_id)
		elif sys.platform == "darwin": # for MacOS
			self.player.set_agl(win_id)


	def prepare(self):
		
		"""
		Opens the video file for playback and compiles the event handler code

		Returns:
		True on success, False on failure
		"""

		# Pass the word on to the parent
		item.item.prepare(self)

		# Give a sensible error message if the proper back-end has not been
		# selected
		if not self.has("canvas_backend"):
			raise exceptions.runtime_error("Backend not initialized!")

		# Byte-compile the event handling code (if any)
		if self.event_handler.strip() != "":
			self._event_handler = compile(self.event_handler, "<string>", "exec")
		else:
			self._event_handler = None

		# Determine when the event handler should be called
		if self.event_handler_trigger == "on keypress":
			self._event_handler_always = False
		else:
			self._event_handler_always = True

		# Find the full path to the video file. This will point to some
		# temporary folder where the file pool has been placed
		path = self.experiment.get_file(str(self.eval_text(self.get( \
			"video_src"))))

		debug.msg("loading '%s'" % path)

		# Open the video file
		if not os.path.exists(path) or str(self.eval_text("video_src")).strip() \
			== "":
			raise exceptions.runtime_error( \
				"Video file '%s' was not found by video_player '%s' (or no video file was specified)." \
				% (os.path.basename(path), self.name))

		if self.hasMediaInfo:
			debug.msg("Reading file media parameters")
			mi = MediaInfo.parse(path)
			try:
				mi = MediaInfo.parse(path)
				for track in mi.tracks:
					if track.track_type == "Video":		
						self.framerate = float(track.frame_rate)
						if self.framerate < 1:
							debug.msg("Frame rate info unavailable!", \
								reason="warning")
						else:
							self.frame_duration = 1000/self.framerate
			except:
				raise exceptions.runtime_error( \
					"Error parsing media file. Possibly the video file is corrupt")
			
		try:
			self.media = self.vlcInstance.media_new(path)
			self.player.set_media(self.media)
			self.media.parse()
			self.file_loaded = True
		except:
			raise exceptions.runtime_error( \
				"Error loading media file. Unsupported format?")

		# If playaudio is set to no, tell vlc to mute the movie
		if self.playaudio == "no":
			self.player.audio_set_mute(True)
		else:
			self.player.audio_set_mute(False)
			# Solves bug in vlc bindings: unmute sets sound status to unmuted but
			# sets volume to 0
			self.player.audio_set_volume(50)   

		# create reference to vlc event handler and set up event handling
		self.vlc_event_handler = self.player.event_manager()

		# Send info to eyelink if it is found attached
		if self.sendInfoToEyelink == "yes":
			self.vlc_event_handler.event_attach( \
				vlc.EventType.MediaPlayerTimeChanged, self.startCheck)

		# Pass thru vlc output to experiment window
		self._set_display_window()

		if self.get("canvas_backend") in ["legacy","opengl"]:
			self.screen = self.experiment.surface

		# Indicate function for clean up that is run after the experiment finishes
		self.experiment.cleanup_functions.append(self.closePlayer)
		
		# Reinitialize variables
		self.playbackStarted = False
		self.startPlaybackTime = 0

		# Report success
		return True

	def startCheck(self, event):
		
		"""
		TODO: Informative docstring
		"""
		
		# Check for player init of the time and start frame counting
		self.playbackStarted = True	
		
		# frame_no_check = int(self.player.get_time()/self.frame_duration)
		
		# if self.playbackStarted and self.startPlaybackTime > 0:
			# calculated_frame = int((self.experiment.time() - self.startPlaybackTime)/self.frame_duration)
			# print "Calculated frame no. {0}".format(calculated_frame)
		
		# print "Real frame no. {0}".format(frame_no_check)
		# print "---------------------------------"
		
	def sendFrameInfoToEyelink(self):
		
		"""
		Sends frame info to the eye link log file which enables to create
		frame-based message reports
		"""
		
		if self.frame_duration > 0:	
			frame_no = int((self.experiment.time() - self.startPlaybackTime) \
				/ self.frame_duration)
			if hasattr(self.experiment,"eyelink") and \
				self.experiment.eyelink.connected():
				self.experiment.eyelink.log("videoframe {0}".format(frame_no) )
				self.experiment.eyelink.status_msg("videoframe {0}".format( \
					frame_no))
				
	def handleEvent(self, event=None):
		
		"""
		Allows the user to insert custom code. Code is stored in the event_handler
		variable.

		Arguments:
		event -- a dummy argument passed by the signal handler
		
		Returns:
		True if playback should continue, False otherwise
		"""
		
		if self.frame_duration == 0:
			frame_no = 0
		else:
			frame_no = int((self.experiment.time() - self.startPlaybackTime) \
				/ self.frame_duration)
		
		if event is not None:
			key = pygame.key.name(event.key)
		else:
			key = None

		continue_playback = True

		try:
			exec(self._event_handler)
		except Exception as e:
			raise exceptions.runtime_error( \
				"Error while executing event handling code: %s" % e)

		if type(continue_playback) != bool:
			continue_playback = False

		return continue_playback
		
	def run(self):
		
		"""
		Starts the playback of the video file. You can specify an optional
		callable object to handle events between frames (like keypresses).

		Returns:
		True on success, False on failure
		"""

		# Log the onset time of the item
		self.set_item_onset()

		# Set some response variables, in case a response will be given
		if self.experiment.start_response_interval == None:
			self.experiment.start_response_interval = self.get("time_%s" % \
				self.name)
			self.experiment.end_response_interval = \
				self.experiment.start_response_interval
		self.experiment.response = None

		if not self.file_loaded:
			raise exceptions.runtime_error("No video loaded")
			
		#Lock the surface for VLC input when backend is legacy or opengl
		if hasattr(self,"screen"):
			self.screen.lock()

		#Start movie playback
		self.player.play()
		debug.msg("Movie framerate: {0}".format(self.framerate))
		
		while self.player.get_state() == vlc.State.Opening:
			pass #Wait until movie has opened
		
		self.playing = True
		while self.player.get_state() != vlc.State.Ended and self.playing:		
			starttime = self.experiment.time()
			
			if self.playbackStarted and self.startPlaybackTime == 0:
				self.startPlaybackTime = self.experiment.time()
				
			if self._event_handler_always:
				self.playing = self.handleEvent()
			else:
				# Process pygame event (legacy and xpyriment)
				for event in pygame.event.get():
					if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
						if self._event_handler != None:
							self.playing = self.handleEvent(event)
						elif event.type == pygame.KEYDOWN and self.duration == \
							"keypress":
							self.playing = False
							self.experiment.response = pygame.key.name(event.key)
							self.experiment.end_response_interval = \
								pygame.time.get_ticks()
						elif event.type == pygame.MOUSEBUTTONDOWN and \
							self.duration == "mouseclick":
							self.playing = False
							self.experiment.response = event.button
							self.experiment.end_response_interval = \
								pygame.time.get_ticks()

						# Catch escape presses
						if event.type == pygame.KEYDOWN and event.key \
							== pygame.K_ESCAPE:
							raise exceptions.runtime_error( \
								"The escape key was pressed")

					# Check if max duration has been set, and exit if exceeded
					if type(self.duration) == int:
						if pygame.time.get_ticks() - startTime > \
							(self.duration*1000):
							self.playing = False

					# Check if max duration has been set, and exit if exceeded
					if type(self.duration) == int:
						if self.timer.getTime() - startTime > self.duration:
							self.playing = False
				
			#Send info to the eyelink if applicable
			if self.sendInfoToEyelink == "yes" and self.playbackStarted:
				if self.frame_duration > 0:
					self.sendFrameInfoToEyelink()
				else:
					# Maybe not necessary to raise an exception, but without
					# reliable frame info the data sent to the EyeLink is
					# virtually useless.
					raise exceptions.runtime_error( \
						"Cannot send reliable info to the EyeLink as there is no info about the frame rate of this movie.") 
				
			#Sleep for rest of frame
			if self.frame_duration > 0:
				sleeptime = int(self.frame_duration - \
					(self.experiment.time() - starttime))
				if sleeptime > 0:
					self.experiment.sleep(sleeptime) 
						

		#Stop playback
		self.player.stop()

		#Free the surface
		if hasattr(self,"screen"):
			self.screen.unlock()

		generic_response.generic_response.response_bookkeeping(self)
		return True

	def closePlayer(self):
		self.player.release()
		self.vlcInstance.release()
		self.media = None
		debug.msg("Released VLC modules")
		if hasattr(self, "screen"):
			self.screen = None

	def var_info(self):
		return generic_response.generic_response.var_info(self)

class qtmedia_player_vlc(media_player_vlc, qtplugin.qtplugin):

	"""Handles the GUI aspects of the plug-in"""

	def __init__(self, name, experiment, string = None):

		"""
		Constructor. This function doesn't do anything specific
		to this plugin. It simply calls its parents. Don't need to
		change, only make sure that the parent name matches the name
		of the actual parent.

		Arguments:
		name -- the name of the item
		experiment -- the opensesame experiment

		Keyword arguments:
		string -- a definition string for the item (Default = None)
		"""

		# Pass the word on to the parents
		media_player_vlc.__init__(self, name, experiment, string)
		qtplugin.qtplugin.__init__(self, __file__)

	def init_edit_widget(self):

		"""This function creates the controls for the edit widget"""

		# Lock the widget until we're doing creating it
		self.lock = True

		# Pass the word on to the parent
		qtplugin.qtplugin.init_edit_widget(self, False)

		# We don't need to bother directly with Qt4, since the qtplugin class contains
		# a number of functions which directly create controls, which are automatically
		# applied etc. A list of functions can be found here:
		# http://files.cogsci.nl/software/opensesame/doc/libqtopensesame/libqtopensesame.qtplugin.html
		self.add_filepool_control("video_src", "Video file", self.browse_video, \
			default = "", tooltip = "A video file")
		self.add_combobox_control("playaudio", "Play audio", ["yes", "no"], \
			tooltip= \
			"Specifies if the video has to be played with audio, or in silence")
		self.add_combobox_control("sendInfoToEyelink", \
			"Send frame no. to EyeLink", ["yes", "no"], tooltip= \
			"If an eyelink is connected, then it will receive the number of each displayed frame as a msg event.\r\nYou can also see this information in the eyelink's status message box.\r\nThis option requires the installation of the OpenSesame EyeLink plugin and an established connection to the EyeLink.")
		self.add_combobox_control("event_handler_trigger", \
			"Call custom Python code", ["on keypress", "after every frame"], \
			tooltip = "Determine when the custom event handling code is called.")
		self.add_line_edit_control("duration", "Duration", tooltip = \
			"Expecting a value in seconds, 'keypress' or 'mouseclick'")
		self.add_editor_control("event_handler", \
			"Custom Python code for handling keypress and mouseclick events (See Help for more information)", \
			syntax = True, tooltip = \
			"Specify how you would like to handle events like mouse clicks or keypresses. When set, this overrides the Duration attribute")
		self.add_text( \
			"<small><b>Media Player VLC OpenSesame Plugin v%.2f, Copyright (2010-2012) Daniel Schreij</b></small>" \
			% self.version)

		# Unlock
		self.lock = True

	def browse_video(self):

		"""
		This function is called when the browse button is clicked
		to select a video from the file pool. It displays a filepool
		dialog and changes the video_src field based on the selection.
		"""

		s = pool_widget.select_from_pool(self.experiment.main_window)
		if str(s) == "":
				return
		self.auto_line_edit["video_src"].setText(s)
		self.apply_edit_changes()

	def apply_edit_changes(self):

		"""
		Set the variables based on the controls. The code below causes
		this to be handles automatically. Don't need to change.

		Returns:
		True on success, False on failure
		"""

		# Abort if the parent reports failure of if the controls are locked
		if not qtplugin.qtplugin.apply_edit_changes(self, False) or self.lock:
			return False

		# Refresh the main window, so that changes become visible everywhere
		self.experiment.main_window.refresh(self.name)

		# Report success
		return True

	def edit_widget(self):

		"""
		Set the controls based on the variables. The code below causes
		this to be handled automatically. Don't need to change.
		"""

		# Lock the controls, otherwise a recursive loop might arise
		# in which updating the controls causes the variables to be
		# updated, which causes the controls to be updated, etc...
		self.lock = True

		# Let the parent handle everything
		qtplugin.qtplugin.edit_widget(self)
		
		self.auto_line_edit['duration'].setEnabled(self.auto_combobox[ \
			'event_handler_trigger'].currentIndex() == 0)
		
		# Unlock
		self.lock = False

		# Return the _edit_widget
		return self._edit_widget

