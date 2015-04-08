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

from libopensesame import item, debug, generic_response
from libopensesame.exceptions import osexception
from libqtopensesame import pool_widget
from libqtopensesame.items.qtautoplugin import qtautoplugin
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
			"This plug-in requires that VLC player 2.X is installed in the default location. You can download VLC player for free from http://www.videolan.org/. Error: %s"
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

	description = u"Plays a video from file"

	def reset(self):

		"""
		desc:
			Initialize/ reset the plug-in.
		"""

		self.file_loaded = False
		self.resizeVideo = u"yes"
		self.duration = u"keypress"
		self.playaudio = u"yes"
		self.sendInfoToEyelink = u"no"
		self.event_handler = u""
		self.event_handler_trigger = u"on keypress"
		self.vlc_event_handler = None

		self.media = None
		self.framerate = 0
		self.frame_duration = 0
		self.startPlaybackTime = 0
		self.playbackStarted = False
		self.hasMediaInfo = False

		#See if MediaInfo functions are available
		try:
			MediaInfo.parse(u"")
			self.hasMediaInfo = True
		except:
			debug.msg( \
				u"MediaInfo CLI not found. Frame info might be unavailable.",
				reason=u"warning")
			self.hasMediaInfo = False

	def _set_display_window(self):

		"""
		Routes vlc output to correct experiment window dependig on the opensesame
		backend used
		"""

		if self.has(u"canvas_backend"):
			backend = self.get(u"canvas_backend")
			if backend in [u"legacy", u"xpyriment"]:
				win_id = pygame.display.get_wm_info()[u'window']
			else:
				raise osexception( \
					u"Only the legacy and xpyriment back-ends are supported. Sorry!")

		debug.msg(u"Rendering video to window: {0}".format(win_id))

		if sys.platform == u"linux2": # for Linux using the X Server
			self.player.set_xwindow(win_id)
		elif sys.platform == u"win32": # for Windows
			self.player.set_hwnd(win_id)
		elif sys.platform == u"darwin": # for MacOS
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
		if not self.has(u"canvas_backend"):
			raise osexception(u"Backend not initialized!")

		# Byte-compile the event handling code (if any)
		if self.event_handler.strip() != "":
			self._event_handler = compile(self.event_handler, u"<string>", \
				u"exec")
		else:
			self._event_handler = None

		# Determine when the event handler should be called
		if self.event_handler_trigger == u"on keypress":
			self._event_handler_always = False
		else:
			self._event_handler_always = True
			if self._event_handler is None:
				raise osexception(
					u'No event-handling code specified in %s' % self.name)

		# Find the full path to the video file. This will point to some
		# temporary folder where the file pool has been placed
		path = self.experiment.get_file(str(self.eval_text(self.get( \
			u"video_src"))))

		debug.msg(u"loading '%s'" % path)

		# Open the video file
		if not os.path.exists(path) or str(self.eval_text(u"video_src")) \
			.strip() == "":
			raise osexception( \
				u"Video file '%s' was not found by video_player '%s' (or no video file was specified)." \
				% (os.path.basename(path), self.name))

		if self.hasMediaInfo:
			debug.msg(u"Reading file media parameters")
			mi = MediaInfo.parse(path)
			try:
				mi = MediaInfo.parse(path)
				for track in mi.tracks:
					if track.track_type == u"Video":
						self.framerate = float(track.frame_rate)
						if self.framerate < 1:
							debug.msg(u"Frame rate info unavailable!", \
								reason=u"warning")
						else:
							self.frame_duration = 1000/self.framerate
			except:
				raise osexception( \
					u"Error parsing media file. Possibly the video file is corrupt")

		self.vlcInstance = vlc.Instance(u"--no-video-title-show")
		self.player = self.vlcInstance.media_player_new()

		try:
			self.media = self.vlcInstance.media_new(path)
			self.player.set_media(self.media)
			self.media.parse()
			self.file_loaded = True

			# Determines if cleanup is necessary later
			# If vlc memory is freed, set to True.
			self.released = False
		except:
			raise osexception( \
				u"Error loading media file. Unsupported format?")

		# If playaudio is set to no, tell vlc to mute the movie
		if self.playaudio == u"no":
			self.player.audio_set_mute(True)
		else:
			self.player.audio_set_mute(False)
			# Solves bug in vlc bindings: unmute sets sound status to unmuted but
			# sets volume to 0
			self.player.audio_set_volume(75)

		# create reference to vlc event handler and set up event handling
		self.vlc_event_handler = self.player.event_manager()

		# Send info to eyelink if it is found attached
		if self.sendInfoToEyelink == u"yes":
			self.vlc_event_handler.event_attach( \
				vlc.EventType.MediaPlayerTimeChanged, self.startCheck)

		# Pass thru vlc output to experiment window
		self._set_display_window()

		# Indicate function for clean up that is run after the experiment finishes
		self.experiment.cleanup_functions.append(self.closePlayer)

		if self.resizeVideo == u"no":
			self.player.video_set_scale(1.0)

		# Reinitialize variables
		self.playbackStarted = False
		self.startPlaybackTime = 0

	def startCheck(self, event):

		"""
		TODO: Informative docstring
		"""

		# Check for player init of the time and start frame counting
		self.playbackStarted = True

	def sendFrameInfoToEyelink(self):

		"""
		Sends frame info to the eye link log file which enables to create
		frame-based message reports
		"""

		if self.frame_duration > 0:
			frame_no = int((self.experiment.time() - self.startPlaybackTime) \
				/ self.frame_duration)
			if hasattr(self.experiment, u"eyelink") and \
				self.experiment.eyelink.connected():
				self.experiment.eyelink.log(u"videoframe {0}".format(frame_no) )
				self.experiment.eyelink.status_msg(u"videoframe {0}".format( \
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

		if event is not None and event.type == pygame.KEYDOWN:
			key = pygame.key.name(event.key)
		else:
			key = None

		continue_playback = True

		try:
			exec(self._event_handler)
		except Exception as e:
			raise osexception( \
				u"Error while executing event handling code: %s" % e)

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
			self.experiment.start_response_interval = self.get(u"time_%s" % \
				self.name)
			self.experiment.end_response_interval = \
				self.experiment.start_response_interval
		self.experiment.response = None

		if not self.file_loaded:
			raise osexception(u"No video loaded")

		#Start movie playback
		self.player.play()
		debug.msg(u"Movie framerate: {0}".format(self.framerate))

		while self.player.get_state() == vlc.State.Opening:
			pass #Wait until movie has opened

		self.playing = True
		self.starttime = self.experiment.time()
		while self.player.get_state() != vlc.State.Ended and self.playing:

			if self.playbackStarted and self.startPlaybackTime == 0:
				self.startPlaybackTime = self.experiment.time()

			if self._event_handler_always:
				self.playing = self.handleEvent()
			else:
				# Process pygame event (legacy and xpyriment)
				for event in pygame.event.get([pygame.KEYDOWN,
					pygame.MOUSEBUTTONDOWN]):
					if self._event_handler != None:
						self.playing = self.handleEvent(event)
					elif event.type == pygame.KEYDOWN and self.duration == \
						u"keypress":
						self.playing = False
						self.experiment.response = pygame.key.name(event.key)
						self.experiment.end_response_interval = \
							pygame.time.get_ticks()
					elif event.type == pygame.MOUSEBUTTONDOWN and \
						self.duration == u"mouseclick":
						self.playing = False
						self.experiment.response = event.button
						self.experiment.end_response_interval = \
							pygame.time.get_ticks()

					# Catch escape presses
					if event.type == pygame.KEYDOWN and event.key \
						== pygame.K_ESCAPE:
						raise osexception( \
							u"The escape key was pressed")

			# Check if max duration has been set, and exit if exceeded
			if type(self.duration) == int:
				if self.experiment.time() - self.starttime > \
					(self.duration*1000):
					self.playing = False

			#Send info to the eyelink if applicable
			if self.sendInfoToEyelink == "yes" and self.playbackStarted:
				if self.frame_duration > 0:
					self.sendFrameInfoToEyelink()
				else:
					# Maybe not necessary to raise an exception, but without
					# reliable frame info the data sent to the EyeLink is
					# virtually useless.
					raise osexception( \
						u"Cannot send reliable info to the EyeLink as there is no info about the frame rate of this movie.")

			#Sleep for rest of frame
			if self.frame_duration > 0:
				sleeptime = int(self.frame_duration - \
					(self.experiment.time() - self.starttime))
				if sleeptime > 0:
					self.experiment.sleep(sleeptime)

		#Stop playback
		self.player.stop()

		#Clean up player memory
		self.closePlayer()

		generic_response.generic_response.response_bookkeeping(self)

	def closePlayer(self):
		if not self.released:
			self.media.release()
			self.player.release()
			self.vlcInstance.release()
			self.media = None
			debug.msg(u"Released VLC modules")
			self.released = True

	def var_info(self):
		return generic_response.generic_response.var_info(self)

class qtmedia_player_vlc(media_player_vlc, qtautoplugin):

	"""GUI part of the plug-in."""

	def __init__(self, name, experiment, script=None):

		"""
		Constructor.

		Arguments:
		name		--	The item name.
		experiment	--	The experiment object.

		Keyword arguments:
		script		--	The definition script. (default=None).
		"""

		media_player_vlc.__init__(self, name, experiment, script)
		qtautoplugin.__init__(self, __file__)

	def apply_edit_changes(self):

		"""Applies changes to the controls."""

		qtautoplugin.apply_edit_changes(self)
		self.update_controls()

	def edit_widget(self):

		"""Updates the controls."""

		self.update_controls()
		return qtautoplugin.edit_widget(self)

	def update_controls(self):

		"""Media-player-specific control updates."""

		# The duration field is enabled or disabled based on whether a custom
		# event handler is called or not.
		self.line_edit_duration.setEnabled( \
			self.combobox_event_handler_trigger.currentIndex() == 0)
		if len(self.event_handler.strip()) > 0:
			self.user_hint_widget.add(
				u'Keypress and mouseclick durations are ignored if you use event-handling code. Use `continue_playback = False` to stop playback.')
			self.user_hint_widget.refresh()
