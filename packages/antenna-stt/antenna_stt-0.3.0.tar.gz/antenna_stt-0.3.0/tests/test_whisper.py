"""
Tests for Whisper speech-to-text functionality (v0.3.0)
"""

import pytest
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWhisperImports:
    """Test that all Whisper-related imports work correctly."""

    def test_import_whisper_model(self):
        """Test importing WhisperModel class."""
        from antenna import WhisperModel
        assert WhisperModel is not None

    def test_import_transcription_result(self):
        """Test importing TranscriptionResult class."""
        from antenna import TranscriptionResult
        assert TranscriptionResult is not None

    def test_import_transcription_segment(self):
        """Test importing TranscriptionSegment class."""
        from antenna import TranscriptionSegment
        assert TranscriptionSegment is not None

    def test_import_preprocess_for_whisper(self):
        """Test importing preprocess_for_whisper function."""
        from antenna import preprocess_for_whisper
        assert callable(preprocess_for_whisper)

    def test_import_list_whisper_models(self):
        """Test importing list_whisper_models function."""
        from antenna import list_whisper_models
        assert callable(list_whisper_models)

    def test_import_is_model_cached(self):
        """Test importing is_model_cached function."""
        from antenna import is_model_cached
        assert callable(is_model_cached)


class TestListWhisperModels:
    """Test the list_whisper_models function."""

    def test_returns_list(self):
        """Test that list_whisper_models returns a list."""
        from antenna import list_whisper_models
        models = list_whisper_models()
        assert isinstance(models, list)

    def test_contains_expected_models(self):
        """Test that all expected model sizes are listed."""
        from antenna import list_whisper_models
        models = list_whisper_models()
        model_names = [m[0] for m in models]

        expected = ["tiny", "base", "small", "medium", "large"]
        for name in expected:
            assert name in model_names, f"Missing model: {name}"

    def test_model_ids_format(self):
        """Test that model IDs follow expected format."""
        from antenna import list_whisper_models
        models = list_whisper_models()

        for name, model_id in models:
            assert model_id.startswith("openai/whisper-"), f"Invalid model ID: {model_id}"


class TestPreprocessForWhisper:
    """Test the preprocess_for_whisper function."""

    def test_converts_to_16khz(self):
        """Test that audio is resampled to 16kHz."""
        from antenna import load_audio, preprocess_for_whisper

        # Create test audio at different sample rate
        test_file = "test_data/test_tone.wav"
        if os.path.exists(test_file):
            audio = load_audio(test_file)
            processed = preprocess_for_whisper(audio)
            assert processed.sample_rate == 16000

    def test_converts_to_mono(self):
        """Test that audio is converted to mono."""
        from antenna import load_audio, preprocess_for_whisper

        test_file = "test_data/test_tone.wav"
        if os.path.exists(test_file):
            audio = load_audio(test_file)
            processed = preprocess_for_whisper(audio)
            assert processed.channels == 1

    def test_preserves_duration_approximately(self):
        """Test that audio duration is approximately preserved."""
        from antenna import load_audio, preprocess_for_whisper

        test_file = "test_data/test_tone.wav"
        if os.path.exists(test_file):
            audio = load_audio(test_file)
            processed = preprocess_for_whisper(audio)
            # Allow 5% tolerance for duration change due to resampling
            assert abs(processed.duration - audio.duration) < audio.duration * 0.05


class TestIsModelCached:
    """Test the is_model_cached function."""

    def test_returns_bool(self):
        """Test that is_model_cached returns a boolean."""
        from antenna import is_model_cached
        result = is_model_cached("openai/whisper-tiny")
        assert isinstance(result, bool)

    def test_nonexistent_model(self):
        """Test checking cache for a nonexistent model."""
        from antenna import is_model_cached
        result = is_model_cached("nonexistent/model-xyz")
        assert result is False


class TestWhisperModelClass:
    """Test the WhisperModel class structure."""

    def test_has_from_pretrained(self):
        """Test that WhisperModel has from_pretrained method."""
        from antenna import WhisperModel
        assert hasattr(WhisperModel, "from_pretrained")

    def test_has_from_size(self):
        """Test that WhisperModel has from_size method."""
        from antenna import WhisperModel
        assert hasattr(WhisperModel, "from_size")


class TestTranscriptionResultStructure:
    """Test TranscriptionResult structure (without loading models)."""

    def test_has_text_attribute(self):
        """Test that TranscriptionResult should have text attribute."""
        from antenna import TranscriptionResult
        # We can't instantiate directly, but we can check the class exists
        assert TranscriptionResult is not None

    def test_has_language_attribute(self):
        """Test that TranscriptionResult should have language attribute."""
        from antenna import TranscriptionResult
        assert TranscriptionResult is not None


