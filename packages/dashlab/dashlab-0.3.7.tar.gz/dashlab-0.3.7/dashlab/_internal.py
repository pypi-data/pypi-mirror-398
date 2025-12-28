import time
import traitlets
from contextlib import nullcontext
from datetime import datetime
from functools import wraps
from typing import Union, Callable

from ipywidgets import DOMWidget, Output, fixed, ValueWidget, Button

from .widgets import JupyTimer
from .utils import _fix_init_sig

_active_output = nullcontext() # will be overwritten by function calls
_active_timer = JupyTimer() # will be displayed inside Interact

def monitor(timeit: Union[bool,Callable]=False, throttle:int=None, debounce:int=None, logger:Callable[[str],None]=None):
    """Decorator that throttles and/or debounces a function, with optional logging and timing.

    - timeit: bool, if True logs function execution time.
    - throttle: int milliseconds, minimum interval between calls.
    - debounce: int milliseconds, delay before trailing call. If throttle is given, this is ignored.
    - logger: callable(str), optional logging function (e.g. print or logging.info).

    This type of call will be automatically timed:

    ```python
    @monitor
    def f(*args,**kwargs):
        pass
    ```

    but `@monitor()` will do nothing, as no option was used.

    **Note**: Return value of function is not captured because it will skipp calls and throw None returns most of the time.
    """
    throttle = throttle / 1000 if throttle else 0 # seconds now, but keep debounce in milliseconds

    def log(ctx, msg):
        if callable(logger): return logger(msg)
        elif isinstance(ctx, Output): ctx.append_stdout(msg + '\n') # avoids clearing previous output
        else:
            with ctx: print(msg)
    
    def stamp(): return datetime.now().strftime("\033[37m%H:%M:%S\033[0m")

    def decorator(fn):
        if all(not v for v in [timeit, throttle,debounce]):
            return fn # optimized way to dodge default settings
        
        last_call_time = [0.0]
        last_args = [()]
        last_kwargs = [{}]
        fname = fn.__name__

        @wraps(fn)
        def wrapped(*args, **kwargs):
            now = time.time()
            last_args[0] = args
            last_kwargs[0] = kwargs
 
            def call(out):
                # print(fn, out, throttle, debounce) # debugging
                if isinstance(out, Output): # clean output as it is full call
                    out.clear_output(wait=True)

                start = time.time()
                with out:
                    fn(*last_args[0], **last_kwargs[0])
                    duration = time.time() - start
                    last_call_time[0] = time.time()
                    
                    if timeit:
                        log(nullcontext(), # want to be not overwritten above output 
                            f"\033[34m[Timed]\033[0m     {stamp()} | {fname!r}: " 
                            f"executed in {duration*1000:.3f} milliseconds"
                        )

            time_since_last = now - last_call_time[0]
            if throttle and time_since_last >= throttle: # no tolerance required here
                call(_active_output)
            else:
                if throttle:
                    log(_active_output, f"\033[31m[Throttled]\033[0m {stamp()} | {fname!r}: skipped call")

                elif debounce:
                    log(_active_output, f"\033[33m[Debounced]\033[0m {stamp()} | {fname!r}: reset timer")
                    # This part loses outputs (which go to jupyter logger) if we use threading.Timer os asyncio.
                    # so I created a JupyTimer for Jupyter. You may suspect we can debounce for a simple time check
                    # like in throttle, but we need to take initial args and kwargs to produce correct ouput
                    if _active_timer.idle(): # Do not overlap
                        _active_timer.run(debounce, call, args=(_active_output,), loop=False, tol = debounce/20) # 5% tolerance
                else:
                    call(_active_output)
        return wrapped
    
    if callable(timeit): # called without parenthesis, automatically timed
        return decorator(timeit)
    return decorator


