//! Streaming Engine for Real-Time Transcription
//!
//! Orchestrates VAD, audio buffering, STT backend calls, and agreement policy
//! to produce stable streaming transcription results.

use parking_lot::Mutex;
use std::sync::Arc;
use uuid::Uuid;

use super::agreement::{AgreementConfig, LocalAgreementPolicy, TokenInfo};
use super::buffer::AudioRingBuffer;
use super::types::{AudioChunk, PartialTranscript, StreamingConfig};
use super::vad::{StreamingVad, VadConfig, VadFrame, VoiceState};
use crate::server::stt::{SttBackend, SttResult};

/// Configuration for the streaming engine
#[derive(Debug, Clone)]
pub struct EngineConfig {
    /// Streaming transcription configuration
    pub streaming: StreamingConfig,
    /// VAD configuration
    pub vad: VadConfig,
    /// Agreement policy configuration
    pub agreement: AgreementConfig,
    /// Whether to use VAD for segmentation (vs time-based)
    pub use_vad: bool,
    /// Time-based chunk interval when VAD is disabled (seconds)
    pub chunk_interval: f64,
    /// Maximum time to buffer before forcing processing (seconds)
    pub max_latency: f64,
}

impl Default for EngineConfig {
    fn default() -> Self {
        Self {
            streaming: StreamingConfig::default(),
            vad: VadConfig::default(),
            agreement: AgreementConfig::default(),
            use_vad: true,
            chunk_interval: 2.0,
            max_latency: 5.0,
        }
    }
}

/// Events emitted by the streaming engine
#[derive(Debug, Clone, serde::Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum StreamingEvent {
    /// Partial transcription (may change)
    Partial(PartialTranscript),
    /// Final transcription (stable, won't change)
    Final(PartialTranscript),
    /// Speech segment started
    SegmentStart { timestamp: f64 },
    /// Speech segment ended
    SegmentEnd { timestamp: f64, duration: f64 },
    /// VAD state changed
    VadStateChange { state: VoiceState, timestamp: f64 },
    /// Error occurred
    Error(String),
}

/// Internal state for the streaming engine
#[derive(Debug)]
struct EngineState {
    /// Current stream timestamp (seconds)
    current_time: f64,
    /// Segment start time (if in segment)
    segment_start: Option<f64>,
    /// Time of last processing
    last_process_time: f64,
    /// Time of last chunk received
    last_chunk_time: f64,
    /// Whether we're currently processing
    processing: bool,
    /// Accumulated text for current segment
    segment_text: String,
    /// Previous VAD state
    prev_vad_state: VoiceState,
}

impl EngineState {
    fn new() -> Self {
        Self {
            current_time: 0.0,
            segment_start: None,
            last_process_time: 0.0,
            last_chunk_time: 0.0,
            processing: false,
            segment_text: String::new(),
            prev_vad_state: VoiceState::Silence,
        }
    }

    fn reset(&mut self) {
        *self = Self::new();
    }
}

/// Streaming transcription engine
///
/// Combines VAD, buffering, STT backend, and agreement policy into
/// a unified streaming transcription pipeline.
pub struct StreamingEngine<B: SttBackend> {
    /// Configuration
    config: EngineConfig,
    /// STT backend
    backend: Arc<B>,
    /// Audio buffer
    buffer: AudioRingBuffer,
    /// Voice activity detector
    vad: StreamingVad,
    /// Local agreement policy
    agreement: LocalAgreementPolicy,
    /// Internal state
    state: Mutex<EngineState>,
    /// Session ID
    session_id: Uuid,
}

impl<B: SttBackend> std::fmt::Debug for StreamingEngine<B> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("StreamingEngine")
            .field("config", &self.config)
            .field("session_id", &self.session_id)
            .finish()
    }
}

impl<B: SttBackend> StreamingEngine<B> {
    /// Create a new streaming engine with the given backend
    pub fn new(backend: Arc<B>, config: EngineConfig) -> Self {
        let buffer = AudioRingBuffer::new(
            config.max_latency * 2.0, // Buffer can hold 2x max latency
            config.streaming.sample_rate,
            0.5, // 500ms overlap for context
        );

        let vad = StreamingVad::with_config(config.vad.clone());
        let agreement = LocalAgreementPolicy::with_config(config.agreement.clone());

        Self {
            config,
            backend,
            buffer,
            vad,
            agreement,
            state: Mutex::new(EngineState::new()),
            session_id: Uuid::new_v4(),
        }
    }

