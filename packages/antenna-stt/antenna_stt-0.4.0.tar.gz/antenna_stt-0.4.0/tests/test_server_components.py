"""Tests for server-exposed components: AgreementConfig, AudioRingBuffer, stable preset."""

import pytest
import math
import antenna


class TestAgreementConfigCreation:
    """Test AgreementConfig creation."""

    def test_create_default(self):
        """Can create default agreement config."""
        config = antenna.AgreementConfig()
        assert config.agreement_count == 2
        assert config.max_buffer_tokens == 100
        assert config.min_emit_tokens == 1

    def test_create_with_params(self):
        """Can create agreement config with custom parameters."""
        config = antenna.AgreementConfig(
            agreement_count=3, max_buffer_tokens=50, min_emit_tokens=2
        )
        assert config.agreement_count == 3
        assert config.max_buffer_tokens == 50
        assert config.min_emit_tokens == 2

    def test_strict_preset(self):
        """Strict preset requires more agreement."""
        config = antenna.AgreementConfig.strict()
        assert config.agreement_count == 3
        assert config.max_buffer_tokens == 50

    def test_fast_preset(self):
        """Fast preset has larger buffer."""
        config = antenna.AgreementConfig.fast()
        assert config.agreement_count == 2
        assert config.max_buffer_tokens == 200

    def test_repr(self):
        """Repr includes key information."""
        config = antenna.AgreementConfig()
        repr_str = repr(config)
        assert "AgreementConfig" in repr_str
        assert "agreement_count=" in repr_str


class TestAudioRingBufferCreation:
    """Test AudioRingBuffer creation."""

    def test_create_default(self):
        """Can create default ring buffer."""
        buffer = antenna.AudioRingBuffer()
        assert buffer.sample_rate == 16000
        assert buffer.capacity > 0
        assert buffer.overlap_samples > 0
        assert buffer.duration == 0.0

    def test_create_with_params(self):
        """Can create ring buffer with custom parameters."""
        buffer = antenna.AudioRingBuffer(
            capacity_seconds=30.0, sample_rate=44100, overlap_seconds=1.0
        )
        assert buffer.sample_rate == 44100
        assert buffer.overlap_samples == 44100  # 1 second at 44100Hz

    def test_is_empty_initially(self):
        """Buffer is empty when created."""
        buffer = antenna.AudioRingBuffer()
        assert buffer.is_empty()
        assert buffer.len == 0

    def test_repr(self):
        """Repr includes duration and capacity."""
        buffer = antenna.AudioRingBuffer()
        repr_str = repr(buffer)
        assert "AudioRingBuffer" in repr_str
        assert "duration=" in repr_str
        assert "capacity=" in repr_str


class TestAudioRingBufferOperations:
    """Test AudioRingBuffer push/read operations."""

    def test_push_updates_len(self):
        """Push updates buffer length."""
        buffer = antenna.AudioRingBuffer()
        buffer.push([1.0, 2.0, 3.0])
        assert buffer.len == 3
        assert not buffer.is_empty()

    def test_push_updates_duration(self):
        """Push updates duration."""
        buffer = antenna.AudioRingBuffer(sample_rate=16000)
        buffer.push([0.0] * 16000)  # 1 second
        assert abs(buffer.duration - 1.0) < 0.001

    def test_read_consumes_samples(self):
        """Read consumes samples from buffer."""
        buffer = antenna.AudioRingBuffer(overlap_seconds=0.0)
        buffer.push([1.0, 2.0, 3.0, 4.0, 5.0])
        samples = buffer.read(3)
        assert samples == [1.0, 2.0, 3.0]
        assert buffer.len == 2

    def test_read_all(self):
        """Read all samples from buffer."""
        buffer = antenna.AudioRingBuffer()
        buffer.push([1.0, 2.0, 3.0])
        samples = buffer.read_all()
        assert len(samples) == 3
        assert buffer.is_empty()

    def test_peek_does_not_consume(self):
        """Peek does not consume samples."""
        buffer = antenna.AudioRingBuffer()
        buffer.push([1.0, 2.0, 3.0])
        peeked = buffer.peek(2)
        assert peeked == [1.0, 2.0]
        assert buffer.len == 3  # Not consumed

    def test_clear_empties_buffer(self):
        """Clear empties the buffer."""
        buffer = antenna.AudioRingBuffer()
        buffer.push([1.0, 2.0, 3.0])
        buffer.clear()
        assert buffer.is_empty()

    def test_read_with_overlap(self):
        """Read with overlap preserves context."""
        buffer = antenna.AudioRingBuffer(
            capacity_seconds=10.0, sample_rate=1000, overlap_seconds=0.002  # 2 samples
        )
        buffer.push([1.0, 2.0, 3.0, 4.0, 5.0])
        samples = buffer.read_with_overlap(10)
        # Should read 3 samples (5 - 2 overlap)
        assert len(samples) == 3
        assert buffer.len == 2  # Overlap preserved

    def test_capacity_limit(self):
        """Buffer respects capacity limit."""
        # 1 sample capacity (0.001s at 1000Hz)
        buffer = antenna.AudioRingBuffer(
            capacity_seconds=0.001, sample_rate=1000, overlap_seconds=0.0
        )
        buffer.push([1.0, 2.0, 3.0])
        assert buffer.len == 1  # Only last sample kept

    def test_len_magic_method(self):
        """__len__ returns sample count."""
        buffer = antenna.AudioRingBuffer()
        buffer.push([1.0, 2.0, 3.0])
        assert len(buffer) == 3


