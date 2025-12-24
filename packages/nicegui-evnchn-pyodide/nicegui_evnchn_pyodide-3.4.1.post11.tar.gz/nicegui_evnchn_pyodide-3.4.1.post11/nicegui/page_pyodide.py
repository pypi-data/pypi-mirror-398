"""
Simplified page module for Pyodide environments.
This provides a minimal page class that doesn't require FastAPI or server components.
"""


class page:
    """Minimal page class for Pyodide - just holds configuration."""
    
    def __init__(self, path: str, **kwargs):
        self._path = path
        self.title = kwargs.get('title')
        self.viewport = kwargs.get('viewport')
        self.favicon = kwargs.get('favicon')
        self.dark = kwargs.get('dark', ...)
        self.language = kwargs.get('language', ...)
        self.response_timeout = kwargs.get('response_timeout', 3.0)
        self.reconnect_timeout = kwargs.get('reconnect_timeout')
        self.api_router = None
        self.kwargs = {}
    
    @property
    def path(self) -> str:
        return self._path
    
    def resolve_title(self) -> str:
        return self.title if self.title is not None else 'NiceGUI'
    
    def resolve_viewport(self) -> str:
        return self.viewport if self.viewport is not None else 'width=device-width, initial-scale=1'
    
    def resolve_dark(self) -> bool | None:
        return self.dark if self.dark is not ... else None
    
    def resolve_language(self) -> str:
        from .language import Language
        lang = self.language if self.language is not ... else Language('en-US')
        return lang if isinstance(lang, str) else lang.value
    
    def resolve_reconnect_timeout(self) -> float:
        return self.reconnect_timeout if self.reconnect_timeout is not None else 10.0
    
    def __call__(self, func):
        # In Pyodide, we don't register routes
        return func
