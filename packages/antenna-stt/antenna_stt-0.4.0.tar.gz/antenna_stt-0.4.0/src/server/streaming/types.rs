//! Core types for streaming audio processing
//!
//! These types are used throughout the server to represent audio chunks
//! and partial transcription results.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// A chunk of audio data for processing
#[derive(Debug, Clone)]
pub struct AudioChunk {
    /// Unique identifier for this chunk
    pub id: Uuid,
    /// Audio samples (mono, f32, normalized to [-1, 1])
    pub samples: Vec<f32>,
    /// Sample rate in Hz (typically 16000 for Whisper)
    pub sample_rate: u32,
    /// Timestamp when this chunk was received (monotonic, in seconds)
    pub timestamp: f64,
    /// Whether this is the final chunk in a stream
    pub is_final: bool,
}

impl AudioChunk {
    /// Create a new audio chunk
    pub fn new(samples: Vec<f32>, sample_rate: u32, timestamp: f64) -> Self {
        Self {
            id: Uuid::new_v4(),
            samples,
            sample_rate,
            timestamp,
            is_final: false,
        }
    }

    /// Create a final (end-of-stream) chunk
    pub fn final_chunk(samples: Vec<f32>, sample_rate: u32, timestamp: f64) -> Self {
        Self {
            id: Uuid::new_v4(),
            samples,
            sample_rate,
            timestamp,
            is_final: true,
        }
    }

    /// Duration of this chunk in seconds
    pub fn duration(&self) -> f64 {
        self.samples.len() as f64 / self.sample_rate as f64
    }
}

/// A partial or final transcription result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartialTranscript {
    /// Unique identifier for this transcript
    pub id: Uuid,
    /// The transcribed text
    pub text: String,
    /// Start time in the audio stream (seconds)
    pub start_time: f64,
    /// End time in the audio stream (seconds)
    pub end_time: f64,
    /// Whether this is a final (stable) result or partial (may change)
    pub is_final: bool,
    /// Confidence score (0.0 to 1.0), if available
    pub confidence: Option<f32>,
    /// Detected language code (e.g., "en", "es")
    pub language: Option<String>,
}

impl PartialTranscript {
    /// Create a new partial transcript
    pub fn partial(text: String, start_time: f64, end_time: f64) -> Self {
        Self {
            id: Uuid::new_v4(),
            text,
            start_time,
            end_time,
            is_final: false,
            confidence: None,
            language: None,
        }
    }

    /// Create a final transcript
    pub fn final_result(text: String, start_time: f64, end_time: f64) -> Self {
        Self {
            id: Uuid::new_v4(),
            text,
            start_time,
            end_time,
            is_final: true,
            confidence: None,
            language: None,
        }
    }

    /// Add confidence score
    pub fn with_confidence(mut self, confidence: f32) -> Self {
        self.confidence = Some(confidence);
        self
    }

    /// Add language
    pub fn with_language(mut self, language: String) -> Self {
        self.language = Some(language);
        self
    }
}

/// Configuration for streaming transcription
#[derive(Debug, Clone)]
pub struct StreamingConfig {
    /// Minimum audio duration before processing (seconds)
    pub min_chunk_duration: f64,
    /// Maximum audio duration to buffer before forcing processing (seconds)
    pub max_chunk_duration: f64,
    /// Sample rate expected by the STT backend
    pub sample_rate: u32,
    /// Language code for transcription (None for auto-detection)
    pub language: Option<String>,
    /// Whether to enable Voice Activity Detection
    pub use_vad: bool,
    /// VAD threshold in dB (below this is considered silence)
    pub vad_threshold_db: f32,
    /// Minimum silence duration to trigger processing (seconds)
    pub vad_min_silence: f64,
}

impl Default for StreamingConfig {
    fn default() -> Self {
        Self {
            min_chunk_duration: 0.5,    // 500ms minimum
            max_chunk_duration: 30.0,   // 30s maximum (Whisper limit)
            sample_rate: 16000,         // Whisper expects 16kHz
            language: None,             // Auto-detect
            use_vad: true,
            vad_threshold_db: -40.0,    // Fairly sensitive
            vad_min_silence: 0.5,       // 500ms of silence
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audio_chunk_duration() {
        let chunk = AudioChunk::new(vec![0.0; 16000], 16000, 0.0);
        assert!((chunk.duration() - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_partial_transcript() {
        let transcript = PartialTranscript::partial("hello".to_string(), 0.0, 1.0)
            .with_confidence(0.95)
            .with_language("en".to_string());

        assert_eq!(transcript.text, "hello");
        assert!(!transcript.is_final);
        assert_eq!(transcript.confidence, Some(0.95));
        assert_eq!(transcript.language, Some("en".to_string()));
    }
}
