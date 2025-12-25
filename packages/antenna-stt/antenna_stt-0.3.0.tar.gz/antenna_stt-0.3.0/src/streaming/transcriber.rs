//! Streaming Transcriber - Main entry point for streaming transcription

use crate::error::AntennaError;
use crate::ml::registry::DynSpeechModel;
use crate::ml::traits::{SpeechModel, TranscriptionOptions, TranscriptionTask};
use crate::types::AudioData;

use super::agreement::{text_to_tokens, LocalAgreementPolicy};
use super::buffer::AudioBuffer;
use super::config::StreamingConfig;
use super::vad::{SimpleVad, VadConfig, VoiceState};

/// Events emitted during streaming transcription
#[derive(Debug, Clone)]
pub enum StreamingEvent {
    /// Partial transcription result (may change with more audio)
    Partial {
        /// Transcribed text
        text: String,
        /// Start time in audio stream (seconds)
        start_time: f64,
        /// End time in audio stream (seconds)
        end_time: f64,
        /// Whether this segment is finalized
        is_final: bool,
    },
    /// Final transcription result (won't change)
    Final {
        /// Transcribed text
        text: String,
        /// Start time in audio stream (seconds)
        start_time: f64,
        /// End time in audio stream (seconds)
        end_time: f64,
        /// Detected language (if available)
        language: Option<String>,
    },
    /// Speech segment started (VAD detected voice)
    SegmentStart {
        /// Timestamp when segment started
        timestamp: f64,
    },
    /// Speech segment ended (VAD detected silence)
    SegmentEnd {
        /// Timestamp when segment ended
        timestamp: f64,
        /// Duration of the segment
        duration: f64,
    },
    /// Voice activity state changed
    VadStateChange {
        /// New state
        state: VoiceState,
        /// Timestamp of change
        timestamp: f64,
    },
}

impl StreamingEvent {
    /// Get the text content if this is a Partial or Final event
    pub fn text(&self) -> Option<&str> {
        match self {
            StreamingEvent::Partial { text, .. } => Some(text),
            StreamingEvent::Final { text, .. } => Some(text),
            _ => None,
        }
    }

    /// Check if this is a partial result
    pub fn is_partial(&self) -> bool {
        matches!(self, StreamingEvent::Partial { .. })
    }

    /// Check if this is a final result
    pub fn is_final(&self) -> bool {
        matches!(self, StreamingEvent::Final { .. })
    }

    /// Get the event type as a string
    pub fn event_type(&self) -> &'static str {
        match self {
            StreamingEvent::Partial { .. } => "partial",
            StreamingEvent::Final { .. } => "final",
            StreamingEvent::SegmentStart { .. } => "segment_start",
            StreamingEvent::SegmentEnd { .. } => "segment_end",
            StreamingEvent::VadStateChange { .. } => "vad_change",
        }
    }
}

/// Streaming transcriber state
#[derive(Debug)]
struct TranscriberState {
    /// Current timestamp in the audio stream
    current_time: f64,
    /// Time when last transcription was performed
    last_transcription_time: f64,
    /// Start time of current segment
    segment_start: Option<f64>,
    /// Previous VAD state
    prev_vad_state: VoiceState,
    /// Accumulated text for current segment
    segment_text: String,
}

impl TranscriberState {
    fn new() -> Self {
        Self {
            current_time: 0.0,
            last_transcription_time: 0.0,
            segment_start: None,
            prev_vad_state: VoiceState::Silence,
            segment_text: String::new(),
        }
    }

    fn reset(&mut self) {
        *self = Self::new();
    }
}

/// Streaming transcriber for chunk-by-chunk transcription
///
/// Wraps a speech model and provides a simple API for streaming transcription.
/// Handles buffering, VAD, and incremental transcription.
///
/// # Agreement Policy
///
/// When `use_agreement` is enabled in the config, the transcriber uses a
/// local agreement policy to stabilize partial results. This means partial
/// transcription events will only contain text that has been confirmed across
/// multiple transcription runs, preventing the "flickering" effect where
/// partial results change rapidly.
#[derive(Debug)]
pub struct StreamingTranscriber {
    /// The underlying speech model
    model: DynSpeechModel,
    /// Configuration
    config: StreamingConfig,
    /// Audio buffer
    buffer: AudioBuffer,
    /// Voice activity detector
    vad: SimpleVad,
    /// Local agreement policy for stable partial results (optional)
    agreement: Option<LocalAgreementPolicy>,
    /// Internal state
    state: TranscriberState,
}

