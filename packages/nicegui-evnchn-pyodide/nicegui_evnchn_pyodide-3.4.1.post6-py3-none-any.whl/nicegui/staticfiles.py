try:
    from starlette.responses import Response
    from starlette.staticfiles import StaticFiles
    from starlette.types import Scope
except ImportError:
    Response = None  # type: ignore
    StaticFiles = object  # type: ignore
    Scope = None  # type: ignore


class CacheControlledStaticFiles(StaticFiles):  # type: ignore

    def __init__(self, *args, max_cache_age: int = 3600, **kwargs) -> None:
        self.max_cache_age = max_cache_age
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers['Cache-Control'] = f'public, max-age={self.max_cache_age}'
        return response
