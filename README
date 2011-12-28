Copyright, 2010-2011, Daniel Schreij

1. ABOUT
========
The media_player plug-in adds video playback capabilities
to the OpenSesame experiment builder.

2. LINKS
========
- OpenSesame <http://www.cogsci.nl/opensesame>
- Plug-in page <http://osdoc.cogsci.nl/plug-ins/media-player-plug-in>

3. DEPENDENCIES
===============
- PyAudio <http://people.csail.mit.edu/hubert/pyaudio/>
- FFMpeg <http://www.ffmpeg.org/>
- PyFFMpeg <http://code.google.com/p/pyffmpeg/>

4. INSTALLATION INSTRUCTIONS
============================

4.1. WINDOWS XP
===============
The media_player plug-in is included with the binary package of Mac OS for
Windows. If you want to use the media_player while running OpenSesame from
source you need to follow these instructions. This has been tested with
Python 2.6.

- Install pyAudio for your Python version using the installer that is provided
  here:
  <http://people.csail.mit.edu/hubert/pyaudio/> 

- Download PyFFMpeg. This has been tested with 2.1 Beta. You need the 2.1
  Windows binaries package.
  <http://code.google.com/p/pyffmpeg/>
  Extract the files into the site-packages folder (directly, not into a
  subfolder)
  [Your Python folder]\Lib\site-packages

- Download the shared library binary of FFMpeg. This has been tested with
  version 0.7.1, but new versions are released regularly.  
  <http://ffmpeg.zeranoe.com/builds/win32/shared/>
  Extract the .dll files (which are in the "bin" subfolder of the archive) into
  a "ffmpeg" subfolder of site-packages
  [Your Python folder]\Lib\site-packages\ffmpeg
  
- Copy libgcc_s_dw2-1.dll into the same folder
  [Your Python folder]\Lib\site-packages\ffmpeg
  <http://www.cogsci.nl/dbbschreij/media_player/win32_resources/libgcc_s_dw2-1.dll>  
  
- Add the ffmpeg folder to the Path.
  My computer -> View system information -> Advanced -> Environment variables
  Select "path" under System variables and click "Edit".
  Add "[Your Python folder]\Lib\site-packages\ffmpeg;" to the path.
  
- Test if pyffmpeg has been installed properly by opening a Python prompt and
  typing:
  >>> import pyffmpeg
  This should return without error.
    
Finally, you will have to download the media_player plug-in and install it by
copying the media_player folder into the plug-in folder of OpenSesame. For more
information, see <http://osdoc.cogsci.nl/plug-ins/plug-in-installation>

4.2. LINUX
==========

You need to install PyAudio, FFMpeg and PyFFMpeg, PyAudio and FFMpeg are  most
likely in the repository of your linux distribution. E.g., under Ubuntu they can
be installed by typing:

$ sudo apt-get install ffmpeg python-pyaudio

You will have to install PyFFMpeg manually, by downloading the package from here
(tested with 2.1beta) and placing the files in one of the Python package
folders, such as

/usr/local/lib/python2.6/dist-packages/

Finally, you will have to download the media_player plug-in and install it by
copying the media_player folder into the plug-in folder of OpenSesame. For more
information, see <http://osdoc.cogsci.nl/plug-ins/plug-in-installation>

4.3. MAC OS
===========
<To do>




