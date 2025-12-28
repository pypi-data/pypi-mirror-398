import inspect, re, sys, textwrap
import ipywidgets as ipw

from contextlib import contextmanager
from pathlib import Path
from IPython.core.ultratb import AutoFormattedTB
from ipywidgets import DOMWidget

# These few functions are used in ipyslides, especially _build_css
# So do not move around or make changes without checking ipyslides

def _fix_trait_sig(cls):
    "Avoid showing extra kwargs by having a class attribute _no_kwargs"
    params = [inspect.Parameter(key, inspect.Parameter.KEYWORD_ONLY, default=value) 
        for key, value in cls.class_own_traits().items() if not key.startswith('_')] # avoid private
    
    if not hasattr(cls,'_no_kwargs'):
        params.append(inspect.Parameter('kwargs', inspect.Parameter.VAR_KEYWORD)) # Inherited widgets traits
    cls.__signature__ = inspect.Signature(params)
    return cls

def _inline_style(kws_or_widget):
    "CSS inline style from keyword arguments having _ inplace of -. Handles widgets layout keys automatically."
    if isinstance(kws_or_widget, ipw.DOMWidget):
        kws = {k:v for k,v in kws_or_widget.layout.get_state().items() if v and (k[0]!='_')}
    elif isinstance(kws_or_widget, dict):
        kws = kws_or_widget
    else:
        raise TypeError("expects dict or ipywidgets.Layout!")
    out = ''.join(f"{k.replace('_','-')}:{v};" for k,v in kws.items())
    return f'style="{out}"' if kws else ''

def _fix_init_sig(cls):
    # widgets ruin signature of subclass, let's fix it
    cls.__signature__ = inspect.signature(cls.__init__)
    return cls

def _format_docs(**variables):
    def decorator(obj):
        if obj.__doc__:
            try:
                obj.__doc__ = obj.__doc__.format(**variables)
            except Exception as e:
                raise ValueError(f"Failed to format docs for {obj.__name__}: {str(e)}") from e
        return obj
    return decorator

# ipywidgets AppLayout restricts units to px,fr,% or int, need to add rem, em
def _size_to_css(size):
    if re.match(r'\d+\.?\d*(px|fr|%|em|rem|pt)$', size):
        return size
    if re.match(r'\d+\.?\d*$', size):
        return size + 'fr'
    raise TypeError("the pane sizes must be in one of the following formats: "
        "'10px', '10fr', '10em','10rem', '10pt', 10 (will be converted to '10fr')."
        "Conversions: 1px = 1/96in, 1pt = 1/72in 1em = current font size"
        "Got '{}'".format(size))
    
@contextmanager
def disabled(*widgets):
    "Disable widget and enable it after code block runs under it. Useful to avoid multiple clicks on a button that triggers heavy operations."
    for widget in widgets:
        if not isinstance(widget, DOMWidget):
            raise TypeError(f"Expected ipywidgets.DOMWidget, got {type(widget).__name__}")
        widget.disabled = True
        widget.add_class("Context-Disabled")
    try:
        yield
    finally:
        for widget in widgets:
            widget.disabled = False
            widget.remove_class("Context-Disabled")

# We will capture error at user defined callbacks level
_autoTB = AutoFormattedTB('Context', 'linux')

@contextmanager
def print_error(tb_offset=2):
    "Contextmanager to catch error and print to stderr instead of raising it to keep code executing forward."
    try:
        yield
    except:
        tb = '\n'.join(_autoTB.structured_traceback(*sys.exc_info(),tb_offset=tb_offset))
        print(tb, file=sys.stderr) # This was dead simple, but I was previously stuck with ansi2html
        # In future if need to return error, use Ansi2HTMLConverter(inline=True).convert(tb, full = False)

def _validate_key(key):
    "Validate key for CSS,allow only string or tuple of strings. commas are allowed only in :is(.A,#B),:has(.A,#B) etc."
    if not isinstance(key,str):
        raise TypeError(f'key should be string, got {key!r}')

    if ',' in key:
        all_matches = re.findall(r'\((.*?)\)',key,flags=re.DOTALL)
        for match in all_matches:
            key = key.replace(f'{match}',match.replace(',','$'),1)  # Make safe from splitting with comma
    return key

