"""Tests for the SpeechModel trait and unified API.

These tests verify that the trait-based architecture works correctly
and that model info/capabilities are properly exposed.
"""
import pytest
import antenna


class TestModelInfoAPI:
    """Test the ModelInfo class exposed from WhisperModel."""

    @pytest.mark.slow
    def test_whisper_model_has_info(self):
        """WhisperModel.info() returns ModelInfo with expected fields."""
        model = antenna.WhisperModel.from_size("tiny", device="cpu")
        info = model.info()

        assert info.name == "Whisper tiny"
        assert info.family == "whisper"
        assert info.variant == "tiny"

    @pytest.mark.slow
    def test_info_repr(self):
        """ModelInfo has useful __repr__."""
        model = antenna.WhisperModel.from_size("tiny", device="cpu")
        info = model.info()

        repr_str = repr(info)
        assert "ModelInfo" in repr_str
        assert "whisper" in repr_str
        assert "tiny" in repr_str


class TestModelCapabilitiesAPI:
    """Test the ModelCapabilities class exposed from WhisperModel."""

    @pytest.mark.slow
    def test_whisper_model_has_capabilities(self):
        """WhisperModel.capabilities() returns expected capabilities."""
        model = antenna.WhisperModel.from_size("tiny", device="cpu")
        caps = model.capabilities()

        # Whisper supports all these features
        assert caps.supports_translation is True
        assert caps.supports_language_detection is True
        assert caps.supports_timestamps is True
        assert caps.max_audio_duration == 30.0

        # Should have many languages
        assert len(caps.supported_languages) > 50
        assert "en" in caps.supported_languages
        assert "es" in caps.supported_languages
        assert "zh" in caps.supported_languages

    @pytest.mark.slow
    def test_capabilities_repr(self):
        """ModelCapabilities has useful __repr__."""
        model = antenna.WhisperModel.from_size("tiny", device="cpu")
        caps = model.capabilities()

        repr_str = repr(caps)
        assert "ModelCapabilities" in repr_str
        # Rust uses lowercase 'true'/'false' for bools
        assert "translation=true" in repr_str


class TestDeviceAPI:
    """Test the device() method exposed from WhisperModel."""

    @pytest.mark.slow
    def test_device_returns_string(self):
        """WhisperModel.device() returns device string."""
        model = antenna.WhisperModel.from_size("tiny", device="cpu")
        device = model.device()

        assert device == "cpu"

    @pytest.mark.slow
    @pytest.mark.skipif(not antenna.is_cuda_available(), reason="CUDA not available")
    def test_device_cuda(self):
        """WhisperModel.device() returns 'cuda' when on GPU."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda")
        device = model.device()

        assert device == "cuda"


class TestPreprocessAPI:
    """Test the preprocess() method that uses SpeechModel trait."""

    @pytest.mark.slow
    def test_preprocess_loads_and_processes(self):
        """Model.preprocess() works with loaded audio."""
        import os
        model = antenna.WhisperModel.from_size("tiny", device="cpu")

        # Load test audio file
        test_audio = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_audio.wav")
        audio = antenna.load_audio(test_audio)

        # Preprocess should produce 16kHz mono audio
        preprocessed = model.preprocess(audio)
        assert preprocessed.sample_rate == 16000
        assert preprocessed.channels == 1

    @pytest.mark.slow
    def test_preprocess_idempotent(self):
        """Model.preprocess() is idempotent - preprocessing again doesn't change it."""
        import os
        model = antenna.WhisperModel.from_size("tiny", device="cpu")

        # Load and preprocess
        test_audio = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_audio.wav")
        audio = antenna.load_audio(test_audio)
        preprocessed1 = model.preprocess(audio)

        # Preprocess again
        preprocessed2 = model.preprocess(preprocessed1)

        # Should be identical
        assert preprocessed1.sample_rate == preprocessed2.sample_rate
        assert preprocessed1.channels == preprocessed2.channels
        assert preprocessed1.duration == preprocessed2.duration


class TestWhisperModelRepr:
    """Test the improved __repr__ for WhisperModel."""

    @pytest.mark.slow
    def test_repr_includes_details(self):
        """WhisperModel __repr__ shows name, variant, and device."""
        model = antenna.WhisperModel.from_size("tiny", device="cpu")

        repr_str = repr(model)
        assert "WhisperModel" in repr_str
        assert "Whisper tiny" in repr_str
        assert "cpu" in repr_str


class TestExportsExist:
    """Test that new classes are exported in antenna module."""

    def test_model_info_exported(self):
        """ModelInfo is exported from antenna."""
        assert hasattr(antenna, "ModelInfo")

    def test_model_capabilities_exported(self):
        """ModelCapabilities is exported from antenna."""
        assert hasattr(antenna, "ModelCapabilities")
