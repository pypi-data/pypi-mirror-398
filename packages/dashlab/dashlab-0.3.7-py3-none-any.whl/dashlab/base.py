"""
Enhanced version of ipywidgets's interact/interactive functionality.
Use as interactive/@interact or subclass DashboardBase. 
"""

import re, textwrap
import inspect 
import traitlets
import ipywidgets as ipw

from contextlib import nullcontext
from collections import namedtuple
from types import FunctionType
from ipywidgets import DOMWidget # for clean type annotation

from . import _internal # for side effects 
from ._internal import AnyTrait, WidgetTrait, Changed, _ValFunc, monitor, _general_css
from .widgets import FullscreenButton
from .patches import patched_plotly
from .utils import print_error, disabled, _build_css, _fix_init_sig, _format_docs, _size_to_css


# Us
_user_ctx = nullcontext # this can be set from external packages like ipyslides will set one
        
_running_callbacks = set()  # Global set to track currently running callbacks

def _func2widget(func, change_tracker):
    func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
    out = None # If No CSS class provided, no output widget will be created, default
    
    if klass := func.__dict__.get('_css_class', None):
        out = ipw.Output()
        out.add_class(klass)
        out._kwarg = klass # store for access later
        
    last_kws = {} # store old kwargs to avoid re-running the function if not changed
    callback_id = id(func)
    
    def call_func(kwargs):
        # callbacks should not run if already running, to avoid infinite loops, specially due to assignments on params
        if callback_id in _running_callbacks:
            return  # Skip if this callback is already running
        
        old_ctx = _internal._active_output
        if out:
            out.clear_output(wait=True) # clear previous output
            _internal._active_output = out # to get it for debounce in monitor

        filtered_kwargs = {k: v for k, v in kwargs.items() if k in func_params}

        # Check if any parameter is a Button, and skip them
        buttons = [v for v in filtered_kwargs.values() if isinstance(v, ipw.Button)]
        
        # Any parameter which is widget does not change identity even if underlying data changes.
        # For example, Plotly's FigureWidget relies on underlying data for ==, which can make `new_fig != old_fig`
        # evaluate to True even when `new_fig is old_fig`. This can trigger unnecessary function calls during active
        # selections, which cannot be removed from the Python side (unfortunately). 
        # Checking identity is a mess later together with == and in, we can just exclude them here, widget is supposed to have a static identity
        other_params  = {k: v for k, v in filtered_kwargs.items() if not isinstance(v, ipw.DOMWidget)}
        
        # Unwrap _ValFunc instances to get the actual value
        unwrapped_kws = {k: v.value if isinstance(v,_ValFunc) else v for k, v in filtered_kwargs.items()}
        
        # Compare values properly by checking each parameter that is not a Widget (should already be same object)
        # Not checking identity here to take benifit of mutations like list/dict content
        values_changed = [k for k, v in other_params.items() 
            if (k not in last_kws) or (v != last_kws[k]) 
        ] # order of checks matters
        
        try:
            change_tracker._set(values_changed)
            _running_callbacks.add(callback_id)  # Mark as running
            with (out or nullcontext()): # capture function output to given output widget if any or to main output
                if buttons:
                    if not any(btn.clicked for btn in buttons): return # first check if any button clicked
                    with print_error(), disabled(*buttons): # disable buttons during function call
                        func(**unwrapped_kws)
                elif values_changed: # and only if values changed
                    with print_error():
                        func(**unwrapped_kws)
        finally:
            _running_callbacks.discard(callback_id) # Always remove when done
            change_tracker._set([]) # reset if error happens before function call
            last_kws.update(filtered_kwargs) # update old kwargs to latest values
            _internal._active_output = old_ctx # reset active output in any case
    
    return (call_func, out)


def _hint_update(btn, remove = False):
    (btn.remove_class if remove else btn.add_class)('Rerun')

def _run_callbacks(fcallbacks, kwargs, box):
    # Each callback is executed, Error in any of them don't stop other callbacks, handled in print_error context manager
    _internal._active_output = box.out if box else nullcontext() # default, unless each func sets and resets
    try:
        for func in fcallbacks:
            func(box.kwargs if box else kwargs) # get latest from box due to internal widget changes
    finally:
        _internal._active_output = nullcontext()


# We need to link useful traits to set from outside, these will be linked from inside
# But these raise error if tried to set from __init__, only linked in there
_useful_traits =  [
    'pane_widths','pane_heights','merge', 'width','height',
    'grid_gap', 'justify_content','align_items'
]
# for validation
_pmethods = ['set_css','set_layout','update','gather','_handle_callbacks']
_pattrs = ['params','changed','isfullscreen', 'children', 'layout','comm']
_omethods = ["_interactive_params"]

class _DashMeta(type):
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        # Identify the first meaningful base class (skip 'object')
        primary_base = ([base for base in bases if base is not object] or [None])[0]
        
        # Check protected methods and attributes
        for attr in [*_pmethods,*_pattrs, *_useful_traits]:
            if attr in namespace and primary_base and hasattr(primary_base, attr):
                raise TypeError(f"Class '{name}' cannot override '{attr}'.")

        # Check mandatory methods
        for method_name in _omethods:
            if method_name not in namespace:
                raise TypeError(f"Class '{name}' must override '{method_name}'.")

# Need to avoid conflict with metaclass of interactive, so build a composite metaclass
_metaclass = type("DashboardMeta", (_DashMeta, type(ipw.interactive)), {})

def _add_traits(cls):
    for name in _useful_traits:
        setattr(cls, name, ipw.AppLayout.class_traits()[name])
    return cls

