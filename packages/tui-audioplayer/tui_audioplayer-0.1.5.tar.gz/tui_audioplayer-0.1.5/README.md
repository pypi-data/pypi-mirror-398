# AudioPlayer
![](res/audioplayer.png)

## New in this Version
### -- 23.12.2025 --
* Play URL added. Now you can enter an url to play it
### -- 21.12.2025 --
* Small design changes
* Playlist items can now be played by hiting enter key or mouse click
* Prepared for playlist editing - but still not working

## A textual.app for playing online radio streams
The app was actually developed for the Raspberry Pi to provide a simple but attractive interface for a Raspi LCD display.
However, the app works in principle on all Linux distributions that meet the following requirements:

* a terminal which supports Rich Python library
* can run a VLC-Player
* uses ALSA soundsystem (also pipewire with ALSA)

You can run the app also remote with *ssh*.

The app can also be controlled in a browser.  
To do so go into the `src/tui_audioplayer` directory and run `python3 server.py`

## Installation
you can install the app with ```pip install tui_audioplayer```  
`pipx` will not work :-(

You can also clone the repository  
go into te *src* folder and run ```python3 -m tui_audioplayer```

### On Raspi
If you want to install the package on a Raspi, you will possibly get an error.
The problem is the `pyalsa` package. This package has to be installed with `sudo apt install python3-pyalsa`
Then run `pip install tui_audioplayer` again.

## Playlist
The Playlist is the [JSON](https://www.xspf.org/jspf) version off XSPF. 

Each Category has its own folder in the *Playlist* folder.
You can create categories as you like.

Every category folder contains a playlist file (.jspf). The playlist file has the same name in lower case as the category e.g.:
category *Jazz* playlist file name *jazz.jspf*.

The playlist entries -the radio stations- are organized in *tracks* as followed:

* **location**: the url (in []) where the music comes from
* **title**: the radio station name
* **image**: the file name for the image of the radio station. The image is a 400x400 *png* in the same folder of the playlist. Please avoid spaces in file names.
 
To open and close the Playlist press the *p* key

![](res/playlist.png)

## Issues
* Key events are ignored for changing the volume, so changing the volume works only with mouse scrolling up or down.
