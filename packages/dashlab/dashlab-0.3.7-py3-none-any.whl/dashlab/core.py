import markdown as mdlib

from contextlib import suppress
from IPython.display import display

from ipywidgets import DOMWidget, HTML, HBox, VBox

from .base import _docs, DashboardBase, callback, _useful_traits
from .utils import _format_docs, _fix_init_sig

@_format_docs(**_docs)
def interactive(*funcs:list[callable], post_init: callable=None, **kwargs):
    """Enhanced interactive widget with multiple callbacks, grid layout and fullscreen support.

    This function is used for quick dashboards. Subclass `DashboardBase` for complex applications.
    {features}
    **Basic Usage**:    

    ```python
    from dashlab import interactive, callback, monitor
    import ipywidgets as ipw
    import plotly.graph_objects as go
    
    fig = go.FigureWidget()
    
    @callback('out-plot', timeit=True)  # check execution time
    def update_plot(x, y, fig):
        fig.data = []
        fig.add_scatter(x=[0, x], y=[0, y])
    
    def resize_fig(fig, fs):
        fig.layout.autosize = False # double trigger
        fig.layout.autosize = True # plotly's figurewidget always make trouble with sizing
    
    # Above two functions can be merged since we can use changed detection
    @monitor  # check execution time
    def respond(x, y, fig , fs, changed):
        if 'fs' in changed: # or changed('fs')
            fig.layout.autosize = False # double trigger
            fig.layout.autosize = True
        else:
            fig.data = []
            fig.add_scatter(x=[0, x], y=[0, y])
    
    dashboard = interactive(
        update_plot,
        resize_fig, # responds to fullscreen change
        # respond, instead of two functions
        x = ipw.IntSlider(0, 0, 100),
        y = ipw.FloatSlider(0, 1),
        fig = ipw.fixed(fig),
        changed = '.changed', # detect a change in parameter
        fs = '.isfullscreen', # detect fullscreen change on instance itself
    )
    ```

    **Parameters**:     

    - `*funcs`: One or more callback functions
    - post_init: Optional function to run after all widgets are created as lambda self: (self.set_css(), self.set_layout(),...). 
      You can annotate the type in function argument with `DashboardBase` to enable IDE hints and auto-completion e.g. `def post_init(self:DashboardBase): ...`
    - `**kwargs`: Widget parameters

    **Widget Parameters**:     
    {widgets}
    **Callbacks**:   
    {callbacks}  
    **Attributes and Traits**:
    {props}
    **Notes**:       

    - Avoid modifying global slide state
    - Use widget descriptions to prevent name clashes
    - See set_css() method for styling options
    - interactive(no_args_func,) is perfectly valid and run on button click to do something like fetch latest data from somewhere.
    
    **Python dictionary to CSS**
    {css_info}
    """
    class Interactive(DashboardBase): # Encapsulating
        def _interactive_params(self): return kwargs # Must be overriden in subclass
        def _registered_callbacks(self): return funcs # funcs can be provided by @callback decorated methods or optionally ovveriding it
        
        def __dir__(self): # avoid clutter of traits for end user on instance
            return ['set_css','set_layout','gather', 'groups','outputs','params','isfullscreen','changed', 'layout', *_useful_traits] 
        
        def __init__(self):
            super().__init__()
            if callable(post_init):
                if len(post_init.__code__.co_varnames) != 1:
                    raise TypeError("post_init should be a callable which accepts instance of interact as single argument!")
                post_init(self) # call it with self, so it can access all methods and attributes
    return Interactive()

    
