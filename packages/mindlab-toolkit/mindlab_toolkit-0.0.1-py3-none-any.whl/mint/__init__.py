"""
Mind Lab Toolkit (MinT) - the Open Infrastructure for Experiential Intelligence.

All tinker APIs are available directly:
    import mint
    client = mint.TrainingClient(...)

MinT extends tinker with additional functionality while maintaining
full backward compatibility.
"""
import os as _os

# Configure mint defaults before importing tinker
# MINT_API_KEY takes precedence, falls back to TINKER_API_KEY
if "MINT_API_KEY" in _os.environ and "TINKER_API_KEY" not in _os.environ:
    _os.environ["TINKER_API_KEY"] = _os.environ["MINT_API_KEY"]

# MINT_BASE_URL takes precedence, falls back to TINKER_BASE_URL, then mint default
if "MINT_BASE_URL" in _os.environ:
    _os.environ["TINKER_BASE_URL"] = _os.environ["MINT_BASE_URL"]
elif "TINKER_BASE_URL" not in _os.environ:
    _os.environ["TINKER_BASE_URL"] = "https://mint-alpha.macaron.im"

# Re-export everything from tinker
from tinker import *
from tinker import __all__ as _tinker_all
from tinker import __version__ as _tinker_version

__version__ = "0.0.1"
__tinker_version__ = _tinker_version

# mint-specific extensions will be added here
# from .extensions import ...

__all__ = [
    *_tinker_all,
    "__version__",
    "__tinker_version__",
]
