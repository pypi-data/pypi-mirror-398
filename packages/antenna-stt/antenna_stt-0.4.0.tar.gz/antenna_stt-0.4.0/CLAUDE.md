# CLAUDE.md

This file provides guidance to Claude Code when working with the Antenna codebase.

## Overview

Antenna is a Rust-powered multi-model Speech-to-Text toolkit with Python bindings via PyO3/maturin.

| Model | Backend | GPU Support | Status |
|-------|---------|-------------|--------|
| Whisper (tiny → large-v3) | Candle | CUDA, Metal | Implemented |
| Distil-Whisper | Candle | CUDA, Metal | Implemented |
| Wav2Vec2 | ONNX Runtime | CUDA, TensorRT | Implemented |
| Parakeet (600M FastConformer) | sherpa-rs | CUDA, DirectML | Implemented |
| Conformer | sherpa-rs | - | Stub |
| Canary | NeMo (planned) | - | Stub |

**Version:** 0.3.0

## Quick Reference

### Build Commands

```bash
# CPU only
uv run maturin develop --release

# With GPU support
uv run maturin develop --release --features cuda           # Whisper/Distil CUDA
uv run maturin develop --release --features metal          # Whisper/Distil Metal
uv run maturin develop --release --features onnx           # Wav2Vec2
uv run maturin develop --release --features sherpa         # Parakeet CPU
uv run maturin develop --release --features sherpa-cuda    # Parakeet CUDA

# Multiple features
uv run maturin develop --release --features "cuda,onnx,sherpa-cuda"
```

### Test Commands

```bash
cargo test                          # Rust tests (129 with sherpa)
cargo test --features sherpa        # Include Parakeet tests
uv run pytest tests/ -v             # Python tests (226+)
```

### Feature Flags

| Feature | Backend | Models Enabled |
|---------|---------|----------------|
| `cuda` | Candle CUDA | Whisper, Distil-Whisper |
| `metal` | Candle Metal | Whisper, Distil-Whisper |
| `onnx` | ONNX Runtime | Wav2Vec2 |
| `onnx-cuda` | ONNX + CUDA | Wav2Vec2 GPU |
| `onnx-tensorrt` | ONNX + TensorRT | Wav2Vec2 GPU |
| `sherpa` | sherpa-rs | Parakeet CPU |
| `sherpa-cuda` | sherpa-rs + CUDA | Parakeet GPU |
| `sherpa-directml` | sherpa-rs + DirectML | Parakeet GPU (Windows) |
| `server` | HTTP/WebSocket | Streaming server |

## Architecture

### Directory Structure

```
src/
├── lib.rs                    # PyO3 bindings entry point
├── error.rs                  # AntennaError types
├── types.rs                  # AudioData, shared types
├── audio/                    # Audio processing
│   ├── io.rs                 # load_audio(), save_audio() [symphonia]
│   ├── analysis.rs           # RMS, peak, zero-crossing
│   ├── process.rs            # resample(), mono conversion [rubato]
│   └── silence.rs            # VAD, trim, split
├── streaming/                # Python streaming API
│   ├── config.rs             # StreamingConfig presets
│   ├── buffer.rs             # AudioBuffer accumulation
│   ├── ring_buffer.rs        # Circular buffer with overlap
│   ├── vad.rs                # SimpleVad energy-based
│   ├── agreement.rs          # LocalAgreementPolicy
│   └── transcriber.rs        # StreamingTranscriber, events
├── ml/
│   ├── mod.rs                # Module exports
│   ├── registry.rs           # load_model(), list_models()
│   ├── backends/
│   │   ├── mod.rs            # Backend, ModelFamily enums
│   │   ├── device.rs         # DeviceSpec (cpu, cuda:N, metal)
│   │   └── onnx.rs           # OnnxSession wrapper
│   ├── traits/
│   │   ├── model.rs          # SpeechModel trait
│   │   ├── tokenizer.rs      # Tokenizer traits
│   │   └── decoder.rs        # Decoder traits (CTC, seq2seq)
│   ├── whisper/              # Candle backend
│   │   ├── model.rs          # WhisperModel
│   │   ├── config.rs         # Sizes, languages
│   │   ├── inference.rs      # Mel spectrogram
│   │   └── decode.rs         # Beam/greedy search
│   ├── distil_whisper/       # Candle backend
│   ├── wav2vec2/             # ONNX backend
│   │   └── model.rs          # Wav2Vec2Model
│   ├── parakeet/             # sherpa-rs backend
│   │   ├── config.rs         # ParakeetConfig, ParakeetSize
│   │   └── model.rs          # ParakeetModel
│   ├── conformer/            # Stub
│   └── canary/               # Stub
└── server/                   # HTTP/WS server (Rust-only)
    ├── streaming/            # Engine, buffer, VAD
    ├── stt/                   # Backend trait
    └── http/                  # REST + WebSocket
```

### Key Types

