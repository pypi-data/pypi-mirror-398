"""Dashlab: Interactive dashboard framework for Jupyter notebooks.

Core Components
---------------
- DashboardBase: Base class offering reactive parameters, multi-callback orchestration, layout & CSS helpers.
- Dashboard: Ready-to-use dashboard that lets you register callbacks after construction.
- interactive / interact: Quick helpers to spin up lightweight exploratory dashboards.
- callback: Decorator to register reactive callbacks (optionally with dedicated output areas).
- var: Wrap arbitrary Python objects as reactive parameters with custom equality semantics.
- button: Create buttons with icons and alert tooltips for manual callback triggering flexibly.
- monitor: Decorator providing timing, debounce, throttle and logging for callbacks.

Custom Widgets
--------------
- ListWidget: Select from rich-rendered (repr/HTML/SVG) Python objects.
- AnimationSlider: Frame index / play-pause control with loop & timing traits.
- JupyTimer: Lightweight interval runner for periodic function execution without threads.
- FullscreenButton: Toggle fullscreen on the container element. (mostly used internally in Dashboard)

Utilities
---------
- markdown: Render markdown text to an HTML widget.
- hstack / vstack: Simple horizontal / vertical layout of widgets & markdown strings.
- patched_plotly: Adds reactive 'selected' and 'clicked' traits to a plotly FigureWidget.
- disabled: Context manager that temporarily disables widgets during a block.

"""

from ._version import __version__

from ._internal import var, monitor, button
from .base import DashboardBase, callback
from .core import Dashboard, interactive, interact, markdown, hstack, vstack
from .utils import print_error, disabled
from .patches import patched_plotly
from .widgets import FullscreenButton, AnimationSlider, ListWidget, TabsWidget, JupyTimer


