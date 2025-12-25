"""Antenna: Speech-to-Text processing toolkit with Whisper integration"""

try:
    from antenna._antenna import (
        # Audio processing functions
        load_audio,
        preprocess_audio,
        analyze_audio,
        trim_silence,
        detect_silence,
        split_on_silence,
        normalize_audio,
        save_audio,
        # Whisper functions
        preprocess_for_whisper,
        is_model_cached,
        list_whisper_models,
        # Distil-Whisper functions
        list_distil_whisper_models,
        # Device utilities
        is_cuda_available,
        cuda_device_count,
        is_metal_available,
        metal_device_count,
        is_gpu_available,
        # Backend utilities
        is_onnx_available,
        is_onnx_cuda_available,
        is_onnx_tensorrt_available,
        # Audio types
        PyAudioData,
        PyAudioStats,
        # Model info types (shared across all models)
        PyModelInfo,
        PyModelCapabilities,
        # Whisper types
        PyWhisperModel,
        PyTranscriptionResult,
        PyTranscriptionSegment,
        # Distil-Whisper types
        PyDistilWhisperModel,
        # Unified model registry
        PySpeechModel,
        PyModelEntry,
        py_load_model,
        py_list_models,
        py_is_model_available,
        # Streaming transcription
        PyAgreementConfig,
        PyAudioRingBuffer,
        PyStreamingConfig,
        PyStreamingEvent,
        PyStreamingTranscriber,
        # Async streaming transcription
        PyAsyncStreamingTranscriber,
    )

    # Cleaner aliases
    AudioData = PyAudioData
    AudioStats = PyAudioStats
    ModelInfo = PyModelInfo
    ModelCapabilities = PyModelCapabilities
    WhisperModel = PyWhisperModel
    DistilWhisperModel = PyDistilWhisperModel
    TranscriptionResult = PyTranscriptionResult
    TranscriptionSegment = PyTranscriptionSegment
    # Unified registry aliases
    SpeechModel = PySpeechModel
    ModelEntry = PyModelEntry
    load_model = py_load_model
    list_models = py_list_models
    is_model_available = py_is_model_available
    # Streaming aliases
    AgreementConfig = PyAgreementConfig
    AudioRingBuffer = PyAudioRingBuffer
    StreamingConfig = PyStreamingConfig
    StreamingEvent = PyStreamingEvent
    StreamingTranscriber = PyStreamingTranscriber
    # Async streaming alias
    AsyncStreamingTranscriber = PyAsyncStreamingTranscriber

    __all__ = [
        # Audio processing
        "load_audio",
        "preprocess_audio",
        "analyze_audio",
        "trim_silence",
        "detect_silence",
        "split_on_silence",
        "normalize_audio",
        "save_audio",
        # Whisper
        "preprocess_for_whisper",
        "is_model_cached",
        "list_whisper_models",
        "WhisperModel",
        "TranscriptionResult",
        "TranscriptionSegment",
        # Distil-Whisper
        "list_distil_whisper_models",
        "DistilWhisperModel",
        # Device utilities
        "is_cuda_available",
        "cuda_device_count",
        "is_metal_available",
        "metal_device_count",
        "is_gpu_available",
        # Backend utilities
        "is_onnx_available",
        "is_onnx_cuda_available",
        "is_onnx_tensorrt_available",
        # Types
        "AudioData",
        "AudioStats",
        # Model info (shared across all models)
        "ModelInfo",
        "ModelCapabilities",
        # Unified model registry
        "load_model",
        "list_models",
        "is_model_available",
        "SpeechModel",
        "ModelEntry",
        # Streaming transcription
        "AgreementConfig",
        "AudioRingBuffer",
        "StreamingConfig",
        "StreamingEvent",
        "StreamingTranscriber",
        # Async streaming transcription
        "AsyncStreamingTranscriber",
    ]

    # Wav2Vec2 (optional, requires ONNX backend)
    if is_onnx_available():
        from antenna._antenna import (
            PyWav2Vec2Model,
            list_wav2vec2_models,
        )
        Wav2Vec2Model = PyWav2Vec2Model
        __all__.extend([
            "Wav2Vec2Model",
            "list_wav2vec2_models",
        ])

except ImportError as e:
    import warnings
    warnings.warn(f"Failed to import antenna native module: {e}")

__version__ = "0.3.0"


def transcribe(
    audio_path: str,
    model_size: str = "base",
    language: str = None,
    device: str = "cpu",
) -> "TranscriptionResult":
    """
    Convenience function to transcribe an audio file.

    Args:
        audio_path: Path to audio file (WAV, MP3, FLAC, OGG, M4A)
        model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
        language: Language code (e.g., "en", "es"). None for auto-detection.
        device: Device to run on. Options: "cpu", "cuda", "cuda:0", "metal", "mps".

    Returns:
        TranscriptionResult with text, segments, and detected language

    Example:
        >>> result = antenna.transcribe("speech.wav", model_size="base")
        >>> print(result.text)
        "Hello, this is a test transcription."
        >>> for segment in result.segments:
        ...     print(f"[{segment.start:.2f}s] {segment.text}")

        # Use GPU if available (CUDA or Metal)
        >>> if antenna.is_gpu_available():
        ...     device = "cuda" if antenna.is_cuda_available() else "metal"
        ...     result = antenna.transcribe("speech.wav", device=device)
    """
    # Load and preprocess audio
    audio = load_audio(audio_path)
    audio = preprocess_for_whisper(audio)

    # Load model and transcribe
    model = WhisperModel.from_size(model_size, device)
    return model.transcribe(audio, language=language)

