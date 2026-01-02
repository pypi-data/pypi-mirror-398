# Tobii Gaze Server

A WebSocket server for streaming Tobii Eye Tracker gaze data using the Tobii Stream Engine.

## Features

- Real-time gaze data streaming via WebSocket
- Uses Tobii Stream Engine for calibrated gaze data
- Easy integration with web applications

## Requirements

- Windows OS
- Tobii Eye Tracker with Tobii EyeX software installed
- Python 3.8+

## Installation

### Using Conda (Recommended)

1. Create and activate the conda environment:

```bash
conda env create -f environment.yml
conda activate tobii-gaze-server
```

2. Install the package in development mode:

```bash
pip install -e .
```

### Using pip

```bash
pip install tobii-gaze-server
```

## Usage

### Demo: Gaze-Controlled Mouse

The included demo moves your mouse cursor to where you look. A dwell-activated exit button allows you to quit without using the keyboard.

```bash
conda activate tobii-gaze-server
python examples/demo.py
```

**Features:**
- Mouse cursor follows your gaze
- Red X button in the top-right corner
- Look at the X button for 1.5 seconds to exit
- Automatically starts the gaze server (or uses an existing one)

**Options:**
- `--no-server`: Don't auto-start the server (use if server is already running)
- `--url ws://host:port`: Connect to a different server URL

### Command Line

Start the server:

```bash
tobii-gaze-server
```

The server will start on `ws://localhost:8887` by default.

### As a Library

```python
from tobii_gaze_server import TobiiGazeServer

server = TobiiGazeServer(host="localhost", port=8887)
server.run()
```

### Environment Variables

- `TOBII_STREAM_ENGINE_DLL`: Path to the Tobii Stream Engine DLL (default: `C:\Program Files\Tobii\Tobii EyeX\tobii_stream_engine.dll`)

## WebSocket Protocol

### Messages from Server

#### Gaze Data
```json
{
    "type": "gaze",
    "x": 960.5,
    "y": 540.2
}
```

#### Status
```json
{
    "type": "status",
    "connected": true,
    "mode": "GAZE",
    "message": "Tobii Stream Engine - Calibrated gaze data"
}
```

### Messages to Server

#### Set Screen Size
```json
{
    "action": "set_screen_size",
    "width": 1920,
    "height": 1080
}
```

## License

MIT License - see LICENSE file for details.
