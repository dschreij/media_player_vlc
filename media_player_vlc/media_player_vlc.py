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

from libopensesame import debug, generic_response
from libopensesame.exceptions import osexception
from libopensesame.item import item
from libqtopensesame.items.qtautoplugin import qtautoplugin
from openexp.mouse import mouse
from openexp.keyboard import keyboard
import pygame
import os
import sys
import vlc

# Try to import Mediainfo for obtaining statistics about the media file (like
# framerate and such).
# Download and install from: http://mediainfo.sourceforge.net/en/Download
# Python wrapper from: https://github.com/paltman/pymediainfo
try:
	from pymediainfo import MediaInfo
except ImportError:
	MediaInfo = None
	debug.msg(
		"MediaInfo module not found. This plug-in runs better with pymediainfo installed (http://paltman.github.com/pymediainfo/).",
		reason="warning")

class media_player_vlc(item, generic_response.generic_response):

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

		# Experimental variables
		self.var.resizeVideo = u"yes"
		self.var.duration = u"keypress"
		self.var.event_handler = u""
		self.var.event_handler_trigger = u"on keypress"
		self.var.video_src = u''
		self.var.playaudio = u"yes"

		# Internal variables
		self.file_loaded = False
		self.vlc_event_handler = None
		self.media = None
		self.hasMediaInfo = False
		self.process_feedback = True
		#See if MediaInfo functions are available
		try:
			MediaInfo.parse(u"")
			self.hasMediaInfo = True
		except:
			debug.msg(
				u"MediaInfo CLI not found. Frame info might be unavailable.",
				reason=u"warning")
			self.hasMediaInfo = False

	def _set_display_window(self):

		"""
		desc:
			Routes vlc output to correct experiment window dependig on the
			backend that is used.
		"""

		if u'canvas_backend' not in self.var or \
			self.var.canvas_backend not in [u'legacy', u'xpyriment']:
				raise osexception(
					u"Only the legacy and xpyriment back-ends are supported. Sorry!")
		win_id = pygame.display.get_wm_info()[u'window']
		debug.msg(u"Rendering video to window: {0}".format(win_id))
		if sys.platform == u"linux2": # for Linux using the X Server
			self.player.set_xwindow(win_id)
		elif sys.platform == u"win32": # for Windows
			self.player.set_hwnd(win_id)
		elif sys.platform == u"darwin": # for MacOS
			self.player.set_agl(win_id)
		else:
			raise osexception(u'Unknown platform: %s' % sys.platform)

	def prepare(self):

		"""
		desc:
			Opens the video file for playback and compiles the event handler
			code.

		returns:
			desc:	True on success, False on failure.
			type:	bool
		"""

		item.prepare(self)

		# Byte-compile the event handling code (if any)
		if self.var.event_handler.strip():
			self._event_handler = self.python_workspace._compile(
				self.var.event_handler)
			self._event_handler_always = \
				self.var.event_handler_trigger == u'after every frame'
		else:
			self._event_handler = None
			self._event_handler_always = False

		# Find the full path to the video file in the file pool, and check if it
		# can be found.
		path = self.experiment.pool[self.var.video_src]
		debug.msg(u"loading '%s'" % path)
		if not os.path.isfile(path):
			raise osexception(
				u"Video file '%s' was not found by video_player '%s' (or no video file was specified)."
				% (os.path.basename(path), self.name))

		# Read the framerate from the video file, and fall back to a default
		# framerate if this fails
		if self.hasMediaInfo:
			debug.msg(u"Reading file media parameters")
			mi = MediaInfo.parse(path)
			try:
				mi = MediaInfo.parse(path)
				for track in mi.tracks:
					if track.track_type == u"Video":
						self.framerate = float(track.frame_rate)
			except:
				raise osexception(
					u"Error parsing media file. Possibly the video file is corrupt")
		else:
			self.framerate = 30.
		self.frame_duration = 1000/self.framerate

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
			raise osexception(
				u"Error loading media file. Unsupported format?")

		# If playaudio is set to no, tell vlc to mute the movie
		if self.var.playaudio == u"no":
			self.player.audio_set_mute(True)
		else:
			self.player.audio_set_mute(False)
			# Solves bug in vlc bindings: unmute sets sound status to unmuted
			# but sets volume to 0
			self.player.audio_set_volume(75)

		# create reference to vlc event handler and set up event handling
		self.vlc_event_handler = self.player.event_manager()

		# Pass thru vlc output to experiment window
		self._set_display_window()

		# Indicate function for clean up that is run after the experiment
		# finishes
		self.experiment.cleanup_functions.append(self.closePlayer)

		if self.var.resizeVideo == u"no":
			self.player.video_set_scale(1.0)

		# Set response objects
		self.keyboard = keyboard(self.experiment, timeout=0)

	def handleEvent(self, event=None, resp=None):

		"""
		desc:
			Allows the user to insert custom code. Code is stored in the
			event_handler variable.

		arguments:
			event:
			 	desc:	A dummy argument passed by the signal handler

		returns:
			desc:	True if playback should continue, False otherwise.
			type:	bool
		"""

		self.python_workspace[u'continue_playback'] = True
		self.python_workspace[u'frame_no'] = self.frame_no
		self.python_workspace[u'key'] = resp
		self.python_workspace._exec(self._event_handler)
		return bool(self.python_workspace[u'continue_playback'])

	def run(self):

		"""
		desc:
			Starts the playback of the video file. You can specify an optional
			callable object to handle events between frames (like keypresses).
		"""

		# Prepare responses
		self.set_item_onset()
		self.set_sri(reset=True)
		self.experiment.var.response = None
		self.experiment.end_response_interval = self.sri
		# Start movie playback and wait until the movie has started
		self.player.play()
		while self.player.get_state() == vlc.State.Opening:
			pass
		# Loop until
		# - The video ended
		# - A timeout occurred (for integer durations)
		# - A key was pressed (for keypress durations)
		# - Playback was stopped in custom Python code
		self.playing = True
		self.starttime = self.clock.time()
		self.frame_no = 0
		while self.player.get_state() != vlc.State.Ended and self.playing:
			# Get a keyboard/ mouse response
			resp, t = self.keyboard.get_key()
			if resp is not None:
				self.experiment.var.response = resp
				self.experiment.end_response_interval = t
			# Call the event handler if a key was pressed or after every frame
			if self._event_handler is not None and \
				(self._event_handler_always or resp is not None):
				self.playing = self.handleEvent(resp=resp)
			# Check if a timeout occurred
			if type(self.var.duration) == int and \
				t - self.starttime > self.var.duration*1000:
				self.playing = False
			# Check for keypress endings
			if self.var.duration == u'keypress' and resp is not None:
				self.playing = False
			# Sleep for rest of frame
			sleeptime = self.frame_no * self.frame_duration - t + self.starttime
			if sleeptime > 0:
				self.clock.sleep(int(sleeptime))
			self.frame_no += 1
		self.player.stop()
		self.closePlayer()
		generic_response.generic_response.response_bookkeeping(self)

	def closePlayer(self):

		"""
		desc:
			Clean-up function.
		"""

		if self.released:
				return
		self.media.release()
		self.player.release()
		self.vlcInstance.release()
		self.media = None
		debug.msg(u"Released VLC modules")
		self.released = True

	def var_info(self):

		"""
		desc:
			Provide variable info.
		"""

		return generic_response.generic_response.var_info(self)

class qtmedia_player_vlc(media_player_vlc, qtautoplugin):

	def __init__(self, name, experiment, script=None):

		media_player_vlc.__init__(self, name, experiment, script)
		qtautoplugin.__init__(self, __file__)
