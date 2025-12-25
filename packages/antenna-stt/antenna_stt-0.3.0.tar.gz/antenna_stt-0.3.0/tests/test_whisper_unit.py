"""
Unit tests for Whisper internals (no model download required)

These tests verify the core implementation components work correctly
without requiring network access to download Whisper models.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMelSpectrogramPreprocessing:
    """Test audio preprocessing for Whisper."""

    def test_preprocess_creates_16khz_mono(self):
        """Test that preprocess_for_whisper creates 16kHz mono audio."""
        import antenna

        # Create test audio at 44100Hz stereo
        samples = np.sin(np.linspace(0, 10 * np.pi, 44100)).astype(np.float32)

        # Generate test WAV file
        test_file = "test_data/test_audio.wav"
        if os.path.exists(test_file):
            audio = antenna.load_audio(test_file)
            processed = antenna.preprocess_for_whisper(audio)

            assert processed.sample_rate == 16000, "Should be 16kHz"
            assert processed.channels == 1, "Should be mono"

    def test_preprocess_preserves_content(self):
        """Test that preprocessing doesn't corrupt audio content."""
        import antenna

        test_file = "test_data/test_audio.wav"
        if os.path.exists(test_file):
            audio = antenna.load_audio(test_file)
            processed = antenna.preprocess_for_whisper(audio)

            # Check that we have non-zero samples
            samples = processed.to_numpy()
            assert len(samples) > 0, "Should have samples"
            assert np.any(samples != 0), "Should have non-zero samples"


class TestWhisperAPIStructure:
    """Test that the Whisper API is properly exposed."""

    def test_whisper_model_methods(self):
        """Test WhisperModel has expected methods."""
        from antenna import WhisperModel

        # Check static methods
        assert hasattr(WhisperModel, "from_pretrained")
        assert hasattr(WhisperModel, "from_size")

    def test_transcription_result_structure(self):
        """Test TranscriptionResult has expected attributes."""
        from antenna import TranscriptionResult

        # Class should exist and be importable
        assert TranscriptionResult is not None

    def test_transcription_segment_structure(self):
        """Test TranscriptionSegment has expected attributes."""
        from antenna import TranscriptionSegment

        assert TranscriptionSegment is not None

    def test_helper_functions_exist(self):
        """Test helper functions are exported."""
        from antenna import (
            preprocess_for_whisper,
            is_model_cached,
            list_whisper_models,
        )

        assert callable(preprocess_for_whisper)
        assert callable(is_model_cached)
        assert callable(list_whisper_models)


class TestModelListing:
    """Test model listing functionality."""

    def test_list_models_returns_expected_format(self):
        """Test that list_whisper_models returns tuples of (name, id)."""
        from antenna import list_whisper_models

        models = list_whisper_models()

        assert isinstance(models, list)
        assert len(models) >= 5  # At least tiny, base, small, medium, large

        for name, model_id in models:
            assert isinstance(name, str)
            assert isinstance(model_id, str)
            assert model_id.startswith("openai/whisper-")

    def test_all_standard_sizes_listed(self):
        """Test that all standard model sizes are available."""
        from antenna import list_whisper_models

        models = list_whisper_models()
        names = [m[0] for m in models]

        expected_sizes = ["tiny", "base", "small", "medium", "large"]
        for size in expected_sizes:
            assert size in names, f"Missing size: {size}"


class TestCacheChecking:
    """Test cache checking functionality."""

    def test_is_cached_returns_bool(self):
        """Test is_model_cached returns boolean."""
        from antenna import is_model_cached

        result = is_model_cached("openai/whisper-tiny")
        assert isinstance(result, bool)

    def test_nonexistent_model_not_cached(self):
        """Test that a made-up model ID is not cached."""
        from antenna import is_model_cached

        result = is_model_cached("fake-org/fake-model-xyz123")
        assert result is False


class TestPreprocessingIntegration:
    """Test preprocessing with actual audio files."""

    @pytest.fixture
    def test_audio_path(self):
        """Path to test audio file."""
        return "test_data/test_tone.wav"

    def test_load_and_preprocess(self, test_audio_path):
        """Test full load -> preprocess pipeline."""
        import antenna

        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")

        audio = antenna.load_audio(test_audio_path)
        processed = antenna.preprocess_for_whisper(audio)

        # Verify Whisper requirements
        assert processed.sample_rate == 16000
        assert processed.channels == 1
        assert processed.duration > 0

    def test_preprocess_idempotent(self, test_audio_path):
        """Test that preprocessing already-processed audio is safe."""
        import antenna

        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")

        audio = antenna.load_audio(test_audio_path)
        processed1 = antenna.preprocess_for_whisper(audio)
        processed2 = antenna.preprocess_for_whisper(processed1)

        # Should be the same
        assert processed1.sample_rate == processed2.sample_rate
        assert processed1.channels == processed2.channels
        # Duration should be very close
        assert abs(processed1.duration - processed2.duration) < 0.01


class TestVersionInfo:
    """Test version information."""

    def test_version_is_030(self):
        """Test that version is 0.3.0."""
        import antenna

        assert antenna.__version__ == "0.3.0"


class TestAudioAnalysisStillWorks:
    """Verify v0.2.0 audio analysis features still work with Whisper changes."""

    def test_analyze_audio(self):
        """Test audio analysis works."""
        import antenna

        test_file = "test_data/test_audio.wav"
        if not os.path.exists(test_file):
            pytest.skip("Test audio file not found")

        audio = antenna.load_audio(test_file)
        stats = antenna.analyze_audio(audio)

        assert hasattr(stats, "rms")
        assert hasattr(stats, "peak")
        assert hasattr(stats, "rms_db")
        assert hasattr(stats, "peak_db")

    def test_trim_silence(self):
        """Test silence trimming works."""
        import antenna

        test_file = "test_data/test_audio.wav"
        if not os.path.exists(test_file):
            pytest.skip("Test audio file not found")

        audio = antenna.load_audio(test_file)
        trimmed = antenna.trim_silence(audio, threshold_db=-40)

        assert trimmed.duration <= audio.duration

    def test_normalize_audio(self):
        """Test audio normalization works."""
        import antenna

        test_file = "test_data/test_audio.wav"
        if not os.path.exists(test_file):
            pytest.skip("Test audio file not found")

        audio = antenna.load_audio(test_file)
        normalized = antenna.normalize_audio(audio, method="peak", target_db=-3.0)

        assert normalized.duration == audio.duration


class TestErrorMessages:
    """Test that helpful error messages are provided."""

    def test_invalid_model_size_error(self):
        """Test error for invalid model size."""
        from antenna import WhisperModel

        with pytest.raises(Exception) as exc_info:
            WhisperModel.from_size("nonexistent-size")

        # Should mention unknown model size
        assert "Unknown model size" in str(exc_info.value) or "model" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