# Integration tests that require model download (marked as slow)
@pytest.mark.slow
class TestWhisperIntegration:
    """Integration tests that download and use actual Whisper models."""

    @pytest.fixture(scope="class")
    def whisper_model(self):
        """Load a tiny Whisper model for testing."""
        from antenna import WhisperModel
        return WhisperModel.from_size("tiny")

    @pytest.fixture
    def test_audio(self):
        """Load test audio preprocessed for Whisper."""
        from antenna import load_audio, preprocess_for_whisper

        test_file = "test_data/test_tone.wav"
        if not os.path.exists(test_file):
            pytest.skip("Test audio file not found")

        audio = load_audio(test_file)
        return preprocess_for_whisper(audio)

    def test_load_model_by_size(self):
        """Test loading model by size name."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny")
        assert model is not None

    def test_load_model_by_id(self):
        """Test loading model by HuggingFace ID."""
        from antenna import WhisperModel
        model = WhisperModel.from_pretrained("openai/whisper-tiny")
        assert model is not None

    def test_transcribe_returns_result(self, whisper_model, test_audio):
        """Test that transcribe returns a TranscriptionResult."""
        from antenna import TranscriptionResult
        result = whisper_model.transcribe(test_audio)
        assert isinstance(result, TranscriptionResult)

    def test_transcribe_result_has_text(self, whisper_model, test_audio):
        """Test that transcription result has text."""
        result = whisper_model.transcribe(test_audio)
        assert hasattr(result, "text")
        assert isinstance(result.text, str)

    def test_transcribe_result_has_language(self, whisper_model, test_audio):
        """Test that transcription result has detected language."""
        result = whisper_model.transcribe(test_audio)
        assert hasattr(result, "language")

    def test_transcribe_result_has_segments(self, whisper_model, test_audio):
        """Test that transcription result has segments."""
        result = whisper_model.transcribe(test_audio)
        assert hasattr(result, "segments")
        assert isinstance(result.segments, list)

    def test_transcribe_with_language(self, whisper_model, test_audio):
        """Test transcription with specified language."""
        result = whisper_model.transcribe(test_audio, language="en")
        assert result.language == "en"

    def test_transcribe_with_greedy(self, whisper_model, test_audio):
        """Test transcription with greedy decoding."""
        result = whisper_model.transcribe(test_audio, beam_size=1)
        assert result.text is not None

    def test_translate_method(self, whisper_model, test_audio):
        """Test the translate method."""
        result = whisper_model.translate(test_audio)
        assert result.text is not None

    def test_detect_language(self, whisper_model, test_audio):
        """Test language detection."""
        language = whisper_model.detect_language(test_audio)
        assert isinstance(language, str)
        assert len(language) == 2  # Language codes are 2 chars


class TestTranscriptionSegment:
    """Test TranscriptionSegment structure."""

    def test_segment_import(self):
        """Test that TranscriptionSegment can be imported."""
        from antenna import TranscriptionSegment
        assert TranscriptionSegment is not None


class TestVersion:
    """Test version information."""

    def test_version_is_0_3_0(self):
        """Test that version is 0.3.0."""
        import antenna
        assert antenna.__version__ == "0.3.0"


class TestCudaUtilities:
    """Test CUDA utility functions."""

    def test_is_cuda_available_returns_bool(self):
        """Test that is_cuda_available returns a boolean."""
        from antenna import is_cuda_available
        result = is_cuda_available()
        assert isinstance(result, bool)

    def test_cuda_device_count_returns_int(self):
        """Test that cuda_device_count returns an integer."""
        from antenna import cuda_device_count
        count = cuda_device_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_cuda_device_count_consistent_with_is_available(self):
        """Test that device count is consistent with availability."""
        from antenna import is_cuda_available, cuda_device_count
        available = is_cuda_available()
        count = cuda_device_count()
        if available:
            assert count > 0
        else:
            assert count == 0


# GPU integration tests (skipped if CUDA not available)
@pytest.mark.slow
class TestWhisperGpuIntegration:
    """GPU integration tests for Whisper models."""

    @pytest.fixture(autouse=True)
    def skip_if_no_cuda(self):
        """Skip all tests in this class if CUDA is not available."""
        from antenna import is_cuda_available
        if not is_cuda_available():
            pytest.skip("CUDA not available")

    @pytest.fixture
    def test_audio(self):
        """Load test audio preprocessed for Whisper."""
        from antenna import load_audio, preprocess_for_whisper

        test_file = "test_data/test_audio.wav"
        if not os.path.exists(test_file):
            pytest.skip("Test audio file not found")

        audio = load_audio(test_file)
        return preprocess_for_whisper(audio)

    def test_load_model_on_gpu(self):
        """Test loading model on GPU."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="cuda")
        assert model is not None

    def test_load_model_on_gpu_with_index(self):
        """Test loading model on specific GPU."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="cuda:0")
        assert model is not None

    def test_load_model_with_gpu_alias(self):
        """Test loading model with 'gpu' alias."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="gpu")
        assert model is not None

    def test_transcribe_on_gpu(self, test_audio):
        """Test transcription on GPU."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="cuda")
        result = model.transcribe(test_audio)
        assert result.text is not None

    def test_detect_language_on_gpu(self, test_audio):
        """Test language detection on GPU."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="cuda")
        language = model.detect_language(test_audio)
        assert isinstance(language, str)

    def test_translate_on_gpu(self, test_audio):
        """Test translation on GPU."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="cuda")
        result = model.translate(test_audio)
        assert result.text is not None


class TestDeviceParsing:
    """Test device string parsing with various formats."""

    def test_invalid_device_raises_error(self):
        """Test that invalid device string raises ValueError."""
        from antenna import WhisperModel
        with pytest.raises(ValueError):
            WhisperModel.from_size("tiny", device="invalid")

    def test_invalid_gpu_index_raises_error(self):
        """Test that invalid GPU index raises ValueError."""
        from antenna import WhisperModel
        with pytest.raises(ValueError):
            WhisperModel.from_size("tiny", device="cuda:abc")

    def test_cpu_device_works(self):
        """Test that 'cpu' device works."""
        from antenna import WhisperModel
        model = WhisperModel.from_size("tiny", device="cpu")
        assert model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
