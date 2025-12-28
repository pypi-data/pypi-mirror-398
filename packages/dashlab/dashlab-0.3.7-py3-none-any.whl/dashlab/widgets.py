import time
import traitlets

from pathlib import Path
from ipywidgets import ValueWidget, GridBox, Stack
from anywidget import AnyWidget

from html import escape
from . import utils

__all__ = ['FullscreenButton', 'ListWidget', 'AnimationSlider', 'JupyTimer']

class FullscreenButton(AnyWidget):
    """A button widget that toggles fullscreen mode for its parent element.
    You may need to set `position: relative` on parent element to contain it inside.
    """
    
    _esm = Path(__file__).with_name('static') / 'fscreen.js'
    _css = Path(__file__).with_name('static') / 'fscreen.css'
    
    isfullscreen = traitlets.Bool(False, read_only=True).tag(sync=True)

    def __init__(self):
        super().__init__()
        self.layout.width = 'min-content'
        

@utils._fix_trait_sig
class ListWidget(AnyWidget,ValueWidget):
    """List widget is a flexible widget that displays clickable items with integer indices and rich html content.
    
    - `options`: List[Any], each item can be any python object.
    - `description`: str, will be displayed as a label above the list.
    - `value`: Any, currently selected value. 
    - `transform`: Callable, function such that transform(item) -> str, for each item in options. Default is `repr`.
    - `html`: str, HTML representation of the currently selected item through transform.
    - `vertical`: bool, if False, display as tabs instead of list. If you want to use as tabs, consider using `TabsWidget` instead.

    You can set `ListWidget.layout.max_height` to limit the maximum height (default 400px) of the list. The list will scroll if it exceeds this height.
    """
    _options    = traitlets.List(read_only=True).tag(sync=True) # will by [(index, obj),...]
    description = traitlets.Unicode('Select an option', allow_none=True).tag(sync=True)
    transform   = traitlets.Callable(None, allow_none=True,help="transform(value) -> str")
    index       = traitlets.Int(None, allow_none=True).tag(sync=True)
    options     = traitlets.List() # only on backend
    value       = traitlets.Any(None, allow_none=True,read_only=True) # only backend
    html        = traitlets.Unicode('',read_only=True, help="html = transform(value)")  # This is only python side
    vertical    = traitlets.Bool(True,help="If False, display as tabs instead of list").tag(sync=True)
    
    _esm = Path(__file__).with_name('static') / 'listw.js'
    _css = Path(__file__).with_name('static') / 'listw.css'
    
    def __init__(self, *args, **kwargs):
        if kwargs.get('transform', None) is None:
            def default_transform(obj):
                if isinstance(obj, str):
                    return obj
                if hasattr(obj, '_repr_svg_'):
                    return getattr(obj, '_repr_svg_')()
                elif hasattr(obj, '_repr_html_'):
                    return getattr(obj, '_repr_html_')()
                else:
                    return escape(repr(obj)) # escap as most repr return str with <,>
            kwargs['transform'] = default_transform
            
        super().__init__(*args, **kwargs)
        self.layout.max_height = '400px' # default max height
    
    @traitlets.validate('index')
    def _set_value_html(self,proposal):
        index = proposal['value']
        if index is None:
            self.set_trait('html','')
            self.set_trait('value',None)
            return index 
        
        _max = len(self.options) - 1
        if isinstance(index, int) and 0 <= index <= _max :
            self.set_trait('html',self._options[index][1]) # second item is html
            self.set_trait('value',self.options[index]) 
            return index
        else:
            raise ValueError(f"index should be None or integer in bounds [0, {_max}], got {index}")

    @traitlets.validate('options')
    def _validate_options(self, proposal):
        options = proposal['value']
        if not isinstance(options, (list,tuple)):
            raise traitlets.TraitError("Options must be a list/tuple.")
        
        if not options: 
            self.set_trait('_options', options) # adjust accordingly, set_trait for readonly
            return options  # allow empty list
        
        if not isinstance(self.transform(options[0]), str):
            raise TypeError("tranform function should return a str")
        
        self.set_trait('_options', [(i, self.transform(op)) for i, op in enumerate(options)])
        return options  

    @traitlets.validate('transform')
    def _validate_func(self, proposal):
        func = proposal['value']
        if self.options and not isinstance(self.transform(self.options[0]), str):
            raise TypeError("tranform function should return a str")
        return func

    def fmt_html(self): # this method is important in ipyslides as well
        klass = 'list-widget has-description' if self.description else 'list-widget'
        html = ''
        for i, opt in self._options:
            html += '<div class="list-item {}">{}</div>'.format("selected" if i == self.index else "", opt)
        return f'''<style>{self._css}</style>
            <div class="{klass}" {utils._inline_style(self)} data-description="{self.description}">{html}</div>'''
            