_docs = {
    "widgets": """
    - Regular ipywidgets with value trait
    - Fixed widgets using ipw.fixed(widget)
    - String pattern 'widget.trait' for trait observation, 'widget' must be in kwargs or e.g. '.trait' to observe traits on this instance.
    - Tuple pattern (widget, 'trait') for trait observation where widget is accessible via params and trait value goes to callback.
      This is useful to have widget and trait in a single parameter, such as `x = (fig, 'selected')` for plotly FigureWidget. Other traits of same widget can be observed by separate parameters with `y = 'x.trait'` pattern.
    - You can use '.fullscreen' to detect fullscreen change and do actions based on that.
    - Use `P = '.params'` to access all parameters in a callback, e.g. `P.x.value = 10` will set x's value to 10 and trigger dependent callbacks.
    - Any DOM widget that needs display (inside fixed too). A widget and its observed trait in a single function are not allowed, such as `f(fig, v)` where `v='fig.selected'`.
    - Wrap any object in `param = var(obj, match)` to use it as a parameter with custom equality check like `match(a, b) -> bool` for dataframes or other objects. Assigning `param.value = new_value` will update the widget and trigger callbacks
    - Plotly FigureWidgets (use patched_plotly)
    - `dashlab.button`/`ipywidgets.Button` for manual updates on heavy callbacks besides. Add tooltip for info on button when not synced.
        - You can have multiple buttons in a single callback and check `btn.clicked` attribute to run code based on which button was clicked.
        - The manual button offered by ipywidgets.interactive is not suitable to hold a GUI with multiple callbacks, so that functionality is replaced by more flexible dashlab.button.
    - Plotly FigureWidgets (use patched_plotly for selection support)
    """,
    "callbacks": """
    - Methods decorated with `@callback`. Run in the order of definition.
    - Optional CSS class via `@callback('out-myclass')`
    - Decorate with @monitor to check execution time, kwargs etc.
    - CSS class must start with 'out-' excpet reserved 'out-main'
    - Each callback gets only needed parameters and updates happen only when relevant parameters change
    - Callbacks cannot call themselves recursively to prevent infinite loops
    - **Output Widget Behavior**:
        - An output widget is created only if a CSS class is provided via `@callback`.
        - If no CSS class is provided, the callback will use the main output widget, labeled as 'out-main'.
    """,
    "props": """
    - changed: Read-only trait to detect which parameters of a callback changed:
        - By providing `changed = '.changed'` in parameters and later in callback by checking `changed('param') -> Bool`.
        - Directly access `self.changed` in a subclass and use `changed('param') -> Bool` / `'param' in self.changed`. Useful to merge callback.
    - isfullscreen: Read-only trait to detect fullscreen change on python side. Can be observed as '.isfullscreen' in params.
    - params: Read-only trait for all parameters used in this interact in widget form. Can be accessed inside callbacks by observing as `P = '.params'` 
      alongwith some `x = True` -> Checkbox, and then inside a callback `P.x.value = False` will uncheck the Checkbox and trigger depnendent callbacks.
    - groups: NamedTuple(controls, outputs, others) - Widget names by type
    - outputs: tuple[Output] - Output widgets from callbacks
    """,
    "features": """
    **Features**:    

    - Multiple function support with selective updates
    - CSS Grid layout system
    - Extended widget trait observation
    - Dynamic widget property updates
    - Built-in fullscreen support
    """,
    "css_info": re.sub(r'\bcode(\[.*?\])?\`', '`', _build_css.__doc__, flags=re.DOTALL), # inline code` or code['css']` not supported is dashlab itself
    "gather": """        
        - Name of widgets from params or output widgets from callbacks by their CSS class names (e.g. 'out-stats').
        - Special group names: `*all`, `*out`, `*ctrl`, `*repr` for all widgets, outputs, controls, representation widgets respectively.
          - Special groups support exclusion patterns with '!' suffix (e.g. '*all!debug.*', '*ctrl!btn.*' to exclude specific widgets or regex patterns from the group).
          - Exclusion patterns can be exact names or regex patterns and are applied only to the widgets in the specified group.
        - Regex patterns to match full widget names (e.g. 'fig.*' to match 'fig1', 'fig2' etc.). Only raises error if regex is invalid, not if no matches found.
        - Direct DOMWidget instances can also be passed inside list in any order to include external widgets not in params/outputs.
    """,
}

def _expose_widget(v):
    if isinstance(v,WidgetTrait):
        return v.widget
    elif isinstance(v,ipw.fixed) and isinstance(v.value, DOMWidget):
        return v.value
    return v

def _used_widgets(box): # recursively find used widget names in layout
    used_names = {box._kwarg} if hasattr(box, '_kwarg') else set() # box itself can be a widget with _kwarg
    for w in box.children:
        if isinstance(w, ipw.Box):
            used_names.update(_used_widgets(w))
        elif hasattr(w, '_kwarg') and w._kwarg not in used_names:
            used_names.add(w._kwarg)
    return used_names

