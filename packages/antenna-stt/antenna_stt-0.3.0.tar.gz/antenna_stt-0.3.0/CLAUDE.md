# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Antenna is a Rust-powered speech-to-text library with Python bindings. It provides multi-model speech recognition through a unified `SpeechModel` trait, with multiple inference backends:

- **Candle** (default): Native Rust ML framework for Whisper/Distil-Whisper
- **ONNX Runtime**: Cross-platform inference for Wav2Vec2 and other models
- **CTranslate2**: Optional 4x faster Whisper inference
- **External libraries**: sherpa-rs, parakeet-rs for specialized models

**Current Version:** 0.3.0 with full CUDA GPU support.

## Current Implementation Status

**Layered Backend Architecture Plan** (see `~/.claude/plans/abstract-discovering-platypus.md`):

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Backend Foundation (mod.rs, device.rs) | ✅ Complete |
| Phase 2 | ONNX Runtime Backend (onnx.rs) | ✅ Complete |
| Phase 3 | Wav2Vec2 Model (ONNX) + Python bindings | ✅ Complete |
| Phase 6 | Unified Model Registry | ✅ Complete |
| Phase 7 | Python Streaming API (synchronous, VAD-enabled) | ✅ Complete |
| Phase 7b | Python Async Streaming API | ✅ Complete |
| Phase 7c | Server Components (Agreement, RingBuffer) | ✅ Complete |
| Phase 4 | CTranslate2 Backend (optional) | 🔲 Pending |
| Phase 5 | External Libraries (optional) | 🔲 Pending |

### Known Gaps / Future Work

**Full Server Module**: The `src/server/` HTTP/WebSocket/WebRTC server is Rust-only. Key streaming components (LocalAgreementPolicy, AudioRingBuffer) are now exposed to Python, but the full HTTP server infrastructure is not.

## Development Commands

```bash
# Build (required after Rust changes)
uv run maturin develop           # Debug build (CPU only)
uv run maturin develop --release # Optimized build (CPU only)

# Build with CUDA support (requires CUDA toolkit)
uv run maturin develop --release --features cuda

# Test
cargo test                       # Rust unit tests (86 tests)
uv run pytest tests/ -v          # All Python tests (226+ tests)

# Run specific test suites
uv run pytest tests/test_basic.py -v       # Audio loading tests
uv run pytest tests/test_v0_2_0.py -v      # Audio processing tests
uv run pytest tests/test_whisper.py -v     # Whisper integration tests
uv run pytest tests/test_whisper_unit.py -v # Whisper unit tests

# Run single test
uv run pytest tests/test_whisper.py::TestWhisperIntegration::test_transcribe_returns_result -v

# Run demo
uv run python examples/whisper_demo.py [audio_file]
```

## Feature Flags

Antenna uses Cargo feature flags for optional functionality:

```toml
# In Cargo.toml
[features]
# GPU acceleration
cuda = ["candle-core/cuda", "candle-nn/cuda", "candle-transformers/cuda"]
metal = ["candle-core/metal", "candle-nn/metal", "candle-transformers/metal"]

# ML Backend Features
onnx = ["dep:ort"]                        # ONNX Runtime backend
onnx-tensorrt = ["onnx", "ort/tensorrt"]  # TensorRT acceleration
onnx-cuda = ["onnx", "ort/cuda"]          # ONNX with CUDA
ctranslate2 = ["dep:ct2rs"]               # 4x faster Whisper
sherpa = ["dep:sherpa-rs"]                # Conformer/Zipformer models
parakeet = ["dep:parakeet-rs"]            # NVIDIA Parakeet models
```

Build with features:
```bash
# CUDA GPU support (Candle)
uv run maturin develop --release --features cuda

# ONNX Runtime backend
uv run maturin develop --release --features onnx

# Multiple features
uv run maturin develop --release --features "cuda,onnx"
```

## GPU Support

### CUDA (NVIDIA GPUs)

