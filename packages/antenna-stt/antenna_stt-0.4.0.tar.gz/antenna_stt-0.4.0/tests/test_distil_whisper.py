"""Tests for Distil-Whisper model implementation.

These tests verify the Distil-Whisper model works correctly,
including both English-only and multilingual variants.
"""
import pytest
import antenna


class TestDistilWhisperExports:
    """Test that Distil-Whisper is properly exported."""

    def test_distil_whisper_model_exported(self):
        """DistilWhisperModel is exported from antenna."""
        assert hasattr(antenna, "DistilWhisperModel")

    def test_list_distil_whisper_models_exported(self):
        """list_distil_whisper_models is exported from antenna."""
        assert hasattr(antenna, "list_distil_whisper_models")


class TestListDistilWhisperModels:
    """Test the model listing function."""

    def test_returns_list(self):
        """list_distil_whisper_models returns a list of tuples."""
        models = antenna.list_distil_whisper_models()
        assert isinstance(models, list)
        assert len(models) >= 4  # At least 4 models

    def test_model_format(self):
        """Each model is a (name, model_id, description) tuple."""
        models = antenna.list_distil_whisper_models()
        for model in models:
            assert len(model) == 3
            name, model_id, description = model
            assert isinstance(name, str)
            assert isinstance(model_id, str)
            assert isinstance(description, str)
            assert "distil-whisper" in model_id

    def test_expected_models_listed(self):
        """Expected Distil-Whisper variants are listed."""
        models = antenna.list_distil_whisper_models()
        names = [m[0] for m in models]

        assert "distil-small.en" in names
        assert "distil-medium.en" in names
        assert "distil-large-v2" in names
        assert "distil-large-v3" in names


class TestDistilWhisperAPIStructure:
    """Test the API structure matches WhisperModel."""

    @pytest.mark.slow
    def test_has_transcribe_method(self):
        """DistilWhisperModel has transcribe method."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        assert hasattr(model, "transcribe")

    @pytest.mark.slow
    def test_has_translate_method(self):
        """DistilWhisperModel has translate method."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        assert hasattr(model, "translate")

    @pytest.mark.slow
    def test_has_info_method(self):
        """DistilWhisperModel has info method."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        assert hasattr(model, "info")

    @pytest.mark.slow
    def test_has_capabilities_method(self):
        """DistilWhisperModel has capabilities method."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        assert hasattr(model, "capabilities")

    @pytest.mark.slow
    def test_has_preprocess_method(self):
        """DistilWhisperModel has preprocess method."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        assert hasattr(model, "preprocess")


class TestDistilWhisperEnglishOnly:
    """Test English-only Distil-Whisper models."""

    @pytest.mark.slow
    def test_english_only_flag(self):
        """English-only models report is_english_only = True."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        assert model.is_english_only() is True

    @pytest.mark.slow
    def test_english_only_capabilities(self):
        """English-only models don't support translation."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        caps = model.capabilities()

        assert caps.supports_translation is False
        assert caps.supports_language_detection is False
        assert caps.supported_languages == ["en"]

    @pytest.mark.slow
    def test_english_only_info(self):
        """English-only model info is correct."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        info = model.info()

        assert info.family == "distil-whisper"
        assert "distil-small.en" in info.variant


class TestDistilWhisperMultilingual:
    """Test multilingual Distil-Whisper models."""

    @pytest.mark.slow
    def test_multilingual_flag(self):
        """Multilingual models report is_english_only = False."""
        model = antenna.DistilWhisperModel.from_size("distil-large-v3", device="cpu")
        assert model.is_english_only() is False

    @pytest.mark.slow
    def test_multilingual_capabilities(self):
        """Multilingual models support translation."""
        model = antenna.DistilWhisperModel.from_size("distil-large-v3", device="cpu")
        caps = model.capabilities()

        assert caps.supports_translation is True
        assert caps.supports_language_detection is True
        assert len(caps.supported_languages) > 50


class TestDistilWhisperRepr:
    """Test the __repr__ method."""

    @pytest.mark.slow
    def test_repr_includes_info(self):
        """__repr__ includes useful information."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")
        repr_str = repr(model)

        assert "DistilWhisperModel" in repr_str
        assert "distil-small.en" in repr_str
        assert "cpu" in repr_str
        assert "english_only=True" in repr_str or "english_only=true" in repr_str


class TestDistilWhisperPreprocess:
    """Test the preprocess method."""

    @pytest.mark.slow
    def test_preprocess_works(self):
        """preprocess() produces 16kHz mono audio."""
        import os
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")

        test_audio = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_audio.wav")
        audio = antenna.load_audio(test_audio)

        preprocessed = model.preprocess(audio)
        assert preprocessed.sample_rate == 16000
        assert preprocessed.channels == 1


class TestDistilWhisperTranscribe:
    """Test the transcribe method."""

    @pytest.mark.slow
    def test_transcribe_returns_result(self):
        """transcribe() returns a TranscriptionResult."""
        import os
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cpu")

        test_audio = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_audio.wav")
        audio = antenna.load_audio(test_audio)
        audio = model.preprocess(audio)

        result = model.transcribe(audio)

        assert hasattr(result, "text")
        assert hasattr(result, "segments")
        assert hasattr(result, "language")
        assert isinstance(result.text, str)


class TestDistilWhisperGPU:
    """Test GPU functionality for Distil-Whisper."""

    @pytest.mark.slow
    @pytest.mark.skipif(not antenna.is_cuda_available(), reason="CUDA not available")
    def test_load_on_gpu(self):
        """DistilWhisperModel can be loaded on GPU."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")
        assert model.device() == "cuda"

    @pytest.mark.slow
    @pytest.mark.skipif(not antenna.is_cuda_available(), reason="CUDA not available")
    def test_transcribe_on_gpu(self):
        """Transcription works on GPU."""
        import os
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")

        test_audio = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_audio.wav")
        audio = antenna.load_audio(test_audio)
        audio = model.preprocess(audio)

        result = model.transcribe(audio)
        assert isinstance(result.text, str)


class TestDistilWhisperErrorHandling:
    """Test error handling."""

    def test_invalid_size_error(self):
        """Invalid model size raises an error with helpful message."""
        with pytest.raises(Exception) as exc_info:
            antenna.DistilWhisperModel.from_size("invalid-size", device="cpu")

        assert "invalid-size" in str(exc_info.value).lower() or "unknown" in str(exc_info.value).lower()
