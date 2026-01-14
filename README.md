# Vosk WebSocket Server

WebSocket server for speech recognition using Vosk speech recognition library.

## Model

This server uses **vosk-model-small-en-us-0.15** - a small English (US) speech recognition model.

- **Model Name**: vosk-model-small-en-us-0.15
- **Language**: English (US)
- **Size**: Small model (suitable for real-time processing)
- **Version**: 0.15

### Model Location

The model should be placed in the same directory as the script or in the working directory where the script is run. The model directory name should be: `vosk-model-small-en-us-0.15`

## Audio Format Requirements

The server expects audio in the following format:
- **Sample Rate**: 16kHz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit PCM
- **Format**: Raw PCM or WAV (if WAV, header is automatically handled)

## Installation

1. Install Python dependencies:
```bash
pip install vosk websockets
```

2. Download the model (if not already present):
  

## Usage

### Starting the Server

Run the server:
```bash
python vosk_ws.py
```

The server will:
- Start listening on `0.0.0.0:2700` (all interfaces, port 2700)
- Accept WebSocket connections
- Process audio chunks and return transcription results

### WebSocket API

**Endpoint**: `ws://localhost:2700` (or `ws://your-server:2700`)

**Protocol**:
1. Connect to the WebSocket server
2. Send audio chunks as binary messages (16kHz mono 16-bit PCM)
3. Send an empty buffer (`new Uint8Array(0)`) to signal end-of-stream
4. Receive final transcription result
5. Connection closes after sending final result

**Message Flow**:
- Client sends audio chunks → Server processes them
- Client sends empty buffer → Server finalizes and sends final result
- Server sends JSON result: `{"text": "transcribed text"}`


