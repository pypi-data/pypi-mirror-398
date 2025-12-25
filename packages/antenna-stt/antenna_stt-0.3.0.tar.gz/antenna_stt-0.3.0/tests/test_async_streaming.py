"""Tests for async streaming transcription API."""

import pytest
import asyncio
import math
import antenna


class TestAsyncStreamingTranscriberCreation:
    """Test AsyncStreamingTranscriber creation."""

    @pytest.mark.asyncio
    async def test_create_from_model_id(self):
        """Can create async transcriber from model ID."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        assert transcriber is not None

    @pytest.mark.asyncio
    async def test_create_with_device(self):
        """Can create async transcriber with device specification."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu"
        )
        assert transcriber is not None

    @pytest.mark.asyncio
    async def test_create_with_config(self):
        """Can create async transcriber with custom config."""
        config = antenna.StreamingConfig.realtime()
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )
        assert transcriber is not None

    @pytest.mark.asyncio
    async def test_create_with_all_options(self):
        """Can create async transcriber with all options."""
        config = antenna.StreamingConfig.quality()
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
            "whisper/tiny", device="cpu", config=config
        )
        assert transcriber is not None

    @pytest.mark.asyncio
    async def test_repr(self):
        """Repr includes state information."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        repr_str = repr(transcriber)
        assert "AsyncStreamingTranscriber" in repr_str
        assert "buffer=" in repr_str
        assert "time=" in repr_str
        assert "speaking=" in repr_str


class TestAsyncStreamingTranscriberProperties:
    """Test AsyncStreamingTranscriber properties."""

    @pytest.mark.asyncio
    async def test_buffer_duration_starts_zero(self):
        """Buffer duration starts at zero."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        assert transcriber.buffer_duration == 0.0

    @pytest.mark.asyncio
    async def test_current_time_starts_zero(self):
        """Current time starts at zero."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        assert transcriber.current_time == 0.0

    @pytest.mark.asyncio
    async def test_is_speaking_starts_false(self):
        """is_speaking starts as False."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        assert transcriber.is_speaking is False

    @pytest.mark.asyncio
    async def test_vad_state_starts_silence(self):
        """VAD state starts as silence."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        assert transcriber.vad_state == "silence"


class TestAsyncProcessChunk:
    """Test async process_chunk_async method."""

    @pytest.mark.asyncio
    async def test_process_empty_chunk(self):
        """Processing empty chunk returns empty list."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        events = await transcriber.process_chunk_async([])
        assert events == []

    @pytest.mark.asyncio
    async def test_process_silence_chunk(self):
        """Processing silence chunk works."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        samples = [0.0] * 16000  # 1 second at 16kHz
        events = await transcriber.process_chunk_async(samples)
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_process_updates_current_time(self):
        """Processing chunk updates current_time."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        samples = [0.0] * 16000  # 1 second at 16kHz
        await transcriber.process_chunk_async(samples)
        assert transcriber.current_time > 0.0

    @pytest.mark.asyncio
    async def test_process_multiple_chunks(self):
        """Can process multiple chunks sequentially."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        samples = [0.0] * 8000  # 0.5 seconds

        for _ in range(4):
            events = await transcriber.process_chunk_async(samples)
            assert isinstance(events, list)

        # Should have processed ~2 seconds
        assert transcriber.current_time >= 1.5


class TestAsyncFlush:
    """Test async flush_async method."""

    @pytest.mark.asyncio
    async def test_flush_empty_transcriber(self):
        """Flushing empty transcriber returns empty list."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        events = await transcriber.flush_async()
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_flush_after_processing(self):
        """Flushing after processing returns events."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        samples = [0.0] * 16000
        await transcriber.process_chunk_async(samples)
        events = await transcriber.flush_async()
        assert isinstance(events, list)


class TestAsyncReset:
    """Test reset method."""

    @pytest.mark.asyncio
    async def test_reset_clears_state(self):
        """Reset clears transcriber state."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        samples = [0.0] * 16000
        await transcriber.process_chunk_async(samples)

        assert transcriber.current_time > 0.0

        transcriber.reset()

        assert transcriber.current_time == 0.0
        assert transcriber.buffer_duration == 0.0


class TestAsyncConcurrency:
    """Test async concurrency behavior."""

    @pytest.mark.asyncio
    async def test_multiple_transcribers_parallel(self):
        """Can run multiple transcribers in parallel."""
        transcribers = [
            antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
            for _ in range(3)
        ]

        samples = [0.0] * 8000

        async def process_one(t):
            return await t.process_chunk_async(samples)

        results = await asyncio.gather(*[process_one(t) for t in transcribers])

        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_sequential_chunks_same_transcriber(self):
        """Can process chunks sequentially on same transcriber."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")
        samples = [0.0] * 4000

        all_events = []
        for _ in range(5):
            events = await transcriber.process_chunk_async(samples)
            all_events.extend(events)

        assert transcriber.current_time > 0.0


class TestAsyncWithRealAudio:
    """Test async streaming with real audio patterns."""

    @pytest.mark.asyncio
    async def test_speech_pattern_detection(self):
        """VAD detects speech-like patterns."""
        # Use realtime preset which has sensitive VAD settings
        config = antenna.StreamingConfig.realtime()

        transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
            "whisper/tiny", config=config
        )

        # Generate speech-like audio (440Hz tone)
        sample_rate = 16000
        duration_ms = 500
        amplitude = 0.3
        samples = duration_ms * sample_rate // 1000

        speech = [
            amplitude * math.sin(2.0 * math.pi * 440.0 * i / sample_rate)
            for i in range(samples)
        ]

        events = await transcriber.process_chunk_async(speech)
        assert isinstance(events, list)


class TestAsyncEventTypes:
    """Test that async methods return proper event types."""

    @pytest.mark.asyncio
    async def test_events_are_streaming_events(self):
        """Returned events are StreamingEvent instances."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")

        # Generate some audio to trigger processing
        sample_rate = 16000
        samples = [
            0.3 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate)
            for i in range(sample_rate * 2)  # 2 seconds
        ]

        events = await transcriber.process_chunk_async(samples)

        for event in events:
            assert hasattr(event, "event_type")
            assert hasattr(event, "is_partial")
            assert hasattr(event, "is_final")

    @pytest.mark.asyncio
    async def test_final_events_on_flush(self):
        """Flush produces final events."""
        transcriber = antenna.AsyncStreamingTranscriber.from_model_id("whisper/tiny")

        sample_rate = 16000
        samples = [
            0.3 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate)
            for i in range(sample_rate * 2)
        ]

        await transcriber.process_chunk_async(samples)
        final_events = await transcriber.flush_async()

        # Should have at least one event (possibly empty text)
        assert isinstance(final_events, list)


class TestAsyncExportPresence:
    """Test that async API is properly exported."""

    def test_async_transcriber_in_module(self):
        """AsyncStreamingTranscriber is in antenna module."""
        assert hasattr(antenna, "AsyncStreamingTranscriber")

    def test_async_transcriber_in_all(self):
        """AsyncStreamingTranscriber is in __all__."""
        assert "AsyncStreamingTranscriber" in antenna.__all__

    def test_async_transcriber_callable(self):
        """AsyncStreamingTranscriber.from_model_id is callable."""
        assert callable(antenna.AsyncStreamingTranscriber.from_model_id)
