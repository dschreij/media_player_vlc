# Media_player_vlc

The media_player plug-in plays back a video file. Many formats are
supported, but the playback quality of certain formats varies. The
recommended formats for now are *DivX or XVid* (avi) and *Flash Video*
(flv). For successful playback of *MPEG* (mpg) and *Windows Media* (wmv)
files, please make sure the files are not corrupt and the indices of
keyframes are intact. If this is not the case, it will result in choppy
playback and skipping audio.

## Response collection

The response will be set to the last keypress that was collected while the video was playing, or to None if no response was collected. Responses will be logged in the regular way. That is, the following variables will be set:

-   *response*
-   *response_time*
-   *correct*
-   *average_response\_time* (or *avg_rt*)
-   *accuracy* (or *acc*)

## Custom Python code

Any code that you enter under 'Custom Python code' will executed:

- After every frame, if 'Call custom Python code' is set to 'after every frame'; or
- After every keypress, if 'Call custom Python code' is set to 'on keypress'.

The code is executed in the same Python workspace as inline_script, so you can fully interact with the experiment. In addition, there are the following important global variables:

- `key` has the value of the current keypress, or `None` if no response was collected.
- `continue_playback` controls whether the experiment continues running.
- `frame_no` contains the current frame number.

For example, the following code snippet stops playback when the spacebar is pressed:

~~~ .python
if resp == 'space':
    continue_playback = False
~~~

## Other options

The following options are available:

-   *Video file*: A video file from the file pool. Which formats are
    supported depends on your platform, but most common formats (such as
    .avi and .mpeg) are supported everywhere.
-   *Play audio*: Specify if the sound that comes with the video has to
    be played. If *no* is selected, the sound is muted during playback
    of the video
-   *Resize to fit screen*: Indicates if the video needs to be resized
    so that it fits the entire screen. If not, the video will be
    displayed in the center of the display in its original dimensions.
-   *Call custom Python code*: See 'Custom Python code'
-   *Duration*: A duration in milliseconds, or 'keypress' to stop when a key is
    pressed.
