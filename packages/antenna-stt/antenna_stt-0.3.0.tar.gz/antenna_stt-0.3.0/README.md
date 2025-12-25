# Antenna

Rust-powered Speech-to-Text toolkit for Python with Whisper integration.

## Status

Antenna is now in **v0.3.0 - Whisper Integration**, providing speech-to-text transcription using OpenAI's Whisper models via the Candle ML framework.

## Features

### v0.3.0 - Whisper Integration
- **Whisper Models**: Load any Whisper model (tiny, base, small, medium, large, large-v2, large-v3)
- **Transcription**: Convert speech to text with timestamps
- **Translation**: Translate any language to English
- **Language Detection**: Automatic detection of 99 languages
- **Model Caching**: Automatic caching for faster subsequent loads
- **GPU Acceleration**: Full CUDA support for NVIDIA GPUs (3-10x faster than CPU)
- **CPU Support**: Full functionality on CPU for systems without GPU

### v0.2.0 - Enhanced Audio Foundation
- **Multi-Format Support**: Load MP3, FLAC, OGG, M4A, and WAV files
- **Audio Analysis**: RMS, peak, zero-crossing rate, energy calculations
- **Silence Detection**: Detect, trim, and split audio on silence
- **Audio Normalization**: Peak, RMS, and LUFS normalization
- **Save Functionality**: Export processed audio to WAV format
- **Format Conversion**: Convert stereo to mono
- **Resampling**: High-quality resampling using sinc interpolation
- **NumPy Integration**: Seamless conversion to NumPy arrays

### Planned
- v0.4.0: Real-time streaming and async API
- v0.5.0: Voice Activity Detection (VAD) and advanced preprocessing

## Installation

### Prerequisites
- Python 3.8+
- Rust (will be installed automatically by maturin if not present)
- uv package manager