**Prerequisites**: CUDA toolkit must be installed (provides `nvcc` compiler).
- Ubuntu: `sudo apt install nvidia-cuda-toolkit`
- Or download from [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

### Metal (macOS GPUs)

**Prerequisites**: macOS with Apple Silicon or AMD GPU. Build with `--features metal`.

### Device Selection in Python

```python
import antenna

# Check GPU availability (CUDA or Metal)
if antenna.is_gpu_available():
    print("GPU acceleration available!")

# Check specific backends
print(f"CUDA: {antenna.is_cuda_available()} ({antenna.cuda_device_count()} devices)")
print(f"Metal: {antenna.is_metal_available()} ({antenna.metal_device_count()} devices)")

# Check ONNX backend GPU support
print(f"ONNX: {antenna.is_onnx_available()}")
print(f"ONNX CUDA: {antenna.is_onnx_cuda_available()}")
print(f"ONNX TensorRT: {antenna.is_onnx_tensorrt_available()}")

# Load model on GPU (auto-detect best available)
if antenna.is_cuda_available():
    model = antenna.WhisperModel.from_size("base", device="cuda")
elif antenna.is_metal_available():
    model = antenna.WhisperModel.from_size("base", device="metal")
else:
    model = antenna.WhisperModel.from_size("base", device="cpu")

# Explicit device selection
model = antenna.WhisperModel.from_size("base", device="cuda")     # First CUDA GPU
model = antenna.WhisperModel.from_size("base", device="cuda:1")   # Second CUDA GPU
model = antenna.WhisperModel.from_size("base", device="gpu")      # Alias for cuda
model = antenna.WhisperModel.from_size("base", device="metal")    # Metal (macOS)
model = antenna.WhisperModel.from_size("base", device="mps")      # Alias for metal
```

## Architecture

### Binding Layer
- `src/lib.rs` - PyO3 module definition, all Python-exposed functions and classes
- `python/antenna/__init__.py` - Python package that re-exports from native `antenna._antenna` module
- Native types use `Py` prefix (e.g., `PyWhisperModel`, `PyAudioData`) and are aliased to cleaner names in Python

### Audio Processing (`src/audio/`)
| File | Purpose |
|------|---------|
| `io.rs` | Multi-format loading (WAV, MP3, FLAC, OGG, M4A via symphonia) and WAV saving |
| `analysis.rs` | RMS, peak, zero-crossing rate, energy calculations |
| `process.rs` | Resampling (rubato), mono conversion, normalization |
| `silence.rs` | Detection, trimming, and splitting on silence |

### Backend Abstraction (`src/ml/backends/`)
| File | Purpose |
|------|---------|
| `mod.rs` | Backend enum (Candle, Onnx, CTranslate2, Sherpa, Parakeet), ModelFamily enum, auto-selection |
| `device.rs` | Unified DeviceSpec (CPU, CUDA, TensorRT, Metal) across all backends |
| `onnx.rs` | ONNX Runtime wrapper with ExecutionProvider (CPU, CUDA, TensorRT, CoreML, DirectML) |

**Key types:**
- `Backend` - Available inference backends
- `DeviceSpec` - Unified device specification (parses "cpu", "cuda:0", "tensorrt", "metal")
- `ModelFamily` - Model categories (Whisper, DistilWhisper, Wav2Vec2, Conformer, Parakeet, Canary)
- `OnnxSession` - ONNX Runtime session wrapper (requires `onnx` feature)

### Unified Model Registry (`src/ml/registry.rs`)

The registry provides a single entry point for loading any supported model:

```python
# Python API
import antenna

# Load any model with auto backend selection
model = antenna.load_model("whisper/base", device="cuda")
model = antenna.load_model("distil-whisper/distil-small.en", device="cpu")
model = antenna.load_model("wav2vec2/base-960h", device="cpu")  # Requires ONNX

# Also accepts HuggingFace format
model = antenna.load_model("openai/whisper-tiny", device="cpu")

# List available models
for m in antenna.list_models():
    print(f"{m.id}: {m.description}")

# Check model availability
if antenna.is_model_available("wav2vec2/base-960h"):
    model = antenna.load_model("wav2vec2/base-960h")
```

**Key types:**
- `DynSpeechModel` - Enum wrapping all model types, implements `SpeechModel` trait
- `ModelSpec` - Parsed model specification (family, variant, HuggingFace ID)
- `ModelEntry` - Catalog entry with model metadata
- `load_model()` - Unified loading function with auto backend selection

### Python Streaming API (`src/streaming/`)

Lightweight streaming transcription with VAD (Voice Activity Detection) for chunk-by-chunk audio processing:

```python
import antenna

# Create streaming transcriber from model ID
transcriber = antenna.StreamingTranscriber.from_model_id(
    "whisper/tiny",
    device="cpu",
    config=antenna.StreamingConfig.realtime()  # Low-latency preset
)

# Process audio chunks (e.g., from microphone)
for chunk in audio_chunks:
    events = transcriber.process_chunk(chunk)
    for event in events:
        if event.is_partial():
            print(f"[partial] {event.text()}")
        elif event.is_final():
            print(f"[final] {event.text()}")

# Flush remaining audio at end of stream
final_events = transcriber.flush()
```

**Configuration presets:**
- `StreamingConfig.realtime()` - Low latency (0.5-2s chunks)
- `StreamingConfig.quality()` - Higher accuracy (2-5s chunks)
- `StreamingConfig.no_vad()` - Time-based chunking without VAD
- `StreamingConfig.stable()` - Stable partial results (agreement policy enabled)

**Local Agreement Policy (stable partials):**

The agreement policy prevents "flickering" in partial transcription results by only emitting tokens that have been confirmed across multiple transcription runs:

```python
# Enable stable partial results
config = antenna.StreamingConfig.stable()
transcriber = antenna.StreamingTranscriber.from_model_id("whisper/tiny", config=config)

# Or use custom agreement configuration
agreement_config = antenna.AgreementConfig.strict()  # More conservative
config = antenna.StreamingConfig(use_agreement=True, agreement_config=agreement_config)
```

**AgreementConfig presets:**
- `AgreementConfig()` - Default (2 runs must agree)
- `AgreementConfig.strict()` - 3 runs must agree, smaller buffer
- `AgreementConfig.fast()` - 2 runs, larger buffer for faster emission

**AudioRingBuffer (advanced):**

For advanced audio handling with overlap support:

```python
# Create a ring buffer for efficient audio accumulation
ring = antenna.AudioRingBuffer(capacity_seconds=30.0, sample_rate=16000, overlap_seconds=0.5)

# Push audio chunks
ring.push(audio_samples)

# Read with overlap preservation (keeps context for next read)
samples = ring.read_with_overlap(16000)  # Read up to 1 second

# Check buffer state
print(f"Buffered: {ring.duration:.2f}s, Samples: {len(ring)}")
```

**Event types:**
- `Partial` - Interim transcription (may change)
- `Final` - Finalized transcription
- `SegmentStart` / `SegmentEnd` - VAD segment boundaries
- `VadStateChange` - Voice activity state transitions

| Module | Purpose |
|--------|---------|
| `config.rs` | `StreamingConfig` with presets and validation |
| `buffer.rs` | `AudioBuffer` for sample accumulation |
| `ring_buffer.rs` | `AudioRingBuffer` efficient circular buffer with overlap |
| `vad.rs` | `SimpleVad` energy-based voice activity detection |
| `agreement.rs` | `LocalAgreementPolicy` for stable partial results |
| `transcriber.rs` | `StreamingTranscriber` and `StreamingEvent` |

### Python Async Streaming API

For async applications, use `AsyncStreamingTranscriber` which integrates with Python's asyncio:

```python
import asyncio
import antenna

async def transcribe_stream(audio_chunks):
    # Create async transcriber (same options as sync version)
    transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
        "whisper/tiny",
        device="cuda",
        config=antenna.StreamingConfig.realtime()
    )

    # Process chunks asynchronously
    for chunk in audio_chunks:
        events = await transcriber.process_chunk_async(chunk)
        for event in events:
            if event.is_final():
                print(event.text())

    # Flush at end
    final_events = await transcriber.flush_async()

asyncio.run(transcribe_stream(my_audio_chunks))
```

**Key differences from sync API:**
- Uses `await transcriber.process_chunk_async(samples)` instead of `transcriber.process_chunk(samples)`
- Uses `await transcriber.flush_async()` instead of `transcriber.flush()`
- Runs transcription in a background tokio thread, freeing the asyncio event loop
- Thread-safe: can be shared across async tasks (uses `Arc<Mutex>` internally)

### ML Traits (`src/ml/traits/`)
| File | Purpose |
|------|---------|
| `model.rs` | `SpeechModel` trait - unified interface for all STT models |
| `tokenizer.rs` | Tokenizer traits for different decoding strategies |
| `decoder.rs` | Decoder traits (CTC, encoder-decoder) |

### Whisper ML (`src/ml/whisper/`)
| File | Purpose |
|------|---------|
| `model.rs` | Model loading from HuggingFace Hub, transcription orchestration, language detection, device management |
| `config.rs` | Model size definitions, special tokens, language codes (99 languages) |
| `inference.rs` | Mel spectrogram generation (80 bins, 30s chunks), transcription options |
| `decode.rs` | Greedy and beam search decoding algorithms |

### Other Models (`src/ml/`)
| Directory | Status | Backend |
|-----------|--------|---------|
| `distil_whisper/` | Implemented | Candle |
| `wav2vec2/` | Implemented | ONNX Runtime |
| `conformer/` | Stub | sherpa-rs |
| `canary/` | Blocked | N/A (not ONNX-exportable) |

### Tokenizer (`src/ml/tokenizer.rs`)
- Whisper-specific tokenizer with special token handling
- Timestamp token conversion (0.00s - 30.00s in 0.02s increments)
- Language token mapping for 99 supported languages

### Streaming Server (`src/server/`, requires `--features server`)
Real-time transcription server with HTTP/WebSocket API (Rust-only, not exposed to Python yet):

| Module | Purpose |
|--------|---------|
| `streaming/engine.rs` | `StreamingEngine` - Orchestrates VAD, buffering, STT, agreement |
| `streaming/buffer.rs` | `AudioRingBuffer` - Efficient circular buffer for incoming audio |
| `streaming/vad.rs` | `StreamingVad` - Voice Activity Detection for segmentation |
| `streaming/agreement.rs` | `LocalAgreementPolicy` - Stabilizes partial results (prevents flicker) |
| `stt/backend.rs` | `SttBackend` trait - Pluggable backends (Whisper, Triton) |
| `http/` | REST + WebSocket endpoints for clients |

**Architecture:**
```
Client ─HTTP POST─> /sessions/:id/audio ──> SessionManager ──> StreamingEngine
   │                                                                    │
   │◄───WebSocket◄─── /sessions/:id/ws ◄── Event Broadcast ◄───────────┘
                                                   │
                                             Partial/Final Transcripts
```

**142 tests pass** with `cargo test --features server`

### Data Flow
1. Audio loaded via symphonia → `AudioData` struct (any format, any sample rate)
2. `preprocess_for_whisper()` resamples to 16kHz mono
3. `audio_to_mel_spectrogram()` converts to 80-bin mel features
4. Whisper encoder processes mel → hidden states (on CPU or GPU)
5. Decoder generates tokens via beam/greedy search
6. Tokenizer decodes to text with optional timestamps

## Key Dependencies

- **candle-core/nn/transformers**: HuggingFace ML framework for Whisper inference
- **hf-hub**: Model downloading and caching from HuggingFace Hub
- **symphonia**: Multi-format audio decoding (WAV, MP3, FLAC, OGG, M4A)
- **rubato**: High-quality sinc-based audio resampling
- **pyo3/maturin**: Rust-Python bindings

## Testing Notes

- Tests in `tests/test_whisper.py` marked with `@pytest.mark.slow` download models from HuggingFace
- Test audio files are in `test_data/`:
  - `test_audio.wav` - Primary test audio (speech)
  - `test_tone.wav` - Symlink to test_audio.wav
  - `example_speech.mp3` - MP3 format test
  - `the_quick_brown_fox.mp3` - Quick transcription test
- Models are cached in HuggingFace Hub cache (`~/.cache/huggingface/hub/`) after first download
- GPU tests (`TestWhisperGpuIntegration`) automatically skip if CUDA is not available

## Common Issues & Solutions

### Build Issues
- **"nvcc not found"**: Install CUDA toolkit or build without `--features cuda`
- **Compilation slow**: Use `--release` for faster runtime but slower build
- **Wheel not updating**: Delete `target/` and rebuild

### Runtime Issues
- **Model download fails**: Check internet connection; models cache after first download
- **Out of memory**: Use smaller model (tiny, base) or ensure sufficient RAM/VRAM
- **CUDA errors**: Verify `nvcc --version` works and driver is installed

### Test Issues
- **Tests skipped**: Some tests require model downloads or CUDA; check skip messages
- **"Test audio file not found"**: Ensure `test_data/` contains test files

## File Structure Quick Reference

```
antenna/
├── src/
│   ├── lib.rs              # PyO3 bindings entry point
│   ├── error.rs            # AntennaError types
│   ├── audio/
│   │   ├── io.rs           # load_audio(), save_audio()
│   │   ├── analysis.rs     # analyze_audio()
│   │   ├── process.rs      # preprocess_audio(), normalize_audio()
│   │   └── silence.rs      # detect_silence(), trim_silence(), split_on_silence()
│   ├── streaming/          # Python streaming API
│   │   ├── mod.rs          # Module exports
│   │   ├── config.rs       # StreamingConfig with presets
│   │   ├── buffer.rs       # AudioBuffer for sample accumulation
│   │   ├── ring_buffer.rs  # AudioRingBuffer circular buffer with overlap
│   │   ├── vad.rs          # SimpleVad energy-based VAD
│   │   ├── agreement.rs    # LocalAgreementPolicy for stable partials
│   │   └── transcriber.rs  # StreamingTranscriber, StreamingEvent
│   └── ml/
│       ├── mod.rs          # ML module exports
│       ├── registry.rs     # Unified model registry, load_model(), list_models()
│       ├── tokenizer.rs    # Whisper tokenizer (legacy)
│       ├── backends/       # Inference backend abstraction
│       │   ├── mod.rs      # Backend enum, ModelFamily, select_backend()
│       │   ├── device.rs   # DeviceSpec (CPU, CUDA, TensorRT, Metal)
│       │   └── onnx.rs     # ONNX Runtime wrapper (#[cfg(feature = "onnx")])
│       ├── traits/         # Core trait definitions
│       │   ├── model.rs    # SpeechModel trait
│       │   ├── tokenizer.rs # Tokenizer traits
│       │   └── decoder.rs  # Decoder traits
│       ├── features/       # Feature extraction
│       │   └── mel.rs      # Mel spectrogram
│       ├── decode/         # Decoding algorithms
│       │   ├── beam.rs     # Beam search
│       │   └── ctc.rs      # CTC decoding
│       ├── tokenizers/     # Tokenizer implementations
│       │   └── ctc.rs      # CTC character tokenizer
│       ├── whisper/        # Whisper implementation (Candle)
│       │   ├── model.rs    # WhisperModel class
│       │   ├── config.rs   # Model configs, languages
│       │   ├── inference.rs # Mel spectrogram, transcription
│       │   └── decode.rs   # Beam search decoder
│       ├── distil_whisper/ # Distil-Whisper (Candle)
│       ├── wav2vec2/       # Wav2Vec2 (ONNX Runtime)
│       │   ├── mod.rs      # Module exports
│       │   └── model.rs    # Wav2Vec2Model (requires `onnx` feature)
│       ├── conformer/      # Conformer stub (sherpa-rs)
│       └── canary/         # Canary stub (blocked)
├── python/antenna/
│   └── __init__.py         # Python re-exports
├── tests/
│   ├── test_basic.py       # Basic audio loading (9 tests)
│   ├── test_v0_2_0.py      # Audio processing (10 tests)
│   ├── test_whisper.py     # Whisper integration (45 tests)
│   ├── test_whisper_unit.py # Whisper unit tests (14 tests)
│   ├── test_registry.py    # Unified model registry tests (25 tests)
│   ├── test_streaming.py   # Streaming transcription tests (34 tests)
│   ├── test_device_utils.py # Device utility tests (30 tests)
│   ├── test_async_streaming.py # Async streaming tests (24 tests)
│   └── test_server_components.py # Agreement & RingBuffer tests (35 tests)
└── examples/
    ├── whisper_demo.py     # Full Whisper demo
    ├── basic_usage.py      # Basic audio loading
    └── audio_processing_demo.py # Audio analysis
```