@utils._fix_init_sig
class TabsWidget(GridBox):
    """A tabbed view widget that can contain multiple child widgets, with clickable tabs to switch between them.
    
    - `children`: List[Widget], list of child widgets to display in tabs.
    - `titles`: List[str], list of titles for each tab. If not provided, defaults to "Tab 0", "Tab 1", etc.
    - `selected_index`: int, index of the currently selected tab. Default is 0.
    - `vertical`: bool, if True, display tabs vertically on the left side. Default is False (horizontal tabs).
    - `tabs_width`: str, width of the tabs when vertical. Can be any valid CSS width (e.g., '200px', '20%'). Default is 'auto'.
    - `tabs_height`: str, height of the tabs when horizontal. Can be any valid CSS height (e.g., '2em', '50px'). Default is '2em'.
    
    Example usage:
    ```python
    from ipywidgets import Text, IntSlider
    from dashlab.widgets import TabsWidget
    tab1 = Text(description="Name")
    tab2 = IntSlider(description="Age", min=0, max=100)
    tabs = TabsWidget(children=[tab1, tab2], titles=["Personal Info", "Age Selector"], vertical=False)
    display(tabs)
    ```
    """
    titles = traitlets.List([], help="List of tab titles")
    selected_index = traitlets.Int(0, allow_none=True, help="Index of currently selected tab")
    tabs_width = traitlets.Unicode('auto', help="width of tabs when vertical") # can be any valid css width
    tabs_height = traitlets.Unicode('2em', help="height of tabs when horizontal") # can be any valid css height
    vertical = traitlets.Bool(False, help="If True, display tabs vertically on the left side")
    
    def __init__(self, children=None, titles=None, vertical=False, tabs_width='auto', tabs_height='2em', **kwargs):
        self._lw = ListWidget(description=None, vertical=vertical)
        self._stack = Stack().add_class('tabs-stack')
        self._init_titles = titles or [] # store initial titles as list even if no children yet
        super().__init__(**kwargs)
        self.add_class('tabs-widget') # for custom styling
        self.titles = self._reset_titles(titles)
        traitlets.link((self,'titles'),(self._lw,'options'))
        
        self.children = children or [] # set children to stack
        self.tabs_width = tabs_width
        self.tabs_height = tabs_height
        self._update_layout(None) # initial layout update
        traitlets.link((self._lw,'index'),(self,'selected_index')) # on click, it should update selected_index
        traitlets.link((self._lw,'vertical'),(self,'vertical')) # link vertical to listwidget
    
    @traitlets.observe('selected_index')
    def _validate_selected(self, change):
        if change['new'] is not None:
            if not (0 <= change['new'] < len(self._stack.children)):
                raise ValueError(f"selected_index should be in [0, {len(self._stack.children)-1}], got {change['new']}")
            self._stack.selected_index = change['new'] # delegate to stack, it can't directly be linked as value should be in limites
    
    @traitlets.observe('vertical', 'tabs_width', 'tabs_height')
    def _update_layout(self, change):
        self.layout.grid_template_columns = f'{self.tabs_width} 1fr' if self.vertical else '1fr'
        self.layout.grid_template_rows = '1fr' if self.vertical else f'{self.tabs_height} 1fr'
        self._lw.layout.height = self.tabs_height if not self.vertical else 'auto'
    
    @traitlets.validate('children')
    def _validate_children(self, proposal):
        children = proposal['value']
        self._stack.children = children # delegate children to stack
        self.titles = self._reset_titles(self.titles)
        if self._stack.children:
            self._lw.index = 0 # select first by default at each reset of children
            self._stack.selected_index = 0 # don't know why this does not update automatically
        return (self._lw, self._stack) # Always two children
    
    def _reset_titles(self, titles):
        titles = (titles or self._init_titles)[:len(self._stack.children)] # handle None titles
        if len(titles) < len(self._stack.children):
            titles += ['Tab {}'.format(i) for i in range(len(titles), len(self._stack.children))]
        return titles
    
    @traitlets.validate('titles')
    def _validate_titles(self, proposal):
        return self._reset_titles(proposal['value'])
        

