#!/usr/bin/env python3
"""
Tobii Gaze Server - WebSocket server for Tobii Eye Tracker gaze data.
Uses the Tobii Stream Engine for direct gaze data (already calibrated!)
"""

import asyncio
import json
import sys
import ctypes
import time
import threading
import os
from collections import deque
from typing import Optional, Set, Deque, Any

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("Error: websockets not installed!")
    print("Please install with: pip install websockets")
    sys.exit(1)


# ===== Tobii Stream Engine Structures =====

class TobiiGazePoint(ctypes.Structure):
    """Structure for Tobii gaze point data."""
    _fields_ = [
        ('timestamp_us', ctypes.c_int64),
        ('validity', ctypes.c_int),
        ('position_xy', ctypes.c_float * 2)
    ]


GAZE_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.POINTER(TobiiGazePoint), ctypes.c_void_p)


class TobiiGazeServer:
    """WebSocket server for streaming Tobii Eye Tracker gaze data."""
    
    # Default DLL path - can be overridden via environment variable
    DEFAULT_DLL_PATH = r'C:\Program Files\Tobii\Tobii EyeX\tobii_stream_engine.dll'
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8887,
        dll_path: Optional[str] = None,
        smoothing_enabled: bool = True,
        smoothing_samples: int = 3
    ):
        """
        Initialize the Tobii Gaze Server.
        
        Args:
            host: WebSocket server host
            port: WebSocket server port
            dll_path: Path to tobii_stream_engine.dll (default: from env or standard path)
            smoothing_enabled: Enable gaze smoothing
            smoothing_samples: Number of samples for smoothing
        """
        self.host = host
        self.port = port
        self.dll_path = dll_path or os.environ.get(
            'TOBII_STREAM_ENGINE_DLL', 
            self.DEFAULT_DLL_PATH
        )
        self.smoothing_enabled = smoothing_enabled
        self.smoothing_samples = smoothing_samples
        
        # Stream Engine state
        self._stream_engine: Optional[ctypes.CDLL] = None
        self._api: Optional[ctypes.c_void_p] = None
        self._device: Optional[ctypes.c_void_p] = None
        self._gaze_callback_ref: Optional[GAZE_CALLBACK] = None
        
        # Client management
        self._connected_clients: Set[WebSocketServerProtocol] = set()
        
        # Screen dimensions
        self.screen_width = 1920
        self.screen_height = 1080
        
        # Thread-safe queue for gaze data
        self._gaze_queue: Deque[dict] = deque(maxlen=100)
        self._gaze_lock = threading.Lock()
        
        # Smoothing
        self._position_history: Deque[tuple] = deque(maxlen=smoothing_samples)
        
        # Status
        self._running = False
        self._gaze_count = 0
    
    def _detect_screen_resolution(self) -> None:
        """Detect screen resolution using Windows API."""
        try:
            user32 = ctypes.windll.user32
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
            print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        except Exception:
            pass
    
    def _init_stream_engine(self) -> bool:
        """Initialize the Tobii Stream Engine."""
        print("Loading Tobii Stream Engine...")
        try:
            self._stream_engine = ctypes.CDLL(self.dll_path)
        except OSError as e:
            print(f"Error loading Stream Engine: {e}")
            print(f"Make sure Tobii EyeX is installed: {self.dll_path}")
            return False
        
        # Define API functions
        self._stream_engine.tobii_api_create.argtypes = [
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_void_p
        ]
        self._stream_engine.tobii_api_create.restype = ctypes.c_int
        
        self._stream_engine.tobii_enumerate_local_device_urls.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        ]
        self._stream_engine.tobii_enumerate_local_device_urls.restype = ctypes.c_int
        
        self._stream_engine.tobii_device_create.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
        ]
        self._stream_engine.tobii_device_create.restype = ctypes.c_int
        
        self._stream_engine.tobii_gaze_point_subscribe.argtypes = [
            ctypes.c_void_p, GAZE_CALLBACK, ctypes.c_void_p
        ]
        self._stream_engine.tobii_gaze_point_subscribe.restype = ctypes.c_int
        
        self._stream_engine.tobii_device_process_callbacks.argtypes = [ctypes.c_void_p]
        self._stream_engine.tobii_device_process_callbacks.restype = ctypes.c_int
        
        # Create API
        self._api = ctypes.c_void_p()
        result = self._stream_engine.tobii_api_create(ctypes.byref(self._api), None, None)
        if result != 0:
            print(f"Error creating API: {result}")
            return False
        print("✓ Stream Engine API created")
        
        # Search for devices
        devices_found = []
        
        @ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_void_p)
        def device_callback(url, user_data):
            devices_found.append(url.decode('utf-8'))
        
        self._stream_engine.tobii_enumerate_local_device_urls(self._api, device_callback, None)
        
        if not devices_found:
            print("No Tobii Eye Tracker found!")
            return False
        
        device_url = devices_found[0]
        print(f"✓ Eye Tracker found: {device_url}")
        
        # Connect to device
        self._device = ctypes.c_void_p()
        result = self._stream_engine.tobii_device_create(
            self._api, device_url.encode(), 1, ctypes.byref(self._device)
        )
        if result != 0:
            print(f"Error connecting: {result}")
            return False
        print("✓ Connected to Eye Tracker")
        
        # Gaze Subscription
        def gaze_callback_func(gaze_point, user_data):
            self._gaze_count += 1
            gp = gaze_point.contents
            
            if gp.validity == 1:  # Valid data
                # Convert normalized coordinates (0-1) to screen coordinates
                screen_x = gp.position_xy[0] * self.screen_width
                screen_y = gp.position_xy[1] * self.screen_height
                
                # Smoothing
                if self.smoothing_enabled:
                    self._position_history.append((screen_x, screen_y))
                    if len(self._position_history) >= 2:
                        screen_x = sum(p[0] for p in self._position_history) / len(self._position_history)
                        screen_y = sum(p[1] for p in self._position_history) / len(self._position_history)
                
                # Clamp to screen
                screen_x = max(0, min(self.screen_width, screen_x))
                screen_y = max(0, min(self.screen_height, screen_y))
                
                message = {
                    'type': 'gaze',
                    'x': screen_x,
                    'y': screen_y
                }
                
                with self._gaze_lock:
                    self._gaze_queue.append(message)
        
        self._gaze_callback_ref = GAZE_CALLBACK(gaze_callback_func)
        result = self._stream_engine.tobii_gaze_point_subscribe(
            self._device, self._gaze_callback_ref, None
        )
        if result != 0:
            print(f"Error subscribing: {result}")
            return False
        print("✓ Gaze data activated")
        
        return True
    
    def _gaze_polling_thread(self) -> None:
        """Thread for gaze data polling."""
        print("Gaze polling started...")
        last_report = time.time()
        
        while self._running:
            if self._device:
                self._stream_engine.tobii_device_process_callbacks(self._device)
            time.sleep(0.008)  # ~120 Hz polling
            
            # Status report every 5 seconds
            if time.time() - last_report > 5:
                print(f"  [Status] Gaze callbacks: {self._gaze_count}")
                last_report = time.time()
    
    async def _gaze_sender(self) -> None:
        """Sends gaze data to all connected clients."""
        send_count = 0
        
        while self._running:
            messages_to_send = []
            with self._gaze_lock:
                messages_to_send = list(self._gaze_queue)
                self._gaze_queue.clear()
            
            if messages_to_send and self._connected_clients:
                latest = messages_to_send[-1]
                message_str = json.dumps(latest)
                
                send_count += 1
                if send_count % 120 == 0:
                    print(f"→ Sending: x={latest['x']:.0f}, y={latest['y']:.0f} to {len(self._connected_clients)} client(s)")
                
                disconnected = set()
                for client in self._connected_clients:
                    try:
                        await client.send(message_str)
                    except Exception:
                        disconnected.add(client)
                
                for client in disconnected:
                    self._connected_clients.discard(client)
            
            await asyncio.sleep(0.016)  # ~60 Hz send rate
    
    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handles WebSocket connections."""
        print("New client connected")
        self._connected_clients.add(websocket)
        
        try:
            # Send status
            await websocket.send(json.dumps({
                'type': 'status',
                'connected': True,
                'mode': 'GAZE',
                'message': 'Tobii Stream Engine - Calibrated gaze data'
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Screen resolution from client
                    if data.get('action') == 'set_screen_size':
                        self.screen_width = int(data.get('width', self.screen_width))
                        self.screen_height = int(data.get('height', self.screen_height))
                        print(f"  Screen resolution: {self.screen_width}x{self.screen_height}")
                    
                    # Calibration no longer needed!
                    elif data.get('action') == 'start_calibration':
                        print("  Calibration skipped - Tracker is already calibrated!")
                        await websocket.send(json.dumps({
                            'type': 'calibration_finished',
                            'points': 0,
                            'message': 'Tobii is already calibrated - no extra calibration needed!'
                        }))
                        
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            print("Client disconnected")
            self._connected_clients.discard(websocket)
    
    async def _run_async(self) -> None:
        """Async main loop."""
        print("=" * 50)
        print("Tobii Gaze Server")
        print("=" * 50)
        
        # Detect screen resolution
        self._detect_screen_resolution()
        
        # Initialize Stream Engine
        if not self._init_stream_engine():
            print("\nError: Stream Engine could not be initialized!")
            return
        
        self._running = True
        
        # Start gaze polling thread
        polling_thread = threading.Thread(target=self._gaze_polling_thread, daemon=True)
        polling_thread.start()
        
        print("\n" + "=" * 50)
        print(f"WebSocket server running on ws://{self.host}:{self.port}")
        print("Tracking mode: GAZE (calibrated)")
        print("=" * 50)
        print("\nPress Ctrl+C to exit\n")
        
        # Start WebSocket Server
        async with websockets.serve(self._handle_client, self.host, self.port):
            sender_task = asyncio.create_task(self._gaze_sender())
            try:
                await asyncio.Future()  # Runs forever
            except asyncio.CancelledError:
                pass
            finally:
                self._running = False
                sender_task.cancel()
    
    def run(self) -> None:
        """Start the server (blocking)."""
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            print("\nServer terminated")


def main() -> None:
    """Entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tobii Gaze Server - WebSocket server for eye tracking")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8887, help="Server port (default: 8887)")
    parser.add_argument("--dll", help="Path to tobii_stream_engine.dll")
    parser.add_argument("--no-smoothing", action="store_true", help="Disable gaze smoothing")
    
    args = parser.parse_args()
    
    server = TobiiGazeServer(
        host=args.host,
        port=args.port,
        dll_path=args.dll,
        smoothing_enabled=not args.no_smoothing
    )
    server.run()


if __name__ == "__main__":
    main()