class AnyTrait(fixed):
    "Observe any trait of a widget with name trait inside interactive."
    def __init__(self,  widget, trait):
        self._widget = widget
        self._trait = trait

        if isinstance(widget, fixed): # user may be able to use it
            widget = widget.value
        
        if not isinstance(widget, DOMWidget):
            raise TypeError(f"widget expects an ipywidgets.DOMWidget even if wrapped in fixed, got {type(widget)}")
        
        if trait not in widget.trait_names():
            raise traitlets.TraitError(f"{widget.__class__} does not have trait {trait}")
        
        # Initialize with current value first, then link
        super().__init__(value=getattr(widget,trait,None))
        traitlets.dlink((widget, trait),(self, 'value'))
        
class WidgetTrait(AnyTrait):
    "Class to use (widget, trait_name) as interactive parameter."
    @property
    def widget(self):
        return self._widget

class Changed:
    """A class to track changes in values of params. It itself does not trigger a change. 
    Can be used as `changed = '.changed'` in params and then `changed` can be used in callbacks to check 
    some other value y as changed('y') → True if y was changed else False. You can also test `'y' in changed`.
    This is useful to merge callbacks and execute code blocks conditionally.
    Using `if changed:` will evalutes to true if any of params is changed.
    
    ```python
    interactive(lambda a,changed: print(a,'a' in changed, changed('changed')), a = 2, changed = '.changed')
    # If a = 5 and changed from a = 6, prints '5 True False'
    # If a = 5 and did not change, prints '5 False False', so changed itself is fixed.
    ```

    In callbacks in subclasses of `DashboardBase`, you can just check `self.changed('a')/'a' in self.changed` instead of adding an extra parameter.
    """
    def __init__(self, tuple_ = ()):
        self._set(tuple_)
        
    def _set(self, tuple_):
        if not isinstance(tuple_, (tuple,list)): raise TypeError("tuple expected!")
        self.__values = tuple(tuple_)
    
    def __repr__(self):
        return f"Changed({list(self.__values)})"
    
    def __call__(self, key):
        "Check name of a variable in changed variabls inside a callback."
        # We are using key, because value can not be tracked from source,
        # so in case of x = 8, y = 8, we get 8 == 8 → True and  8 is 8 → True, but 'x' is never 'y'.
        if not isinstance(key, str): raise TypeError(f"expects name of variable as str, got {type(key)!r}")
        if key in self.__values:
            return True
        return False
    
    def __contains__(self, key): # 'y' in changed
        return self(key)
    
    def __bool__(self): # any key changed
        return bool(self.__values)
    
class _ValFunc:
    def __init__(self, value, match):
        self.value = value
        self.match = match

    def __eq__(self, other):
        if isinstance(other, _ValFunc):
            return self.match(self.value, other.value)
        return self.match(self.value, other)
    
    
    def __ne__(self, other):
        return not self.__eq__(other)
    

@_fix_init_sig
class var(ValueWidget):
    """An object wrapper to be used in interactive with custom comparison for change detection. Default: identity comparison (a is b).
    
    Objects such as DataFrames, numpy arrays, or any other objects which do not return boolean on equality comparison can be used.
    
    Example:
    
    ```python
    import pandas as pd
    from dashlab import var, interactive
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    itv = interactive(lambda x: print(x), x = var(df, match=lambda a, b: a.equals(b))) # or match = pd.DataFrame.equals
    itv # display itv to see the widget
    # In another cell, you can change value on x and it will trigger the callback
    itv.params.x.value = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 7]}) # this will trigger callback
    ```
    This would have been failed without using `var` as default `==` comparison because DataFrame handles such comparison by `equals` method.
    """
    def __init__(self, value, match = None):
        if match is None:
            match = lambda a, b: a is b
        
        if not callable(match) or len(match.__code__.co_varnames) != 2:
            raise TypeError("match must be callable with two arguments: match(a, b) -> bool")
        
        self.match = match
        self._type = type(value) # keep type first
        super().__init__() # Then init
        self.value = value # set value at last

    def get_interact_value(self):
        return _ValFunc(self.value, self.match)
        
    @traitlets.validate("value")
    def _cast(self, proposal):
        value = proposal["value"]
        if not isinstance(value, self._type):
            raise TypeError(f"The 'value' trait of 'var' instance expected {self._type}, not {type(value)}.")
        return value
    
