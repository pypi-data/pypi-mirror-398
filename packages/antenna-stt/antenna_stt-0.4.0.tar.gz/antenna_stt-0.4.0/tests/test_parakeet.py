"""Tests for Parakeet model via sherpa-rs backend."""

import os
import pytest
import antenna


def is_sherpa_available():
    """Check if sherpa feature is enabled."""
    return antenna.is_model_available("parakeet/tdt-0.6b-v2")


def is_parakeet_model_downloaded():
    """Check if Parakeet model files are downloaded."""
    cache_dir = os.path.expanduser("~/.cache/antenna/parakeet")
    model_dir = os.path.join(cache_dir, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8")
    # Check for int8 model (preferred) or regular ONNX
    encoder_int8 = os.path.join(model_dir, "encoder.int8.onnx")
    encoder_onnx = os.path.join(model_dir, "encoder.onnx")
    return os.path.exists(encoder_int8) or os.path.exists(encoder_onnx)


# Skip all tests if sherpa feature not enabled
pytestmark = pytest.mark.skipif(
    not is_sherpa_available(),
    reason="sherpa feature not enabled (build with --features sherpa)"
)


class TestParakeetListModels:
    """Tests for Parakeet models in registry."""

    def test_list_models_has_parakeet(self):
        """list_models() includes Parakeet models when sherpa is enabled."""
        models = antenna.list_models()
        parakeet_models = [m for m in models if m.family == "parakeet"]
        assert len(parakeet_models) >= 3  # tdt-0.6b-en, tdt-0.6b-v2, tdt-0.6b-v3

    def test_parakeet_model_attributes(self):
        """Parakeet ModelEntry has correct attributes."""
        models = antenna.list_models()
        parakeet_models = [m for m in models if m.family == "parakeet"]

        for model in parakeet_models:
            assert model.family == "parakeet"
            assert model.default_backend == "sherpa"
            assert model.feature_flag == "sherpa"
            assert "parakeet" in model.id

    def test_is_model_available_parakeet(self):
        """is_model_available returns True for Parakeet when sherpa enabled."""
        assert antenna.is_model_available("parakeet/tdt-0.6b-v2") is True
        assert antenna.is_model_available("parakeet/tdt-0.6b-v3") is True
        assert antenna.is_model_available("parakeet/tdt-0.6b-en") is True


# Tests that require the model to be downloaded
@pytest.mark.skipif(
    not is_parakeet_model_downloaded(),
    reason="Parakeet model not downloaded. Run: wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 && tar xvf sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 -C ~/.cache/antenna/parakeet/"
)
class TestParakeetModelLoading:
    """Tests for loading Parakeet models."""

    def test_load_parakeet_v2(self):
        """Can load parakeet/tdt-0.6b-v2 model."""
        model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cpu")
        assert model is not None
        assert model.model_family() == "parakeet"
        assert model.backend() == "sherpa"
        assert model.device() == "cpu"

    def test_speech_model_info(self):
        """SpeechModel.info() returns Parakeet model information."""
        model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cpu")
        info = model.info()
        assert info.name is not None
        assert "parakeet" in info.family.lower()

    def test_speech_model_capabilities(self):
        """SpeechModel.capabilities() returns Parakeet capabilities."""
        model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cpu")
        caps = model.capabilities()
        # Parakeet doesn't support translation
        assert caps.supports_translation is False
        # v2 is English-only, no language detection
        assert caps.supports_language_detection is False
        assert caps.supports_timestamps is True
        assert caps.max_audio_duration > 0

    def test_speech_model_repr(self):
        """SpeechModel has a useful repr."""
        model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cpu")
        repr_str = repr(model)
        assert "SpeechModel" in repr_str
        assert "parakeet" in repr_str.lower()


@pytest.mark.skipif(
    not is_parakeet_model_downloaded(),
    reason="Parakeet model not downloaded"
)
class TestParakeetTranscription:
    """Transcription tests for Parakeet model."""

    @pytest.fixture
    def quick_brown_fox_audio(self):
        """Load quick brown fox test audio (contains actual speech)."""
        audio_path = "test_data/the_quick_brown_fox.mp3"
        if not os.path.exists(audio_path):
            pytest.skip("Quick brown fox audio file not found")
        audio = antenna.load_audio(audio_path)
        return antenna.preprocess_audio(audio, target_sample_rate=16000, mono=True)

    @pytest.fixture
    def model(self):
        """Load Parakeet model."""
        return antenna.load_model("parakeet/tdt-0.6b-v2", device="cpu")

    def test_transcribe_basic(self, model, quick_brown_fox_audio):
        """Can transcribe audio with Parakeet."""
        result = model.transcribe(quick_brown_fox_audio)

        assert result is not None
        assert hasattr(result, 'text')
        assert len(result.text) > 0

    def test_transcribe_returns_segments(self, model, quick_brown_fox_audio):
        """Transcription result has segments."""
        result = model.transcribe(quick_brown_fox_audio)

        assert hasattr(result, 'segments')
        assert len(result.segments) > 0

        segment = result.segments[0]
        assert hasattr(segment, 'start')
        assert hasattr(segment, 'end')
        assert hasattr(segment, 'text')

    def test_transcribe_quick_brown_fox(self, model, quick_brown_fox_audio):
        """Transcribes 'the quick brown fox' correctly."""
        result = model.transcribe(quick_brown_fox_audio)

        text_lower = result.text.lower()
        # Should contain key words from "the quick brown fox jumps over the lazy dog"
        assert "quick" in text_lower or "brown" in text_lower or "fox" in text_lower

    def test_preprocess(self, model, quick_brown_fox_audio):
        """Can preprocess audio for Parakeet."""
        processed = model.preprocess(quick_brown_fox_audio)

        assert processed is not None
        assert processed.sample_rate == 16000
        assert processed.channels == 1


@pytest.mark.skipif(
    not is_parakeet_model_downloaded(),
    reason="Parakeet model not downloaded"
)
@pytest.mark.skipif(
    not antenna.is_cuda_available(),
    reason="CUDA not available"
)
class TestParakeetGPU:
    """GPU tests for Parakeet model (requires sherpa-cuda feature)."""

    def test_load_parakeet_cuda(self):
        """Can load Parakeet model on CUDA."""
        try:
            model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cuda")
            assert model is not None
            assert model.device() == "cuda"
        except RuntimeError as e:
            # May fail if sherpa-cuda feature not enabled
            if "cuda" in str(e).lower() or "provider" in str(e).lower():
                pytest.skip("sherpa-cuda feature not enabled")
            raise

    def test_transcribe_cuda(self):
        """Can transcribe on CUDA."""
        audio_path = "test_data/the_quick_brown_fox.mp3"
        if not os.path.exists(audio_path):
            pytest.skip("Quick brown fox audio file not found")

        try:
            model = antenna.load_model("parakeet/tdt-0.6b-v2", device="cuda")
            audio = antenna.load_audio(audio_path)
            audio = antenna.preprocess_audio(audio, target_sample_rate=16000, mono=True)

            result = model.transcribe(audio)
            assert result is not None
            assert len(result.text) > 0
        except RuntimeError as e:
            if "cuda" in str(e).lower() or "provider" in str(e).lower():
                pytest.skip("sherpa-cuda feature not enabled")
            raise
