from importlib.metadata import PackageNotFoundError, version

from .solver import hanoi

__all__ = ['hanoi']


try:
    __version__ = version('hanoi-viz')
except PackageNotFoundError:
    __version__ = '0.0.0'