@_fix_init_sig
class button(Button):
    """A button widget to be used as interactive parameter to run a callback on click irrespective of other changes.
    It can be used in multiple callbacks and will trigger all of them on click.
    A global manual button offered by `ipywidgets.interact` is not suitable to hold a multi-callback application.
    
    All parameters of `ipywidgets.Button` can be used here. `alert` is used as tooltip which is displayed when other
    parameters are changed but button is not clicked yet. So it indicates user to click the button to update the GUI.
    
    Example:
    ```python
    from dashlab import interactive, button
    itv = interactive(lambda x, btn: print(x), x = 5, btn = button(description="Run", alert="🔴"))
    itv # display itv to see the button
    ```
    """
    def __init__(self, description="Run Callback", icon="refresh", alert="update", **kwargs):
        kwargs['tooltip'] = kwargs.get('tooltip', alert) # respect user given tooltip
        super().__init__(description=description, icon=icon, **kwargs)

_general_css = {
    'display': 'grid',
    'grid-gap': '4px',
    'box-sizing': 'border-box',
    '.Refresh-Btn.Rerun:before': {
        'content': 'attr(title)',
        'padding': '0 8px',
        'color': 'red !important',
    },
    '.out-*': {
        'padding': '4px 8px',
        'display': 'grid', # outputs are not displaying correctly otherwise
    },
    '< .dl-dashboard': {
        '^:fullscreen > *, > *': {'margin' : 0}, # this is import for fullscreen mode to be margin-less directly
        '.jp-RenderedHTML': {'padding-right':0}, # feels bad
    },
    # below widget-html-content creates issue even in nested divs
    '> *, > .center > *, .widget-html-content' : { # .center is GridBox
        'min-width': '0', # Preventing a Grid Blowout by css-tricks.com
        'box-sizing': 'border-box',
    },
    '.Context-Disabled:after': { 
        "content": "''", # should not trigger by minimal interactions
        "color": "var(--accent-color, skyblue)",
        'animation': 'dotsFade 0.8s steps(4, end) infinite',
        'position': 'absolute', 'left': '50%', 'bottom': '0','transform': 'translateX(-50%)',
    },
    "^.Context-Loading:before": {
        "content": "''", # should not trigger by minimal interactions
        "position": "absolute","left": "50%", "top": "0",
        "z-index": "9999", "transform": "translateX(-50%)",
        "animation": "dotsFade 0.8s steps(4, end) infinite",
        "font-size": "16px", "color": "var(--accent-color, skyblue)",
    },
    "@keyframes dotsFade": { "0%": { "content": "''" }, 
        "25%": { "content": "'●'" }, "50%": { "content": "'●●●'" }, 
        "75%": { "content": "'●●●●●'" }, "100%": { "content": "''" },
    },
    '< .dl-dashboard > .other-area:not(:empty)': { # to distinguish other area when not empty
        'border-top': '0.2px inset var(--jp-border-color2, #8988)',
    },
    '.widget-vslider, .jupyter-widget-vslider': {'width': 'auto'}, # otherwise it spans too much area
    '.content-width-button.jupyter-button, .content-width-button .jupyter-button': {
            'width':'max-content',
            'padding-left': '8px', 'padding-right': '8px',
    },
    '.widget-gridbox, .jupyter-widget-gridbox': {'overflow': 'unset'}, # unexpected scrollbars in gridbox
    '> * .widget-box': {'flex-shrink': 0}, # avoid collapse of boxes,
    '.js-plotly-plot': {'flex-grow': 1}, # stretch parent, rest is autosize stuff
    '.columns':{
        'width':'100%',
        'max-width':'100%',
        'display':'inline-flex',
        'flex-direction':'row',
        'column-gap':'0.2em',
        'height':'auto',
        'box-sizing':'border-box !important',
        '> *': {'box-sizing':'border-box !important',}
    }, # as dashlab supports vtack, this is good here
}
