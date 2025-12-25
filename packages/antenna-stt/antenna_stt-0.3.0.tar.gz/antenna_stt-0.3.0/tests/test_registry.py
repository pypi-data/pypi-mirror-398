"""Tests for the unified model registry API."""

import pytest
import antenna


class TestListModels:
    """Tests for antenna.list_models()"""

    def test_list_models_returns_list(self):
        """list_models() returns a list of ModelEntry objects."""
        models = antenna.list_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_list_models_has_whisper(self):
        """list_models() includes Whisper models."""
        models = antenna.list_models()
        whisper_models = [m for m in models if m.family == "whisper"]
        assert len(whisper_models) >= 7  # tiny, base, small, medium, large, large-v2, large-v3

    def test_list_models_has_distil_whisper(self):
        """list_models() includes Distil-Whisper models."""
        models = antenna.list_models()
        distil_models = [m for m in models if m.family == "distilwhisper"]
        assert len(distil_models) >= 4

    def test_list_models_has_wav2vec2(self):
        """list_models() includes Wav2Vec2 models."""
        models = antenna.list_models()
        wav2vec2_models = [m for m in models if m.family == "wav2vec2"]
        assert len(wav2vec2_models) >= 3

    def test_model_entry_attributes(self):
        """ModelEntry has all expected attributes."""
        models = antenna.list_models()
        model = models[0]

        assert hasattr(model, 'id')
        assert hasattr(model, 'hf_id')
        assert hasattr(model, 'description')
        assert hasattr(model, 'family')
        assert hasattr(model, 'default_backend')
        assert hasattr(model, 'feature_flag')

    def test_model_entry_repr(self):
        """ModelEntry has a useful repr."""
        models = antenna.list_models()
        model = models[0]
        repr_str = repr(model)
        assert "ModelEntry" in repr_str
        assert model.id in repr_str


class TestIsModelAvailable:
    """Tests for antenna.is_model_available()"""

    def test_whisper_always_available(self):
        """Whisper models are always available (Candle is default)."""
        assert antenna.is_model_available("whisper/base") is True
        assert antenna.is_model_available("whisper/tiny") is True
        assert antenna.is_model_available("whisper/large-v3") is True

    def test_distil_whisper_always_available(self):
        """Distil-Whisper models are always available."""
        assert antenna.is_model_available("distil-whisper/distil-small.en") is True

    def test_wav2vec2_depends_on_onnx(self):
        """Wav2Vec2 availability depends on ONNX feature."""
        # This test validates the function works regardless of ONNX status
        result = antenna.is_model_available("wav2vec2/base-960h")
        assert isinstance(result, bool)
        # Should match the ONNX availability
        assert result == antenna.is_onnx_available()

    def test_invalid_model_not_available(self):
        """Invalid model IDs return False."""
        assert antenna.is_model_available("invalid/model") is False
        assert antenna.is_model_available("unknown") is False


class TestLoadModelParsing:
    """Tests for load_model() model ID parsing (without loading models)."""

    def test_load_model_exists(self):
        """load_model function exists and is callable."""
        assert hasattr(antenna, 'load_model')
        assert callable(antenna.load_model)

    def test_invalid_model_id_raises(self):
        """Invalid model ID raises RuntimeError."""
        with pytest.raises(RuntimeError):
            antenna.load_model("invalid/unknown/format")

    def test_unknown_family_raises(self):
        """Unknown model family raises RuntimeError."""
        with pytest.raises(RuntimeError):
            antenna.load_model("unknown_family/base")


class TestSpeechModelClass:
    """Tests for SpeechModel class existence."""

    def test_speech_model_exists(self):
        """SpeechModel class exists in the module."""
        assert hasattr(antenna, 'SpeechModel')

    def test_model_entry_exists(self):
        """ModelEntry class exists in the module."""
        assert hasattr(antenna, 'ModelEntry')


# Integration tests that actually load models (marked as slow)
@pytest.mark.slow
class TestLoadModelIntegration:
    """Integration tests for load_model() that download models."""

    def test_load_whisper_base(self):
        """Can load whisper/base model."""
        model = antenna.load_model("whisper/base", device="cpu")
        assert model is not None
        assert model.model_family() == "whisper"
        assert model.backend() == "candle"
        assert model.device() == "cpu"

    def test_load_whisper_with_hf_format(self):
        """Can load model using HuggingFace format."""
        model = antenna.load_model("openai/whisper-tiny", device="cpu")
        assert model is not None
        assert model.model_family() == "whisper"

    def test_load_distil_whisper(self):
        """Can load distil-whisper model."""
        model = antenna.load_model("distil-whisper/distil-small.en", device="cpu")
        assert model is not None
        assert model.model_family() == "distilwhisper"

    def test_speech_model_info(self):
        """SpeechModel.info() returns model information."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        info = model.info()
        assert info.name is not None
        assert info.family is not None
        assert "whisper" in info.family.lower()

    def test_speech_model_capabilities(self):
        """SpeechModel.capabilities() returns model capabilities."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        caps = model.capabilities()
        assert caps.supports_translation is True
        assert caps.supports_language_detection is True
        assert caps.max_audio_duration > 0

    def test_speech_model_repr(self):
        """SpeechModel has a useful repr."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        repr_str = repr(model)
        assert "SpeechModel" in repr_str
        assert "whisper" in repr_str.lower()


@pytest.mark.slow
class TestSpeechModelTranscription:
    """Transcription tests for unified SpeechModel."""

    @pytest.fixture
    def audio(self):
        """Load test audio file."""
        audio = antenna.load_audio("test_data/test_audio.wav")
        return antenna.preprocess_for_whisper(audio)

    def test_transcribe_basic(self, audio):
        """Can transcribe audio with unified API."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        result = model.transcribe(audio, beam_size=1)

        assert result is not None
        assert hasattr(result, 'text')
        assert len(result.text) > 0

    def test_transcribe_with_language(self, audio):
        """Can specify language for transcription."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        result = model.transcribe(audio, language="en", beam_size=1)

        assert result is not None
        assert result.text is not None

    def test_transcribe_translate_task(self, audio):
        """Can translate audio to English."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        result = model.transcribe(audio, task="translate", beam_size=1)

        assert result is not None
        assert result.text is not None

    def test_preprocess(self, audio):
        """Can preprocess audio for the model."""
        model = antenna.load_model("whisper/tiny", device="cpu")
        processed = model.preprocess(audio)

        assert processed is not None
        assert processed.sample_rate == 16000
        assert processed.channels == 1