@utils._fix_trait_sig
class AnimationSlider(AnyWidget, ValueWidget):
    """This is a simple slider widget that can be used to control the animation with an observer function.

    You need to provide parameters like `nframes` and `interval` (milliseconds) to control the animation. 
    The `value` trait can be observed to get the current frame index.
    The `cyclic` trait can be set to `True` to make the animation cyclic and only works when loop mode is ON.

    ```python
    from plotly.graph_objects import FigureWidget
    from dashlab.widgets import AnimationSlider

    fig = FigureWidget()
    fig.add_scatter(y=[1, 2, 3, 4, 5])
    widget = AnimationSlider() 

    def on_change(change):
        value = change['new']
        fig.data[0].color = f'rgb({int(value/widget.nframes*100)}, 100, 100)' # change color based on frame index

    widget.observe(on_change, names='value')
    display(widget, fig) # display it in the notebook
    ```

    This widget can be passed to `ipywidgets.interactive` as keyword argument to create a dynamic control for the animation.

    ```python
    from ipywidgets import interact

    @interact(frame=widget)
    def show_frame(frame):
        print(frame)
    ```
    """
    _esm = Path(__file__).with_name('static') / 'animator.js'
    _css = Path(__file__).with_name('static') / 'animator.css'
    
    value = traitlets.CInt(0).tag(sync=True)          
    description = traitlets.Unicode(None, allow_none=True).tag(sync=True) 
    loop = traitlets.Bool(False).tag(sync=True)     
    nframes = traitlets.CInt(100).tag(sync=True)     
    interval = traitlets.Float(50.0).tag(sync=True) 
    playing = traitlets.Bool(False).tag(sync=True) 
    continuous_update = traitlets.Bool(True).tag(sync=True)
    cyclic = traitlets.Bool(False).tag(sync=True) 

    @traitlets.validate("nframes")
    def _ensure_min_frames(self, proposal):
        value = proposal["value"]
        if not isinstance(value, int):
            raise TypeError(f"nframes should be integere, got {type(value)!r}")
        
        if value < 2:
            raise ValueError(f"nframes > 1 should hold, got {value}")
        return value

        
