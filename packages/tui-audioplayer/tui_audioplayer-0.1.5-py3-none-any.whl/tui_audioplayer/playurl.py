from urllib.parse import urlparse
from textual import on
from pathlib import Path
from textual.screen import ModalScreen
from textual.widgets import Input, Static, Label, Button
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, Horizontal
from textual.validation import Function, Length, ValidationResult, Validator, URL

class PlayUrl(ModalScreen):

    CSS = """
            PlayUrl {
                align: center middle;

            }
            #dialog{
                padding: 1;

                width: 50%;
                height: 50%;
                background: #8f8f8f;
            }
            #play{
                dock: right;
            }
        """
    def __init__(self, player=None):
        super().__init__()
        self.player = player
        self.errors = dict()
        self.input_error = False

    def compose(self)->ComposeResult:
        yield Vertical(
            Horizontal(
                Label("URL", id="url"),
                Input(placeholder= "Inser a valid URL ...", validators=[URL()], id="input" ),
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
        if uri.is_valid:
            self.notify(f'Playing {uri.value}')

            self.player.play_url(uri.value)
            self.app.pop_screen()
        else:
            self.notify("Url not valid",severity="error")


    #@on(Input.Changed, "#input")
    #def show_invalid_uri(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
    #    if not event.validation_result.is_valid:
    #        self.input_error = True
    #        self.errors["url"] = str(event.validation_result.failure_descriptions)

    #    else:
    #        self.input_error = False
