# Media_player

The media_player plug-in plays back a video file. Many formats are
supported, but the playback quality of certain formats varies. The
recommended formats for now are *DivX or XVid* (avi) and *Flash Video*
(flv). For successful playback of *MPEG* (mpg) and *Windows Media* (wmv)
files, please make sure the files are not corrupt and the indices of
keyframes are intact. If this is not the case, it will result in choppy
playback and skipping audio. The following options are available:

-   *Video file*: A video file from the file pool. Which formats are
    supported depends on your platform, but most common formats (such as
    .avi and .mpeg) are supported everywhere.

-   *Play audio*: Specify if the sound that comes with the video has to
    be played. If *no* is selected, the sound is muted during playback
    of the video

-   *Resize to fit screen*: Indicates if the video needs to be resized
    so that it fits the entire screen. If not, the video will be
    displayed in the center of the display in its original dimensions.

-   *Send frame no. to EyeLink*: If this PC can connect to an SR
    Research EyeLink, the media player can automatically log the number
    of each frame that is displayed. This makes it easier later to
    analyze the data file per frame. For this to work, it is required
    that the connection to the eyelink has been established already and
    that the OpenSesame eyelink plug-ins are installed.

-   *Call custom Python code*: In the text field below you can enter
    custom Python code. With his option you can determine if this code
    needs to be executed either

    1.  after a key has been pressed during the movie
    2.  after each frame of the movie.

    For more details, see the bottom of this page.

-   *Duration*: A duration in seconds, 'keypress' (to stop when a key is
    pressed) or 'mouseclick' (to stop when a mousbutton is clicked).

## Response collection

If you enter 'keypress' or 'mouseclick' as a duration, responses will be
logged in the regular way. That is, the following variables will be set:

-   *response*
-   *response_time*
-   *correct*
-   *average_response\_time* (or *avg_rt*)
-   *accuracy* (or *acc*)

## Custom event handling

If you want, you use your own code to handle keypress and mouseclick
events, which should be entered in the edit field. The PyGame event is
passed as 'event'. For example, in order to register if the spacebar is
pressed or if a mousebutton is clicked, you enter:

	if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
		print "Spacebar is pressed"
	if event.type == pygame.MOUSEBUTTONDOWN:
		print "Mouse button clicked"

Please refer to the PyGame documentation for more information:

- <http://www.pygame.org/docs/ref/key.html>

The number of the last played frame is also available under the
variable: `frame_no`
