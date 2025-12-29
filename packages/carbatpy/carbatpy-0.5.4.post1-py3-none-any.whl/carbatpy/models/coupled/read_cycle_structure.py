# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 14:33:04 2023

@author: atakan
"""

import datetime
import pandas as pd
import graphviz as gv

DIRNAME = "..//..//data"
FILE_NAME = "orc_structure.xlsx"


def plot_cycle_structure(fname, dirname=DIRNAME, cycle_name="cycle",
                         format_="png",
                         engine="circo"):
    """
    read an Excel file with information about the cycle structure and use graphviz

    for visualization, a file is generated.

    Parameters
    ----------
    fname : string
        the excel filename.
    dirname : string, optional
        the directory name to read the file and to store afterwards. The default is DIRNAME.
    cycle_name : string, optional
        name of the cycle. The default is "cyle".
    format : String, optional
        plot-format (png, pdf etc). The default is "png".
    engine : string, optional
        an engine name from graphviz (dot, circo etc.). The default is "circo".

    Returns
    -------
    None.

    """

    verbose = False
    fname_exel = dirname + "//" + fname
    fname_out = dirname + "//" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M") +\
        cycle_name

    data = pd.read_excel(fname_exel, index_col=0)
    dot = gv.Digraph(cycle_name, comment='ORC in a Carnot Battery')
    dot.engine = engine
    dot.attr(rankdir="TB")

    for line_n, node_name in enumerate(data["Name(unique)"]):
        if data["in_cycle"].iloc[line_n]:
            shape = "box"
            style = "filled"
            color = "yellow"
            arrowhead = "normal"
            acolor = "red"
        else:
            shape = "egg"
            style = "filled"
            color = "cyan"
            arrowhead = "vee"
            acolor = "blue"

        dot.node(node_name, shape=shape, style=style, color=color)
        if pd.notnull(data["input1"].iloc[line_n]):
            label = str(line_n)
            dot.edge(data["input1"].iloc[line_n], node_name, label=label,
                     arrowhead=arrowhead,
                     color=acolor)
        if pd.notnull(data["output1"].iloc[line_n]):
            if not data["in_cycle"].iloc[line_n]:
                dot.edge(node_name, data["output1"].iloc[line_n],
                         label=str(line_n),
                         arrowhead=arrowhead,
                         color=acolor)

    if verbose:
        print(dot.source, fname_out)
    dot.render(format=format_, filename=fname_out, view=True)


if __name__ == "__main__":
    plot_cycle_structure(FILE_NAME, cycle_name="orc")
    plot_cycle_structure("hp_structure.xlsx", cycle_name="heat_pump")
