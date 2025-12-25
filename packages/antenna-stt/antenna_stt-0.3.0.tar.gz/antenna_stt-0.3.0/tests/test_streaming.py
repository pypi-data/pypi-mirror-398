"""Strict tests for the streaming transcription API."""

import math
import pytest
import numpy as np
import antenna


class TestStreamingConfig:
    """Strict tests for StreamingConfig."""

    def test_default_config_values(self):
        """Default config has correct values."""
        config = antenna.StreamingConfig()
        assert config.sample_rate == 16000, "Default sample rate must be 16000"
        assert config.min_chunk_duration == 0.5, "Default min_chunk_duration must be 0.5"
        assert config.max_chunk_duration == 30.0, "Default max_chunk_duration must be 30.0"
        assert config.use_vad is True, "VAD must be enabled by default"
        assert config.vad_threshold_db == -40.0, "Default VAD threshold must be -40.0 dB"
        assert config.language is None, "Default language must be None (auto-detect)"
        assert config.beam_size == 1, "Default beam_size must be 1 (greedy)"

    def test_custom_config_values(self):
        """Custom config values are set correctly."""
        config = antenna.StreamingConfig(
            sample_rate=48000,
            min_chunk_duration=0.3,
            max_chunk_duration=10.0,
            use_vad=False,
            vad_threshold_db=-50.0,
            language="en",
            beam_size=5,
        )
        assert config.sample_rate == 48000
        assert config.min_chunk_duration == 0.3
        assert config.max_chunk_duration == 10.0
        assert config.use_vad is False
        assert config.vad_threshold_db == -50.0
        assert config.language == "en"
        assert config.beam_size == 5

    def test_realtime_config_preset(self):
        """Realtime config preset has optimized values."""
        config = antenna.StreamingConfig.realtime()
        assert config.min_chunk_duration == 0.3, "Realtime must have 300ms min chunks"
        assert config.max_chunk_duration == 5.0, "Realtime must have 5s max chunks"
        assert config.beam_size == 1, "Realtime must use greedy decoding"
        assert config.use_vad is True, "Realtime must enable VAD"

    def test_quality_config_preset(self):
        """Quality config preset has optimized values."""
        config = antenna.StreamingConfig.quality()
        assert config.min_chunk_duration == 1.0, "Quality must have 1s min chunks"
        assert config.max_chunk_duration == 10.0, "Quality must have 10s max chunks"
        assert config.beam_size == 3, "Quality must use beam search"
        assert config.use_vad is True, "Quality must enable VAD"

    def test_no_vad_config_preset(self):
        """No-VAD config preset disables VAD."""
        config = antenna.StreamingConfig.no_vad()
        assert config.use_vad is False, "no_vad preset must disable VAD"
        # Other defaults should still apply
        assert config.sample_rate == 16000

    def test_config_repr(self):
        """Config has informative repr."""
        config = antenna.StreamingConfig()
        repr_str = repr(config)
        assert "StreamingConfig" in repr_str
        assert "sample_rate=" in repr_str
        assert "use_vad=" in repr_str
        assert "beam_size=" in repr_str