class TestStreamingConfigStablePreset:
    """Test StreamingConfig stable preset."""

    def test_stable_preset(self):
        """Stable preset enables agreement."""
        config = antenna.StreamingConfig.stable()
        assert config.use_agreement is True
        assert config.use_vad is True  # VAD still enabled

    def test_default_has_agreement_disabled(self):
        """Default config has agreement disabled."""
        config = antenna.StreamingConfig()
        assert config.use_agreement is False

    def test_create_with_agreement(self):
        """Can create config with agreement enabled."""
        config = antenna.StreamingConfig(use_agreement=True)
        assert config.use_agreement is True

    def test_create_with_custom_agreement_config(self):
        """Can create config with custom agreement config."""
        agreement_config = antenna.AgreementConfig.strict()
        config = antenna.StreamingConfig(
            use_agreement=True, agreement_config=agreement_config
        )
        assert config.use_agreement is True

    def test_repr_shows_agreement(self):
        """Repr shows agreement setting."""
        config = antenna.StreamingConfig.stable()
        repr_str = repr(config)
        assert "use_agreement=true" in repr_str


class TestStreamingTranscriberAgreement:
    """Test StreamingTranscriber agreement policy integration."""

    def test_transcriber_has_agreement_property(self):
        """Transcriber exposes has_agreement property."""
        transcriber = antenna.StreamingTranscriber.from_model_id("whisper/tiny")
        assert hasattr(transcriber, "has_agreement")
        assert transcriber.has_agreement is False  # Default

    def test_transcriber_with_stable_config(self):
        """Transcriber with stable config has agreement enabled."""
        config = antenna.StreamingConfig.stable()
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )
        assert transcriber.has_agreement is True

    def test_agreement_confirmed_count(self):
        """Transcriber tracks agreement confirmed count."""
        config = antenna.StreamingConfig.stable()
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )
        assert transcriber.agreement_confirmed_count == 0

    def test_process_with_agreement_enabled(self):
        """Can process audio with agreement enabled."""
        config = antenna.StreamingConfig.stable()
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )

        # Generate some audio
        samples = [0.0] * 16000  # 1 second silence
        events = transcriber.process_chunk(samples)
        assert isinstance(events, list)


class TestExportPresence:
    """Test that new classes are properly exported."""

    def test_agreement_config_in_module(self):
        """AgreementConfig is in antenna module."""
        assert hasattr(antenna, "AgreementConfig")

    def test_audio_ring_buffer_in_module(self):
        """AudioRingBuffer is in antenna module."""
        assert hasattr(antenna, "AudioRingBuffer")

    def test_agreement_config_in_all(self):
        """AgreementConfig is in __all__."""
        assert "AgreementConfig" in antenna.__all__

    def test_audio_ring_buffer_in_all(self):
        """AudioRingBuffer is in __all__."""
        assert "AudioRingBuffer" in antenna.__all__

    def test_streaming_config_has_stable(self):
        """StreamingConfig has stable() method."""
        assert callable(antenna.StreamingConfig.stable)


class TestRealAudioWithAgreement:
    """Test agreement policy with speech-like audio."""

    def test_speech_pattern_with_agreement(self):
        """Agreement policy works with speech patterns."""
        config = antenna.StreamingConfig.stable()
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )

        # Generate speech-like audio (440Hz tone)
        sample_rate = 16000
        duration_ms = 500
        amplitude = 0.3
        samples_count = duration_ms * sample_rate // 1000

        speech = [
            amplitude * math.sin(2.0 * math.pi * 440.0 * i / sample_rate)
            for i in range(samples_count)
        ]

        events = transcriber.process_chunk(speech)
        assert isinstance(events, list)

    def test_multiple_chunks_with_agreement(self):
        """Can process multiple chunks with agreement enabled."""
        config = antenna.StreamingConfig.stable()
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )

        samples = [0.0] * 8000  # 0.5 seconds

        for _ in range(4):
            events = transcriber.process_chunk(samples)
            assert isinstance(events, list)

        assert transcriber.current_time >= 1.5


class TestRingBufferWithTranscriber:
    """Test using AudioRingBuffer for advanced audio handling."""

    def test_buffer_and_transcribe(self):
        """Can use ring buffer to accumulate then transcribe."""
        # Create ring buffer
        ring = antenna.AudioRingBuffer(capacity_seconds=10.0, sample_rate=16000)

        # Simulate receiving audio chunks
        for _ in range(5):
            chunk = [0.0] * 3200  # 200ms chunks
            ring.push(chunk)

        assert ring.duration >= 0.9  # ~1 second accumulated

        # Read all and transcribe
        all_samples = ring.read_all()
        assert len(all_samples) == 16000  # 1 second

        # Could pass to transcriber
        transcriber = antenna.StreamingTranscriber.from_model_id("whisper/tiny")
        events = transcriber.process_chunk(all_samples)
        assert isinstance(events, list)
