# Desmos Graphs Within Jupyter
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

from IPython.display import Javascript, display


class HTMLString(str):
    def __new__(cls, value: str):
        return super().__new__(cls, value)

    def getvalue(self) -> str:
        return str(self)

    def get_value(self) -> str:
        return str(self)


def desmos_graph(expressions=[],
                 sliders=[],
                 points=[],
                 size=[1000, 400],
                 axlim=[-10, 10, -10, 10],
                 font=1,  # Desmos font size
                 javascript=False):
    """
    Create a Desmos graph in javascript format and display it in Jupyter.

    Examples:
        expressions = {'latex': '0.05x+0.10y<=150'},

        desmos_graph(expressions=expressions,
                     sliders=[],
                     points=[],
                     size=[1000, 400],
                     axlim=[-100, 2000, -100, 2000])

        graph_html = desmos_graph(expressions=expressions)
        with open('graph.html',"w",encoding="utf-8") as f:
            f.write(graph_html.getvalue())

        graph_html, graph_java = desmos_graph(expressions=expressions,
                                              javascript=True)
        from IPython.display import HTML,IFrame
        HTML(graph_html.getvalue())
        IFrame('graph.html',width='100%',height=400)

    Args:
        expressions: Optional. A dictionary of expressions formatted in
            Desmos syntax.
        sliders: Optional. A dictionary of sliders formatted in Desmos syntax.
        points: Optional. A dictionary of points formatted in Desmos syntax.
        size: A list of two elements denoting the figure size along x and y.
            Optional. Defaults to [1000, 400].
        axlim: A list of four elements denoting, in order, the x lower bound,
            x upper bound, y lower bound and y upper bound. Defaults to
            [-10, 10, -10, 10].
        font: A number denoting the font size. Defaults to 1, the default
            font size in Desmos.
        javascript: A Boolean value (True/False) indicating whether a
            javascript string should be returned. Defaults to ``False``.

    Returns:
        An html string containing the Desmos graph. This string can be
            displayed as a Desmos graph within Jupyter as shown in the
            examples listed above. Alternatively, this string can be saved
            as an html file to save the graph with the notebook.
        If ``javascript`` is set to ``True``, a javascript string generated
            by cropping the html string. This string can be pasted into the
            the Desmos calculator (https://www.desmos.com/calculator) console,
            which can be invoked on a browser by using Ctrl+Shft+J (Windows)
            or Cmd+Shft+J (Mac).

    """

    api = (
        "https://www.desmos.com/api/v1.11/calculator.js?" +
        "apiKey=dcb31709b452b1cf9dc26972add0fda6"
    )

    hsize = size[0]  # horizontal size of graph
    vsize = size[1]  # vertical size of graph

    lbor = axlim[0]  # left border (x-coordinate)
    rbor = axlim[1]  # right border (x-coordinate)
    bbor = axlim[2]  # bottom border (y-coordinate)
    tbor = axlim[3]  # top border (y-coordinate)

    indent = ''

    H = '<script src="' + api + '"></script>\n'

    H = (
        H +
        '<div id="calculator" style=' +
        '"width: hsizepx; height: vsizepx;"></div>\n'
    )

    H = H.replace('hsize', str(hsize))
    H = H.replace('vsize', str(vsize))

    H = H + '<script>\n'

    H = (
        H + indent +
        "var elt = document.getElementById('calculator');\n"
    )

    H = H + indent + 'var Calc = Desmos.GraphingCalculator(elt);\n'
    H = H + '\n'

    S = ''

    if expressions != [[]]:
        for exp in expressions:
            s = indent + 'Calc.setExpression({text'
            s = s.replace('text', f"latex:'{exp['latex']}'")
            if 'id' in exp.keys():
                s = s + f", id:'{exp['id']}'"
            if 'color' in exp.keys():
                s = s + f", color:'{exp['color']}'"
            if 'fillOpacity' in exp.keys():
                s = s + f", fillOpacity:'{exp['fillOpacity']}'"
            if 'hidden' in exp.keys():
                s = s + f", hidden:'{exp['hidden']}'"
            s = s + '})'

            S = S + s + '\n'
        S = S + '\n'

    if sliders != [[]]:
        for exp in sliders:
            s = indent + 'Calc.setExpression({text})'
            s = s.replace(
                'text',
                f"id:'{exp['variable']}', latex:'{exp['variable']}=0'"
            )
            S = S + s + '\n'

            s = indent + 'Calc.setExpression({text,sliderBounds:{sliderparams'
            s = s.replace('text', f"id:'{exp['variable']}'")
            if 'min' in exp.keys():
                s = s.replace('sliderparams', f"min:'{exp['min']}'")
            else:
                s = s + f", min:'{exp['min']}'"
            if 'max' in exp.keys():
                s = s + f", max:'{exp['max']}'"
            else:
                s = s + f", max:'{exp['max']}'"
            if 'step' in exp.keys():
                s = s + f", step:'{exp['step']}'"
            else:
                s = s + f", step:'{exp['step']}'"
            s = s + '}})'

            S = S + s + '\n'
        S = S + '\n'

    if points != [[]]:
        for exp in points:
            s = indent + 'Calc.setExpression({text'
            s = s.replace('text', f"latex:'{exp['latex']}'")
            if 'hidden' in exp.keys():
                s = s + f", hidden:'{exp['hidden']}'"
            if 'color' in exp.keys():
                s = s + f", color:'{exp['color']}'"
            if 'label' in exp.keys():
                s = s + f", label:'{exp['label']}'"
            if 'showLabel' in exp.keys():
                s = s + f", showLabel:'{exp['showLabel']}'"
            if 'labelOrientation' in exp.keys():
                s = s + f", labelOrientation:'{exp['labelOrientation']}'"
            if 'labelSize' in exp.keys():
                s = s + f", labelSize:'{exp['labelSize']}'"
            s = s + '})'

            S = S + s + '\n'
        S = S + '\n'

    s = (
        indent +
        'Calc.setMathBounds({left:lbor,right:rbor,bottom:bbor,top:tbor})'
    )
    s = s.replace('lbor', str(lbor))
    s = s.replace('rbor', str(rbor))
    s = s.replace('tbor', str(tbor))
    s = s.replace('bbor', str(bbor))
    S = S + s + '\n'  # axis ranges

    S = S + (
        indent + 'Calc.updateSettings' +
        '({showGrid:true,showXAxis:true,showYAxis:true,' +
        'lockViewport:true,expressionsCollapsed:true})\n'
    )

    H = H + S + '</script>\n'

    graph_html = H
    expr_java = S

    Sj = (
        indent + "element.style.height = '" + str(size[1]) + "px';\n" +
        indent + "element.style.width = '" + str(size[0]) + "px';\n" +
        indent + "var Calc = Desmos.GraphingCalculator(element);\n" +
        S
    )

    js = Javascript(Sj, lib=[api])
    display(js)

    if javascript is False:
        return HTMLString(graph_html)
    else:
        return HTMLString(graph_html), expr_java
