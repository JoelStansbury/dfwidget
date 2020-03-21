# dfwidget
IPython widget for displaying pandas DataFrames (Jupyterlab)

Currently just an idea.

# Plan
* Table contents (cells) are in a single `HTML` element
* Use ipyevents to determine the location of the cursor within the widget
* Header is a row of `ipyw.Button()`s to sort the columns

## TODO:
 * Pretty much everything
 * I expect to be able to render very large tables using this method. I might look into using Cython to speed up the string concatonation. This is mainly because I want to learn Cython.
 