@_add_traits
@_fix_init_sig
@_format_docs(**_docs)
class DashboardBase(ipw.interactive, metaclass = _metaclass):
    """Enhanced interactive widgets with multiple callbacks and fullscreen support.
    
    Use `interctive` function or `@interact` decorator for simpler use cases. For comprehensive dashboards, subclass this class.
    For a ready-to-use interactive application with registering callbacks later, use `Dashboard` class.
    {features}
    **Basic Usage**:    

    ```python
    from dashlab import DashboardBase, callback, button
    import ipywidgets as ipw
    import plotly.graph_objects as go

    class MyDashboard(DashboardBase):
        def _interactive_params(self):
            return {{
                'x': ipw.IntSlider(0, 0, 100),
                'y': 'x.value',  # observe x's value or use y = (ipw.IntSlider(), 'value') equivalently
                'fig': ipw.fixed(go.FigureWidget()),
                'btn': button(icon='refresh', alert='Update Plot'), # manual update button
            }}
            
        @callback # captured by out-main 
        def update_plot(self, x, fig, btn): # will need btn click to run
            fig.data = []
            fig.add_scatter(x=[0, x], y=[0, x**2])
            
        @callback('out-stats')  # creates Output widget for it
        def show_stats(self, x, y):
            if 'y' in self.changed: # detect if y was changed
                print(f"Distance: {{np.sqrt(1 + y**2)}}")
            else:
                print(x)
    
    # Create and layout
    dash = MyDashboard()
    dash.set_layout(
        left_sidebar=['*ctrl'],  # control widgets on left
        center= ipw.VBox(dash.gather('fig', ipw.HTML('Showing Stats'), # plot and stats in a VBox explicitly
    )
    
    # Style with CSS Grid
    dash.set_css(center={{
        'grid': 'auto-flow / 1fr 2fr',
        '.fig': {{'grid-area': '1 / 2 / span 2 / 3'}},
        '.out-stats': {{'padding': '1rem'}}
    }})
    ```

    **Widget Parameters** (`_interactive_params`'s returned dict):
    {widgets}
    **Callbacks**:   
    {callbacks}    
    **Attributes & Properties**:  
    {props}
    **Methods**:      

    - set_css(main, center): Update grid CSS
    - set_layout(**kwargs): Reconfigure widget layout
        
    **Notes**:     

    - Widget descriptions default to parameter names if not set
    - Animation widgets work even with manual updates
    - Use AnimationSlider instead of ipywidgets.Play
    - Fullscreen button added automatically
    - Run button shows when updates needed

    **Python dictionary to CSS**
    {css_info}
    """
    isfullscreen = traitlets.Bool(False, read_only=True)
    changed = traitlets.Instance(Changed, default_value=Changed(), read_only=True) # tracks parameters values changed, but fixed itself
    params = traitlets.Instance(tuple, default_value=namedtuple('InteractiveParams', [])(), read_only=True) # hold parameters object forms, not just values

    def __init__(self) -> None:
        self.__css_class = 'i-'+str(id(self))
        self.__style_html = ipw.HTML()
        self.__style_html.layout.position = 'absolute' # avoid being grid part
        self.__app = ipw.AppLayout().add_class('dl-DashApp') # base one
        self.__app.layout.display = 'grid' # for correct export to html, other props in set_css
        self.__app.layout.position = 'relative' # contain absolute items inside
        self.__app._size_to_css = _size_to_css # enables em, rem
        self.__app._user_layout = {} # store user layout for dynamic updates
        self.__other = ipw.VBox().add_class('other-area') # this should be empty to enable CSS perfectly, unless filled below
        self.update = self.__update # needs avoid checking in metaclass, but restric in subclasses, need before setup
        self.__setup()
        
        # do not add traits in __init__, unknow errors arise, just link
        for name in _useful_traits:
            traitlets.link((self, name),(self.__app,name))
        
    def __setup(self):
        self.__icallbacks = () # no callbacks yet, but need to define for binding in __init__
        self.__iparams = {} # just empty reference
        extras = self.__fix_kwargs() # params are internally fixed
        
        # We do not need a global manual button, as each function can have their own button if needed
        # global button just holds the whole GUI and seems irresponsive and odd in a complex GUI
        super().__init__(self.__run_updates, {'manual': False}, **self.__iparams) # each function can have their own manual button if needed, global does not make sense
        self.unobserve_all("params") # even setting a fixed can trigger callbacks, so remove all
        
        # Attach params as namedtuple trait for object instances
        wparams = {k : _expose_widget(v) # expose fixed widgets
            for k,v in self.__iparams.items() 
            if not getattr(v, '_self_iparam_ws',False)
        } # avoid params itself wrappend AnyTrait
        for child in self.children:
            if hasattr(child, '_kwarg') and child._kwarg in wparams: # keep only in params, not all, like button, and outputs
                wparams[child._kwarg] = child # Exposes widgets in params for setting options inside callbacks to trigger updates in chain

        # Make sure widgets are not used from any other instance, which can cause side effects
        for k, w in wparams.items():
            self.__mark_instance(k, w, check=True)
            
        self.set_trait('params', namedtuple('InteractiveParams', wparams.keys())(**wparams))
        
        # Need to fix kwargs_widgets too
        for v in self.kwargs_widgets:
            if getattr(v, '_self_iparam_ws',False):
                v.value = self.params # update to pick widgets in kwargs later
                
        # Fix CSS classes and other stuff
        self.add_class('dl-dashboard').add_class(self.__css_class)
        self.layout.position = 'relative' # contain absolute items inside
        self.layout.height = 'max-content' # adopt to inner height

        self.children += (*extras, self.__style_html) # add extra widgets to box children
        self.out.add_class("out-main")
        self.out._kwarg = "out-main" # needs to be in all widgets
        self.__mark_instance("out-main", self.out)
        self.__out_main = self.out # keep a reference, so if user changes self.out, we still have it     

        for w in self.kwargs_widgets:
            c = getattr(w, '_kwarg','')
            w = _expose_widget(w) # expose fixed/Trait held widgets
            getattr(w, 'add_class', lambda v: None)(c) # for grid area
            
        self._handle_callbacks() # collects callbacks and run updates
        self.set_css() # apply default CSS
    
    def __mark_instance(self, name, widget, check=False):
        if isinstance(widget,DOMWidget): # check used only for params widgets
            if check and hasattr(widget, '_dl_instance_id') and widget._dl_instance_id != self.__css_class:
                raise ValueError(f"Widget {name!r} is already used in another Dashboard instance, use a unique widget for each instance to avoid side effects!")
            widget._dl_instance_id = self.__css_class # mark as used in this instance
        
    def __order_widgets(self, outputs):
        kw_map = {w._kwarg: w for w in self.params if hasattr(w, '_kwarg') and isinstance(w, DOMWidget)}
        # 1) controls in declared order
        ordered = {name:value 
            for name, value in kw_map.items() 
            if isinstance(value, ipw.ValueWidget) 
            and not isinstance(value, (ipw.HTML, ipw.HTMLMath)) # HTML is not control usually
        } #
        # 2) outputs in registration order and shoould have _kwarg internally
        ordered.update({out._kwarg: out for out in outputs})
        # 3) main output
        ordered["out-main"] = self.__out_main
        # 4) anything else with _kwarg not yet included
        ordered.update({name: w for name, w in kw_map.items() if name not in ordered})
        return ordered 
    
    def _handle_callbacks(self):
        self.__icallbacks = self._registered_callbacks() # callbacks after collecting params
        if not isinstance(self.__icallbacks, (list, tuple)):
            raise TypeError("_registered_callbacks should return a tuple of functions!")
        
        outputs = self.__func2widgets() # build stuff, before actual interact
        self.__all_widgets = self.__order_widgets(outputs) # save it once for sending to app layout set afterwards
        self.__groups = self.__create_groups(self.__all_widgets) # create groups of widgets
        if self.__app._user_layout:
            self.set_layout(**self.__app._user_layout) # this will reset new and old outputs in layout
        else:
            self.set_layout(center=list(self.__all_widgets.keys())) # default layout, needs all widgets first time
        self.update() # crucial: run all callbacks once to update outputs, only changed params will trigger callbacks, or new added ones
    
    def __repr__(self): # it throws very big repr, so just show class name and id
        return f"<{self.__module__}.{type(self).__name__} at {hex(id(self))}>"

    def __validate_layout(self, layout):
        if not isinstance(layout, dict):
            raise TypeError("layout should be a dictionary passed to set_layout for positioning widgets!")
        
        allowed_keys = inspect.signature(self.set_layout).parameters.keys()
        layout_widgets = layout.copy() # avoid changing user dict
        for key, value in layout.items():
            if not key in allowed_keys:
                raise KeyError(f"keys in layout should be one of {allowed_keys}, got {key!r}")
            
            if value is None or key not in ["header", "footer", "center", "left_sidebar", "right_sidebar"]:
                continue  # only validate content areas, but go for all, don't retrun

            if not isinstance(value, (list, tuple, DOMWidget)):
                raise TypeError(
                    f"{key!r} in layout should be a list/tuple of widgets/names or "
                    f"a DOMWidget instance, got {type(value).__name__}"
                )
            
            if isinstance(value, (list,tuple)):
                try:
                    layout_widgets[key] = self.gather(*value) # validate and gather widgets
                except Exception as e:
                    raise type(e)(f"In {key!r} of layout: {e}") from e # better error message     
        return layout_widgets
    
    def __unpack_group(self, pattern):
        group, excp = pattern.split('!',1) if '!' in pattern else (pattern, '')
        exclude = []
        if excp.strip(): # only try to exclude if excp is not empty or just whitespace
            try:
                exclude = [name for name in self.__all_widgets if re.fullmatch(excp, name)]
            except re.error as e:
                raise ValueError(f"Invalid exclusion regex pattern {excp!r} in {pattern!r}.\n{e}") from e
        
        if not group in self.__groups:
            raise ValueError(f"Invalid special group name {group!r}, valid names are: {list(self.__groups)} followed by optional '!name|regex...' exclusion")
        return [name for name in self.__groups[group] if name not in exclude]

    @_format_docs(**_docs)
    def gather(self, *widgets: 'str | DOMWidget', verbose: bool=False) -> tuple[DOMWidget]:
        """Get list of widgets by names or general widgets for layout configuration.
        This can be used to collect widgets to embed at any nesting level in layout.
        
        **Parameters** (str | DOMWidget):         
        {gather}
        Use `verbose=True` to print matched widgets for each pattern to ensure correct matching.
        
        **Returns**: List of DOMWidget instances corresponding to the provided names or instances.      

        **Example**:       

        ```python
        # Basic usage
        widgets = dash.gather('fig1', 'fig2', 'out-stats')

        # Special groups
        all_controls = dash.gather('*ctrl')
        all_outputs = dash.gather('*out')

        # Groups with exclusions
        controls_no_buttons = dash.gather('*ctrl!btn.*')
        all_except_debug = dash.gather('*all!.*debug.*')

        # Regex patterns
        fig_widgets = dash.gather('fig.*')  # fig1, fig2, fig_debug
        numbered = dash.gather('.*[0-9].*')  # any widget with numbers at end

        # Mixed patterns
        result = dash.gather('fig1', '*ctrl!btn.*', external_widget)

        # Verbose output with colors
        widgets = dash.gather('*all!debug.*', verbose=True)
        # Shows: [gather (group)]: *all!debug.* → fig1,fig2,x,y,out-stats
        ```
        """
        specials = list(self.__groups) # special group names
        Ws, LC = self.__all_widgets, [name.lower() for name in self.__all_widgets] # all widgets by name and lower case for case insensitive search
    
        collected = [] # And collect included names keeping exluded out
        for name in widgets:
            if isinstance(name, str):
                if not name.strip():  # Handle empty strings and whitespace
                    raise ValueError(f"Invalid widget name {name!r} - empty strings not allowed")
                
                if name in Ws: # catch all names without regex first and exlcuded above
                    collected.append(Ws[name])
                    if verbose:
                        print(f"\033[92m[gather (exact)]\033[0m: {name} → {name}")
                elif name.lower() in LC: # case insensitive match
                    raise ValueError(f"Widget name {name!r} not found, did you mean {list(Ws)[LC.index(name.lower())]!r}? Widget names are case-sensitive.")
                elif name.startswith('*'): # special groups
                    names = []
                    try:
                        names = self.__unpack_group(name)
                        collected.extend([Ws[n] for n in names]) # already filtered above
                    finally:
                        if verbose:
                            print(f"\033[94m[gather (group)]\033[0m: {name} → {','.join(names) if names else 'No matches'}")
                else:
                    matches = []
                    try:
                        matches = [wname for wname in Ws.keys() if re.fullmatch(name, wname)]
                        if matches:
                            collected.extend([Ws[wname] for wname in matches])
                        elif name.isidentifier(): # if simple name, raise error
                            raise ValueError(f"Invalid widget name {name!r}. Valid names: {list(Ws.keys())}, specials: {specials}")
                    except re.error as e: # only raise error if regex is invalid, not if no matches found
                        raise ValueError(
                            f"Invalid widget name {name!r}.\n"
                            f"Valid names: {list(Ws.keys())}\n"
                            f"Special groups: {specials}, optionally followed by exclusion '!name|regex...'\n"
                            f"regex patterns to match full name in params/outputs are also supported.\n{e}")
                    finally:
                        if verbose:
                            print(f"\033[93m[gather (regex)]\033[0m: {name} → {','.join(matches) if matches else 'No matches'}")
                        
            elif isinstance(name, ipw.DOMWidget):
                collected.append(name)
                if verbose:
                    print(f"\033[95m[gather (widget)]\033[0m: {type(name).__name__} → Direct widget")
            else:
                raise TypeError(f"Each item must be a string or DOMWidget, got {type(name).__name__}")
        return tuple(collected)
    
    @_format_docs(gather = textwrap.indent(_docs['gather'], '    '))
    def set_layout(self, 
        header: 'list[str, DOMWidget] | DOMWidget' = None, 
        center: 'list[str, DOMWidget] | DOMWidget' = None, 
        left_sidebar: 'list[str, DOMWidget] | DOMWidget' = None,
        right_sidebar: 'list[str, DOMWidget] | DOMWidget' = None,
        footer: 'list[str, DOMWidget] | DOMWidget' = None,
        pane_widths: tuple[float, float, float] = None, 
        pane_heights: tuple[float, float, float] = None,
        merge: bool = True, 
        grid_gap: str = None, 
        width: str = None,
        height: str = None, 
        justify_content: str = None,
        align_items: str = None,
        ) -> None:
        """Configure widget layout using AppLayout structure.

        **Parameters**:  

        - Content Areas (list[str, DOMWidget] | DOMWidget):
            - header: Widgets at top
            - center: Main content area (uses CSS Grid)
            - left_sidebar: Left side widgets
            - right_sidebar: Right side widgets  
            - footer: Bottom widgets
        
        Each of content areas expect `list[str, DOMWidget] | DOMWidget` of widgets/ params names if given. See details below:
        
        - If a single widget is passed, it will be used directly. If None, the area will be hidden.
        - To get params/outputs by names at a nesting level, use `gather()` method, e.g. `center = TabsWidget(dash.gather('fig', 'out-stats'))`
        - If a list/tuple is passed, it will be wrapped in a VBox (except center which uses GridBox).{gather}
        
        - Grid Properties:
            - pane_widths: list[str] - Widths for [left, center, right]
            - pane_heights: list[str] - Heights for [header, center, footer]
            - grid_gap: str - Gap between grid cells
            - width: str - Overall width
            - height: str - Overall height
            - justify_content: str - Horizontal alignment
            - align_items: str - Vertical alignment

        **Size Units** (for pane_widths and pane_heights): `px`, `fr`, `%`, `em`, `rem`, `pt`. Other can be used inside set_css.

        **Example**:       

        ```python
        dash.set_layout( # dash is an instance of DashboardBase
            left_sidebar=['*ctrl'],  # control widgets on left
            center=['fig', '*out'], # fig and other outputs in center
            pane_widths=['200px', '1fr', 'auto'],
            pane_heights=['auto', '1fr', 'auto'],
            grid_gap='1rem'
        )
        ```

        **Notes**:        

        - Widget names must exist in the return of _interactive_params and callbacks' classes.
        - Center area uses CSS Grid for flexible layouts
        - Other areas use vertical box layout
        """
        layout = {key:value for key,value in locals().items() if key != 'self'}
        layout_widgets = self.__validate_layout(layout)
        self.__app._user_layout = layout # store for dynamic updates if callbacks change widgets, after validation
        self.__other.children = () # reset other area, it will be filled later
        areas = ["header","footer", "center", "left_sidebar","right_sidebar"]
        for key in areas:
            self.__app.set_trait(key, None) # reset all areas first
            
        for key, value in layout_widgets.items():
            if value and key in areas:
                if isinstance(value, (list,tuple)): # otherwise would be a widget
                    value = (ipw.GridBox if key == 'center' else ipw.VBox)(value)
                self.__app.set_trait(key, value.add_class(key.replace('_','-'))) # for user CSS
            elif value: # class own traits and Layout properties are linked here
                self.__app.set_trait(key, value)
                
        del layout_widgets # release references
        if names := _used_widgets(self.__app):
            self.__other.children += tuple([v for k,v in self.__all_widgets.items() if k not in names])
        
        # We are adding a reaonly isfullscreen trait set through button on parent class
        fs_btn = FullscreenButton()
        fs_btn.observe(lambda c: self.set_trait('isfullscreen',c.new), names='isfullscreen') # setting readonly property
        self.children = (self.__app, self.__other, self.__style_html, _internal._active_timer.widget(True), fs_btn)
    
    @_format_docs(css_info = textwrap.indent(_docs['css_info'],'    ')) # one more time indent for nested method
    def set_css(self, main:dict=None, center:dict=None) -> None:
        """Update CSS styling for the main app layout and center grid.
        
        **Parameters**:         

        - main (dict): CSS properties for main app layout
            - Target center grid with ` > .center ` selector
            - Target widgets by their parameter names as classes
            - Use `:fullscreen` at root level of dict to apply styles in fullscreen mode
            - Use `[Button, ToggleButton(s)].add_class('content-width-button')` to fix button widths easily.
        - center (dict): CSS properties for center grid section
            - Direct access to center grid (same as main's ` > .center `)
            - Useful for grid layout of widgets inside center area
            - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

        **CSS Classes Available**:  

        - Parameter names from _interactive_params()
        - Custom 'out-*' classes from `@callback` decorators and 'out-main' from main output.
        - All output widgets have a common 'widget-output' class to style them together.
        - All params widgets have a common 'widget-param' class to style them together.
        - All control widgets inside params also have have a common 'widget-control' class to style them together.
        - The selector `.widget-param:not(.widget-control)` can be used to target only non-control param widgets like figures, HTML etc.
        
        **Example**:       

        ```python
        dash.set_css(
            main={{
                ':fullscreen': {{'min-height':'100vh'}}, # fullscreen mode full height by min-height
                'grid-template-rows': 'auto 1fr auto',
                'grid-template-columns': '200px 1fr',
                '> .center': {{'padding': '1rem'}} # can be done with center parameter too
            }},
            center={{
                'grid': 'auto-flow / 1fr 2fr',
                '.fig': {{'grid-area': '1 / 2 / span 2 / 3'}},
                '.out-stats': {{'padding': '1rem'}}
            }}
        )
        ```

        **Python dictionary to CSS**
        {css_info}
        """
        return self._set_css(main=main, center=center)

    def _set_css(self, main, center): # in ipyvasp I needed ovveriding it, user can, but call super()._set_css for sure
        if main and not isinstance(main,dict):
            raise TypeError('main should be a nesetd dictionary of CSS properties to apply to main app!')
        if center and not isinstance(center,dict):
            raise TypeError('center should be a nesetd dictionary of CSS properties to apply to central grid!')
        
        main_sl = f".{self.__css_class}.widget-interact.dl-dashboard > .dl-DashApp" # directly inside
        cent_sl = f"{main_sl} > .center"
        _css = _build_css(('.dl-dashboard > .dl-DashApp',),_general_css)

        if main:
            if fs_css := main.pop(':fullscreen',{}) or main.pop('^:fullscreen',{}): # both valid
                _css += ('\n' + _build_css((f".{self.__css_class}.widget-interact.dl-dashboard:fullscreen > .dl-DashApp",), fs_css))
            _css += ("\n" + _build_css((main_sl,), main))
        if center:
            _css += ("\n" + _build_css((cent_sl,), center))
        self.__style_html.value = f'<style>{_css}</style>'
    
    def _interactive_params(self) -> dict:
        "Implement this in subclass to provide a dictionary for creating widgets and observers."
        raise NotImplementedError("implement _interactive_params(self) method in subclass, "
            "which should returns a dictionary of interaction parameters.")
    
    def _registered_callbacks(self) -> list[callable]:
        """Collect all methods marked as callbacks. If overridden by subclass, should return a tuple of functions."""
        funcs = []
        for name, attr in self.__class__.__dict__.items():
            if callable(attr) and hasattr(attr, '_is_interactive_callback'):
                # Bind method to instance, we can't get self.method due to traits cuaing issues
                bound_method = attr.__get__(self, self.__class__)
                # Copy CSS class from original function
                if hasattr(attr, '_css_class'):
                    bound_method.__dict__['_css_class'] = attr._css_class
                funcs.append(bound_method)
        return tuple(funcs)
    
    def __validate_params(self, params):
        if not isinstance(params, dict):
            raise TypeError(f"method `_interactive_params(self)` should return a dict of interaction parameters")
                
        for key in params:
            if not isinstance(key, str) or not key.isidentifier():
                raise ValueError(f"{key!r} is not a valid name for python variable!")
 
    def __fix_kwargs(self):
        params = self._interactive_params() # subclass defines it
        self.__validate_params(params)   

        extras = {}
        for key, value in params.copy().items():
            if isinstance(value, ipw.fixed) and isinstance(value.value, ipw.DOMWidget):
                extras[key] = value.value # we need to show that widget
            elif isinstance(value,ipw.interactive):
                value.layout.grid_area = 'auto / 1 / auto / -1' # embeded interactive should be full length, unless user sets it otherwise
            elif isinstance(value, (ipw.HTML, ipw.Label, ipw.HTMLMath)):
                params[key] = ipw.fixed(value) # convert to fixed widget, these can't have user interaction available
                extras[key] = value
            elif isinstance(value, ipw.DOMWidget) and not isinstance(value,ipw.ValueWidget): # value widgets are automatically handled
                params[key] = ipw.fixed(value) # convert to fixed widget, to be passed as value
                extras[key] = value # we need to show that widget
            elif isinstance(value, tuple) and len(value) == 2:
                widget, trait_name = value
                if isinstance(widget, ipw.DOMWidget) and isinstance(trait_name, str): # valid
                    if isinstance(widget, ipw.Button): # Button can only be in extras, by fixed or itself
                        raise ValueError(f"Button widget in parameter {key!r} cannot be observed for traits, use it directly as parameter.")
                    if trait_name in widget.trait_names():
                        # Store widget in params for access, observe trait for callbacks
                        extras[key] = widget  # Widget goes to params/extras/ settings _kwarg for layout
                        params[key] = WidgetTrait(widget, trait_name)  
                    else:
                        raise ValueError(f"Widget in parameter {key!r} does not have trait {trait_name!r}")
                elif isinstance(widget, DOMWidget) and not isinstance(trait_name, str):
                    raise TypeError(f"Second item in parameter {key!r} must be a string when first item is a DOMWidget, got {type(trait_name).__name__}")
                # We do not raise error if first item is not a widget, let it be handled by widget abbreviations later
        
        for key, value in extras.items():
            value._kwarg = key # required for later use
            if isinstance(value, ipw.Button): # Button can only be in extras, by fixed or itself
                # Add click trigger flag and handler, callbacks using this can only be triggered by click
                value.add_traits(clicked=traitlets.Bool(False, read_only=True)) # useful to detect which button pressed in callbacks
                value.add_class('Refresh-Btn') # add class for styling
                value.on_click(self.update) # after setting clicked, update outputs on click
                if not value.tooltip: # will show when not synced
                    value.tooltip = 'Run Callback'

        # All params should be fixed above before doing below
        for key, value in params.copy().items(): 
            if isinstance(value, str) and value.count('.') == 1 and ' ' not in value: # space restricted
                name, trait_name = value.split('.')
                if name == '' and trait_name in self.trait_names() and not trait_name.startswith('_'): # avoid privates
                    fixed_traits = {"changed": self.changed, "params": self.params} # These should not trigger callbacks
                    if trait_name in fixed_traits:
                        params[key] = ipw.fixed(fixed_traits[trait_name]) 
                        if trait_name == 'params': # params is special to remove later from itself
                            params[key]._self_iparam_ws = True # mark it as self params, so we can remove it later
                    else:
                        params[key] = AnyTrait(self, trait_name)
                    # we don't need mutual exclusion on self, as it is not passed
                elif name in params: # extras are already cleaned widgets, otherwise params must have key under this condition
                    w = _expose_widget(params.get(name, None))
                    # We do not want to raise error, so any invalid string can goes to Text widget
                    if isinstance(w, ipw.DOMWidget) and trait_name in w.trait_names():
                        params[key] = AnyTrait(w, trait_name)

        # Set __iparams after clear widgets
        self.__iparams = params
        
        # Tag parameter widgets with their names so we can order later
        for key, val in self.__iparams.items():
            w = _expose_widget(val)
            if isinstance(w, ipw.DOMWidget):
                w._kwarg = key
                
        self.__reset_descp(extras)
        return tuple(extras.values())
    
    def __update(self, *args):
        btn = args[0] if args and isinstance(args[0],ipw.Button) else None # if triggered by click on a button
        try:
            self.__app.add_class("Context-Loading")
            if btn: btn.set_trait('clicked', True) # since read_only
            super().update(*args) # args are ignored anyhow but let it pass
        finally:
            self.__app.remove_class("Context-Loading")
            if btn:
                btn.set_trait('clicked', False)
                _hint_update(btn, remove=True)
    
    def __reset_descp(self, extras):
        # fix description in extras, like if user pass IntSlider etc.
        for key, value in extras.items():
            if 'description' in value.traits() and not value.description \
                and not isinstance(value,(ipw.HTML, ipw.HTMLMath, ipw.Label)): # HTML widgets and Labels should not pick extra
                value.description = key # only if not given
    
    def __func2widgets(self):
        outputs = []  # collecting output widgets from callbacks
        callbacks = [] # collecting processed callback
        used_classes = {}  # track used CSS classes for conflicts 
        seen_funcs = set() # track for any duplicate function

        for f in self.__icallbacks:
            if not callable(f):
                raise TypeError(f'Expected callable, got {type(f).__name__}. '
                    'Only functions accepting a subset of kwargs allowed!')
            
            if f in seen_funcs:
                raise ValueError(f"Duplicate callback detected {f.__name__!r}")

            seen_funcs.add(f)
            
            # Check for CSS class conflicts
            if klass := f.__dict__.get('_css_class', None):
                if klass in used_classes:
                    raise ValueError(
                        f"CSS class {klass!r} is used by multiple callbacks: "
                        f"{f.__name__!r} and {used_classes[klass]!r}"
                    )
                used_classes[klass] = f.__name__
            
            self.__validate_func(f) # before making widget, check
            self.__hint_btns_update(f) # external buttons update hint based on mutated params
            new_func, out = _func2widget(f, self.changed) # converts to output widget if user set class or empty
            callbacks.append(new_func) 
            
            if out is not None:
                self.__mark_instance(out._kwarg, out) 
                outputs.append(out)
        
        self.__icallbacks = tuple(callbacks) # set back
        del used_classes, seen_funcs, callbacks # no longer needed
        return tuple(outputs)
    
    def __validate_func(self, f):
        ps = inspect.signature(f).parameters
        f_ps = {k:v for k,v in ps.items()}
        has_varargs = any(param.kind == param.VAR_POSITIONAL for param in ps.values())
        has_varkwargs = any(param.kind == param.VAR_KEYWORD for param in ps.values())

        if has_varargs or has_varkwargs:
            raise TypeError(
                f"Function {f.__name__!r} cannot have *args or **kwargs in its signature. "
                "Only explicitly named keywords from interactive params are allowed."
            )

        if len(ps) == 0:
            raise ValueError(f"Function {f.__name__!r} must have at least one parameter even if it is a button to click for this func to run.")
        
        gievn_params = set(self.__iparams)
        extra_params = set(f_ps) - gievn_params
        if extra_params:
            raise ValueError(f"Function {f.__name__!r} has parameters {extra_params} that are not defined in interactive params.")
        
    def __create_groups(self, widgets_dict):
        controls, outputs, others = [], [], []
        for key, widget in widgets_dict.items():
            if isinstance(widget, ipw.Output):
                outputs.append(key)
            elif (isinstance(widget, ipw.ValueWidget) and 
              not isinstance(widget, (ipw.HTML, ipw.HTMLMath))):
                controls.append(key)
            elif isinstance(widget, ipw.Button):
                controls.append(key) # run buttons always in controls
            else:
                others.append(key)
        for c in controls:
            widgets_dict[c].add_class('widget-param').add_class('widget-control') # similar to widget-output added by ipywidgets
        for o in others:
            widgets_dict[o].add_class('widget-param') # what else
        return {'*all': tuple(widgets_dict), '*ctrl': tuple(controls), '*out': tuple(outputs), '*repr': tuple(others)}
    
    def __hint_btns_update(self, func):
        func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
        # Let's observe buttons by shared value widgets in func_params
        controls = {c:v for c,v in self.params._asdict().items() if c in func_params} # filter controls by func_params
        btns = [controls[k] for k in func_params if isinstance(controls.get(k,None), ipw.Button)]
        ctrls = [v for v in controls.values() if isinstance(v, ipw.ValueWidget)] # other controls
        
        for btn in btns:
            for w in ctrls:
                if hasattr(w, '_hinting_btn_update'):
                    w.unobserve(w._hinting_btn_update, names='value') # remove old if any
                
                def update_hint(change, button=btn): _hint_update(button) # closure
                w.observe(update_hint, names='value') # update button hint on value change
                w._hinting_btn_update = update_hint # keep reference to clean up before adding next time
               
    @property
    def outputs(self) -> tuple: raise DeprecationWarning("outputs property is deprecated, use gather('*out') instead.")

    @property
    def groups(self) -> namedtuple: raise DeprecationWarning("groups property is deprecated, use gather('*ctrl'), gather('*out'), gather('*repr') instead to pick a group of widgets.")
    
    def __run_updates(self, **kwargs):
        with self.__user_ctx(), print_error():
            _run_callbacks(self.__icallbacks, kwargs, self) 
    
    def __user_ctx(self):
        global _user_ctx
        try:
            with _user_ctx(): pass # test if it works
        except Exception as e:
            print(f"Failed to access dashlab.base._user_ctx patched externally: {e}\nSetting to nullcontext. You can patch it again with correct context manager.")
            _user_ctx = nullcontext
        return _user_ctx()



