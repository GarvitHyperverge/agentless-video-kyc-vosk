"""
Vosk WebSocket Server for Speech Recognition

This server accepts audio chunks via WebSocket, processes them using Vosk,
and returns real-time transcription results (partial and final).
"""

import asyncio
import websockets
import json
from vosk import Model, KaldiRecognizer

# Load the Vosk speech recognition model
# Model expects 16kHz mono 16-bit PCM audio
print("Loading Vosk model...")
model = Model("vosk-model-en-in-0.5")
print("Model loaded successfully")


def initialize_connection(websocket, path):
    """
    Initialize connection and recognizer.
    
    Args:
        websocket: WebSocket connection object
        path: Optional connection path
        
    Returns:
        KaldiRecognizer: Initialized recognizer instance
    """
    print(f"New client connected from {websocket.remote_address}")
    if path:
        print(f"Connection path: {path}")
    
    # Initialize Vosk recognizer with 16kHz sample rate
    rec = KaldiRecognizer(model, 16000)
    print(f"Recognizer initialized for {websocket.remote_address}")
    
    return rec

def validate_message(message):
    """
    Validate incoming message.
    
    Args:
        message: Incoming message from client
        
    Returns:
        bool: True if message is valid, False otherwise
    """
    # Validate message type - Vosk requires binary audio data (bytes)
    if not isinstance(message, bytes):
        print(f"Warning: Unexpected message type {type(message)}, skipping")
        return False
    return True

async def handle_end_of_stream(websocket, rec, partial, final):
    """
    Handle end-of-stream signal (empty buffer).
    
    Args:
        websocket: WebSocket connection object
        rec: KaldiRecognizer instance
        partial: Current last partial result
        final: Current last final result
        
    Returns:
        None
    """
    print(f"Received end of stream signal from {websocket.remote_address}, finalizing...")
    # If we got a final result, use it
    if final:
        result = json.dumps({"text": final})
        print(f"Sending final result: {final}")
        await websocket.send(result)
    # If no final , use last partial
    elif partial:
        result = json.dumps({"text": partial})
        print(f"Sending last partial as final result: {partial}")
        await websocket.send(result)
    # If no partial either, send empty
    else:
        result = json.dumps({"text": ""})
        print(f"No results found, sending empty text")
        await websocket.send(result)
    
    print(f"Stream ended for {websocket.remote_address}")

async def process_audio_chunk(websocket, rec, message, partial, final):
    """
    Process audio chunk (or empty buffer for end-of-stream).
    
    Args:
        websocket: WebSocket connection object
        rec: KaldiRecognizer instance
        message: Audio chunk (bytes) or empty buffer for end-of-stream
        partial: Current last partial result
        final: Current last final result
        
    Returns:
        tuple: (partial: str, final: str) - Updated tracking variables
    """
    # Check if this is an end-of-stream signal (empty buffer)
    if len(message) == 0:
        await handle_end_of_stream(websocket, rec, partial, final)
        return None, None  # Reset for new stream
    
    # Process normal audio chunk
    # AcceptWaveform processes the audio chunk:
    # - True: Recognized a complete phrase/sentence 
    # - False: only partial result available
    if rec.AcceptWaveform(message):
        # Vosk recognized a complete phrase
        result = rec.Result()
        result_json = json.loads(result)
        result_text = result_json.get('text', '')
        if result_text:
            # Store the final result
            print(f"Final result: {result_text}")
            final = result_text
    else:
        # Get partial/interim result
        partial_result = rec.PartialResult()
        partial_json = json.loads(partial_result)
        partial_text = partial_json.get('partial', '')
        if partial_text:
            # Store the partial result
            partial = partial_text
            print(f"Partial result: {partial_text}")
    
    return partial, final

async def main_message_loop(websocket, rec):
    """
    Main message loop - receive and process messages.
    
    Args:
        websocket: WebSocket connection object
        rec: KaldiRecognizer instance
        
    Returns:
        None
    """
    # Track the last partial and final results
    # Used as fallback if stream ends without final result
    partial = None
    final = None
    
    # Main message loop: process audio chunks as they arrive
    # The loop exits when client stops sending or closes connection
    async for message in websocket:
        try:
            # Validate message
            if not validate_message(message):
                continue
            
            # Process message
            partial, final = await process_audio_chunk(websocket, rec, message, partial, final)
            print(f"Processed message chunk from {websocket.remote_address}")
        except Exception as e:
            # Log errors but continue processing (don't crash on single bad chunk)
            print(f"Error processing message from {websocket.remote_address}: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise, just log and continue

async def recognize(websocket, path=None):
    """
    Handle WebSocket connection for speech recognition.
    
    Main orchestration function that coordinates all steps:
    1. Initialize connection and recognizer
    2. Process messages in main loop
    3. Handle errors
    
    Args:
        websocket: WebSocket connection object
        path: Optional connection path (not used but required by websockets library)
    """
    try:
        # Initialize connection and recognizer
        rec = initialize_connection(websocket, path)    
        # Main message loop - receive and process messages
        await main_message_loop(websocket, rec)
    except Exception as e:
        print(f"Error processing client {websocket.remote_address}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"Connection closed for {websocket.remote_address}")

async def main():
    """
    Start the WebSocket server.
    
    Server listens on 0.0.0.0:2700 and accepts connections from any interface.
    Each connection is handled by the recognize() function.
    """
    print("Starting WebSocket server on 0.0.0.0:2700")
    # Start WebSocket server on all interfaces (0.0.0.0) on port 2700
    # Each incoming connection is handled by the recognize() coroutine
    async with websockets.serve(recognize, "0.0.0.0", 2700):
        print("Server is running and accepting connections...")
        # Keep the server running indefinitely
        # asyncio.Future() creates a future that never completes
        await asyncio.Future()

# Run the server
if __name__ == "__main__":
    asyncio.run(main())
