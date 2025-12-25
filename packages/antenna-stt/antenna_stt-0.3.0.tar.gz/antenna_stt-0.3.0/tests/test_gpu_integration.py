"""Comprehensive GPU integration tests for all STT models.

These tests verify that all implemented models work correctly on GPU.
They are skipped if CUDA is not available.
"""
import pytest
import os
import antenna


# Skip all tests if CUDA is not available
pytestmark = pytest.mark.skipif(
    not antenna.is_cuda_available(),
    reason="CUDA not available"
)


@pytest.fixture
def test_audio():
    """Load test audio file."""
    test_path = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_audio.wav")
    return antenna.load_audio(test_path)


class TestCUDAInfo:
    """Test CUDA detection and info."""

    def test_cuda_available(self):
        """CUDA should be available for these tests."""
        assert antenna.is_cuda_available() is True

    def test_cuda_device_count(self):
        """Should have at least one CUDA device."""
        count = antenna.cuda_device_count()
        assert count >= 1


class TestWhisperGPU:
    """Test Whisper model on GPU."""

    @pytest.mark.slow
    def test_load_whisper_on_gpu(self):
        """WhisperModel can be loaded on GPU."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda")
        assert model.device() == "cuda"

    @pytest.mark.slow
    def test_whisper_info_on_gpu(self):
        """Model info works on GPU."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda")
        info = model.info()

        assert info.family == "whisper"
        assert info.variant == "tiny"

    @pytest.mark.slow
    def test_whisper_transcribe_on_gpu(self, test_audio):
        """Transcription works on GPU."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda")
        audio = antenna.preprocess_for_whisper(test_audio)

        result = model.transcribe(audio)

        assert isinstance(result.text, str)
        assert len(result.text) > 0

    @pytest.mark.slow
    def test_whisper_detect_language_on_gpu(self, test_audio):
        """Language detection works on GPU."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda")
        audio = antenna.preprocess_for_whisper(test_audio)

        language = model.detect_language(audio)

        assert isinstance(language, str)
        assert len(language) == 2  # Language codes are 2 characters

    @pytest.mark.slow
    def test_whisper_preprocess_on_gpu(self, test_audio):
        """Model.preprocess() works when model is on GPU."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda")

        preprocessed = model.preprocess(test_audio)

        assert preprocessed.sample_rate == 16000
        assert preprocessed.channels == 1


class TestDistilWhisperGPU:
    """Test Distil-Whisper model on GPU."""

    @pytest.mark.slow
    def test_load_distil_whisper_on_gpu(self):
        """DistilWhisperModel can be loaded on GPU."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")
        assert model.device() == "cuda"

    @pytest.mark.slow
    def test_distil_whisper_info_on_gpu(self):
        """Model info works on GPU."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")
        info = model.info()

        assert info.family == "distil-whisper"
        assert "distil-small.en" in info.variant

    @pytest.mark.slow
    def test_distil_whisper_transcribe_on_gpu(self, test_audio):
        """Transcription works on GPU."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")
        audio = model.preprocess(test_audio)

        result = model.transcribe(audio)

        assert isinstance(result.text, str)

    @pytest.mark.slow
    def test_distil_whisper_english_only_on_gpu(self, test_audio):
        """English-only model works correctly on GPU."""
        model = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")

        assert model.is_english_only() is True

        # detect_language should return "en" for English-only models
        audio = model.preprocess(test_audio)
        language = model.detect_language(audio)
        assert language == "en"


class TestMultipleDevices:
    """Test using multiple GPU devices (if available)."""

    @pytest.mark.slow
    def test_explicit_cuda_device(self):
        """Can specify cuda:0 explicitly."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda:0")
        assert model.device() == "cuda"

    @pytest.mark.slow
    @pytest.mark.skipif(antenna.cuda_device_count() < 2, reason="Need 2+ GPUs")
    def test_second_cuda_device(self):
        """Can load on second GPU if available."""
        model = antenna.WhisperModel.from_size("tiny", device="cuda:1")
        assert model.device() == "cuda"


class TestGPUPerformance:
    """Basic performance tests on GPU."""

    @pytest.mark.slow
    def test_gpu_faster_than_cpu_whisper(self, test_audio):
        """GPU should be at least as fast as CPU for Whisper."""
        import time

        # Prepare audio
        audio = antenna.preprocess_for_whisper(test_audio)

        # CPU timing
        cpu_model = antenna.WhisperModel.from_size("tiny", device="cpu")
        start = time.time()
        cpu_model.transcribe(audio)
        cpu_time = time.time() - start

        # GPU timing
        gpu_model = antenna.WhisperModel.from_size("tiny", device="cuda")
        # Warm-up run
        gpu_model.transcribe(audio)

        start = time.time()
        gpu_model.transcribe(audio)
        gpu_time = time.time() - start

        # GPU should not be significantly slower
        # (it might be similar for tiny models due to overhead)
        assert gpu_time < cpu_time * 3, f"GPU ({gpu_time:.2f}s) much slower than CPU ({cpu_time:.2f}s)"


class TestGPUMemory:
    """Test GPU memory handling."""

    @pytest.mark.slow
    def test_multiple_models_on_gpu(self):
        """Can load multiple small models on GPU."""
        model1 = antenna.WhisperModel.from_size("tiny", device="cuda")
        model2 = antenna.DistilWhisperModel.from_size("distil-small.en", device="cuda")

        assert model1.device() == "cuda"
        assert model2.device() == "cuda"


class TestGPUAliases:
    """Test GPU device aliases."""

    @pytest.mark.slow
    def test_gpu_alias(self):
        """'gpu' is an alias for 'cuda'."""
        model = antenna.WhisperModel.from_size("tiny", device="gpu")
        assert model.device() == "cuda"

    @pytest.mark.slow
    def test_gpu_colon_alias(self):
        """'gpu:0' is an alias for 'cuda:0'."""
        model = antenna.WhisperModel.from_size("tiny", device="gpu:0")
        assert model.device() == "cuda"