impl StreamingTranscriber {
    /// Create a new streaming transcriber
    ///
    /// # Arguments
    /// * `model` - The speech model to use for transcription
    /// * `config` - Streaming configuration
    pub fn new(model: DynSpeechModel, config: StreamingConfig) -> Result<Self, AntennaError> {
        config.validate().map_err(AntennaError::ModelError)?;

        let buffer = AudioBuffer::new(config.max_chunk_duration * 2.0, config.sample_rate);

        let vad_config = VadConfig {
            sample_rate: config.sample_rate,
            threshold_db: config.vad_threshold_db,
            min_speech_duration: config.vad_min_speech_duration,
            min_silence_duration: config.vad_min_silence_duration,
        };
        let vad = SimpleVad::with_config(vad_config);

        // Create agreement policy if enabled
        let agreement = if config.use_agreement {
            Some(LocalAgreementPolicy::with_config(
                config.agreement_config.clone(),
            ))
        } else {
            None
        };

        Ok(Self {
            model,
            config,
            buffer,
            vad,
            agreement,
            state: TranscriberState::new(),
        })
    }

    /// Create with default configuration
    pub fn with_defaults(model: DynSpeechModel) -> Result<Self, AntennaError> {
        Self::new(model, StreamingConfig::default())
    }

    /// Process a chunk of audio samples
    ///
    /// # Arguments
    /// * `samples` - Audio samples (mono, f32, at configured sample rate)
    ///
    /// # Returns
    /// Vector of streaming events generated from this chunk
    pub fn process_chunk(&mut self, samples: &[f32]) -> Result<Vec<StreamingEvent>, AntennaError> {
        if samples.is_empty() {
            return Ok(vec![]);
        }

        let mut events = Vec::new();

        // Update timing
        let chunk_duration = samples.len() as f64 / self.config.sample_rate as f64;
        let chunk_start = self.state.current_time;
        self.state.current_time += chunk_duration;

        // Add to buffer
        self.buffer.push(samples);

        // Process VAD if enabled
        if self.config.use_vad {
            let (state_changed, segment_ended) = self.vad.process(samples);

            // Emit VAD state change event
            if state_changed {
                let new_state = self.vad.state();
                events.push(StreamingEvent::VadStateChange {
                    state: new_state,
                    timestamp: self.state.current_time,
                });

                // Track segment start
                if new_state == VoiceState::Speech && self.state.prev_vad_state == VoiceState::Silence
                {
                    self.state.segment_start = Some(chunk_start);
                    events.push(StreamingEvent::SegmentStart {
                        timestamp: chunk_start,
                    });
                }

                self.state.prev_vad_state = new_state;
            }

            // Segment ended - transcribe and finalize
            if segment_ended {
                let segment_start = self.state.segment_start.unwrap_or(0.0);
                let duration = self.state.current_time - segment_start;

                events.push(StreamingEvent::SegmentEnd {
                    timestamp: self.state.current_time,
                    duration,
                });

                // Transcribe the segment
                let transcribe_events = self.transcribe_buffer(true)?;
                events.extend(transcribe_events);

                self.state.segment_start = None;
                self.state.segment_text.clear();
            } else if self.should_transcribe() {
                // Periodic transcription for partial results
                let transcribe_events = self.transcribe_buffer(false)?;
                events.extend(transcribe_events);
            }
        } else {
            // Time-based chunking (no VAD)
            if self.should_transcribe() {
                let transcribe_events = self.transcribe_buffer(false)?;
                events.extend(transcribe_events);
            }
        }

        Ok(events)
    }

    /// Check if we should trigger transcription
    fn should_transcribe(&self) -> bool {
        let buffer_duration = self.buffer.duration();
        let time_since_last = self.state.current_time - self.state.last_transcription_time;

        // Transcribe if:
        // 1. Buffer has minimum content AND enough time has passed
        // 2. OR buffer is approaching maximum
        (buffer_duration >= self.config.min_chunk_duration && time_since_last >= 1.0)
            || buffer_duration >= self.config.max_chunk_duration * 0.9
    }

    /// Transcribe buffered audio
    fn transcribe_buffer(&mut self, is_final: bool) -> Result<Vec<StreamingEvent>, AntennaError> {
        let mut events = Vec::new();

        if self.buffer.is_empty() {
            return Ok(events);
        }

        // Get audio from buffer
        let samples = if is_final {
            self.buffer.read_all()
        } else {
            // Keep some audio for context
            let to_read = (self.buffer.len() as f64 * 0.8) as usize;
            self.buffer.read(to_read)
        };

        if samples.is_empty() {
            return Ok(events);
        }

        let start_time = self.state.segment_start.unwrap_or(self.state.last_transcription_time);
        let end_time = self.state.current_time;

        // Create AudioData for transcription
        let audio = AudioData {
            samples,
            sample_rate: self.config.sample_rate,
            channels: 1,
        };

        // Transcribe
        let options = TranscriptionOptions {
            language: self.config.language.clone(),
            task: TranscriptionTask::Transcribe,
            beam_size: self.config.beam_size,
            timestamps: false, // Disable for speed in streaming
            ..Default::default()
        };

        let result = self.model.transcribe(&audio, options)?;

        if !result.text.trim().is_empty() {
            if is_final {
                // Final results bypass agreement policy
                events.push(StreamingEvent::Final {
                    text: result.text.trim().to_string(),
                    start_time,
                    end_time,
                    language: result.language,
                });

                // Reset agreement policy on final (new segment coming)
                if let Some(ref mut agreement) = self.agreement {
                    agreement.reset();
                }
            } else if let Some(ref mut agreement) = self.agreement {
                // Use agreement policy for stable partial results
                let tokens = text_to_tokens(result.text.trim());
                let agreement_result = agreement.process(tokens);

                // Emit confirmed text as partial
                if !agreement_result.confirmed_text.trim().is_empty() {
                    events.push(StreamingEvent::Partial {
                        text: agreement_result.confirmed_text.trim().to_string(),
                        start_time,
                        end_time,
                        is_final: false,
                    });
                }
                // Note: pending_text is not emitted to avoid flickering
                // Users can access it through get_pending_text() if needed
            } else {
                // No agreement policy - emit raw partial results
                events.push(StreamingEvent::Partial {
                    text: result.text.trim().to_string(),
                    start_time,
                    end_time,
                    is_final: false,
                });
            }
        }

        self.state.last_transcription_time = self.state.current_time;

        Ok(events)
    }

