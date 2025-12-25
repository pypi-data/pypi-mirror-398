#!/usr/bin/env python3
"""Test script for the Antenna STT server.

This script tests basic server functionality without needing a browser.

Usage:
    python examples/test_server.py [--server URL] [--audio FILE]

Examples:
    # Test with default audio file
    python examples/test_server.py

    # Test with custom audio
    python examples/test_server.py --audio path/to/audio.wav

    # Test against different server
    python examples/test_server.py --server http://localhost:9000
"""

import argparse
import asyncio
import json
import struct
import sys
from pathlib import Path

try:
    import httpx
    import websockets
except ImportError:
    print("Required packages not installed. Run:")
    print("  pip install httpx websockets")
    sys.exit(1)


async def test_health(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test health endpoints."""
    print("\n=== Testing Health Endpoints ===\n")

    # Basic health
    print("GET /health")
    r = await client.get(f"{base_url}/health")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")

    # Liveness probe
    print("\nGET /health/live")
    r = await client.get(f"{base_url}/health/live")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")

    # Readiness probe
    print("\nGET /health/ready")
    r = await client.get(f"{base_url}/health/ready")
    ready_data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Response: {ready_data}")

    # Detailed health
    print("\nGET /health/detailed")
    r = await client.get(f"{base_url}/health/detailed")
    print(f"  Status: {r.status_code}")
    data = r.json()
    print(f"  Backend: {data['backend']['name']} ({data['backend']['model']})")
    print(f"  Device: {data['backend']['device']}")
    print(f"  Ready: {data['backend']['ready']}")
    print(f"  Sessions: {data['sessions']['active']}/{data['sessions']['max']}")

    return ready_data.get("ready", False)


async def test_info(client: httpx.AsyncClient, base_url: str):
    """Test info endpoint."""
    print("\n=== Testing Info Endpoint ===\n")

    print("GET /info")
    r = await client.get(f"{base_url}/info")
    print(f"  Status: {r.status_code}")
    data = r.json()
    print(f"  Name: {data['name']}")
    print(f"  Version: {data['version']}")
    print(f"  Backend: {data['backend']['name']}")


async def test_session_lifecycle(client: httpx.AsyncClient, base_url: str):
    """Test session creation and deletion."""
    print("\n=== Testing Session Lifecycle ===\n")

    # Create session
    print("POST /sessions")
    r = await client.post(f"{base_url}/sessions", json={})
    print(f"  Status: {r.status_code}")
    data = r.json()

    if not data.get("success"):
        print(f"  Error: {data.get('error')}")
        return None

    session_id = data["data"]["session_id"]
    print(f"  Session ID: {session_id}")
    print(f"  WebSocket URL: {data['data']['websocket_url']}")
    print(f"  Audio URL: {data['data']['audio_url']}")

    # List sessions
    print("\nGET /sessions")
    r = await client.get(f"{base_url}/sessions")
    sessions = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Active sessions: {len(sessions.get('data', []))}")

    # Get session details
    print(f"\nGET /sessions/{session_id[:8]}...")
    r = await client.get(f"{base_url}/sessions/{session_id}")
    print(f"  Status: {r.status_code}")
    session_data = r.json()
    if session_data.get("success"):
        print(f"  State: {session_data['data']['state']}")

    # Delete session
    print(f"\nDELETE /sessions/{session_id[:8]}...")
    r = await client.delete(f"{base_url}/sessions/{session_id}")
    print(f"  Status: {r.status_code}")

    return session_id


async def test_transcription(client: httpx.AsyncClient, base_url: str, audio_path: Path):
    """Test full transcription flow with audio file."""
    print("\n=== Testing Transcription ===\n")

    # Load audio file
    print(f"Loading audio: {audio_path}")

    # Use antenna to load and process audio
    try:
        import antenna
        audio = antenna.load_audio(str(audio_path))
        print(f"  Original: {audio.sample_rate}Hz, {audio.channels} channel(s), {audio.duration:.2f}s")
        # Resample to 16kHz mono using preprocess_for_whisper
        audio = antenna.preprocess_for_whisper(audio)
        samples = audio.to_numpy().tolist()  # Convert to Python list
        print(f"  Preprocessed: {audio.sample_rate}Hz, {len(samples)} samples")
        print(f"  Duration: {len(samples) / 16000:.2f}s")
    except ImportError:
        print("  Warning: antenna not installed, using raw file read")
        # Fallback: try to read as raw f32 samples
        with open(audio_path, "rb") as f:
            data = f.read()
        samples = list(struct.unpack(f"<{len(data)//4}f", data))

    # Create session
    print("\nCreating session...")
    r = await client.post(f"{base_url}/sessions", json={})
    session_data = r.json()
    if not session_data.get("success"):
        print(f"  Error: {session_data.get('error')}")
        return

    session_id = session_data["data"]["session_id"]
    ws_path = session_data["data"]["websocket_url"]
    print(f"  Session: {session_id[:8]}...")

    # Connect WebSocket
    ws_url = f"{base_url.replace('http', 'ws')}{ws_path}"
    print(f"\nConnecting WebSocket: {ws_url}")

    transcripts = []

    async def receive_events(ws):
        try:
            async for message in ws:
                event = json.loads(message)
                event_type = event.get("type", "")

                if event_type == "partial":
                    text = event.get("text", "")
                    print(f"  [Partial] {text}")
                elif event_type == "final":
                    text = event.get("text", "")
                    print(f"  [Final] {text}")
                    if text.strip():
                        transcripts.append(text)
                elif event_type == "error":
                    print(f"  [Error] {event.get('message', 'Unknown error')}")
                elif event_type == "segment_start":
                    print(f"  [Segment Start] {event.get('timestamp', 0):.2f}s")
                elif event_type == "segment_end":
                    print(f"  [Segment End] {event.get('timestamp', 0):.2f}s ({event.get('duration', 0):.2f}s)")
                elif event_type == "vad_state_change":
                    print(f"  [VAD] {event.get('state', '')} at {event.get('timestamp', 0):.2f}s")
                else:
                    print(f"  [Unknown] {event}")
        except websockets.exceptions.ConnectionClosed:
            pass

    async with websockets.connect(ws_url) as ws:
        # Start receiving events
        receive_task = asyncio.create_task(receive_events(ws))

        # Send audio in chunks
        print("\nSending audio...")
        chunk_size = 16000  # 1 second chunks
        for i in range(0, len(samples), chunk_size):
            chunk = samples[i : i + chunk_size]
            # Convert to f32 little-endian bytes
            audio_bytes = struct.pack(f"<{len(chunk)}f", *chunk)

            r = await client.post(
                f"{base_url}/sessions/{session_id}/audio",
                content=audio_bytes,
                headers={"Content-Type": "application/octet-stream"},
            )
            if r.status_code != 202:
                print(f"  Warning: Audio send returned {r.status_code}")

            # Small delay between chunks
            await asyncio.sleep(0.1)

        print("  Audio sent, waiting for transcription...")

        # Wait longer for processing (Whisper inference can take time on CPU)
        # CPU inference on tiny model: ~4s per second of audio
        await asyncio.sleep(20)

        # Don't close session yet - let the worker process

        # Cancel receive task
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass

    # Clean up session
    try:
        await client.delete(f"{base_url}/sessions/{session_id}")
    except Exception:
        pass

    print(f"\n=== Transcription Result ===")
    print(f"  {' '.join(transcripts) if transcripts else '(no transcription received)'}")


async def main():
    parser = argparse.ArgumentParser(description="Test Antenna STT Server")
    parser.add_argument(
        "--server", default="http://localhost:8080", help="Server URL"
    )
    parser.add_argument("--audio", type=Path, help="Audio file to transcribe")
    args = parser.parse_args()

    print("=" * 50)
    print("Antenna STT Server Test")
    print("=" * 50)
    print(f"\nServer: {args.server}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test health
            is_ready = await test_health(client, args.server)

            if not is_ready:
                print("\n[!] Server not ready, skipping other tests")
                return

            # Test info
            await test_info(client, args.server)

            # Test session lifecycle
            await test_session_lifecycle(client, args.server)

            # Test transcription if audio provided
            if args.audio:
                if not args.audio.exists():
                    print(f"\nError: Audio file not found: {args.audio}")
                else:
                    await test_transcription(client, args.server, args.audio)
            else:
                # Try default test audio
                test_audio = Path("test_data/test_audio.wav")
                if test_audio.exists():
                    await test_transcription(client, args.server, test_audio)
                else:
                    print(f"\nNote: No audio file provided. Use --audio to test transcription.")
                    print(f"  Example: python examples/test_server.py --audio test_data/test_audio.wav")

        except httpx.ConnectError:
            print(f"\nError: Could not connect to {args.server}")
            print("Make sure the server is running:")
            print("  cargo run --bin antenna-server --features server -- --model tiny")

    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
