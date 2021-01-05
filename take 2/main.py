from ipywidgets import HTML, Button, HBox, VBox
from ipyevents import Event
from collections import deque
from time import time

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
        self.add_class("cell")
        if style:
            self.add_class(style)
        self.description = str(data)
        self.on_click(callback)


class _Row(HBox):
    def __init__(self, data, widths, style=None, _types=None):
        super().__init__()
        if style:
            self.add_class(style)
            self.style=style
        self.cells = [_Cell(x, w) for x,w in zip(data,widths)]
        self.cells[0].add_class("index")
        self.children = self.cells

        # d  = Event(source=self, watched_events=['mouseenter'])
        # d.on_dom_event(self.mouse_on)
        # d  = Event(source=self, watched_events=['mouseleave'])
        # d.on_dom_event(self.mouse_out)

    def update(self, data, style=None):
        if style:
            if style != self.style:
                self.remove_class(self.style)
                self.add_class(style)
                self.style = style

        
        for i,c in enumerate(self.cells):
            c.update(data[i])

    # def mouse_on(self, event):
    #     print(event)
    #     if event["deltaY"] == 0:
    #         self.add_class("row_hover")
    # def mouse_out(self, event):
    #     self.remove_class("row_hover")

class _Header(HBox):
    def __init__(self, df, widths, content_widget, **kwargs):
        super().__init__()
        self.df = df
        self.content_widget = content_widget

        def sort_col(btn):
            self.df.sort_values(by=btn.description, inplace = True)
            self.content_widget.update()
        
        def sort_idx(btn):
            self.df.sort_index(inplace = True)
            self.content_widget.update()

        col_names = [""] + list(df.columns)
        callbacks = [sort_idx] + [sort_col]*len(df.columns)
        params = zip(col_names, widths, callbacks)

        self.children = [_ButtonCell(n,w,cb, style="header_btn") for n,w,cb in params]


class _Content(VBox):
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
        self.rows = deque(rows) ### DEQUE ###
        # self.rows = rows ### NO DEQUE ###

        self.children = list(self.rows)[0:self.to_show]
        d  = Event(source=self, watched_events=['wheel', "mousemove", "mouseleave"])
        d.on_dom_event(self.scroll)
        self.row_num = -1
    
    def update(self, _=None):
        self.records = self.df.to_records()
        for i in range(self.num_rows):
            idx = self.idx + i
            self.rows[i].update(self.records[idx])
        self.children = list(self.rows)[0:self.to_show]
        
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

        ### NO DEQUE ###
        # if event["deltaY"] > 0: # down
        #     if self.idx+self.to_show < len(self.records):
        #         self.idx += 1
        # else: # up
        #     if self.idx >0:
        #         self.idx -= 1
        
        # styles = ["row_even","row_odd"]
        # for i in range(self.num_rows):
        #     n = self.idx+i
        #     self.rows[i].update(self.records[n], style=styles[n%2])

        ### DEQUE ###
        if "deltaY" in event:
            self.un_hover()
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
            self.children = [self.rows[i] for i in range(self.num_rows)]
        else:
            self.on_hover(event)


class DataFrame(VBox):
    """
    num_rows: (int) number of rows to be displayed
    widths: dict(
                str(column_name): 
                int(num_characters),
                ...
            )
    """
    def __init__(self, df, **kwargs):
        # .get() any kwargs needed by self, and ignored by super
        num_rows = kwargs.get("num_rows", 10)
        widths = self.auto_width(df,kwargs.get("widths", None))

        super().__init__(layout={"width":self.width}, **kwargs)

        self.css = HTML(CSS)
        self.content = _Content(df, num_rows, widths)
        self.header = _Header(df, widths, self.content)
        self.children = [self.header, self.content, self.css]

    def auto_width(self, df, override=None):
        """
        Uses the pandas formatter to determine the width (number of characters) of each column.
        """
        # TODO:
        #   - if all override skip the to_string

        header_str = df.to_string().split("\n")[0]
        columns = [str(c) for c in df.columns]
        df.columns = columns
        widths = {}
        cursor = 0
        for c in columns:
            end = header_str.find(c) + len(c)
            widths[c] = end - cursor
            cursor = end
        if override is not None:
            widths.update(override)
        total = sum(list(widths.values()))
        widths["index"] = len(str(len(df)-1))+3
        cols = ["index"] + columns

        self.width = f"{total*8}px"

        return [f"{int(100*widths[k]/total)}%" for k in cols]

    