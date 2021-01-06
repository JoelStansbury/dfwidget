from ipywidgets import HTML, Button, HBox, VBox
from ipyevents import Event
from collections import deque
from traitlets import Int, observe, link




class _Cell(HTML):
    def __init__(self, data, width):
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
    def __init__(self, data, widths, on_click, style, _types=None, **kwargs):
        super().__init__(**kwargs)
        self.add_class(style)
        self.observe(on_click, "value")
        d  = Event(source=self, watched_events=['click'])
        d.on_dom_event(self.on_click)

        self.data = data
        self.cells = [_Cell(x, w) for x,w in zip(data,widths)]
        self.cells[0].add_class("index")
        self.children = self.cells

    def update(self, data):
        '''Set the cell values to the new `data`'''
        self.data = data
        for i,c in enumerate(self.cells):
            c.update(data[i])

    def on_click(self, event):
        self.value = -1 # Ensures `value` registers a change event
        # Set self.value to the row index of the dataframe
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
    focus_idx = Int(-1).tag(sync=True)

    def __init__(self, df, to_show, widths, **kwargs):
        super().__init__(**kwargs)
        self.add_class("content")
        d  = Event(source=self, watched_events=['wheel', "mousemove", "mouseleave"])
        d.on_dom_event(self.event_handler)


        self.to_show = to_show
        self.num_rows = min(len(df), to_show if to_show%2==0 else to_show+1)
        self.idx = 0
        self.df = df
        self.records = df.to_records()
        def row_on_click(event):
            if event["new"] != -1:
                self.value = event["new"]
        self.rows = deque(
                [
                    _Row(
                        data=self.records[i], 
                        widths=widths, 
                        on_click=row_on_click,
                        style=["row_even","row_odd"][i%2])
                    for i in range(self.num_rows)
                ]
            )
        self.children = list(self.rows)[0:self.to_show]

    def update(self, _=None):
        # Need to redo this after sorting ( see _Header.__init__() )
        self.records = self.df.to_records()
        # Update each row
        for i in range(self.num_rows):
            idx = self.idx + i
            self.rows[i].update(self.records[idx])
        self.children = list(self.rows)[0:self.to_show]

    @observe("focus_idx")
    def focus(self, change):
        '''Controls the highlighting of rows'''
        old = change["old"]
        new = change["new"]
        if old != -1:
            self.rows[old].remove_class("row_hover")
        if new != -1:
            self.rows[new].add_class("row_hover")
        
    def on_hover(self, event):
        h = event["boundingRectHeight"]
        row_height = h//self.to_show
        y = event["relativeY"]
        i = abs(y//row_height)
        self.focus_idx = min(self.to_show-1, i) # Calls self.focus()

    def scroll(self, deltaY):
        self.focus_idx = -1 # Calls self.focus()
        if deltaY > 0: # down
            for i in range(int(deltaY/100)):
                if self.idx+self.to_show < len(self.records):
                    self.idx += 1
                    n = self.idx + self.num_rows  - 1
                    aux = self.rows.popleft()
                    if n < len(self.records):
                        aux.update(self.records[n])
                    self.rows.append(aux)
        else: # up
            for i in range(int(-deltaY/100)):
                if self.idx >0:
                    self.idx -= 1
                    aux = self.rows.pop()
                    aux.update(self.records[self.idx])
                    self.rows.appendleft(aux)
        self.children = [self.rows[i] for i in range(self.to_show)]
    
    def event_handler(self, event):
        if "deltaY" in event:
            self.scroll(event["deltaY"])
        elif "type" in event and event["type"] == "mouseleave":
            self.focus_idx = -1 # Calls self.focus()
        else:
            self.on_hover(event)


class DataFrame(VBox):
    """
    num_rows: (int) number of rows to be displayed
        default: 10
    cell_padding: (str) Padding to be applied around text
        default: "3px 2px 3px 2px"
    """
    value = Int().tag(sync=True)
    def __init__(self, df, num_rows=10, cell_padding="3px 2px 3px 2px", **kwargs):
        super().__init__(**kwargs)
        CSS = f"""
            <style>
            .dfwidget_main {{
                border:1px solid black;
            }}
            .row_even {{
                background-color:white;
            }}
            .row_odd {{
                background-color:#f5f5f5;
            }}
            .index {{
                font-weight: bold;
                text-align: end;
            }}
            .cell {{
                padding: {cell_padding};
                text-align: end;
                line-height: inherit;
                height: inherit;
            }}
            .header_btn {{
                font-weight: bold;
                background-color:white;
            }}
            .row_hover {{
                background-color: #e1f5fe;
            }}
            .content {{
                border-top: 1px solid #bdbdbd;
            }}
            </style>
            """
        width, widths = self.auto_width(df, num_rows)

        if not self.layout.width:
            self.layout.width = width

        self.css = HTML(CSS)
        self.content = _Content(df, num_rows, widths)
        link((self.content, "value"), (self, "value"))
        self.header = _Header(df, widths, self.content)
        self.children = [self.header, self.content, self.css]

    def auto_width(self, df, num_rows):
        """
        Uses the first `num_rows` elements of each column to determine
        the width of each row element.
        """

        cols = list(df.columns)
        ppc = 8 # Pixels per Character
        spacing = 1 # Padding (# characters)
        widths = {}

        for c in cols:
            c_width = len(str(c))
            d_width = max([len(str(x)) for x in df[c].values[:num_rows]])
            widths[c] = max(c_width, d_width) + spacing

        widths["Index"] = len(str(len(df))) + spacing 
        cols = ["Index"] + cols
        total = sum(list(widths.values()))

        return f"{total*ppc}px", [f"{int(100*widths[k]/total)}%" for k in cols]
    