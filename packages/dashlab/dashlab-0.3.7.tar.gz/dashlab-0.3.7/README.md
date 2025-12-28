# DashLab

[![](https://jupyterlite.rtfd.io/en/latest/_static/badge.svg)](https://asaboor-gh.github.io/litepad/notebooks/index.html?path=dashlab.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/asaboor-gh/dashlab/HEAD?urlpath=%2Fdoc%2Ftree%2Fdemo.ipynb)
[![PyPI version](https://badge.fury.io/py/dashlab.svg)](https://badge.fury.io/py/dashlab)
[![Downloads](https://pepy.tech/badge/dashlab)](https://pepy.tech/project/dashlab)

An enhanced dashboarding library based on ipywidgets' interaction functionality that lets you observe any trait of widgets, observe multiple functions and build beautiful dashboards which can be turned into full screen.

![](interact.png)

## Installation

You can install dashlab using pip:

```bash
pip install dashlab
```

Or if you prefer to install from source, clone the repository and in its top folder, run:

```bash
pip install -e .
```

## Interactive Playground
**✨ Try it in your browser ✨**
| Jupyter Lab  | Notebook | Binder |
|----|---|--- |
|  [![](https://jupyterlite.rtfd.io/en/latest/_static/badge.svg)](https://asaboor-gh.github.io/litepad/lab/index.html?path=dashlab.ipynb)  |  [![](https://jupyterlite.rtfd.io/en/latest/_static/badge.svg)](https://asaboor-gh.github.io/litepad/notebooks/index.html?path=dashlab.ipynb) | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/asaboor-gh/dashlab/HEAD?urlpath=%2Fdoc%2Ftree%2Fdemo.ipynb) |

## Features

- **DashboardBase**: Create interactive dashboard applications with minimal code by extending the `dashlab.DashboardBase` class and defining methods with the `@callback` decorator.
- **Dashboard**: A ready-to-use dashboard class that allows quick setup of interactive dashboards without subclassing and supports callbacks after initialization.
- **Custom Widgets**: 
    - Included custom built widgets for enhanced interaction. 
    - Pass any DOMWidget as a parameter to `interact/interactive` functions unlike default `ipywidgets.interactive` behavior.
    - Observe any trait of the widget by `'widget_name.trait_name'` where `'widget_name'` is assigned to a `widget`/`fixed(widget)` in control parameters, OR `'.trait_name'` if `trait_name` exists on instance of interactive.
    - Tuple pattern (widget, 'trait') for trait observation where widget is accessible via params and trait value goes to callback.
    This is useful to have widget and trait in a single parameter, such as `x = (fig, 'selected')` for plotly FigureWidget. Other traits of same widget can be observed by separate parameters with `y = 'x.trait'` pattern.
    - You can use '.fullscreen' to detect fullscreen change and do actions based on that.
    - Use `.params` to acess widgets built with given parameters.
    - Use `var` to observe any python variable which is not a widget and trigger callbacks when `var.value` changes.
    - Add `ipywidgets.Button` to hold callbacks which use it as paramter for a click
- **Plotly Integration**: Modified plotly support with additional traits like `selected` and `clicked`
- **Markdown support**: 
    - Convert markdown to HTML widget using `dashlab.markdown` function.
    - `hstack` and `vstack` functions support markdown strings to automatically convert to HTML and place in stack.
- **JupyTimer**: A non-blocking widget timer for Jupyter Notebooks without threading/asyncio.
- **Event Callbacks**: Easy widget event handling with the `@callback` decorator inside the subclass of `DashboardBase` or multiple functions in `interact/interactive` functions.
- **Full Screen Mode**: Transform your dashboards into full-screen applications by added button.

## Usage Example

```python
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as ipw
import pandas as pd
import plotly.graph_objects as go
import dashlab as dl

dash = dl.Dashboard(
    fig = dl.patched_plotly(go.FigureWidget()), 
    html = dl.markdown('**Select Box/Lesso on figure traces**'),
    A = (1,10), omega = (0,20), phi = (0,10),
    sdata = 'fig.selected', cdata = 'fig.clicked', fs = '.isfullscreen',
)
@dash.callback('out-click', throttle = 200) # limit click rate by 200 ms
def on_click(cdata,html):
    display(pd.DataFrame(cdata or {}))

@dash.callback('out-select')
def on_select(sdata, html):
    plt.scatter(sdata.get('xs',[]),sdata.get('ys',[]))
    plt.show()

@dash.callback('out-fs')
def detect_fs(fig, fs):
    print("isfullscreen = ",fs)
    fig.layout.autosize = False # double trigger
    fig.layout.autosize = True

@dash.callback
def plot(fig:go.FigureWidget, A, omega,phi): # adding type hint allows auto-completion inside function
    fig.data = []
    x = np.linspace(0,10,100)
    fig.add_trace(go.Scatter(x=x, y=A*np.sin(omega*x + phi), mode='lines+markers'))

dash.set_css({
    '.left-sidebar':{'background':'whitesmoke'},
    ':fullscreen': {'height': '100vh'}}
)
dash.set_layout(
    left_sidebar=['A','omega','phi','html', 'out-select','out-main'], 
    center=['fig','out-click'], 
    pane_widths=[3,7,0],
)

dash
```
![dashboard.gif](dashboard.gif)

## Comprehensive Examples
- Check out the [demo.ipynb](demo.ipynb) which demonstates subclassing `DashboardBase`, using custom widgets, and observing multiple functions through the `@callback` decorator.
- See [Bandstructure Visualizer](https://github.com/asaboor-gh/ipyvasp/blob/d181ba9a1789368c5d8bc1460be849c34dcbe341/ipyvasp/widgets.py#L642) and [KPath Builder](https://github.com/asaboor-gh/ipyvasp/blob/d181ba9a1789368c5d8bc1460be849c34dcbe341/ipyvasp/widgets.py#L935) as comprehensive dashboards.
