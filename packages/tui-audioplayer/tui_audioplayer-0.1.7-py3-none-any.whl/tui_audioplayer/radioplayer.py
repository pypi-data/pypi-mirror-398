from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup, Container, Horizontal, Vertical, Center, Middle
from textual.widgets import Footer, Header, Label, Button, TabbedContent, TabPane, Markdown, Static, Digits, Link, Collapsible,  ListItem, ListView, Sparkline, ProgressBar, Log
from textual import work, events
from textual.worker import Worker, get_current_worker
from textual.color import Color, Gradient
from textual.widget import Widget
from textual.reactive import reactive
from textual_image.widget import Image
from textual.visual import VisualType


import time
import threading
from datetime import datetime
import vlc
import os
import sys
import random
import re

from pathlib import Path
print('Running' if __name__ == '__main__' else 'Importing', Path(__file__).resolve())
from pyalsa import alsamixer

from tui_audioplayer.clock import Clock
from tui_audioplayer.clock import Date
from tui_audioplayer.playlists import PlayList
from tui_audioplayer.playlists import PlaylistEdit
from tui_audioplayer.playurl import PlayUrl


CALENDAR = "'Waiting for the textual Calendar Widget :-)'"

DEBUG = False

class ClockWidget(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Clock()
        yield Date()

class VlcPlayer(Widget):
    
    def __init__(self, widget=None):
        super().__init__()
        self.path = os.path.join(os.path.dirname(__file__),"res","tui_audio.png")
        self.img = Image(self.path, classes="img-width height-auto")
        self.play_widget =  widget
        self.title = "-- No Station Selected --"
        self.running =  False
        self.update_thread =  None
        vlc_instance = vlc.Instance('-q') #quiet, supress output
        self.player = vlc_instance.media_player_new()
    

        
    CSS_PATH = "radioplayer.tcss"
        
        
    def compose(self) -> ComposeResult:
        
        with Horizontal(id="vlcplayer"):
            with Vertical(classes="hatch cross box", id="img"):
                self.img.image = self.path
                yield self.img
                
            with Vertical(classes="hatch cross box"):
                yield Label("Station",id="station")
                yield Label(f'Now playing: {self.title}', id='title')
                yield SoundView()
                #yield Label('Status: Stopped', id='status')
                if DEBUG:
                    yield Label('Debug: Ready', id='debug')
        
    def start_player(self, mrl: str) -> None:
        try:
            # Update Status sofort
            
            #self.query_one("#status", Label).update("Status: Starting...")
            if DEBUG:
                self.query_one("#debug", Label).update("Debug: Creating media...")
            
            media = vlc.Media(mrl)
            self.player.set_media(media)
            self.player.play()
            
            # Starte Update-Thread
            self.running = True
            if self.update_thread is None or not self.update_thread.is_alive():
                self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
                self.update_thread.start()
            
        
        except Exception as e:
            if DEBUG:
                self.query_one("#debug", Label).update(f"Debug: Error - {str(e)}")
            pass
        self.query_one(SoundView).start_snd()
        
    def stop_player(self):
        try:
            self.running = False
            if self.player:
                self.player.stop()
            self.query_one(SoundView).stop_snd()
            # Update UI
            self.query_one("#title", Label).update("Now playing: --- Stopped ---")
            #self.query_one("#status", Label).update("Status: Stopped")
            #self.query_one("#debug", Label).update("Debug: Stopped")
            
        except Exception as e:
            if DEBUG:
                self.query_one("#debug", Label).update(f"Debug: Stop error - {str(e)}")
            pass
    
        
        
    def update_loop(self):
        
        
        while self.running:
            
            try:
                # Update Status
                # self.app.call_from_thread(
                #     self.query_one("#status", Label).update, 
                #     f"Status: Playing )"
                # )
                
                media = self.player.get_media()
                if media:
                    # Parse Metadata
                    media.parse_with_options(vlc.MediaParseFlag.network, 0)
                    time.sleep(1)
                    
                    # Hole Metadaten
                    now_playing = media.get_meta(vlc.Meta.NowPlaying)
                    title = media.get_meta(vlc.Meta.Title)
                    artist = media.get_meta(vlc.Meta.Artist)
                    
                    # Debug-Info
                    debug_parts = []
                    if now_playing:
                        debug_parts.append(f"NP: {now_playing[:30]}")
                    if title:
                        debug_parts.append(f"T: {title[:30]}")
                    if artist:
                        debug_parts.append(f"A: {artist[:30]}")
                    
                    debug_text = " | ".join(debug_parts) if debug_parts else f"No meta data"
                    
                    if DEBUG:
                        # Update Debug
                        self.app.call_from_thread(
                            self.query_one("#debug", Label).update, 
                            f"Debug: {debug_text}"
                        )
                    
                    # Get Title
                    # display_title = ""
                    # if now_playing:
                    #     display_title = now_playing
                    # elif title and artist:
                    #     display_title = f"{artist} - {title}"
                    # elif title:
                    #     display_title = title
                    # else:
                    #     display_title = f"No Data. Stream active - try {iteration}"
                    
                    # Update Titel
                    self.app.call_from_thread( self.query_one("#title", Label).update, f'{now_playing}' )
                    # Update Station
                    self.app.call_from_thread( self.query_one("#station", Label).update, f'{title}' )
                    # Update Volume
                    self.app.call_from_thread(
                        self.play_widget.set_volume
                    )
                    
                elif DEBUG:
                    self.app.call_from_thread(
                        self.query_one("#debug", Label).update, 
                        f"Debug: No media object (try {iteration})"
                    )
                    
            except Exception as e:
                if DEBUG:
                    self.app.call_from_thread(
                        self.query_one("#debug", Label).update, 
                        f"Debug:-- {str(e)}"
                    )
                pass
            
            time.sleep(1)
            

class Player(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.title = "-- No Url Selected --"
        self.url = ""
        self.player = VlcPlayer(self)
        self.is_playing = False
        
        
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            if self.is_playing:
                self.player.stop_player()
                #self.is_playing = False
                #event.button.label = "\u25B6"
                self.btn_changeStatus(False,event.button)
            else:
                self.play()
                #self.is_playing = True
                #event.button.label = "\u25FC"
                self.btn_changeStatus(True,event.button)
           
    def btn_changeStatus(self, status,  btn) -> None:
        self.is_playing = status
        if status:
            btn.label = "\u25FC"
            btn.styles.background = "red"
           
        else:
            btn.label = "\u25B6"
            btn.styles.background = "green"
        
    
    def play(self):
        self.player.start_player(self.url)
        
    def set_volume(self):
        self.query_one(VolumeBar).update_volume()
    
    def compose(self) -> ComposeResult:
        
        with Vertical(id="player-top"):
            with Container():
                yield self.player
            
            with Horizontal(id="player-bottom"):
                yield Button("play", id="start", disabled=True)
                yield VolumeBar()
                
    

class SoundView(Sparkline):
    
    data = reactive(None)
    running = reactive(False)
    snd_thread = reactive( None)
    sp = reactive(None)
    
    
    def on_mount(self):
        pass
        #self.start_snd()
    
    def start_snd(self):
        try:
            self.running = True
            if self.snd_thread is None or not self.snd_thread.is_alive():
                self.snd_thread = threading.Thread(target=self.update_data_loop, daemon=True, name="Sound")
                self.snd_thread.start()
        except Exception as e:
            self.query_one("#debug",Label).update(e)
        
    
    
    def stop_snd(self):
        self.running = False
        self.data = [0]
        self.update_data()
    
    def update_data_loop(self):
        
        while self.running:
            random.seed()
            self.data = [random.expovariate(1 / 3) for _ in range(500)]
            #self.app.call_from_thread(self.query_one('#debug',Label).update, str(self.data[0]))
            self.app.call_from_thread(self.update_data)
            time.sleep(0.1)

        
    def update_data(self):
        sp = self.query_one("#snd",Sparkline)
        sp.data = self.data

    def compose(self) -> ComposeResult:
        yield Sparkline(self.data, summary_function=max, id="snd")

class VolumeBar(ProgressBar):
    def __init__(self):
        super().__init__()
        self.progressbar = None
        self.max_volume = 65536 #Alsa max value
        self.setup_gradients()
    
    def compose(self) -> ComposeResult:
        
        self.progressbar = ProgressBar(total=100, gradient=self.gradient1, show_eta=False, id="volbar")
        self.progressbar.border_title = "Volume"
        yield Label("\U0001F50A" ,id="vol_ico")
        yield self.progressbar
        if DEBUG:
            yield Label("Debug: ", id="dbg")
        
    def setup_gradients(self):
        self.gradient1 = Gradient.from_colors(
            "#aaff00",
            "#55ff00",
            "#00aa00",
            "#4f9d00",
            # "#fcec0c",
            # "#fce327",
            # "#fcbf44",
            # "#fc633d",
            # "#fc3022"
        )
        self.gradient2 = Gradient.from_colors(
            #"#fcec0c",
            "#fce327",
            "#aaff00",
            "#55ff00",
            # "#00aa00",
            "#4f9d00",
            "#4f9d00",
            "#4f9d00",
            
            # "#fcbf44",
            # "#fc633d",
            # "#fc3022"
        )
        self.gradient3 = Gradient.from_colors(
            "#fc3022",
            "#fc633d",
            "#fcec0c",
            "#fce327",
            "#aaff00",
            "#55ff00",
            "#00aa00",
            "#4f9d00",
            
        )
    
    def setup_alsa(self):
        mixer = alsamixer.Mixer()
        mixer.attach()
        mixer.load()
        self.alsa = alsamixer.Element(mixer, "Master")
        
        
    
    def update_volume(self):
        volume = (self.alsa.get_volume()/self.max_volume)*100
        self.progressbar.update(progress=volume)
        
    
    def increase_volume(self):
        #self.progressbar.advance()
        volume = self.alsa.get_volume() + (self.max_volume / 100)
        if volume <= self.max_volume:
            self.query_one("#vol_ico").update("\U0001F50A")
            self.alsa.set_volume_tuple([int(volume),int(volume)])
            self.update_volume()
        
    def decrease_volume(self):
        volume = self.alsa.get_volume() - (self.max_volume / 100)
        if volume >= 0:
            self.alsa.set_volume_tuple([int(volume),int(volume)])
            self.update_volume()
        if volume <= 0:
            self.query_one("#vol_ico").update("\U0001F507")
        
            
        
    def on_key(self, event: events.Key)-> None:
        if event.key == "down":
            self.decrease_volume()
        elif event.k == "up":
            self.increase_volume()

    def on_click(self, event):
        self.focus()

    def on_mouse_scroll_up(self, event) -> None:
        self.increase_volume()
        
    def on_mouse_scroll_down(self, event) -> None:
        self.decrease_volume()

    def on_mount(self) -> None:
        self.setup_alsa()
        self.update_volume()
        #self.progressbar.update(total=100,advance=0)
    
class RadioPlayerApp(App):
    def __init__(self) -> None:
        self.player = Player()
        super().__init__()
    
    """A Textual app to manage radio streams."""
    CSS_PATH = "radioplayer.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),
                ("m", "show_tab('music')", "Player"),
                ("c", "show_tab('clock')", "Clock"),
                ("k", "show_tab('calendar')", "Calendar"),
                ("i", "play_url", "Play URL"),
                ("p", "show_playlist()","Playlist"),
                ("e", "collapse_or_expand(False)", "Expand All"),
                ("b", "edit_playlist","Edit Playlist"),

                
            
    ]

    sb_visible = reactive(False,bindings=True)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        #self.sb_visible = False
        yield Header()
        yield Footer()
        self.sidebar = Static("Sidebar1", id="sidebar")
        #yield self.sidebar
        pl = PlayList()
        with self.sidebar:
            Link.on_click(self)
            for p in pl.playlists:
                data = pl.get_playlist_data(p)
                with Collapsible(title=p):
                    with ListView():
                        cat = data['playlist']['title']
                        for d in data['playlist']["track"]:
                            yield ListItem(Label(f"[@click=app.play('{d['location'][0]}','{cat}','{d['image']}')]{d['title']}[/]", classes="l"))
           
        with TabbedContent(initial="music"):
            with TabPane("Music", id="music"):
                with Container():
                    yield self.player
            with TabPane("Clock", id="clock"):
                yield ClockWidget()
            with TabPane("Calendar", id="calendar"):
                yield Markdown(CALENDAR)

    def on_list_view_selected(self,list_view):
        #pass
        label = list_view.item.children[0].visual.spans
        l = re.search(r'(\(.*\))',label[0][2])
        p = l.group(0)
        p = p.strip('()')
        p = p.replace('\'','')

        params = p.split(',')
        self.notify(f"Playing {list_view.item.children[0].visual}")
        self.action_play(params[0],params[1],params[2])
    
    def action_play(self,url,cat,image):
        #self.query_one("#sidebar").styles.background = "red"
        self.player.player.img.image =   os.path.join(os.path.dirname(__file__),"Playlists",cat,image)        #path to image

        self.player.url = url

        self.player.play()
        btn = self.query_one("#start",Button)
        btn.disabled = False
        self.player.btn_changeStatus( True,  btn)

    def play_url(self,url):

        self.player.url = url
        self.player.play()
        btn = self.query_one("#start",Button)
        btn.disabled = False
        self.player.btn_changeStatus( True,  btn)


    
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:

        if action == "collapse_or_expand" and not self.sb_visible:
            return None
        if action == "edit_playlist" and not self.sb_visible:
            return None

        return True


    def action_show_playlist(self):
        
        if not self.sb_visible:
            self.sidebar.styles.animate("width", value=35,duration=1)
            self.sb_visible = True
        else:
            self.sidebar.styles.animate("width", value=0, duration=1)
            self.sb_visible = False
            
    def action_collapse_or_expand(self, collapse: bool) -> None:
        for child in self.walk_children(Collapsible):
            child.collapsed = collapse  
    
    def action_open_link(self):
        pass
    
    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.query_one(TabbedContent).active = tab
                
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_edit_playlist(self):
        self.push_screen(PlaylistEdit())

    def action_play_url(self):
        self.push_screen(PlayUrl(self))


#if __name__ == "__main__":
#    app = RadioPlayerApp()
#    app.run()