@utils._fix_init_sig
class JupyTimer(traitlets.HasTraits):
    """A widget that provides timer functionality in Jupyter Notebook without threading/blocking.
    
    This widget allows you to run a function at specified intervals, with options for 
    looping and control over the timer's state (play/pause/loop). You can change function too by using `run()` again.
    
    The timer widget must be displayed before calling `run()` to take effect.

    ```python
    timer = JupyTimer(description="My Timer")
    display(timer) # must be displayed before running a function to work correctly

    def my_func(msg):
        print(f"Timer tick: {msg}")
        if timer.nticks > 9:
            timer.pause()

    # Run after 1000ms (1 second)
    if timer.idle(): # not executing function or looping
        timer.run(1000, my_func, args=("Hello!",))

    # For continuous execution, run every 1000ms, 10 times as set in my_func
    timer.run(1000, my_func, args=("Loop!",), loop=True)
    ```

    - Automatically displays in Jupyter, but to acces the associated widget you can use `.widget` method.
    - Use `.widget(minimal = True)` if you want to hide GUI, but still needs to be displayed to work.
    - Call attempts during incomplete interval are skipped. You can alway increase `tol` value to fix unwanted skipping.
    - This is not a precise timer, it includes processing overhead, but good enough for general tracking.
    """
    _value = traitlets.CInt(0).tag(sync=True)  
    _callback = traitlets.Tuple((None, (), {}))     
    description = traitlets.Unicode(None, allow_none=True).tag(sync=True) 
    nticks = traitlets.Int(0, read_only=True)

    def __init__(self, description = None):
        super().__init__()
        self._animator = AnimationSlider(nframes=2) # fixed 2 frames make it work
        traitlets.dlink((self._animator,'value'),(self,'_value'))
        traitlets.link((self,'description'),(self._animator,'description'))
        self.set_trait('description', description) # user set
        self._running = False # executing function
        self._delay = self._animator.interval # check after this much time (ms)
        self._last_called = 0
        self._animator.observe(lambda c: setattr(self, '_last_called', time.time()), 'playing')
    
    def __dir__(self): 
        return "busy clear description elapsed loop nticks pause play run widget".split()
    
    def _repr_mimebundle_(self,**kwargs): # display
        return self._animator._repr_mimebundle_(**kwargs)
    
    @traitlets.observe("_value")
    def _do_call(self, change):
        func, args, kwargs = self._callback

        if ready := self.elapsed >= self._delay:
            self.set_trait("nticks",self.nticks + 1) # how many time intervals passed overall
            
        if func and ready and not self._running: # We need to avoid overlapping calls
            try:
                self._running = True # running call
                func(*args, **kwargs)
            finally:
                self._running = False # free now
                self._last_called = time.time()
    
    @property
    def elapsed(self) -> float:
        """Returns elapsed time since last function call completed in milliseconds.

        If `loop = True`, total time elapsed since start would be approximated as:
            `self.elapsed + self.nticks * interval` (milliseconds)
        """
        return (time.time() - self._last_called) * 1000 # milliseconds
    
    def play(self) -> None: 
        """Start or resume the timer.
        
        If a function was previously set using `run()`, it will be executed at 
        the specified interval. If no function is set, the timer will still run
        but won't execute anything.
        """
        self._animator.playing = True
    
    def pause(self) -> None: 
        """Pause the timer without clearing the underlying function.
        
        The function set by `run()` is preserved and will resume execution when
        `play()` is called again.
        """
        self._animator.playing = False

    def loop(self, b:bool) -> None:
        "Toggle looping programmatically."
        self._animator.loop = b

    def run(self, interval, func, args = (), kwargs = {},loop = False, tol = None) -> None:
        """Set up and start a function to run at specified intervals.
        
        - interval : int. Time between function calls in milliseconds.
        - func : callable. The function to execute.
        - args : tuple, optional. Positional arguments to pass to the function.
        - kwargs : dict, optional. Keyword arguments to pass to the function.
        - loop : bool, optional
            - If True, the function will run repeatedly until paused.
            - If False, the function will run once after `interval` time and stop.
        - tol : int (milliseconds), we check for next execution after `interval - tol`, default is `0.05*interval`.

        **Notes**:

        - The timer widget must be displayed before calling `run()`.
        - Calling `run()` will stop any previously running timer.
        - The first function call occurs after the specified interval.
        """
        if tol is None:
            tol = 0.05*float(interval) # default is 5%
        
        if not (0 < tol < interval):
            raise ValueError("0 < tol < interval should hold!")
        
        if not callable(func): raise TypeError("func should be a callable to accept args and kwargs")
        self.clear()
        self._animator.interval = float(interval) # type casting to ensure correct types given
        self._animator.loop = bool(loop) 
        self._delay = interval - float(tol) # break time to check next, ms
        self._callback = (func, tuple(args), dict(kwargs))
        self.play()

    def widget(self, minimal=False) -> ValueWidget:
        "Get the associated displayable widget. If minimal = True, the widget's size will be visually hidden using zero width and height."
        if minimal:
            self._animator.layout = dict(width='0',height='0',max_width='0',max_height='0')
        return self._animator
    
    def clear(self):
        "Clear function and reset playing state."
        self.set_trait("nticks",0)
        self.pause()
        self._callback = (None, (), {})
        self._last_called = time.time() # seconds

    def idle(self) -> bool:
        """Use this to test before executing next `run()` to avoid overriding.
        
        Returns False:

        - If function is executing right now
        - If loop was set to True, technically it's alway busy.
        
        Otherwise True.
        """
        return not bool(self._animator.loop or self._running)
    
    def busy(self) -> bool: 
        "not self.idle()"
        return not self.idle