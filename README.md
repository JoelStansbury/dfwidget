# dfwidget
IPython widget for displaying pandas DataFrames (Jupyterlab)

# Requirements
* ipywidgets
* nodejs
* ipyevents
* pandas

Prerequisites
```bash
pip install jupyterlab
pip install ipywidgets
pip install nodejs
pip install ipyevents
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install @jupyter-widgets/jupyterlab-manager ipyevents
pip install pandas
```

Installing `dfwidget`. 
From the package root...
```
pip install .
```

Alternatively, you could just copy and paste `src/dfwidget/main.py` wherever you want it so long as you have `ipyevents` working.



# Demo
<img src="examples/demo.gif" alt="alt text" width=200 height=300>

Currently the column headers will only sort the dataframe in ascending order.

The button above the index column resets the order and returns to the top.





 