### GPU Prerequisites (Optional)
For CUDA GPU acceleration:
- NVIDIA GPU with CUDA support
- CUDA Toolkit installed (provides `nvcc` compiler)
  - Ubuntu: `sudo apt install nvidia-cuda-toolkit`
  - Or download from [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

### Development Installation

```bash
# Clone the repository
cd antenna

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
uv add --dev maturin

# CPU-only build
uv run maturin develop --release

# OR build with CUDA/GPU support
uv run maturin develop --release --features cuda

# Install dependencies
uv add numpy
uv add --dev pytest
```

## Quick Start

### Speech-to-Text Transcription (NEW in v0.3.0!)

```python
import antenna

# Quick transcription with convenience function
result = antenna.transcribe("speech.wav", model_size="base")
print(result.text)

# Or step by step with more control:

# 1. Load and preprocess audio
audio = antenna.load_audio("podcast.mp3")
audio = antenna.preprocess_for_whisper(audio)  # Converts to 16kHz mono

# 2. Load Whisper model
model = antenna.WhisperModel.from_size("base")  # tiny, base, small, medium, large

# 3. Transcribe
result = model.transcribe(audio)
print(f"Language: {result.language}")
print(f"Text: {result.text}")

# 4. Access segments with timestamps
for segment in result.segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
```

### Translation to English

```python
import antenna

# Load audio in any language
audio = antenna.load_audio("spanish_speech.wav")
audio = antenna.preprocess_for_whisper(audio)

# Translate to English
model = antenna.WhisperModel.from_size("base")
result = model.translate(audio)
print(result.text)  # English translation
```

### Language Detection

```python
import antenna

audio = antenna.load_audio("mystery_language.wav")
audio = antenna.preprocess_for_whisper(audio)

model = antenna.WhisperModel.from_size("base")
language = model.detect_language(audio)
print(f"Detected language: {language}")  # e.g., "en", "es", "zh"
```

### GPU Acceleration

```python
import antenna

# Check if CUDA is available
if antenna.is_cuda_available():
    print(f"CUDA available with {antenna.cuda_device_count()} device(s)")

    # Load model on GPU (3-10x faster than CPU)
    model = antenna.WhisperModel.from_size("base", device="cuda")

    # Or specify a specific GPU
    model = antenna.WhisperModel.from_size("base", device="cuda:0")

    # "gpu" is an alias for "cuda"
    model = antenna.WhisperModel.from_size("base", device="gpu")
else:
    # Fallback to CPU
    model = antenna.WhisperModel.from_size("base", device="cpu")

# Transcription works the same way
audio = antenna.load_audio("speech.wav")
audio = antenna.preprocess_for_whisper(audio)
result = model.transcribe(audio)
print(result.text)
```

### Audio Processing

```python
import antenna

# Load audio file (supports WAV, MP3, FLAC, OGG, M4A)
audio = antenna.load_audio("podcast.mp3")
print(f"Sample rate: {audio.sample_rate} Hz")
print(f"Channels: {audio.channels}")
print(f"Duration: {audio.duration:.2f}s")

# Analyze audio
stats = antenna.analyze_audio(audio)
print(f"RMS: {stats.rms:.4f}, Peak: {stats.peak:.4f}")
print(f"RMS (dB): {stats.rms_db:.2f}, Peak (dB): {stats.peak_db:.2f}")

# Clean up audio
audio = antenna.trim_silence(audio, threshold_db=-40)
audio = antenna.normalize_audio(audio, method="rms", target_db=-20)

# Preprocess for Whisper (16kHz, mono)
audio = antenna.preprocess_audio(audio, target_sample_rate=16000, mono=True)

# Save processed audio
antenna.save_audio(audio, "processed.wav")

# Access as NumPy array
samples = audio.to_numpy()
print(f"Shape: {samples.shape}, dtype: {samples.dtype}")
```

### Running the Demo

```bash
# Run Whisper transcription demo
uv run python examples/whisper_demo.py [audio_file]

# Generate a test audio file
uv run python examples/generate_test_audio.py

# Run audio processing demo
uv run python examples/audio_processing_demo.py
```

## API Reference

### Whisper Speech-to-Text

#### `WhisperModel.from_size(size: str, device: str = "cpu") -> WhisperModel`

Load a Whisper model by size name.

**Parameters:**
- `size`: Model size - "tiny", "base", "small", "medium", "large", "large-v2", "large-v3"
- `device`: Device to run on - "cpu" or "cuda"

**Returns:**
- `WhisperModel`: Loaded model ready for transcription

#### `WhisperModel.from_pretrained(model_id: str, device: str = "cpu") -> WhisperModel`

Load a Whisper model from HuggingFace Hub.

**Parameters:**
- `model_id`: HuggingFace model ID (e.g., "openai/whisper-tiny")
- `device`: Device to run on - "cpu" or "cuda"

**Returns:**
- `WhisperModel`: Loaded model ready for transcription

#### `WhisperModel.transcribe(audio, language=None, task=None, beam_size=5, timestamps=True) -> TranscriptionResult`

Transcribe audio to text.

**Parameters:**
- `audio`: AudioData object (must be 16kHz mono, use `preprocess_for_whisper()`)
- `language`: Language code (e.g., "en", "es"). None for auto-detection.
- `task`: "transcribe" or "translate" (translate to English)
- `beam_size`: Beam size for decoding (default: 5, use 1 for greedy)
- `timestamps`: Whether to include timestamps (default: True)

**Returns:**
- `TranscriptionResult`: Object with `text`, `language`, and `segments`

#### `WhisperModel.translate(audio) -> TranscriptionResult`

Translate audio to English.

**Parameters:**
- `audio`: AudioData object (must be 16kHz mono)

**Returns:**
- `TranscriptionResult`: English translation with timestamps

#### `WhisperModel.detect_language(audio) -> str`

Detect the language of audio.

**Parameters:**
- `audio`: AudioData object (must be 16kHz mono)

**Returns:**
- `str`: Language code (e.g., "en", "es", "zh")

#### `preprocess_for_whisper(audio: AudioData) -> AudioData`

Preprocess audio for Whisper (convert to 16kHz mono).

**Parameters:**
- `audio`: Input AudioData object

**Returns:**
- `AudioData`: Audio ready for Whisper (16kHz, mono)

#### `transcribe(audio_path, model_size="base", language=None, device="cpu") -> TranscriptionResult`

Convenience function to transcribe an audio file in one call.

**Parameters:**
- `audio_path`: Path to audio file
- `model_size`: Whisper model size
- `language`: Language code (None for auto-detection)
- `device`: "cpu" or "cuda"

**Returns:**
- `TranscriptionResult`: Transcription result

#### `list_whisper_models() -> List[Tuple[str, str]]`

List available Whisper model sizes and their HuggingFace IDs.

#### `is_model_cached(model_id: str) -> bool`

Check if a model is cached locally.

### CUDA Utilities

#### `is_cuda_available() -> bool`

Check if CUDA GPU acceleration is available.

**Returns:**
- `bool`: True if CUDA is available and the library was built with CUDA support

#### `cuda_device_count() -> int`

Get the number of available CUDA devices.

**Returns:**
- `int`: Number of CUDA-capable GPUs (0 if CUDA is not available)

### Data Types

#### `TranscriptionResult`

Transcription result container.

**Properties:**
- `text: str` - Full transcribed text
- `language: str` - Detected or specified language code
- `segments: List[TranscriptionSegment]` - List of timed segments

#### `TranscriptionSegment`

A single segment with timing.

**Properties:**
- `start: float` - Start time in seconds
- `end: float` - End time in seconds
- `text: str` - Segment text

### Audio Loading & Saving

#### `load_audio(path: str) -> AudioData`

Load audio from any supported format.

#### `save_audio(audio: AudioData, path: str) -> None`

Save audio to WAV format.

### Audio Analysis

#### `analyze_audio(audio: AudioData) -> AudioStats`

Analyze audio and return statistics.

#### `AudioStats`

**Properties:**
- `rms: float` - Root Mean Square amplitude
- `peak: float` - Peak amplitude
- `rms_db: float` - RMS level in dB
- `peak_db: float` - Peak level in dB
- `zero_crossing_rate: float` - Rate of zero crossings
- `energy: float` - Total energy

### Silence Detection

#### `detect_silence(audio, threshold_db, min_duration) -> List[Tuple[float, float]]`

Detect silence segments in audio.

#### `trim_silence(audio, threshold_db) -> AudioData`

Trim silence from beginning and end.

#### `split_on_silence(audio, threshold_db, min_silence_duration) -> List[AudioData]`

Split audio into chunks on silence regions.

### Audio Processing

#### `preprocess_audio(audio, target_sample_rate=None, mono=None) -> AudioData`

Preprocess audio data (resample, convert to mono).

#### `normalize_audio(audio, method, target_db) -> AudioData`

Normalize audio to target level.

**Methods:** "peak", "rms", "lufs"

### Data Types

#### `AudioData`

**Properties:**
- `sample_rate: int` - Sample rate in Hz
- `channels: int` - Number of audio channels
- `duration: float` - Duration in seconds

**Methods:**
- `to_numpy() -> np.ndarray` - Convert to NumPy array

## Testing

```bash
# Run all tests
cargo test && uv run pytest tests/ -v

# Run only Whisper tests
uv run pytest tests/test_whisper.py -v

# Run integration tests (downloads models)
uv run pytest tests/test_whisper.py -v -m slow
```

## Development

### Project Structure

```
antenna/
├── Cargo.toml              # Rust dependencies
├── pyproject.toml          # Python package config
├── src/
│   ├── lib.rs              # PyO3 bindings (Python interface)
│   ├── types.rs            # Core types (AudioData, TranscriptionResult)
│   ├── error.rs            # Error types
│   ├── audio/              # Audio processing
│   │   ├── mod.rs
│   │   ├── io.rs           # Audio I/O
│   │   ├── analysis.rs     # Audio analysis
│   │   ├── process.rs      # Preprocessing
│   │   └── silence.rs      # Silence detection
│   └── ml/                 # Machine learning (NEW in v0.3.0)
│       ├── mod.rs
│       ├── tokenizer.rs    # Whisper tokenizer
│       └── whisper/
│           ├── mod.rs
│           ├── model.rs    # Model loading
│           ├── config.rs   # Model configurations
│           ├── inference.rs # Transcription engine
│           └── decode.rs   # Beam search decoder
├── python/
│   └── antenna/
│       └── __init__.py     # Python package entry
├── tests/
│   ├── test_basic.py       # Audio processing tests
│   └── test_whisper.py     # Whisper tests (NEW)
└── examples/
    ├── whisper_demo.py     # Whisper transcription demo (NEW)
    ├── generate_test_audio.py
    └── audio_processing_demo.py
```

### Building

```bash
# Development build
uv run maturin develop

# Release build (optimized)
uv run maturin develop --release

# Build wheel
uv run maturin build --release
```

## Model Selection Guide

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| tiny | ~39M | Fastest | Lower | Quick tests, low resources |
| base | ~74M | Fast | Good | General use, balanced |
| small | ~244M | Medium | Better | Better accuracy needed |
| medium | ~769M | Slower | High | High accuracy needed |
| large | ~1.5G | Slow | Highest | Best quality needed |
| large-v2 | ~1.5G | Slow | Higher | Improved large model |
| large-v3 | ~1.5G | Slow | Best | Latest, best quality |

## Supported Languages

Whisper supports 99 languages including:
- English, Spanish, French, German, Italian, Portuguese
- Chinese, Japanese, Korean
- Arabic, Hindi, Russian
- And 90+ more...

## Troubleshooting

### Model Download Issues

**Problem**: Model download fails or is slow
**Solution**: Check your internet connection. Models are cached after first download.

**Problem**: Out of memory when loading large models
**Solution**: Use a smaller model (tiny, base, small) or ensure sufficient RAM.

### Transcription Issues

**Problem**: Poor transcription quality
**Solution**:
- Ensure audio is clear without excessive background noise
- Try a larger model
- Use `preprocess_for_whisper()` to ensure correct format

**Problem**: Wrong language detected
**Solution**: Specify the language explicitly: `model.transcribe(audio, language="en")`

## Roadmap

### v0.3.0 - Whisper Integration ✅
- [x] Candle ML integration
- [x] Whisper model loading from HuggingFace
- [x] CPU transcription
- [x] Model caching
- [x] Language detection
- [x] Translation to English
- [x] Beam search decoding
- [x] GPU support (CUDA)

### v0.4.0 - Streaming & Async
- [ ] Async API
- [ ] Streaming API
- [ ] Real-time transcription
- [ ] Batch processing

### v0.5.0 - Production Ready
- [ ] Voice Activity Detection (VAD)
- [ ] Advanced preprocessing options
- [ ] Metal support for macOS

## License

MIT

## Acknowledgments

- [PyO3](https://pyo3.rs/) - Rust-Python bindings
- [maturin](https://www.maturin.rs/) - Build tool
- [Candle](https://github.com/huggingface/candle) - ML framework
- [HuggingFace Hub](https://huggingface.co/) - Model hosting
- [rubato](https://github.com/HEnquist/rubato) - Audio resampling
- [symphonia](https://github.com/pdeljanov/Symphonia) - Multi-format audio decoding
- [OpenAI Whisper](https://openai.com/research/whisper) - Original Whisper model
