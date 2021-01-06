from ipywidgets import HTML, Button, HBox, VBox
from ipyevents import Event
from collections import deque
from traitlets import Int, observe, link

CSS = """
    <style>
    .dfwidget_main {
        border:1px solid black;
    }

    .row_even {
        background-color:white;
    }
    .row_odd {
        background-color:#f5f5f5;
    }
    .index {
        font-weight: bold;
        text-align: end;

    }
    .cell {
        padding-left: 2px;
        padding-right: 2px;
        text-align: end;
    }
    .header_btn {
        font-weight: bold;
        background-color:white;
    }

    .row_hover {
        background-color: #e1f5fe;

    }

    .content {
        border-top: 1px solid #bdbdbd;
    }

    </style>

    """


class _Cell(HTML):
    def __init__(self, data, width, style=None):
        super().__init__(layout={"width":width})
        self.add_class("cell")
        self.value = str(data)
    
    def update(self, data):
        self.value = str(data)


class _ButtonCell(Button):
    def __init__(self, data, width, callback, style=None):
        super().__init__(layout={"width":width})
        self.value = data
        self.add_class("cell")
        if style:
            self.add_class(style)
        self.description = str(data)
        self.on_click(callback)


class _Row(HBox):
    value = Int(-1).tag(sync=True)
    def __init__(self, data, widths, style=None, _types=None):
        super().__init__()
        self.data = data
        if style:
            self.add_class(style)
            self.style=style
        self.cells = [_Cell(x, w) for x,w in zip(data,widths)]
        self.cells[0].add_class("index")
        self.children = self.cells

        d  = Event(source=self, watched_events=['click'])
        d.on_dom_event(self.on_click)

    def update(self, data, style=None):
        self.data = data
        if style:
            if style != self.style:
                self.remove_class(self.style)
                self.add_class(style)
                self.style = style

        
        for i,c in enumerate(self.cells):
            c.update(data[i])

    def on_click(self, event):
        # set self.value to the row index of the dataframe
        self.value = -1
        self.value = int(self.data[0])


class _Header(HBox):
    def __init__(self, df, widths, content_widget, **kwargs):
        super().__init__()
        self.df = df
        self.content_widget = content_widget

        def sort_col(btn):
            self.df.sort_values(by=btn.value, inplace = True)
            self.content_widget.update()
        
        def sort_idx(btn):
            self.df.sort_index(inplace = True)
            self.content_widget.idx = 0
            self.content_widget.update()

        col_names = [""] + list(df.columns)
        callbacks = [sort_idx] + [sort_col]*len(df.columns)
        params = zip(col_names, widths, callbacks)

        self.children = [_ButtonCell(n,w,cb, style="header_btn") for n,w,cb in params]


class _Content(VBox):
    value = Int(-1).tag(sync=True)
    def __init__(self, df, to_show, widths, **kwargs):
        super().__init__(**kwargs)
        self.add_class("content")
        self.to_show = to_show
        self.num_rows = min(len(df), to_show if to_show%2==0 else to_show+1)
        self.idx = 0
        self.df = df
        self.records = df.to_records()
        styles = ["row_even","row_odd"]

        rows = [_Row(self.records[i], widths, style=styles[i%2]) for i in range(self.num_rows)]
        for row in rows:
            row.observe(self.set_val, "value")

        self.rows = deque(rows)

        self.children = list(self.rows)[0:self.to_show]
        d  = Event(source=self, watched_events=['wheel', "mousemove", "mouseleave"])
        d.on_dom_event(self.scroll)
        self.row_num = -1

    def set_val(self, event):
        if event["new"] != -1:
            self.value = event["new"]

    def update(self, _=None):
        self.records = self.df.to_records()
        for i in range(self.num_rows):
            idx = self.idx + i
            self.rows[i].update(self.records[idx])
        self.children = list(self.rows)[0:self.to_show]
        self.row_num = -1
        
    def on_hover(self, event):
        if "type" in event and event["type"] == "mouseleave":
            self.un_hover()
        else:
            h = event["boundingRectHeight"]
            row_height = h//self.to_show
            row_num = min(self.num_rows-1, abs(event["relativeY"]//row_height))
            if row_num != self.row_num:
                if self.row_num != -1:
                    self.rows[self.row_num].remove_class("row_hover")
                self.row_num = row_num
                self.rows[self.row_num].add_class("row_hover")

    def un_hover(self):
        if self.row_num !=-1:
            self.rows[self.row_num].remove_class("row_hover")
        
    def scroll(self, event=None):
        if "deltaY" in event:
            self.un_hover()
            self.row_num = -1
            if event["deltaY"] > 0: # down
                for i in range(int(event["deltaY"]/100)):
                    if self.idx+self.to_show < len(self.records):
                        self.idx += 1
                        n = self.idx + self.num_rows  - 1
                        aux = self.rows.popleft()
                        if n < len(self.records):
                            aux.update(self.records[n])
                        self.rows.append(aux)
            else: # up
                for i in range(int(-event["deltaY"]/100)):
                    if self.idx >0:
                        self.idx -= 1
                        aux = self.rows.pop()
                        aux.update(self.records[self.idx])
                        self.rows.appendleft(aux)
            self.children = [self.rows[i] for i in range(self.to_show)]
        else:
            self.on_hover(event)


class DataFrame(VBox):
    """
    num_rows: (int) number of rows to be displayed
    """
    value = Int().tag(sync=True)
    def __init__(self, df, **kwargs):
        self.num_rows = kwargs.get("num_rows", 10)
        widths = self.auto_width(df,kwargs.get("widths", None))

        super().__init__(layout={"width":self.width}, **kwargs)

        self.css = HTML(CSS)
        self.content = _Content(df, self.num_rows, widths)
        link((self.content, "value"), (self, "value"))

        self.header = _Header(df, widths, self.content)
        self.children = [self.header, self.content, self.css]

    def auto_width(self, df, override=None):
        """
        Uses the first `num_rows` elements of each column to determine
        the width of each row element.
        """

        cols = list(df.columns)
        ppc = 7
        spacing = 2
        widths = {}

        for c in cols:
            c_width = len(str(c))
            d_width = max([len(str(x)) for x in df[c].values[:self.num_rows]])
            widths[c] = max(c_width, d_width) + spacing

        widths["Index"] = len(str(len(df))) + spacing 
        cols = ["Index"] + cols
        total = sum(list(widths.values()))
        self.width = f"{total*ppc}px"

        return [f"{int(100*widths[k]/total)}%" for k in cols]
    