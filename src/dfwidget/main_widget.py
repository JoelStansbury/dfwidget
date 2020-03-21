from ipywidgets import HTML, VBox
from ipyevents import Event

CSS = """
<style>
.dfwidget_main {
    width:90%;
    height:500px;
    border:1px solid black;
}

.dfwidget_main_inner_html {
    width:90%;
    margin:3px;
    height:500px;
    border:1px dotted red;
}

</style>

"""

class DataFrame(VBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = HTML()
        self.html = HTML()

        css = HTML(CSS)
        self.children = [self.html, self.output, css]

        self.add_class("dfwidget_main")
        self.html.add_class("dfwidget_main_inner_html")

        d = Event(
            source=self.html, 
            watched_events=['click', 'keydown', 'mouseenter']
        )

        def handle_event(event):
            if event["type"] == "click":
                x, y = event["relativeX"], event["relativeY"]
                self.output.value = f"{x},{y}"

        self.output.value = "waiting for event"
        d.on_dom_event(handle_event)
