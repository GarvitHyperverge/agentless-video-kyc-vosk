# Vosk WebSocket Server - Learning Notes

## Overview
This document explains key concepts about how the Vosk WebSocket server works for real-time speech recognition.

## Key Concepts

### 1. Vosk's Internal Buffer
- **Purpose**: Stores context and unfinalized audio, NOT all audio chunks
- **What it contains**:
  - Recent audio for context (helps recognize words that need surrounding context)
  - Unfinalized audio (incomplete words/phrases waiting for more audio)
- **Size**: Small buffer (last few seconds), not the entire audio stream

### 2. How Vosk Processes Audio

#### Incremental Processing
- Vosk processes chunks **immediately** as they arrive
- Returns partial results as it processes
- Returns final results when it recognizes complete phrases
- Does NOT wait to process everything at once

#### Example Flow:
```
Chunk 1: "hello" → Processes → Returns "hello" (final)
Chunk 2: "world" → Processes → Returns "world" (final)  
Chunk 3: "how are" → Processes → Returns "how are" (final)
Last chunk: "ing" → Processes → Can't finalize (incomplete) → Keeps in buffer
```

### 3. End-of-Stream Signal (Empty Buffer)

#### What it is:
- Client sends empty buffer (`new Uint8Array(0)`) to signal "no more audio"
- This is a **signal**, not audio data

#### What it does:
- Tells Vosk: "No more audio is coming, finalize what's left in your buffer"
- Triggers Vosk to process any remaining unfinalized audio
- Allows server to return the complete final transcription

#### Why it's needed:
- Vosk doesn't know when audio stream ends
- Keeps waiting for more audio indefinitely
- Empty buffer explicitly signals the end

### 4. AcceptWaveform() Return Values

#### True (Complete Phrase Recognized):
- Vosk found a complete phrase/sentence in the processed audio
- Result is finalized and complete
- Example: Buffer has "how are you" → Returns `True` → Complete phrase

#### False (Still Processing):
- Vosk doesn't have a complete phrase yet
- May have partial/incomplete words
- Example: Buffer has "doin" → Returns `False` → Incomplete word

### 5. Why We Need Both If/Else Branches

When flushing with empty buffer:

```python
if rec.AcceptWaveform(b''):  # Returns True
    # Got complete phrase - use it
    final_result = rec.Result()
else:  # Returns False
    # Still try to get result - might have partial text
    final_result = rec.Result()
```

**Reason**: Even if `AcceptWaveform()` returns `False`, `rec.Result()` might still return text. The else branch ensures we capture any available transcription, even if incomplete.

### 6. Finalization Strategy

The server uses a three-tier fallback approach:

1. **Try flush with empty buffer** → Get final result from Vosk
2. **If no result from flush** → Use last final result received
3. **If no final result** → Use last partial result as final

This ensures the client always receives a transcription result.

### 7. WebSocket Connection Management

#### Normal Closure (Code 1000):
- Server sends final result
- Closes connection gracefully
- Indicates successful completion

#### Error Codes:
- **1005**: No status received (connection closed without proper close frame)
- **1011**: Internal server error (server encountered an error)

#### Best Practice:
- Client should wait for server to close connection
- Server closes after sending final result
- Avoids premature connection closure

### 8. Audio Format Requirements

- **Sample Rate**: 16kHz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit PCM
- **Format**: Raw PCM or WAV (skip 44-byte header if WAV)

## Common Patterns

### Client Flow:
1. Connect to WebSocket server
2. Send audio chunks in binary format
3. Receive partial/final results as they arrive
4. Send empty buffer when done
5. Wait for final result
6. Close connection

### Server Flow:
1. Accept connection
2. Initialize Vosk recognizer
3. Process audio chunks as they arrive
4. Send partial/final results back
5. Detect end-of-stream signal (empty buffer)
6. Finalize and send final result
7. Close connection gracefully

## Key Takeaways

1. **Vosk processes incrementally** - not all at once
2. **Buffer is for context** - not for storing all chunks
3. **Empty buffer is a signal** - triggers finalization
4. **Always check both True/False cases** - might have result either way
5. **Use fallback strategy** - ensure client always gets a result
6. **Handle connection closure properly** - avoid 1005/1011 errors