@_format_docs(other=interactive.__doc__)
def interact(*funcs:list[callable], post_init: callable=None, **kwargs) -> None:
    """{other}

    **Tips**:    

    - You can use this inside columns using delayed display trick, like code`write('First column', C2)` where code`C2 = Slides.hold(Slides.ei.interact, f, x = 5) or Slides.ei.interactive(f, x = 5)`.
    - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *funcs, post_init=post_init, **kwargs))
    return inner


@_fix_init_sig
@_format_docs(**_docs)
class Dashboard(DashboardBase):
    """A ready-to-use interactive dashboard application which allows registering callbacks after initialization.
    {features}
    **Parameters**:
    - interactive_params: kwargs, parameters for interactive widgets, must be provided at initialization.

    **Widget Parameters** (`interactive_params` passed at initialization):
    {widgets}
    **Callbacks**:   
    {callbacks}
    **Attributes and Traits**:
    {props}
    **Usage**:

    ```python
    from dashlab import Dashboard
    app = Dashboard(x=5, y=True, z='.params') # no callbacks yet
    
    @app.callback('out-f') # creates an output widget with class/name 'out-f'
    def f(x, z):
        print(x) # prints value of x
        print(z.x) # prints reper of IntSlider build internally by x parameter
        print(app.params == z) # True, as z is a reference to params 
        
    @app.callback # without class, will use main output widget
    def g(x,y):
        print(x+5,y)
    
    # after adding callbacks, we can set CSS and layout to include all output widgets created
    app.set_layout(left_sidebar=['*ctrl'],center=['*out'])
    
    app # at end of cell to display the app
    ```
    
    This class is different from `DashboardBase`, `interactive` and `interact` functions, as it allows registering callbacks dynamically after the app is created, much like a regular app framework.
    This enables you to build interactive applications step by step, adding functionality as needed instead of defining every callback upfront.
    
    **Notes**:
    - Do not use gloabal callback decorator here which will not add any effect, use `app.callback` instead.
    - This class does not support subclassing, use DashboardBase if you need to create a custom interactive app.
    
    
    """
    def __init_subclass__(cls, **kwargs):
        raise TypeError(f"{cls.mro()[1]} does not support subclassing. Subclass DashboardBase if you really need to do so.")

    def __init__(self, **interactive_params):
        self._iapp_params = interactive_params
        self._iapp_callbacks = {} # ensures unique functions
        super().__init__()
    
    def __dir__(self): # avoid clutter of traits for end user on instance
        return ['callback', 'set_css','set_layout', 'gather', 'groups','outputs','params','isfullscreen','changed', 'layout', *_useful_traits] 

    def _interactive_params(self): return self._iapp_params
    def _registered_callbacks(self): return tuple(self._iapp_callbacks.values())

    def callback(self, output:str = None, *, timeit:bool = False, throttle:int = None, debounce:int = None, logger:callable = None) -> callable:
        """Decorator to register a callback function in Dashboard after initialization.
        This is different from the @callback decorator used in DashboardBase, as it allows dynamic registration of callbacks.
        
        **Parameters**:
        - output: str, optional name for the callback's output widget. Must be prefixed 'out-' for CSS class and widget name acess.
        - timeit: bool, if True, logs function execution time.
        - throttle: int, minimum interval between calls.
        - debounce: int, delay before trailing call.
        - logger: callable, optional logging function (e.g. print or logging.info).
        
        **Usage**:
        ```python
        @app.callback('out-f', timeit=True) # app is an instance of Dashboard class
        def my_callback(x, y):
            print(f"x: {x}, y: {y}")
        ```
        
        **Notes**:
        - The callback function must accept parameters defined in the interactive_params of the app.
        - If output is not provided, the callback will use the main output widget.
        
        **Returns**: The decorated function itself, which is registered as a callback in the app.
        """
        def decorator(func):
            wrapped = callback(output, timeit=timeit, throttle=throttle, debounce=debounce, logger=logger)
            if not callable(output):
                wrapped = wrapped(func)
            self._iapp_callbacks[wrapped.__name__] = wrapped
            self._handle_callbacks() # re-handle callbacks to include new one
            return wrapped
        
        if callable(output):
            return decorator(output)
        return decorator
    

def markdown(md:str, extensions=None) -> HTML:
    """Parse and render markdown text in dashboard as HTML widget.
    Markdown extensions can be provided as a list of strings or markdown.Extension instances for Python-Markdown.
    """
    return HTML(mdlib.markdown(md, extensions=extensions or []))

def _set_sizes(sizes, children, name):
    if not isinstance(sizes, (list, tuple)):
            raise TypeError(f'{name}s should be a list or tuple of sizes, got {type(sizes)}')
        
    if len(sizes) != len(children):
        raise ValueError(f"Argument '{name}s' must have same length as 'objs', got {len(sizes)} and {len(children)}")
        
    for s in sizes:
        if not isinstance(s, (int, float)):
            raise TypeError(f'{name} should be an int or float, got {type(s)}')
        
    total = sum(sizes)
    return [s/total*100 for s in sizes]

def hstack(objs: list, widths: list=None, **layout_props):
    """Stack widget representation of objs in columns with optionally setting widths (relative integers). Returns a widget.
    
    Only str and widgets are supported. Strings are rendered as markdown using Python-Markdown.
    layout_props are applied to container widget's layout.
    """
    children = [markdown(obj) if not isinstance(obj, DOMWidget) else obj for obj in objs]
    if widths is not None:
        widths = _set_sizes(widths, children, 'width')
        for w, child in zip(widths, children):
            with suppress(BaseException): # some widgets like plotly don't like to set dimensions this way
                child.layout.min_width = "0px" # avoids overflow
                child.layout.flex = f"{w} 1"
                child.layout.width = f"{w}%" 

    return HBox(children=children, layout = layout_props)

def vstack(objs: list, heights: list=None, **layout_props):
    """Stack widget representation of objs vertically with optionally setting heights (relative integers). Returns a widget.
    
    Only str and widgets are supported. Strings are rendered as markdown using Python-Markdown.
    layout_props are applied to container widget's layout. Set height of container to apply heights on children.
    """
    children = [markdown(obj) if not isinstance(obj, DOMWidget) else obj for obj in objs]
    if heights is not None:
        heights = _set_sizes(heights, children, 'height')
        for h, child in zip(heights, children):
            with suppress(BaseException): # some widgets like plotly don't like to set dimensions this way
                child.layout.min_height = "0px" # avoids overflow
                child.layout.flex = f"{h} 1"
                child.layout.height = f"{h}%"

    return VBox(children=children, layout=layout_props)

    