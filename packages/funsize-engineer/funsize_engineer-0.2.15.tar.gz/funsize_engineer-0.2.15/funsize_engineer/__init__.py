from .card import main as card

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__all__ = ['card', '__version__']