    /// Create with default configuration
    pub fn with_backend(backend: Arc<B>) -> Self {
        Self::new(backend, EngineConfig::default())
    }

    /// Get the session ID
    pub fn session_id(&self) -> Uuid {
        self.session_id
    }

    /// Process incoming audio samples
    ///
    /// # Arguments
    /// * `samples` - Audio samples (mono, f32, at configured sample rate)
    /// * `timestamp` - Timestamp of this audio chunk
    ///
    /// # Returns
    /// Vector of streaming events generated
    pub async fn process_audio(
        &self,
        samples: &[f32],
        timestamp: f64,
    ) -> SttResult<Vec<StreamingEvent>> {
        let mut events = Vec::new();

        // Update timing state
        {
            let mut state = self.state.lock();
            state.current_time = timestamp;
            state.last_chunk_time = timestamp;
        }

        // Add samples to buffer
        self.buffer.push(samples);

        // Process through VAD if enabled
        if self.config.use_vad {
            let vad_events = self.process_vad(samples, timestamp);
            events.extend(vad_events);
        }

        // Check if we should trigger processing
        let should_process = self.should_process(timestamp);

        if should_process {
            let process_events = self.run_transcription().await?;
            events.extend(process_events);
        }

        Ok(events)
    }

    /// Process samples through VAD
    fn process_vad(&self, samples: &[f32], timestamp: f64) -> Vec<StreamingEvent> {
        let mut events = Vec::new();
        let frame_size = self.config.vad.frame_size;

        // Process in frames
        for chunk in samples.chunks(frame_size) {
            if chunk.len() < frame_size {
                // Pad short chunk
                let mut padded = chunk.to_vec();
                padded.resize(frame_size, 0.0);
                let frame = self.vad.process_frame(&padded);
                events.extend(self.handle_vad_frame(frame, timestamp));
            } else {
                let frame = self.vad.process_frame(chunk);
                events.extend(self.handle_vad_frame(frame, timestamp));
            }
        }

        events
    }

    /// Handle a single VAD frame result
    fn handle_vad_frame(&self, frame: VadFrame, timestamp: f64) -> Vec<StreamingEvent> {
        let mut events = Vec::new();
        let mut state = self.state.lock();

        // Emit state change events
        if frame.state != state.prev_vad_state {
            events.push(StreamingEvent::VadStateChange {
                state: frame.state,
                timestamp,
            });

            // Track segment boundaries
            match (state.prev_vad_state, frame.state) {
                (VoiceState::Silence, VoiceState::Speech) |
                (VoiceState::Uncertain, VoiceState::Speech) => {
                    state.segment_start = Some(timestamp);
                    events.push(StreamingEvent::SegmentStart { timestamp });
                }
                (VoiceState::Speech, VoiceState::Silence) => {
                    if let Some(start) = state.segment_start.take() {
                        let duration = timestamp - start;
                        events.push(StreamingEvent::SegmentEnd { timestamp, duration });
                    }
                }
                _ => {}
            }

            state.prev_vad_state = frame.state;
        }

        // Check if segment ended (good time to finalize)
        if frame.segment_ended {
            if let Some(start) = state.segment_start.take() {
                let duration = timestamp - start;
                events.push(StreamingEvent::SegmentEnd { timestamp, duration });
            }
        }

        events
    }

    /// Determine if we should trigger transcription
    fn should_process(&self, timestamp: f64) -> bool {
        let state = self.state.lock();

        // Don't process if already processing
        if state.processing {
            return false;
        }

        let buffer_duration = self.buffer.duration();
        let time_since_last = timestamp - state.last_process_time;

        // Process if buffer has minimum audio
        if buffer_duration < self.config.streaming.min_chunk_duration {
            return false;
        }

        if self.config.use_vad {
            // VAD-based: process when segment ends or max latency reached
            let vad_segment_ended = !self.vad.in_segment() && buffer_duration > 0.1;
            let max_latency_reached = time_since_last >= self.config.max_latency;
            let max_duration_reached = buffer_duration >= self.config.streaming.max_chunk_duration;

            vad_segment_ended || max_latency_reached || max_duration_reached
        } else {
            // Time-based: process at fixed intervals
            time_since_last >= self.config.chunk_interval
                || buffer_duration >= self.config.streaming.max_chunk_duration
        }
    }

