import traitlets

def patched_plotly(fig):
    """Plotly's FigureWidget with two additional traits `selected` and `clicked` to observe.
    
    - selected: Dict - Points selected by box/lasso selection
    - clicked: Dict - Last clicked point (only updates when clicking different point, it should not be considered a button click)

    Each of `selected` and `clicked` dict adds a `customdata` silently which in case of plotly.expresse is restricted to be array of shape (columns, len(x))
    and in plotly.graph_objs.Figure case is not restricted but should be indexible by selected points, like an array of shape (len(x), columns) 
    (transpose of above, which is done by plotly.express internally, but not in Figure, which is inconsistant and inconvinient) is a good data 
    where x is in px.line or go.Scatter for example.

    **Note**: You may need to set `fig.layout.autoszie = True` to ensure fig adopts parent container size. 
    (whenever size changes, it may need to be set again in many cases due to some internal issues with plotly)
    """
    if getattr(fig.__class__,'__name__','') != 'FigureWidget':
        raise TypeError("provide plotly's FigureWidget")
    
    if fig.has_trait('selected') and fig.has_trait('clicked'):
        return fig # Already patched, no need to do it again
    
    fig.add_traits(selected = traitlets.Dict(), clicked=traitlets.Dict())

    def _attach_data(change):
        data = change['new']
        if data:
            if data['event_type'] == 'plotly_click': # this runs so much times
                fig.clicked = _attach_custom_data(fig, fig.clicked, data['points'])
            elif data['event_type'] == 'plotly_selected':
                fig.selected = _attach_custom_data(fig, fig.selected, data['points'])
            
    fig.observe(_attach_data, names = '_js2py_pointsCallback')
    return fig

def _attach_custom_data(fig, old, points): # fully forgiven
    if old == points: return old # why process again
    try:
        if not points or not isinstance(points, dict):
            return {}

        # Get indices safely
        ti = points.get('trace_indexes', [])
        pi = points.get('point_indexes', [])
        if not ti or not pi:
            return {**points, 'customdata':[]}

        cdata = []
        for t, p in zip(ti, pi):
            try:
                cdata.append(fig.data[t].customdata[p])
            except:
                cdata.append(None)
        points.update({'customdata': cdata})
        return points
    except:
        points['customdata'] = [None] * len(points.get('trace_indexes', []))
        return points 
