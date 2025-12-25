"""Tests for v0.2.0 features"""

import antenna
import pytest
import os


def test_analyze_audio():
    """Test audio analysis functionality"""
    audio = antenna.load_audio("test_data/test_audio.wav")
    stats = antenna.analyze_audio(audio)

    # Check that stats object has all required attributes
    assert hasattr(stats, "rms")
    assert hasattr(stats, "peak")
    assert hasattr(stats, "peak_db")
    assert hasattr(stats, "rms_db")
    assert hasattr(stats, "zero_crossing_rate")
    assert hasattr(stats, "energy")

    # Check that values are in reasonable ranges
    assert stats.rms >= 0.0
    assert stats.peak >= 0.0
    assert stats.peak >= stats.rms  # Peak should always be >= RMS
    assert stats.peak_db <= 0.0  # Should be negative for normalized audio
    assert stats.zero_crossing_rate >= 0.0


def test_trim_silence():
    """Test silence trimming"""
    audio = antenna.load_audio("test_data/test_audio.wav")
    original_duration = audio.duration

    # Trim silence with -40 dB threshold
    trimmed = antenna.trim_silence(audio, threshold_db=-40.0)

    # Trimmed audio should have same sample rate and channels
    assert trimmed.sample_rate == audio.sample_rate
    assert trimmed.channels == audio.channels

    # Duration might be same or shorter depending on silence
    assert trimmed.duration <= original_duration


def test_detect_silence():
    """Test silence detection"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Detect silence segments
    segments = antenna.detect_silence(audio, threshold_db=-40.0, min_duration=0.1)

    # Should return a list of tuples
    assert isinstance(segments, list)

    # Each segment should be a tuple of (start, end) in seconds
    for segment in segments:
        assert isinstance(segment, tuple)
        assert len(segment) == 2
        start, end = segment
        assert isinstance(start, float)
        assert isinstance(end, float)
        assert end > start
        assert start >= 0.0
        assert end <= audio.duration


def test_split_on_silence():
    """Test splitting audio on silence"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Split on silence
    chunks = antenna.split_on_silence(audio, threshold_db=-40.0, min_silence_duration=0.1)

    # Should return a list of AudioData objects
    assert isinstance(chunks, list)
    assert len(chunks) >= 1  # At least one chunk

    # Each chunk should be valid AudioData
    for chunk in chunks:
        assert isinstance(chunk, antenna.AudioData)
        assert chunk.sample_rate == audio.sample_rate
        assert chunk.channels == audio.channels


def test_normalize_peak():
    """Test peak normalization"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Normalize to -3 dB peak
    normalized = antenna.normalize_audio(audio, method="peak", target_db=-3.0)

    # Check normalized audio properties
    assert normalized.sample_rate == audio.sample_rate
    assert normalized.channels == audio.channels

    # Analyze to verify normalization
    stats = antenna.analyze_audio(normalized)

    # Peak should be close to -3 dB (within 1 dB tolerance)
    assert abs(stats.peak_db - (-3.0)) < 1.0


def test_normalize_rms():
    """Test RMS normalization"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Normalize to -20 dB RMS
    normalized = antenna.normalize_audio(audio, method="rms", target_db=-20.0)

    # Check normalized audio properties
    assert normalized.sample_rate == audio.sample_rate
    assert normalized.channels == audio.channels

    # Analyze to verify normalization
    stats = antenna.analyze_audio(normalized)

    # RMS should be close to -20 dB (within 2 dB tolerance)
    assert abs(stats.rms_db - (-20.0)) < 2.0


def test_normalize_lufs():
    """Test LUFS normalization"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Normalize to -16 LUFS (common for streaming)
    normalized = antenna.normalize_audio(audio, method="lufs", target_db=-16.0)

    # Check normalized audio properties
    assert normalized.sample_rate == audio.sample_rate
    assert normalized.channels == audio.channels


def test_normalize_invalid_method():
    """Test that invalid normalization method raises error"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    with pytest.raises(ValueError, match="Invalid normalization method"):
        antenna.normalize_audio(audio, method="invalid", target_db=-3.0)


def test_save_and_reload_audio():
    """Test saving audio and reloading it"""
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Save to a temporary file
    output_path = "test_data/test_output.wav"

    try:
        antenna.save_audio(audio, output_path)

        # Reload the saved audio
        reloaded = antenna.load_audio(output_path)

        # Check that basic properties match
        assert reloaded.sample_rate == audio.sample_rate
        assert reloaded.channels == audio.channels

        # Duration should be very close (allow small difference due to encoding)
        assert abs(reloaded.duration - audio.duration) < 0.1
    finally:
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)


def test_full_pipeline():
    """Test a complete audio processing pipeline"""
    # Load audio
    audio = antenna.load_audio("test_data/test_audio.wav")

    # Analyze original
    original_stats = antenna.analyze_audio(audio)
    print(f"\nOriginal stats: {original_stats}")

    # Trim silence
    audio = antenna.trim_silence(audio, threshold_db=-40.0)

    # Normalize
    audio = antenna.normalize_audio(audio, method="rms", target_db=-20.0)

    # Preprocess for Whisper
    audio = antenna.preprocess_audio(audio, target_sample_rate=16000, mono=True)

    # Final analysis
    final_stats = antenna.analyze_audio(audio)
    print(f"Final stats: {final_stats}")

    # Verify final properties
    assert audio.sample_rate == 16000
    assert audio.channels == 1

    # Save processed audio
    output_path = "test_data/test_processed.wav"
    try:
        antenna.save_audio(audio, output_path)
        assert os.path.exists(output_path)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
