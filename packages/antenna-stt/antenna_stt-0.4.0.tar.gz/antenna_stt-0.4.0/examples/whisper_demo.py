#!/usr/bin/env python3
"""
Whisper Speech-to-Text Demo

This example demonstrates how to use Antenna's Whisper integration
for speech-to-text transcription.

Requirements:
    - Run `uv run maturin develop` to build the package
    - Internet connection for first-time model download

Usage:
    uv run python examples/whisper_demo.py [audio_file]
"""

import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import antenna


def print_separator(title: str = ""):
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print('=' * 60)
    else:
        print('-' * 60)


def demo_basic_transcription(audio_path: str):
    """Demonstrate basic transcription workflow."""
    print_separator("Basic Transcription")

    # Load audio file
    print(f"\n📁 Loading audio: {audio_path}")
    audio = antenna.load_audio(audio_path)
    print(f"   Duration: {audio.duration:.2f}s")
    print(f"   Sample rate: {audio.sample_rate} Hz")
    print(f"   Channels: {audio.channels}")

    # Preprocess for Whisper (16kHz mono)
    print("\n🔧 Preprocessing for Whisper...")
    audio = antenna.preprocess_for_whisper(audio)
    print(f"   New sample rate: {audio.sample_rate} Hz")
    print(f"   New channels: {audio.channels}")

    # Load Whisper model
    print("\n🤖 Loading Whisper model (tiny)...")
    start = time.time()
    model = antenna.WhisperModel.from_size("tiny")
    load_time = time.time() - start
    print(f"   Model loaded in {load_time:.2f}s")

    # Transcribe
    print("\n🎙️ Transcribing...")
    start = time.time()
    result = model.transcribe(audio)
    transcribe_time = time.time() - start
    print(f"   Transcription completed in {transcribe_time:.2f}s")

    # Print results
    print("\n📝 Results:")
    print(f"   Language: {result.language}")
    print(f"   Text: {result.text}")

    if result.segments:
        print("\n📑 Segments:")
        for seg in result.segments:
            print(f"   [{seg.start:6.2f}s - {seg.end:6.2f}s] {seg.text}")


def demo_language_detection(audio_path: str):
    """Demonstrate automatic language detection."""
    print_separator("Language Detection")

    audio = antenna.load_audio(audio_path)
    audio = antenna.preprocess_for_whisper(audio)

    model = antenna.WhisperModel.from_size("tiny")

    print("\n🌍 Detecting language...")
    language = model.detect_language(audio)
    print(f"   Detected language: {language}")

    # Map to full name
    lang_names = {
        "en": "English", "es": "Spanish", "fr": "French",
        "de": "German", "zh": "Chinese", "ja": "Japanese",
        "ko": "Korean", "pt": "Portuguese", "it": "Italian",
        "ru": "Russian", "ar": "Arabic", "hi": "Hindi",
    }
    full_name = lang_names.get(language, language)
    print(f"   Language name: {full_name}")


def demo_translation(audio_path: str):
    """Demonstrate translation to English."""
    print_separator("Translation to English")

    audio = antenna.load_audio(audio_path)
    audio = antenna.preprocess_for_whisper(audio)

    model = antenna.WhisperModel.from_size("tiny")

    print("\n🔄 Translating to English...")
    result = model.translate(audio)

    print(f"\n📝 Translation: {result.text}")


def demo_convenience_function(audio_path: str):
    """Demonstrate the high-level transcribe() convenience function."""
    print_separator("Convenience Function")

    print(f"\n🚀 Using antenna.transcribe() for quick transcription...")

    result = antenna.transcribe(
        audio_path,
        model_size="tiny",
        device="cpu"
    )

    print(f"\n📝 Result: {result.text}")
    print(f"   Language: {result.language}")
    print(f"   Segments: {len(result.segments)}")


def demo_model_options():
    """Show available model options."""
    print_separator("Available Whisper Models")

    models = antenna.list_whisper_models()

    print("\n📋 Available models:")
    print(f"   {'Size':<12} {'Model ID':<30} {'Recommended For'}")
    print(f"   {'-'*12} {'-'*30} {'-'*25}")

    recommendations = {
        "tiny": "Quick tests, low resource",
        "base": "General use, balanced",
        "small": "Better accuracy",
        "medium": "High accuracy",
        "large": "Best accuracy",
        "large-v2": "Improved large model",
        "large-v3": "Latest, best quality",
    }

    for name, model_id in models:
        rec = recommendations.get(name, "")
        print(f"   {name:<12} {model_id:<30} {rec}")


def demo_check_cache():
    """Check model cache status."""
    print_separator("Model Cache Status")

    models = antenna.list_whisper_models()

    print("\n💾 Cache status:")
    for name, model_id in models:
        cached = antenna.is_model_cached(model_id)
        status = "✅ Cached" if cached else "❌ Not cached"
        print(f"   {name:<12} {status}")


def demo_gpu_info():
    """Show GPU/CUDA information."""
    print_separator("GPU Information")

    cuda_available = antenna.is_cuda_available()
    device_count = antenna.cuda_device_count()

    print(f"\n🖥️  CUDA available: {'✅ Yes' if cuda_available else '❌ No'}")
    print(f"   Device count: {device_count}")

    if cuda_available:
        print("\n   To use GPU acceleration:")
        print("   model = antenna.WhisperModel.from_size('base', device='cuda')")
    else:
        print("\n   To enable GPU support, rebuild with:")
        print("   uv run maturin develop --release --features cuda")


def demo_gpu_transcription(audio_path: str):
    """Demonstrate GPU-accelerated transcription."""
    if not antenna.is_cuda_available():
        print_separator("GPU Transcription (Skipped)")
        print("\n⚠️  CUDA not available, skipping GPU demo")
        return

    print_separator("GPU Transcription")

    audio = antenna.load_audio(audio_path)
    audio = antenna.preprocess_for_whisper(audio)

    print("\n🚀 Loading model on GPU...")
    start = time.time()
    model = antenna.WhisperModel.from_size("tiny", device="cuda")
    load_time = time.time() - start
    print(f"   Model loaded in {load_time:.2f}s")

    print("\n🎙️ Transcribing on GPU...")
    start = time.time()
    result = model.transcribe(audio)
    transcribe_time = time.time() - start
    print(f"   Transcription completed in {transcribe_time:.2f}s")

    print(f"\n📝 Result: {result.text}")


def main():
    print("=" * 60)
    print("  Antenna v0.3.0 - Whisper Speech-to-Text Demo")
    print("=" * 60)

    # Check for audio file argument
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        # Use test audio if available
        test_files = [
            "test_data/test_tone.wav",
            "test_data/speech.wav",
            "examples/test_audio.wav",
        ]
        audio_path = None
        for f in test_files:
            if os.path.exists(f):
                audio_path = f
                break

        if audio_path is None:
            print("\n⚠️  No audio file specified and no test audio found.")
            print("   Usage: python whisper_demo.py <audio_file>")
            print("\n   Showing available options instead...")

            demo_model_options()
            demo_check_cache()
            return

    if not os.path.exists(audio_path):
        print(f"\n❌ Audio file not found: {audio_path}")
        sys.exit(1)

    # Run demos
    try:
        demo_basic_transcription(audio_path)
        demo_language_detection(audio_path)
        demo_translation(audio_path)
        demo_convenience_function(audio_path)
        demo_gpu_info()
        demo_gpu_transcription(audio_path)
        demo_model_options()
        demo_check_cache()

        print_separator("Demo Complete")
        print("\n✅ All demos completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