    /// Run transcription on buffered audio
    async fn run_transcription(&self) -> SttResult<Vec<StreamingEvent>> {
        let mut events = Vec::new();

        // Mark as processing
        {
            let mut state = self.state.lock();
            state.processing = true;
        }

        // Get audio from buffer
        let samples = self.buffer.read_with_overlap(
            (self.config.streaming.max_chunk_duration * self.config.streaming.sample_rate as f64) as usize,
        );

        if samples.is_empty() {
            let mut state = self.state.lock();
            state.processing = false;
            return Ok(events);
        }

        // Get timing info
        let (start_time, _) = {
            let state = self.state.lock();
            (state.segment_start.unwrap_or(state.last_process_time), state.current_time)
        };

        // Create audio chunk for backend
        let chunk = AudioChunk::new(samples, self.config.streaming.sample_rate, start_time);

        // Run transcription
        let transcripts = self.backend.transcribe(&chunk, &self.config.streaming).await?;

        // Process through agreement policy
        for transcript in transcripts {
            let tokens = self.text_to_tokens(&transcript.text);
            let agreement_result = self.agreement.process(tokens);

            // Emit confirmed text as partial (will be finalized on segment end)
            if !agreement_result.confirmed_text.is_empty() {
                let mut state = self.state.lock();
                state.segment_text.push_str(&agreement_result.confirmed_text);

                events.push(StreamingEvent::Partial(PartialTranscript {
                    id: Uuid::new_v4(),
                    text: agreement_result.confirmed_text,
                    start_time: transcript.start_time,
                    end_time: transcript.end_time,
                    is_final: false,
                    confidence: transcript.confidence,
                    language: transcript.language.clone(),
                }));
            }

            // Emit pending text as preview
            if !agreement_result.pending_text.is_empty() {
                events.push(StreamingEvent::Partial(PartialTranscript {
                    id: Uuid::new_v4(),
                    text: agreement_result.pending_text,
                    start_time: transcript.start_time,
                    end_time: transcript.end_time,
                    is_final: false,
                    confidence: None, // Lower confidence for pending
                    language: transcript.language,
                }));
            }
        }

        // Update state
        {
            let mut state = self.state.lock();
            state.processing = false;
            state.last_process_time = state.current_time;
        }

        Ok(events)
    }

    /// Flush any remaining audio and finalize
    pub async fn flush(&self) -> SttResult<Vec<StreamingEvent>> {
        let mut events = Vec::new();

        // Process any remaining buffer
        let remaining = self.buffer.read_all();
        if !remaining.is_empty() {
            let start_time = {
                let state = self.state.lock();
                state.segment_start.unwrap_or(state.last_process_time)
            };

            // Create final chunk and SEND IT TO THE BACKEND for transcription
            let chunk = AudioChunk::final_chunk(
                remaining,
                self.config.streaming.sample_rate,
                start_time,
            );

            // Transcribe the remaining audio
            let transcripts = self.backend.transcribe(&chunk, &self.config.streaming).await?;

            for transcript in transcripts {
                events.push(StreamingEvent::Final(PartialTranscript {
                    id: Uuid::new_v4(),
                    text: transcript.text,
                    start_time: transcript.start_time,
                    end_time: transcript.end_time,
                    is_final: true,
                    confidence: transcript.confidence,
                    language: transcript.language,
                }));
            }
        }

        // Also flush any remaining audio in the backend's internal buffer
        let flush_transcripts = self.backend.flush(&self.config.streaming).await?;
        for transcript in flush_transcripts {
            events.push(StreamingEvent::Final(PartialTranscript {
                id: Uuid::new_v4(),
                text: transcript.text,
                start_time: transcript.start_time,
                end_time: transcript.end_time,
                is_final: true,
                confidence: transcript.confidence,
                language: transcript.language,
            }));
        }

        // Emit final segment text
        {
            let state = self.state.lock();
            if !state.segment_text.is_empty() {
                events.push(StreamingEvent::Final(PartialTranscript {
                    id: Uuid::new_v4(),
                    text: state.segment_text.clone(),
                    start_time: state.segment_start.unwrap_or(0.0),
                    end_time: state.current_time,
                    is_final: true,
                    confidence: None,
                    language: None,
                }));
            }
        }

        Ok(events)
    }