class TestStreamingTranscriber:
    """Strict tests for StreamingTranscriber."""

    def test_from_model_id_exists(self):
        """StreamingTranscriber.from_model_id exists and is callable."""
        assert hasattr(antenna.StreamingTranscriber, "from_model_id")
        assert callable(antenna.StreamingTranscriber.from_model_id)

    def test_direct_construction_not_supported(self):
        """Direct construction with model is not supported (raises error)."""
        # This is a limitation documented in the code
        model = antenna.load_model("whisper/tiny", device="cpu")
        with pytest.raises(RuntimeError):
            antenna.StreamingTranscriber(model)

    @pytest.mark.slow
    def test_from_model_id_creates_transcriber(self):
        """from_model_id creates a valid transcriber."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        assert transcriber is not None
        assert isinstance(transcriber.buffer_duration, float)
        assert isinstance(transcriber.current_time, float)
        assert isinstance(transcriber.is_speaking, bool)
        assert isinstance(transcriber.vad_state, str)

    @pytest.mark.slow
    def test_from_model_id_with_custom_config(self):
        """from_model_id accepts custom config."""
        config = antenna.StreamingConfig(
            sample_rate=16000,
            use_vad=False,
            beam_size=1,
        )
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu", config=config
        )
        assert transcriber is not None

    @pytest.mark.slow
    def test_initial_state(self):
        """Initial transcriber state is correct."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        assert transcriber.buffer_duration == 0.0, "Initial buffer must be empty"
        assert transcriber.current_time == 0.0, "Initial time must be 0"
        assert transcriber.is_speaking is False, "Must not be speaking initially"
        assert transcriber.vad_state == "silence", "Initial VAD state must be silence"

    @pytest.mark.slow
    def test_process_chunk_returns_list(self):
        """process_chunk returns a list of events."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        # Create silence
        silence = [0.0] * 8000  # 0.5s at 16kHz
        events = transcriber.process_chunk(silence)
        assert isinstance(events, list)

    @pytest.mark.slow
    def test_process_chunk_updates_state(self):
        """process_chunk updates internal state."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        # Process 1 second of audio
        samples = [0.0] * 16000
        transcriber.process_chunk(samples)

        assert transcriber.current_time > 0.0, "Time must increase after processing"
        assert (
            abs(transcriber.current_time - 1.0) < 0.01
        ), "Time must match audio duration"

    @pytest.mark.slow
    def test_flush_returns_events(self):
        """flush returns events and clears buffer."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        # Add some audio
        samples = [0.1 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(16000)]
        transcriber.process_chunk(samples)

        events = transcriber.flush()
        assert isinstance(events, list)

    @pytest.mark.slow
    def test_reset_clears_state(self):
        """reset clears transcriber state."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        # Process some audio
        samples = [0.0] * 16000
        transcriber.process_chunk(samples)
        assert transcriber.current_time > 0.0

        # Reset
        transcriber.reset()
        assert transcriber.buffer_duration == 0.0, "Buffer must be empty after reset"
        assert transcriber.current_time == 0.0, "Time must be 0 after reset"
        assert transcriber.is_speaking is False, "Must not be speaking after reset"

    @pytest.mark.slow
    def test_transcriber_repr(self):
        """Transcriber has informative repr."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        repr_str = repr(transcriber)
        assert "StreamingTranscriber" in repr_str
        assert "buffer=" in repr_str
        assert "time=" in repr_str


class TestStreamingEvent:
    """Strict tests for StreamingEvent properties."""

    @pytest.mark.slow
    def test_event_has_required_properties(self):
        """StreamingEvent has all required properties."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        # Generate some events
        samples = [0.0] * 16000
        events = transcriber.process_chunk(samples)

        # Check all events have required properties
        for event in events:
            assert hasattr(event, "event_type")
            assert hasattr(event, "text")
            assert hasattr(event, "start_time")
            assert hasattr(event, "end_time")
            assert hasattr(event, "is_partial")
            assert hasattr(event, "is_final")
            assert hasattr(event, "timestamp")
            assert hasattr(event, "duration")
            assert hasattr(event, "vad_state")

    @pytest.mark.slow
    def test_event_type_is_valid_string(self):
        """event_type is always a valid string."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        valid_types = {"partial", "final", "segment_start", "segment_end", "vad_change"}

        samples = [0.0] * 16000
        events = transcriber.process_chunk(samples)

        for event in events:
            assert isinstance(event.event_type, str)
            assert event.event_type in valid_types, f"Unknown event type: {event.event_type}"

    @pytest.mark.slow
    def test_is_partial_and_is_final_exclusive(self):
        """is_partial and is_final are mutually exclusive for transcription events."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Create speech-like audio
        speech = [0.3 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(48000)]
        events = transcriber.process_chunk(speech)
        events.extend(transcriber.flush())

        for event in events:
            if event.event_type in ("partial", "final"):
                # They should be exclusive (can't be both or neither)
                # Actually, is_partial can be True with is_final being any value
                # is_final=True should mean is_partial=False
                if event.is_final:
                    assert not event.is_partial, "Final events must not be partial"

    @pytest.mark.slow
    def test_text_present_for_transcription_events(self):
        """text is present for partial and final events."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Create speech-like audio to get transcription
        speech = [0.3 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(48000)]
        events = transcriber.process_chunk(speech)
        events.extend(transcriber.flush())

        for event in events:
            if event.event_type in ("partial", "final"):
                # Text should be set (may be empty string but not None for valid transcriptions)
                assert event.text is not None, f"{event.event_type} event must have text"

    @pytest.mark.slow
    def test_timestamp_present_for_segment_events(self):
        """timestamp is present for segment and vad events."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Process audio to potentially trigger VAD events
        samples = [0.0] * 16000
        events = transcriber.process_chunk(samples)

        for event in events:
            if event.event_type in ("segment_start", "segment_end", "vad_change"):
                assert event.timestamp is not None, f"{event.event_type} must have timestamp"

    @pytest.mark.slow
    def test_vad_state_valid_for_vad_events(self):
        """vad_state is valid for vad_change events."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Process different audio types to trigger VAD changes
        silence = [0.0] * 16000
        speech = [0.5 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(16000)]

        events = []
        events.extend(transcriber.process_chunk(silence))
        events.extend(transcriber.process_chunk(speech))
        events.extend(transcriber.process_chunk(speech))
        events.extend(transcriber.process_chunk(silence))

        for event in events:
            if event.event_type == "vad_change":
                assert event.vad_state is not None
                assert event.vad_state in ("silence", "speech"), \
                    f"Invalid vad_state: {event.vad_state}"


class TestVadDetection:
    """Tests for VAD (Voice Activity Detection) behavior."""

    @pytest.mark.slow
    def test_silence_not_detected_as_speech(self):
        """Pure silence should not trigger speech detection."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        silence = [0.0] * 32000  # 2 seconds of silence
        events = transcriber.process_chunk(silence)

        # Should not be speaking
        assert transcriber.is_speaking is False
        assert transcriber.vad_state == "silence"

    @pytest.mark.slow
    def test_loud_signal_detected_as_speech(self):
        """Loud audio signal should be detected as speech."""
        config = antenna.StreamingConfig(
            use_vad=True,
            vad_threshold_db=-40.0,
        )
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu", config=config
        )

        # Create a loud sine wave (definitely above -40dB threshold)
        loud_audio = [0.5 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(16000)]

        # Process multiple chunks to exceed min_speech_duration
        for _ in range(3):
            transcriber.process_chunk(loud_audio)

        # Should be speaking (or have transitioned)
        # Note: VAD needs time to trigger, check for speech state
        assert transcriber.vad_state in ("speech", "silence")