def callback(output:str = None, *, timeit:bool = False, throttle:int = None, debounce:int = None, logger:callable = None) -> callable:
    """Decorator to mark methods as interactive callbacks in DashboardBase subclasses or for interactive funcs.
    
    **func**: The method to be marked as a callback.  

    - Must be defined inside a class (not nested) or a pure function in module.
    - Must be a regular method (not static/class method).
    
    **output**: Optional string to assign a CSS class/name to the callback's output widget. 

    - Must start with 'out-', but should not be 'out-main' which is reserved for main output
    - Example valid values: 'out-stats', 'out-plot', 'out-details'
    - If no output name is provided, the callback will not create a separate output widget and will use the main output instead.

    Other keyword arguments are passed to `monitor`

    - timeit: bool, if True logs function execution time.
    - throttle: int milliseconds, minimum interval between calls.
    - debounce: int milliseconds, delay before trailing call. If throttle is given, this is ignored.
    - logger: callable(str), optional logging function (e.g. print or logging.info).

    **Usage**:                  

    - Inside a subclass of DashboardBase, decorate methods with `@callback` and `@callback('out-important')` to make them interactive.
    - See example usage in docs of DashboardBase.

    **Returns**: The decorated method itself.
    """  
    def decorator(func):
        if not isinstance(func, FunctionType):
            raise TypeError(f"@callback can only decorate functions, got {type(func).__name__}")
    
        # get a new function after monitor and then apply attributes
        func = monitor(timeit=timeit,throttle=throttle,debounce=debounce,logger=logger)(func)
        
        nonlocal output # to be used later
        if isinstance(output, str):
            func = _classed(func, output) # assign CSS class if provided
        
        qualname = getattr(func, '__qualname__', '')
        if not qualname:
            raise Exception("@callback can only be used on named functions")
        
        if qualname.count('.') == 1:
            if len(inspect.signature(func).parameters) < 1:
                raise Exception(f"{func.__name__!r} cannot be transformed into a bound method!")
            func._is_interactive_callback = True # for methods in class

        return func

    # Handle both @callback and @callback('out-myclass') syntax
    if callable(output):
        return decorator(output)
    return decorator

def _classed(func, output):
    # callable and str already check in callback
    if not output.startswith('out-'):
        raise ValueError(f"output must start with 'out-', got {output!r}")
    if output == 'out-main':
        raise ValueError("out-main is reserved class for main output widget")
    if output and not re.match(r'^out-[a-zA-Z0-9-]+$', output):
        raise ValueError(f"output is not a valid CSS class, must only contain letters, numbers or hyphens, got {output!r}")
    func.__dict__['_css_class'] = output # set on __dict__ to avoid issues with bound methods
    return func