def _handle_raw_css(value):
    "Handle raw CSS from string or Path object."
    if not isinstance(value, (str, Path)):
        raise TypeError("Raw CSS value for empty key must be string or file path!")
    
    if isinstance(value, Path):
        value = value.read_text()
    elif Path(value).is_file():
        value = Path(value).read_text()
    
    value = '\n'.join(line.strip() for line in value.splitlines()) # Clean extra spaces
    return value

def _build_css(selector, props):
    """
    CSS is formatted using a `props` nested dictionary to simplify the process. 
    
    There are few special rules in `props`:

    - All nested selectors are joined with space, so code`'.A': {'.B': ... }` becomes code['css']`.A .B {...}` in CSS.
    - A '^' in start of a selector joins to parent selector without space, so code`'.A': {'^:hover': ...}` becomes code['css']`.A:hover {...}` in CSS. You can also use code`'.A:hover'` directly but it will restrict other nested keys to hover only.
    - A list/tuple of values for a key in dict generates CSS fallback, so code`'.A': {'font-size': ('20px','2em')}` becomes code['css']`.A {font-size: 20px; font-size: 2em;}` in CSS.
    - An empty key with a string/path value injects raw CSS wrapped in nested code['css']`&`, so code`'.A': {'': 'raw css here'}` becomes code['css']`& { .A { raw css here } }` in CSS. 
      This, however, can NOT be used to inject complex CSS like `@import`, `@layer` etc.  `:root` is replaced with `&` to make variables local to the selector at given nesting level.

    Read about specificity of CSS selectors [here](https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity).
    """
    # selector is tuple of string(s), props contains nested dictionaries of selectors, attributes etc."
    content = '\n' # Start with new line so style tag is above it
    children = []
    attributes = []
    
    for key, value in props.items():
        key = _validate_key(key) # Just validate key
        if not key.strip(): # Empty key with string value is direct CSS
            # We can't handle complex @import, @charset here since that neede to be at root level, and we have scattered styles everywhere
            value = _handle_raw_css(value)
            value = value.replace(':root','&') # Take external root to this scope only
            content += (" ".join(selector) + " {\n\t & {\n") # nested scope with added spcificity
            content += (textwrap.indent(value, '\t\t') + "\n\t}\n}\n") 
            continue
        
        if isinstance(value, dict):
            children.append( (key, value) )
        elif isinstance(value, (list, tuple)): # Fallbacks
            for item in value:
                attributes.append( (key, item) )
        else: # str, int, float etc. No need to check. User is responsible for it
            attributes.append( (key, value) )
    if attributes:
        content += re.sub(r'\s+\^','', (' '.join(selector) + " {\n").lstrip()) # Join nested tags to parent if it starts with ^
        content += '\n'.join(f"\t{key.replace('_','-')} : {value};"  for key, value in attributes)  # _ allows to write dict(key=value) in python, but not in CSS props
        content += "\n}\n"

    for key, value in children:
        if key.startswith('<'): # Make it root level
            content += _build_css((key.lstrip('<'),), value)
        elif key.startswith('@media') or key.startswith('@container'): # Media query can be inside a selector and will go outside
            content += f"{key} {{\n\t"
            content += _build_css(selector, value).replace('\n','\n\t').rstrip('\t') # last tab is bad
            content += "}\n"
        elif key.startswith('@'): # @page, @keyframes etc.
            content += f"{key} " # braces added by _build_css below, no extra needed
            content += _build_css((), value).strip(' \n\t\r') # strip both sides here to take brace at previous line
            content += "\n"
        elif  key.startswith(':root'): # This is fine
            content+= _build_css((key,), value)
        else:
            old_sels = re.sub(r'\s+', ' ',' '.join(selector)).replace('\n','').split(',') # clean up whitespace
            sels = ',\n'.join([f"{s} {k}".strip() for s in old_sels for k in key.split(',')]) # Handles all kind of nested selectors
            content += _build_css((sels,), value)

    
    content = re.sub(r'\$', ',', content) # Replace $ with ,
    content = re.sub(r'\n\s+\n|\n\n','\n', content) # Remove empty lines after tab is replaced above
    content = re.sub(r'\t', '    ', content) # 4 space instead of tab is bettter option
    content = re.sub(r'\^',' ', content) # Remove left over ^ from start of main selector
        
    return content
