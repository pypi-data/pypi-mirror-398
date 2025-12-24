"""
bilby_pipe
==========

bilby_pipe is a python3 tool for automating the process of running `bilby
<https://bilby-dev.github.io/bilby>`_ for gravitational-wave parameter
estimation on computing clusters.

"""

from . import bilbyargparser, main, parser, utils

try:
    from ._version import version as __version__
except ModuleNotFoundError:  # development mode
    __version__ = "unknown"

__short_version__ = __version__
__long_version__ = __version__
