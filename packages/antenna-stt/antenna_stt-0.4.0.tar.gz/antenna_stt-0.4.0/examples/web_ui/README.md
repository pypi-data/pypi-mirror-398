# Antenna STT Web UI

A simple web interface for testing the Antenna real-time speech-to-text server.

## Quick Start

### 1. Start the Antenna Server

Open a terminal and run:

```bash
cd /home/rusen/Desktop/codebase/fiction-studios/antenna

# Build and run with the "tiny" model (fastest, ~75MB download)
cargo run --bin antenna-server --features server --release -- --model tiny

# Or use "base" model for better accuracy (~150MB download)
cargo run --bin antenna-server --features server --release -- --model base
```

You should see output like:
```
Antenna STT Server v0.3.0

Configuration:
  Model: tiny
  Device: cpu
  Host: 0.0.0.0
  Port: 8080
  Shutdown timeout: 30s

Loading Whisper model...
Backend initialized:
  Name: whisper-candle
  Model: tiny
  Device: cpu
  ...

Server running on http://0.0.0.0:8080
```

### 2. Start the Web UI

Open another terminal:

```bash
cd /home/rusen/Desktop/codebase/fiction-studios/antenna/examples/web_ui

# Using Python (recommended)
python serve.py

# Or using Python's built-in server
python -m http.server 3000
```

### 3. Open in Browser

Go to: **http://localhost:3000**

### 4. Use the UI

1. Click **"Check Server"** to verify connection
2. Click **"Start Recording"** to begin transcription
3. Speak into your microphone
4. Watch real-time transcripts appear
5. Click **"Stop Recording"** when done

## Server Options

```bash
# Use GPU (if CUDA is available)
cargo run --bin antenna-server --features server,cuda --release -- --model base --device cuda

# Use a specific GPU
cargo run --bin antenna-server --features server,cuda --release -- --model base --device cuda:1

# Change port
cargo run --bin antenna-server --features server --release -- --model tiny --port 9000

# Longer shutdown timeout
cargo run --bin antenna-server --features server --release -- --model tiny --shutdown-timeout 60
```

## Model Options

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | ~75MB | Fastest | Lower | Testing, demos |
| `base` | ~150MB | Fast | Good | General use |
| `small` | ~500MB | Medium | Better | Production |
| `medium` | ~1.5GB | Slower | High | High accuracy |
| `large` | ~3GB | Slowest | Best | Maximum accuracy |

## API Endpoints

Once the server is running, you can also use these endpoints directly:

```bash
# Health check
curl http://localhost:8080/health

# Detailed health (includes backend info)
curl http://localhost:8080/health/detailed

# Server info
curl http://localhost:8080/info

# Create a session
curl -X POST http://localhost:8080/sessions \
  -H "Content-Type: application/json" \
  -d '{}'

# List sessions
curl http://localhost:8080/sessions

# Get session info
curl http://localhost:8080/sessions/{session_id}

# Close session
curl -X DELETE http://localhost:8080/sessions/{session_id}
```

## Troubleshooting

### "Connection Failed"
- Make sure the server is running on port 8080
- Check the server terminal for errors
- Try `curl http://localhost:8080/health`

### No transcription appearing
- Check that your microphone is working
- Allow microphone access in browser
- Check the Event Log for errors
- The first transcription may take a moment to load the model

### Audio quality issues
- Use a good microphone
- Reduce background noise
- Speak clearly and at moderate pace

### Server slow to start
- First run downloads the model (~75MB-3GB depending on size)
- Model is cached in `~/.cache/huggingface/hub/` for future runs
- Use `tiny` model for faster startup during testing

## Architecture

```
Browser                        Server
   │                             │
   ├─── POST /sessions ─────────►│ Create session
   │◄── session_id, ws_url ──────┤
   │                             │
   ├─── WebSocket connect ──────►│ Subscribe to events
   │                             │
   ├─── POST /audio (f32 LE) ───►│ Send audio chunks
   │                             │
   │◄── {"Partial": {...}} ──────┤ Receive partial results
   │◄── {"Final": {...}} ────────┤ Receive final results
   │                             │
   ├─── DELETE /sessions/:id ───►│ Close session
   │                             │
```