    /// Flush any remaining audio and finalize
    ///
    /// Call this when the audio stream ends to get final results.
    pub fn flush(&mut self) -> Result<Vec<StreamingEvent>, AntennaError> {
        let mut events = Vec::new();

        // Transcribe any remaining audio
        if !self.buffer.is_empty() {
            let transcribe_events = self.transcribe_buffer(true)?;
            events.extend(transcribe_events);
        }

        // Emit segment end if we were in a segment
        if self.state.segment_start.is_some() {
            let start = self.state.segment_start.take().unwrap();
            events.push(StreamingEvent::SegmentEnd {
                timestamp: self.state.current_time,
                duration: self.state.current_time - start,
            });
        }

        Ok(events)
    }

    /// Reset the transcriber for a new session
    pub fn reset(&mut self) {
        self.buffer.clear();
        self.vad.reset();
        self.state.reset();
        if let Some(ref mut agreement) = self.agreement {
            agreement.reset();
        }
    }

    /// Get the current buffer duration
    pub fn buffer_duration(&self) -> f64 {
        self.buffer.duration()
    }

    /// Get the current stream time
    pub fn current_time(&self) -> f64 {
        self.state.current_time
    }

    /// Check if currently detecting speech
    pub fn is_speaking(&self) -> bool {
        self.vad.in_segment()
    }

    /// Get the VAD state
    pub fn vad_state(&self) -> VoiceState {
        self.vad.state()
    }

    /// Get the configuration
    pub fn config(&self) -> &StreamingConfig {
        &self.config
    }

    /// Check if agreement policy is enabled
    pub fn has_agreement(&self) -> bool {
        self.agreement.is_some()
    }

    /// Get the number of confirmed tokens in the agreement policy
    ///
    /// Returns 0 if agreement policy is not enabled.
    pub fn agreement_confirmed_count(&self) -> usize {
        self.agreement
            .as_ref()
            .map(|a| a.confirmed_count())
            .unwrap_or(0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_silence(duration_ms: usize, sample_rate: u32) -> Vec<f32> {
        vec![0.0; (duration_ms * sample_rate as usize) / 1000]
    }

    fn create_speech(duration_ms: usize, sample_rate: u32, amplitude: f32) -> Vec<f32> {
        let samples = (duration_ms * sample_rate as usize) / 1000;
        (0..samples)
            .map(|i| {
                amplitude
                    * (2.0 * std::f32::consts::PI * 440.0 * i as f32 / sample_rate as f32).sin()
            })
            .collect()
    }

    #[test]
    fn test_streaming_event_types() {
        let partial = StreamingEvent::Partial {
            text: "hello".to_string(),
            start_time: 0.0,
            end_time: 1.0,
            is_final: false,
        };
        assert!(partial.is_partial());
        assert!(!partial.is_final());
        assert_eq!(partial.text(), Some("hello"));
        assert_eq!(partial.event_type(), "partial");

        let final_event = StreamingEvent::Final {
            text: "world".to_string(),
            start_time: 1.0,
            end_time: 2.0,
            language: Some("en".to_string()),
        };
        assert!(!final_event.is_partial());
        assert!(final_event.is_final());
        assert_eq!(final_event.text(), Some("world"));
        assert_eq!(final_event.event_type(), "final");

        let segment_start = StreamingEvent::SegmentStart { timestamp: 0.0 };
        assert_eq!(segment_start.text(), None);
        assert_eq!(segment_start.event_type(), "segment_start");
    }

    #[test]
    fn test_config_validation() {
        let valid = StreamingConfig::default();
        assert!(valid.validate().is_ok());

        let invalid = StreamingConfig {
            min_chunk_duration: 0.0,
            ..Default::default()
        };
        assert!(invalid.validate().is_err());
    }
}
