import flet as ft
from flet.core.column import Column
from flet.core.row import Row


class Container(ft.Container):
    # Class to add margin to the container

    def __init__(self, *args, margin=None, **kwargs):
        if margin is None:
            margin = ft.margin.only(left=120, top=0, bottom=0, right=120)

        super().__init__(*args, margin=margin, **kwargs)

class Controller:
    # Class creates a container for a page
    # with a title and content

    def __init__(self, page, app_settings, page_route):
        self.content = []

        self.page = page

        self.route = page_route

        self.app_settings = app_settings

    def build(self, text, content):

        self.content = content

        content.insert(0, ft.Text(text, size=30, weight=ft.FontWeight.BOLD, font_family="Inter"))
        container = Container(content=Column(content, spacing=24, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, expand=True), expand=True)

        return container

    def _refresh(self):
        pass
