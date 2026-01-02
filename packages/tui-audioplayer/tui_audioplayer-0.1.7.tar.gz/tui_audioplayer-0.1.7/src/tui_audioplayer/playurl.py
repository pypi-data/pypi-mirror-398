from urllib.parse import urlparse
from textual import on
from pathlib import Path
from textual.screen import ModalScreen
from textual.widgets import Input, Static, Label, Button
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, Horizontal
from textual.validation import Function, Length, ValidationResult, Validator, URL
from tui_audioplayer.playlists import SaveUnsorted

class PlayUrl(ModalScreen):

    CSS = """
            PlayUrl {
                align: center middle;

            }
            #dialog{
                padding: 1;

                width: 60%;
                height: 70%;
                background: #8f8f8f;
            }
            #play{
                dock: right;
            }
            .hz{
                margin: 1;
            }
            .auto{
                width: 1fr;
            }
        """
    def __init__(self, player=None):
        super().__init__()
        self.player = player
        self.errors = dict()
        self.input_error = False
        self.su = SaveUnsorted()

    def compose(self)->ComposeResult:
        yield Vertical(
            Horizontal(
                Label("Title"),
                Input(placeholder="Insert a title... (min 3 chars)", validators=[Length(minimum=3,maximum=None)],id="pl_title"),
                classes= "hz",
                ),
            Horizontal(
                Label("URL", id="url"),
                Static(classes="auto"),
                Input(placeholder= "Inser a valid URL ...", validators=[URL()], id="input" ),
                classes="hz",
            ),
            Horizontal(
                Button("Cancel",id="cancel"),
                Button("Play",id="play"),
            ),
                id="dialog"
        )

    @on(Button.Pressed,"#cancel")
    def close_pop_up(self,event: Button.Pressed) -> None:
        self.app.pop_screen()

    @on(Button.Pressed,"#play")
    def play_uri(self,event: Button.Pressed)-> None:
        uri = self.query_one("#input")
        title = self.query_one("#pl_title")

        if uri.is_valid:
            self.notify(f'Playing {uri.value} Title: {title.value}')
            self.su.add_to_pl(uri.value, title.value)
            self.player.play_url(uri.value)

            self.app.pop_screen()
        else:
            self.notify("Url not valid",severity="error")