    /// Reset the engine for a new session
    pub async fn reset(&self) -> SttResult<()> {
        self.buffer.clear();
        self.vad.reset();
        self.agreement.reset();
        self.state.lock().reset();
        self.backend.reset().await?;
        Ok(())
    }

    /// Get the configuration
    pub fn config(&self) -> &EngineConfig {
        &self.config
    }

    /// Get current buffer duration
    pub fn buffer_duration(&self) -> f64 {
        self.buffer.duration()
    }

    /// Check if VAD detects active speech
    pub fn is_speaking(&self) -> bool {
        self.vad.in_segment()
    }

    /// Convert text to tokens for agreement policy
    fn text_to_tokens(&self, text: &str) -> Vec<TokenInfo> {
        text.split_whitespace()
            .enumerate()
            .map(|(i, word)| TokenInfo {
                text: format!("{} ", word),
                position: i,
                confidence: None,
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Mock backend for testing
    #[derive(Debug)]
    struct MockBackend {
        response: Mutex<Vec<PartialTranscript>>,
    }

    impl MockBackend {
        fn new() -> Self {
            Self {
                response: Mutex::new(vec![]),
            }
        }

        fn set_response(&self, text: &str) {
            *self.response.lock() = vec![PartialTranscript::partial(
                text.to_string(),
                0.0,
                1.0,
            )];
        }
    }

    #[async_trait::async_trait]
    impl SttBackend for MockBackend {
        fn info(&self) -> &crate::server::stt::BackendInfo {
            static INFO: std::sync::OnceLock<crate::server::stt::BackendInfo> = std::sync::OnceLock::new();
            INFO.get_or_init(|| crate::server::stt::BackendInfo {
                name: "mock".to_string(),
                model: "test".to_string(),
                device: "cpu".to_string(),
                capabilities: Default::default(),
            })
        }

        fn is_ready(&self) -> bool {
            true
        }

        async fn transcribe(
            &self,
            _chunk: &AudioChunk,
            _config: &StreamingConfig,
        ) -> SttResult<Vec<PartialTranscript>> {
            Ok(self.response.lock().clone())
        }

        async fn flush(&self, _config: &StreamingConfig) -> SttResult<Vec<PartialTranscript>> {
            Ok(self.response.lock().clone())
        }

        async fn reset(&self) -> SttResult<()> {
            Ok(())
        }
    }

    #[test]
    fn test_engine_config_defaults() {
        let config = EngineConfig::default();
        assert!(config.use_vad);
        assert_eq!(config.max_latency, 5.0);
    }

    #[tokio::test]
    async fn test_engine_creation() {
        let backend = Arc::new(MockBackend::new());
        let engine = StreamingEngine::with_backend(backend);
        assert!(!engine.is_speaking());
        assert_eq!(engine.buffer_duration(), 0.0);
    }

    #[tokio::test]
    async fn test_process_silence() {
        let backend = Arc::new(MockBackend::new());
        let engine = StreamingEngine::with_backend(backend);

        // Process silence
        let silence = vec![0.0f32; 16000]; // 1 second
        let events = engine.process_audio(&silence, 0.0).await.unwrap();

        // Should not be speaking
        assert!(!engine.is_speaking());
    }

    #[tokio::test]
    async fn test_reset() {
        let backend = Arc::new(MockBackend::new());
        let engine = StreamingEngine::with_backend(backend);

        // Add some audio
        let audio = vec![0.5f32; 16000];
        engine.process_audio(&audio, 0.0).await.unwrap();

        // Reset
        engine.reset().await.unwrap();

        assert_eq!(engine.buffer_duration(), 0.0);
        assert!(!engine.is_speaking());
    }
}