| Type | Location | Purpose |
|------|----------|---------|
| `SpeechModel` | `ml/traits/model.rs` | Unified interface for all STT models |
| `DynSpeechModel` | `ml/registry.rs` | Enum wrapping all model types |
| `DeviceSpec` | `ml/backends/device.rs` | Parses "cpu", "cuda:0", "metal" |
| `Backend` | `ml/backends/mod.rs` | Candle, Onnx, Sherpa, etc. |
| `ModelFamily` | `ml/backends/mod.rs` | Whisper, Wav2Vec2, Parakeet, etc. |
| `StreamingTranscriber` | `streaming/transcriber.rs` | Chunk-by-chunk processing |
| `AudioData` | `types.rs` | Samples + sample_rate + channels |

### Data Flow

```
Audio File → symphonia → AudioData → preprocess (16kHz mono)
    ↓
Whisper: mel spectrogram → encoder → decoder → tokens → text
Wav2Vec2: waveform → ONNX encoder → CTC decode → text
Parakeet: waveform → sherpa TransducerRecognizer → text
```

## Model-Specific Notes

### Whisper / Distil-Whisper (Candle)

- Models auto-download from HuggingFace Hub on first use
- Cache: `~/.cache/huggingface/hub/`
- Sizes: tiny (39M), base (74M), small (244M), medium (769M), large-v3 (1.5G)
- 99 supported languages with translation capability

```python
model = antenna.WhisperModel.from_size("base", device="cuda")
result = model.transcribe(audio, language="en", task="transcribe")
```

### Wav2Vec2 (ONNX)

- Uses community ONNX exports from `onnx-community/` or `Xenova/`
- Models auto-download from HuggingFace
- CTC decoding with character-level tokens

```python
# Requires: --features onnx
model = antenna.load_model("wav2vec2/base-960h", device="cpu")
```

### Parakeet (sherpa-rs)

- NVIDIA FastConformer-TDT (600M params)
- **Manual download required** (not HuggingFace hosted):

```bash
mkdir -p ~/.cache/antenna/parakeet
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
tar xvf sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 -C ~/.cache/antenna/parakeet/
```

Variants:
- `parakeet/tdt-0.6b-v2` - English (recommended)
- `parakeet/tdt-0.6b-v3` - Multilingual (25 languages)
- `parakeet/tdt-0.6b-en` - English (original)

```python
# Requires: --features sherpa or sherpa-cuda
model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cuda")
```

## Unified Model Registry

The registry (`src/ml/registry.rs`) provides a single entry point:

```python
import antenna

# Load any model
model = antenna.load_model("whisper/base", device="cuda")
model = antenna.load_model("distil-whisper/distil-small.en")
model = antenna.load_model("wav2vec2/base-960h")      # Requires onnx
model = antenna.load_model("parakeet/tdt-0.6b-v2")    # Requires sherpa

# List available models
for m in antenna.list_models():
    print(f"{m.id}: {m.description}")

# Check availability
if antenna.is_model_available("wav2vec2/base-960h"):
    model = antenna.load_model("wav2vec2/base-960h")
```

## Streaming API

### Synchronous

```python
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

### Async

```python
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
```

### Config Presets

| Preset | Use Case |
|--------|----------|
| `StreamingConfig.realtime()` | Low latency (0.5-2s chunks) |
| `StreamingConfig.quality()` | Higher accuracy (2-5s chunks) |
| `StreamingConfig.stable()` | Stable partials (agreement policy) |
| `StreamingConfig.no_vad()` | Time-based chunking only |

## GPU Support

### Check Availability

```python
import antenna

antenna.is_cuda_available()         # CUDA (Candle)
antenna.cuda_device_count()
antenna.is_metal_available()        # Metal (Candle)
antenna.is_onnx_available()         # ONNX Runtime
antenna.is_onnx_cuda_available()    # ONNX + CUDA
antenna.is_onnx_tensorrt_available()
```

### Device Strings

| String | Device |
|--------|--------|
| `"cpu"` | CPU |
| `"cuda"` or `"gpu"` | First CUDA GPU |
| `"cuda:0"`, `"cuda:1"` | Specific CUDA GPU |
| `"metal"` or `"mps"` | Metal (macOS) |
| `"tensorrt"` | TensorRT (ONNX) |

## Test Files

Located in `test_data/`:
- `test_audio.wav` - Primary test speech
- `the_quick_brown_fox.mp3` - Quick transcription test
- `example_speech.mp3` - MP3 format test

## Common Issues

| Issue | Solution |
|-------|----------|
| `nvcc not found` | Install CUDA toolkit or build without `--features cuda` |
| Model download fails | Check internet; models cache after first download |
| Out of memory | Use smaller model (tiny, base) |
| Wheel not updating | Delete `target/` and rebuild |
| Parakeet model not found | Manual download required (see above) |

## Key Dependencies

| Crate | Purpose |
|-------|---------|
| `candle-*` | ML framework for Whisper |
| `ort` | ONNX Runtime for Wav2Vec2 |
| `sherpa-rs` | Parakeet/Conformer inference |
| `symphonia` | Audio decoding (WAV, MP3, FLAC, etc.) |
| `rubato` | Audio resampling |
| `pyo3` | Python bindings |
| `hf-hub` | HuggingFace model downloads |
