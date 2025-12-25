"""Integration tests for antenna"""
import pytest
import antenna
import numpy as np
from pathlib import Path

TEST_AUDIO_PATH = Path("test_data/test_audio.wav")

@pytest.fixture(scope="session", autouse=True)
def download_test_audio():
    """Download test audio file if it doesn't exist"""
    if not TEST_AUDIO_PATH.exists():
        import urllib.request
        TEST_AUDIO_PATH.parent.mkdir(exist_ok=True)
        url = "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav"
        urllib.request.urlretrieve(url, TEST_AUDIO_PATH)

def test_load_audio():
    """Test loading a WAV audio file"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    assert audio.sample_rate > 0
    assert audio.channels > 0
    assert audio.duration > 0

def test_audio_properties():
    """Test AudioData properties"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    assert hasattr(audio, 'sample_rate')
    assert hasattr(audio, 'channels')
    assert hasattr(audio, 'duration')
    assert isinstance(audio.sample_rate, int)
    assert isinstance(audio.channels, int)
    assert isinstance(audio.duration, float)

def test_preprocess_mono():
    """Test converting to mono"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    processed = antenna.preprocess_audio(audio, mono=True)
    assert processed.channels == 1

def test_preprocess_resample():
    """Test resampling to 16kHz"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    processed = antenna.preprocess_audio(audio, target_sample_rate=16000)
    assert processed.sample_rate == 16000

def test_preprocess_combined():
    """Test combined preprocessing: resample + mono"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    processed = antenna.preprocess_audio(
        audio, 
        target_sample_rate=16000, 
        mono=True
    )
    assert processed.sample_rate == 16000
    assert processed.channels == 1

def test_to_numpy():
    """Test converting AudioData to NumPy array"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    samples = audio.to_numpy()
    assert isinstance(samples, np.ndarray)
    assert samples.dtype == np.float32
    assert len(samples) > 0
    assert samples.min() >= -1.0
    assert samples.max() <= 1.0

def test_audio_repr():
    """Test AudioData string representation"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    repr_str = repr(audio)
    assert "AudioData" in repr_str
    assert str(audio.sample_rate) in repr_str
    assert str(audio.channels) in repr_str

def test_invalid_file():
    """Test error handling for invalid file path"""
    with pytest.raises(Exception):
        antenna.load_audio("nonexistent_file.wav")

def test_preprocess_no_change():
    """Test preprocessing with no changes"""
    audio = antenna.load_audio(str(TEST_AUDIO_PATH))
    # Don't specify any preprocessing
    processed = antenna.preprocess_audio(audio)
    # Should return audio with same properties
    assert processed.sample_rate == audio.sample_rate
    assert processed.channels == audio.channels

