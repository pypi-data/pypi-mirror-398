"""
Static files utilities for FastAPI
"""

import os
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, Response
from starlette.types import Scope


class StaticFilesCache(StaticFiles):
    """
    StaticFiles subclass with configurable cache control headers for HTML and text files
    """

    def __init__(self, *args, cachecontrol="no-cache, no-store, must-revalidate", **kwargs):
        """
        Initialize StaticFilesCache

        Args:
            *args: Arguments passed to StaticFiles
            cachecontrol: Cache control header value for HTML/text files
            **kwargs: Keyword arguments passed to StaticFiles
        """
        self.cachecontrol = cachecontrol
        super().__init__(*args, **kwargs)

    def file_response(
        self,
        full_path,
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        """
        Create a file response with cache control headers for HTML and text files

        Args:
            full_path: Full path to the file
            stat_result: File stat result
            scope: ASGI scope
            status_code: HTTP status code

        Returns:
            Response object
        """
        if full_path.endswith(".html") or full_path.endswith(".txt"):
            resp: Response = FileResponse(full_path, status_code=status_code, stat_result=stat_result)
            resp.headers.setdefault("Cache-Control", self.cachecontrol)
            return resp
        else:
            return super().file_response(full_path, stat_result, scope, status_code)