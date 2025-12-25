# Antenna

Rust-powered multi-model Speech-to-Text toolkit for Python.

## Supported Models

| Model | Backend | GPU | Description |
|-------|---------|-----|-------------|
| **Whisper** | Candle | CUDA, Metal | OpenAI's encoder-decoder model (tiny → large-v3) |
| **Distil-Whisper** | Candle | CUDA, Metal | 2x faster distilled Whisper variants |
| **Wav2Vec2** | ONNX | CUDA, TensorRT | Meta's CTC-based model |
| **Parakeet** | sherpa-rs | CUDA, DirectML | NVIDIA's FastConformer-TDT (600M params, blazing fast) |

## Installation

### CPU Version
```bash
pip install antenna-stt
```

### GPU Version (CUDA)
```bash
# Option A: Pre-built wheel
pip install antenna-stt[cuda]

# Option B: Build from source (requires CUDA toolkit)
git clone https://github.com/fiction-ai-studios/antenna.git
cd antenna
pip install maturin
maturin build --release --features cuda
pip install target/wheels/antenna_stt-*.whl
```

### Development Installation
```bash
git clone https://github.com/fiction-ai-studios/antenna.git
cd antenna
uv venv && source .venv/bin/activate
uv add --dev maturin pytest pytest-asyncio

# Build options:
uv run maturin develop --release                    # CPU only
uv run maturin develop --release --features cuda    # + Whisper GPU
uv run maturin develop --release --features onnx    # + Wav2Vec2
uv run maturin develop --release --features sherpa  # + Parakeet
uv run maturin develop --release --features sherpa-cuda  # + Parakeet GPU
```

## Quick Start

### Basic Transcription
```python
import antenna

# One-liner
result = antenna.transcribe("speech.wav", model_size="base")
print(result.text)

# With more control
audio = antenna.load_audio("speech.wav")
audio = antenna.preprocess_for_whisper(audio)
model = antenna.WhisperModel.from_size("base", device="cuda")
result = model.transcribe(audio)

for segment in result.segments:
    print(f"[{segment.start:.2f}s] {segment.text}")
```

### Unified Model Registry
```python
import antenna

# Load ANY model through unified API
model = antenna.load_model("whisper/base", device="cuda")
model = antenna.load_model("distil-whisper/distil-small.en", device="cpu")
model = antenna.load_model("wav2vec2/base-960h", device="cpu")      # Requires ONNX
model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cuda")   # Requires sherpa

# List all available models
for m in antenna.list_models():
    print(f"{m.id}: {m.description}")
```

### Streaming Transcription
```python
import antenna

# Real-time chunk-by-chunk processing
transcriber = antenna.StreamingTranscriber.from_model_id(
    "whisper/tiny",
    device="cpu",
    config=antenna.StreamingConfig.realtime()
)

for chunk in audio_chunks:
    events = transcriber.process_chunk(chunk)
    for event in events:
        if event.is_final():
            print(event.text())

transcriber.flush()
```

### Async Streaming
```python
import asyncio
import antenna

async def transcribe():
    transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
        "whisper/tiny", device="cuda"
    )
    for chunk in audio_chunks:
        events = await transcriber.process_chunk_async(chunk)
        for event in events:
            if event.is_final():
                print(event.text())
    await transcriber.flush_async()

asyncio.run(transcribe())
```

## Feature Flags

| Feature | Description | Models Enabled |
|---------|-------------|----------------|
| `cuda` | Candle CUDA GPU | Whisper, Distil-Whisper |
| `metal` | Candle Metal GPU (macOS) | Whisper, Distil-Whisper |
| `onnx` | ONNX Runtime | Wav2Vec2 |
| `onnx-cuda` | ONNX with CUDA | Wav2Vec2 (GPU) |
| `sherpa` | sherpa-rs backend | Parakeet |
| `sherpa-cuda` | sherpa with CUDA | Parakeet (GPU) |

Build with multiple features:
```bash
uv run maturin develop --release --features "cuda,onnx,sherpa-cuda"
```

## Parakeet Models (NEW)

NVIDIA Parakeet is incredibly fast (can transcribe 60min audio in ~1 second).

**Setup:**
```bash
# 1. Build with sherpa feature
uv run maturin develop --release --features sherpa-cuda

# 2. Download model
mkdir -p ~/.cache/antenna/parakeet
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
tar xvf sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 -C ~/.cache/antenna/parakeet/
```

**Usage:**
```python
import antenna

model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cuda")
result = model.transcribe(audio)
print(result.text)
```

**Variants:**
- `parakeet/tdt-0.6b-v2` - English (recommended)
- `parakeet/tdt-0.6b-v3` - Multilingual (25 languages)

## Audio Processing

```python
import antenna

# Load any format (WAV, MP3, FLAC, OGG, M4A)
audio = antenna.load_audio("podcast.mp3")

# Analyze
stats = antenna.analyze_audio(audio)
print(f"RMS: {stats.rms_db:.1f} dB, Peak: {stats.peak_db:.1f} dB")

# Process
audio = antenna.trim_silence(audio, threshold_db=-40)
audio = antenna.normalize_audio(audio, method="rms", target_db=-20)
audio = antenna.preprocess_audio(audio, target_sample_rate=16000, mono=True)

# Save
antenna.save_audio(audio, "processed.wav")
```

## Model Selection Guide

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| Whisper tiny | 39M | ★★★★★ | ★★ | Quick tests |
| Whisper base | 74M | ★★★★ | ★★★ | General use |
| Whisper large-v3 | 1.5G | ★ | ★★★★★ | Best quality |
| Distil-Whisper | ~350M | ★★★★ | ★★★★ | Fast + accurate |
| Wav2Vec2 | 95-317M | ★★★ | ★★★ | CTC decoding |
| **Parakeet** | 600M | ★★★★★ | ★★★★★ | **Fastest + accurate** |

## GPU Availability Check

```python
import antenna

print(f"CUDA: {antenna.is_cuda_available()} ({antenna.cuda_device_count()} devices)")
print(f"Metal: {antenna.is_metal_available()}")
print(f"ONNX: {antenna.is_onnx_available()}")
print(f"ONNX CUDA: {antenna.is_onnx_cuda_available()}")
```

## Testing

```bash
cargo test --features sherpa    # Rust tests (129)
uv run pytest tests/ -v         # Python tests (226+)
```

## Roadmap

- ✅ Whisper/Distil-Whisper (Candle)
- ✅ Wav2Vec2 (ONNX)
- ✅ Parakeet (sherpa-rs)
- ✅ Streaming API with VAD
- ✅ Async streaming
- ✅ GPU support (CUDA, Metal, DirectML)
- 🔲 Canary (NeMo format)
- 🔲 Conformer (sherpa-rs)
- 🔲 Production HTTP/WebSocket server

## License

MIT

## Acknowledgments

- [PyO3](https://pyo3.rs/) - Rust-Python bindings
- [Candle](https://github.com/huggingface/candle) - ML framework
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) - Parakeet inference
- [ONNX Runtime](https://onnxruntime.ai/) - Cross-platform inference
- [OpenAI Whisper](https://openai.com/research/whisper) - Original Whisper model