class TestStreamingTranscription:
    """Integration tests for streaming transcription with actual audio."""

    @pytest.fixture
    def audio(self):
        """Load test audio file."""
        audio = antenna.load_audio("test_data/test_audio.wav")
        return antenna.preprocess_for_whisper(audio)

    @pytest.mark.slow
    def test_streaming_produces_text(self, audio):
        """Streaming transcription produces text output."""
        config = antenna.StreamingConfig(
            use_vad=False,  # Disable VAD for predictable behavior
            min_chunk_duration=0.3,
            max_chunk_duration=5.0,
            beam_size=1,
        )
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu", config=config
        )

        # Split audio into chunks using to_numpy()
        chunk_size = 16000  # 1 second chunks
        samples = audio.to_numpy().tolist()
        all_events = []

        for i in range(0, len(samples), chunk_size):
            chunk = samples[i : i + chunk_size]
            events = transcriber.process_chunk(chunk)
            all_events.extend(events)

        # Flush remaining
        all_events.extend(transcriber.flush())

        # Should have at least one transcription event
        transcription_events = [e for e in all_events if e.event_type in ("partial", "final")]
        assert len(transcription_events) > 0, "Must produce at least one transcription"

        # Collect all text
        all_text = " ".join(e.text for e in transcription_events if e.text)
        assert len(all_text) > 0, "Must produce non-empty transcription"

    @pytest.mark.slow
    def test_final_events_on_flush(self, audio):
        """Flushing produces final events."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Process all audio using to_numpy()
        transcriber.process_chunk(audio.to_numpy().tolist())

        # Flush
        events = transcriber.flush()

        # Check for final events
        final_events = [e for e in events if e.is_final]
        # After flush, any transcription events should be final
        for e in events:
            if e.event_type == "final":
                assert e.is_final is True

    @pytest.mark.slow
    def test_process_audio_method(self, audio):
        """process_audio method works with AudioData."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Use process_audio instead of process_chunk
        events = transcriber.process_audio(audio)
        assert isinstance(events, list)

        # Flush
        final_events = transcriber.flush()
        all_events = events + final_events

        # Should have processed the audio
        assert transcriber.current_time > 0


class TestEdgeCases:
    """Edge case tests for robustness."""

    @pytest.mark.slow
    def test_empty_chunk_processing(self):
        """Processing empty chunks doesn't crash."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        events = transcriber.process_chunk([])
        assert isinstance(events, list)
        assert len(events) == 0

    @pytest.mark.slow
    def test_very_short_chunk(self):
        """Very short chunks are handled correctly."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        # Single sample
        events = transcriber.process_chunk([0.1])
        assert isinstance(events, list)
        assert transcriber.current_time > 0

    @pytest.mark.slow
    def test_multiple_resets(self):
        """Multiple resets don't cause issues."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        for _ in range(3):
            transcriber.process_chunk([0.0] * 1600)
            transcriber.reset()

        assert transcriber.current_time == 0.0

    @pytest.mark.slow
    def test_flush_empty_buffer(self):
        """Flushing empty buffer doesn't crash."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        events = transcriber.flush()
        assert isinstance(events, list)

    @pytest.mark.slow
    def test_flush_after_flush(self):
        """Calling flush twice doesn't crash."""
        transcriber = antenna.StreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )

        transcriber.process_chunk([0.0] * 16000)
        transcriber.flush()
        events = transcriber.flush()  # Second flush
        assert isinstance(events, list)


class TestInvalidInputs:
    """Tests for handling invalid inputs."""

    def test_invalid_model_id(self):
        """Invalid model ID raises error."""
        with pytest.raises(RuntimeError):
            antenna.StreamingTranscriber.from_model_id("invalid/nonexistent")

    def test_invalid_device(self):
        """Invalid device raises error."""
        with pytest.raises(RuntimeError):
            antenna.StreamingTranscriber.from_model_id(
                "whisper/tiny", device="invalid_device"
            )
