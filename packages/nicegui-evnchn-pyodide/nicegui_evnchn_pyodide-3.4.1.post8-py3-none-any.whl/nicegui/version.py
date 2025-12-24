import importlib.metadata

try:
    __version__: str = importlib.metadata.version('nicegui')
except importlib.metadata.PackageNotFoundError:
    # Fallback for Pyodide where package metadata may not be available
    __version__ = '3.4.1.post8'
