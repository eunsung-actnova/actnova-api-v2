
"""Expose video processor utilities for tests.

Lazy imports are used so that dependencies under ``common`` can be
added to ``sys.path`` by the test suite before the actual modules are
loaded.
"""

__all__ = [
    "VercelVideoDownloader",
    "VideoFrameHandler",
    "NaiveVideoFrameCurator",
    "LocalUploader",
]

def __getattr__(name):
    if name == "VercelVideoDownloader":
        from .video_downloader import VercelVideoDownloader as _cls
        return _cls
    if name in {"VideoFrameHandler", "NaiveVideoFrameCurator"}:
        from .videoframe_handler import (
            VideoFrameHandler as _VideoFrameHandler,
            NaiveVideoFrameCurator as _NaiveVideoFrameCurator,
        )
        return {"VideoFrameHandler": _VideoFrameHandler,
                "NaiveVideoFrameCurator": _NaiveVideoFrameCurator}[name]
    if name == "LocalUploader":
        from .video_uploader import LocalUploader as _cls
        return _cls
    raise AttributeError(name)
