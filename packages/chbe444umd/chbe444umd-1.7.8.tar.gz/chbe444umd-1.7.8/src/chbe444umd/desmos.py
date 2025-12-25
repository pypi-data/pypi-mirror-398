# (C) Ganesh Sriram, gsriram@umd.edu
# Licensed under GNU Public License 3.0

# This script creates a Desmos graph and an html file that can be displayed in a Jupyter cell
# It was written specifically for CHBE444: ChE Design I, University of Maryland

# Changelog
# v. 1.4.0
#     Desmos graph is displayed using javascript, inspired by jdesmos
#     Semicolons are added to each line of Desmos code
#     Long lines of Desmos code are wrapped and indented
# v. 1.3.5
#     Default values of expressions, sliders and points are []
#     Two (long) strings are returned:
#         H (previously diagram_html)
#             An html string containing the Desmos graph
#             This string can be displayed in a notebook cell, where it appears as a Desmos graph
#             Alternatively, saving this string as an html file enables the graph to be saved with the notedbook
#         S
#             A subset of the html string containing a javascript of Desmos expressions
#             This string can be saved as a text file and pasted into the Desmos console
#     Both strings are composed line by line instead of being captured from the standard output
#     Backward compatibility allows the user to also print graph_html.getvalue() instead of just graph_html
#     Currently, graph.html.get_value is also supported


class HTMLString(str):
    def __new__(cls, value: str):
        return super().__new__(cls, value)

    def getvalue(self) -> str:
        return str(self)

    def get_value(self) -> str:
        return str(self)


def desmos_graph(
    expressions=[],
    sliders=[],
    points=[],
    size=[1000, 400],
    axlim=[-10, 10, -10, 10],
    font=1,
    javascript=False):   
    
    import numpy as np
    from IPython.display import Javascript, display

    api = "https://www.desmos.com/api/v1.11/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"
       
    hsize = size[0]  # horizontal size of graph
    vsize = size[1]  # vertical size of graph
    
    lbor = axlim[0]  # left border (x-coordinate)
    rbor = axlim[1]  # right border (x-coordinate)
    bbor = axlim[2]  # bottom border (y-coordinate)
    tbor = axlim[3]  # top border (y-coordinate)
 
    indent = ''  # indentation for html file
       
    H = '<script src="' + api + '"></script>\n'
    
    H = H + '<div id="calculator" style="width: hsizepx; height: vsizepx;"></div>\n'
    H = H.replace('hsize', str(hsize))
    H = H.replace('vsize', str(vsize))
    
    H = H + '<script>\n' 
    
    H = H + indent + "var elt = document.getElementById('calculator');\n"
    H = H + indent + 'var Calc = Desmos.GraphingCalculator(elt);\n'
    H = H + '\n'
       
    S = ''
    
    if expressions != [[]]:
        for exp in expressions:
            s = indent + 'Calc.setExpression({text'
            s = s.replace('text', f"latex:'{exp['latex']}'")
            if 'id' in exp.keys():
                s = s+f", id:'{exp['id']}'"
            if 'color' in exp.keys():
                s = s+f", color:'{exp['color']}'"
            if 'fillOpacity' in exp.keys():
                s = s+f", fillOpacity:'{exp['fillOpacity']}'"
            if 'hidden' in exp.keys():
                s = s+f", hidden:'{exp['hidden']}'"
            s = s + '});'

            S = S + s + '\n'
        S = S + '\n'
    
    if sliders != [[]]:
        for exp in sliders:
            s = indent + 'Calc.setExpression({text})'
            s = s.replace('text', f"id:'{exp['variable']}', latex:'{exp['variable']}=0'")
            S = S + s + '\n'
            
            s = indent + 'Calc.setExpression({text,sliderBounds:{sliderparams'
            s = s.replace('text', f"id:'{exp['variable']}'")
            if 'min' in exp.keys():
                s = s.replace('sliderparams', f"min:'{exp['min']}'")
            else:
                s = s+f", min:'{exp['min']}'"
            if 'max' in exp.keys():
                s = s+f", max:'{exp['max']}'"
            else:
                s = s+f", max:'{exp['max']}'"
            if 'step' in exp.keys():
                s = s+f", step:'{exp['step']}'"
            else:
                s = s+f", step:'{exp['step']}'"
            s = s + '}});'
            
            S = S + s + '\n'
        S = S + '\n'
    
    if points != [[]]:
        for exp in points:
            s = indent + 'Calc.setExpression({text'
            s = s.replace('text', f"latex:'{exp['latex']}'")
            if 'hidden' in exp.keys():
                s = s+f", hidden:'{exp['hidden']}'"
            if 'color' in exp.keys():
                s = s+f", color:'{exp['color']}'"
            if 'label' in exp.keys():
                s = s+f", label:'{exp['label']}'"
            if 'showLabel' in exp.keys():
                s = s+f", showLabel:'{exp['showLabel']}'"
            if 'labelOrientation' in exp.keys():
                s = s+f", labelOrientation:'{exp['labelOrientation']}'"
            if 'labelSize' in exp.keys():
                s = s+f", labelSize:'{exp['labelSize']}'"
            s = s + '});'
            S = S + s + '\n'
        S = S + '\n'
        
    s = indent + 'Calc.setMathBounds({left:lbor,right:rbor,bottom:bbor,top:tbor});'
    s = s.replace('lbor', str(lbor))
    s = s.replace('rbor', str(rbor))
    s = s.replace('tbor', str(tbor))
    s = s.replace('bbor', str(bbor))
    S = S + s + '\n'  # x and y ranges of graph
    
    S = (
        S + indent + 
        '''Calc.updateSettings({
        showGrid: true,
        showXAxis: true,
        showYAxis: true,
        lockViewport: true,
        expressionsCollapsed: true});\n
        '''
        )
    
    H = H + S + '</script>\n'

    graph_html = H
    expr_java = S

    Sj = (
        indent + "element.style.height = '" + str(size[1]) + "px';\n" +
        indent + "element.style.width = '" + str(size[0]) + "px';\n" + 
        indent + "var Calc = Desmos.GraphingCalculator(element);\n" +
        S)
    
    js = Javascript(Sj, lib=[api])
    display(js)
   
    if javascript == False:
        return HTMLString(H)
    else:
        return HTMLString(H), expr_java