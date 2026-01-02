"""
Entry point for running tobii_gaze_server as a module.
Usage: python -m tobii_gaze_server
"""

from .server import main

if __name__ == "__main__":
    main()
