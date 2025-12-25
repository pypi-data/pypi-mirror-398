"""tapoapi package.

Public API:
- Camera: high-level client that auto-connects (logs in) by default.

This project targets TP-Link Tapo local LAN secure v3 endpoints.
"""

from .camera import Camera, TapoAuthError

__version__ = "0.1.0"

__all__ = ["Camera", "TapoAuthError", "__version__"]