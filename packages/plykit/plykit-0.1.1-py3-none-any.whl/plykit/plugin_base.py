"""Plugin base class for ply tools

Each plugin must expose a `get_plugin()` function returning an instance
of a subclass of BasePlugin.

Plugin.run(input, params, logger) should perform the operation and return
an arbitrary dict with results. `input` can be a file-path (str) or an
Open3D point cloud object.
"""

from typing import Any, Dict
from plykit_global import *


class BasePlugin:
    name: str = "base"
    description: str = "Base plugin"
    default_params: Dict[str, Any] = {}

    def __init__(self):
        pass

    def run(self, input_obj, params: Dict[str, Any], logger) -> Dict[str, Any]:
        """Execute plugin.

        input_obj: either a file path (str) or an open3d.geometry.PointCloud
        params: dict of parameters (plugin-specific)
        logger: function-like that accepts a string to append to logs

        Returns a dict with results, plugin-specific.
        """
        raise NotImplementedError()


def simple_logger(widget_append_fn):
    """Return a logger function that appends lines to a UI widget or prints.

    widget_append_fn: callable that accepts a str
    """

    def _log(msg: str):
        try:
            widget_append_fn(str(msg))
        except Exception:
            CUSTOM_LOGGER.info(msg)

    return _log
