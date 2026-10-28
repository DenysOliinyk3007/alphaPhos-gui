"""alphaphos-gui -- local browser GUI for alphaPhos.

The GUI holds no science code: every analysis step is one public
``alphaphos`` call, and the logic lives in :mod:`alphaphos_gui.core`, which
has no web dependency.  :mod:`alphaphos_gui.server` (FastAPI) exposes it as a
JSON API, and the HTML/CSS/JS page in ``static/`` displays it.

Launch with the ``alphaphos-gui`` command.
"""

from alphaphos_gui._version import __version__

__all__ = ["__version__"]
