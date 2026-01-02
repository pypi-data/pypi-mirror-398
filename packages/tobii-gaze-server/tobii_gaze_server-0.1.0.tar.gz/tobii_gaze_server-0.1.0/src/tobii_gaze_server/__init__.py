"""
Tobii Gaze Server - WebSocket server for Tobii Eye Tracker gaze data.
"""

from .server import TobiiGazeServer, main

__version__ = "0.1.0"
__all__ = ["TobiiGazeServer", "main"]
