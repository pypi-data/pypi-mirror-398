import sys
import os
import json
from urllib.parse import urlparse
from textual import on
from textual.suggester import SuggestFromList
from pathlib import Path
from textual.screen import ModalScreen
from textual.widgets import Input, Static, Label, Button
from textual.app import ComposeResult
from textual.containers import Grid
from textual.validation import Function, Length, ValidationResult, Validator, URL

class PlaylistEdit(ModalScreen):

    CSS = """
            PlaylistEdit {
                align: center middle;

            }

            #dialog{
                grid-size: 3;
                grid-gutter: 1;
                padding: 0 1 1 1;
                grid-rows: 15% 1fr 1fr;
                grid-columns: 35% 1fr 50%;
                width: 60%;
                height: 70%;
                background: #8f8f8f;
            }

            #pl_image{
                row-span: 3;
            }

            #pl_title{
                height: 1fr;
                width: 1fr;
                content-align: center middle;
                column-span: 3
            }


            #cancel{
                align: center middle;
            }
          """

    def __init__(self):
        super().__init__()
        self.pl_name = ""
        self.pl_uri = ""
        self.pl_img = ""
        self.pl_cat = ""
        self.playlist = PlayList()
        self.categories = list(self.playlist.get_categories())
        self.errors = dict()
        self.input_error = False

    def compose(self)->ComposeResult:
        yield Grid(
                Label("Add A Playlist Item", id="pl_title"),
                Static(id="pl_image"),
                Label("Name"),
                Input(id="pl_name",validators=[Length(minimum=2,maximum=30)]),
                Label("Category"),
                Input(id="pl_cat",suggester=SuggestFromList(self.categories, case_sensitive=False)),
                Label("URL"),
                Input(id="pl_uri",validators=[URL()]),
                Static(), #place holder
                Button("Cancel",id="cancel"),
                Button("OK",id="save"),
                id="dialog",
            )



    @on(Input.Changed,"#pl_name")
    def show_invalid_name(self, event: Input.Changed) -> None:
        if not event.validation_result.is_valid:
            self.input_error = True
            self.errors["name" ] = str(event.validation_result.failure_descriptions)
        else:
            self.input_error = False

    @on(Input.Changed, "#pl_uri")
    def show_invalid_uri(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if not event.validation_result.is_valid:
            self.input_error = True
            self.errors["url"] = str(event.validation_result.failure_descriptions)

        else:
            self.input_error = False


    @on(Button.Pressed,"#save")
    def add_pldata(self, event: Button.Pressed) -> None:
        if not self.input_error:
            #TODO: save Result
            self.pl_name =  self.query_one("#pl_name").value


            self.app.pop_screen()
        else:
            for err in self.errors:
                self.notify(self.errors[err],title=err,severity="error", timeout=10)

    @on(Button.Pressed,"#cancel")
    def close_pop_up(self,event: Button.Pressed) -> None:
        self.app.pop_screen()


class SaveUnsorted():
    def __init__(self):
        super().__init__()
        self.path = os.path.join(os.path.dirname(__file__),"Playlists","Unsorted","unsorted.jspf")
        self.pl_data = None
        self.image = "unsorted.png"

        self.open_pl()

    def open_pl(self):
        with open(self.path, mode="r", encoding="utf-8") as pl_file:
            self.pl_data = json.load(pl_file)


    def add_to_pl(self,location,title):
        track = {}
        track["location"]= [location]
        track["title"] = title
        track["image"] = self.image
        self.pl_data["playlist"]["track"].append(track)
        json_data = json.dumps(self.pl_data, indent=4)
        with open(self.path, mode="w", encoding="utf-8") as pl_file:
            pl_file.write(json_data)




class PlayList():
    def __init__(self):
        super().__init__()
        self.list_dir = os.path.join(os.path.dirname(__file__),"Playlists")
        print("PL: ",self.list_dir)


        self.playlists = []
        self.get_playlists()
        #self.create_playlist()
        #self.add2Playlist()

    def get_playlists(self)->None:
        pl = Path( self.list_dir)

        for dir in pl.iterdir():
            print(dir)
            pl = str(dir).split("/")
            self.playlists.append(pl[len(pl)-1])


    def get_playlist_data(self,playlist: str)->dict:
        pl = playlist.lower()+".jspf"
        p = Path(self.list_dir)
        path = p / playlist / pl
        data = {}
        if os.path.exists(path):
            js = open(path,"r", encoding="utf-8")
            try:
                data = json.load(js)
            except json.JSONDecodeError as e:
                print(f'json error!\n check your playlist file at {e.lineno}')
                print(e.msg)

        else:
            print(path, " notfound")

        return data

    def get_categories(self)->list:
        pl = Path( self.list_dir)
        categories = dict()

        for dir in pl.iterdir():
            categories[os.path.basename(dir)]=dir

        return categories

    def mk_category(self, category: str )->None:
        p = Path(self.list_dir)
        # make sure that first char is capitalized to ensure to
        # create a valid dirname
        dirname = category.capitalize()
        path = p / dirname

        if os.path.exists(path):
            return
        else:
            path.mkdir()

#     def get_playlist_icon(self,playlist: str)->str:
#         path = Path(self.list_dir)
#         ip = path / playlist / "folder.svg"
#
#         if os.path.exists(ip):
#             return str(ip)
#         else:
#             return ""
#
#     def create_playlist(self):
#
#         lists = self.parent.toolBox.count()
#
#         for i, p in enumerate(self.playlists):
#             icon = self.get_playlist_icon(p)
#             if i < lists:
#                 self.parent.toolBox.setItemText(i,p)
#                 if len(icon) > 0:
#                     self.parent.toolBox.setItemIcon(i,QIcon(icon))
#             else:
#                 qlist = QListWidget(self)
#                 self.parent.toolBox.addItem(qlist,QIcon(icon),p)
#
#             self.parent.toolBox.setCurrentIndex(i)
#             data = self.get_playlist_data(p)
#             if len(data) > 0:
#                 self.add2Playlist(p, data['playlist']['track'], self.parent.toolBox.currentWidget().children()[0])
#
#         self.parent.toolBox.setCurrentIndex(0)
#
#     def add2Playlist(self,pl: str, items: list, qlist: QListWidget):
#         path = f'{self.list_dir}/{pl}'
#         for item in items:
#             plItem = QListWidgetItem()
#             plItem.setText(item['title'])
#             #print(item['location'][0])
#             plItem.setData(3,item['location'][0])
#             plItem.setIcon(QIcon(f"{path}/{item['image']}"))
#             #print(type(qlist))
#             qlist.addItem(plItem)
        #plItem.setText("88.7 WSIE The Jazz Station")
        #plItem.setData(1,"http://streaming.siue.edu:8000/wsie")
        #plItem.setIcon(QIcon("Playlists/Jazz/WSIE_TheJazzStation.png"))


