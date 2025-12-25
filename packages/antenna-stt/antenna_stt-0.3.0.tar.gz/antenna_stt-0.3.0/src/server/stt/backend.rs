//! Speech-to-Text Backend Trait
//!
//! This module defines the `SttBackend` trait that all STT engines must implement.
//! This allows the streaming server to work with different transcription backends
//! (Whisper, FasterWhisper, cloud APIs, etc.) through a unified interface.

use async_trait::async_trait;
use std::fmt::Debug;

use crate::server::streaming::types::{AudioChunk, PartialTranscript, StreamingConfig};

/// Result type for STT operations
pub type SttResult<T> = Result<T, SttError>;

/// Errors that can occur during STT processing
#[derive(Debug, thiserror::Error)]
pub enum SttError {
    #[error("Model not loaded: {0}")]
    ModelNotLoaded(String),

    #[error("Invalid audio format: {0}")]
    InvalidAudioFormat(String),

    #[error("Transcription failed: {0}")]
    TranscriptionFailed(String),

    #[error("Backend initialization failed: {0}")]
    InitializationFailed(String),

    #[error("Backend not ready")]
    NotReady,

    #[error("Operation timed out")]
    Timeout,

    #[error("Internal error: {0}")]
    Internal(String),
}

/// Capabilities of an STT backend
#[derive(Debug, Clone, Default)]
pub struct BackendCapabilities {
    /// Whether the backend supports true streaming (word-by-word output)
    pub streaming: bool,
    /// Whether the backend can detect language automatically
    pub language_detection: bool,
    /// Whether the backend supports translation (to English)
    pub translation: bool,
    /// Whether the backend supports word-level timestamps
    pub word_timestamps: bool,
    /// List of supported languages (ISO 639-1 codes)
    pub supported_languages: Vec<String>,
    /// Maximum audio duration supported (seconds)
    pub max_audio_duration: f64,
    /// Recommended chunk duration for streaming (seconds)
    pub recommended_chunk_duration: f64,
}

/// Information about a loaded STT backend
#[derive(Debug, Clone)]
pub struct BackendInfo {
    /// Name of the backend (e.g., "whisper", "faster-whisper")
    pub name: String,
    /// Model identifier or size (e.g., "tiny", "base", "large-v3")
    pub model: String,
    /// Device the model is running on (e.g., "cpu", "cuda:0")
    pub device: String,
    /// Backend capabilities
    pub capabilities: BackendCapabilities,
}

/// Trait for Speech-to-Text backends
///
/// Implementations of this trait wrap different STT engines and provide
/// a unified interface for the streaming server.
///
/// # Example
///
/// ```ignore
/// use antenna::server::stt::{SttBackend, WhisperBackend};
///
/// let backend = WhisperBackend::new("tiny", "cuda")?;
/// let result = backend.transcribe(audio_chunk).await?;
/// println!("Transcribed: {}", result.text);
/// ```
#[async_trait]
pub trait SttBackend: Send + Sync + Debug {
    /// Get information about this backend
    fn info(&self) -> &BackendInfo;

    /// Get the capabilities of this backend
    fn capabilities(&self) -> &BackendCapabilities {
        &self.info().capabilities
    }

    /// Check if the backend is ready to process audio
    fn is_ready(&self) -> bool;

    /// Transcribe a chunk of audio
    ///
    /// This is the main entry point for transcription. For non-streaming
    /// backends, this processes the entire chunk at once. For streaming
    /// backends, this may return partial results.
    ///
    /// # Arguments
    /// * `chunk` - Audio chunk to transcribe
    /// * `config` - Streaming configuration
    ///
    /// # Returns
    /// A vector of partial transcripts. May be empty if not enough audio
    /// has been accumulated, or contain multiple segments.
    async fn transcribe(
        &self,
        chunk: &AudioChunk,
        config: &StreamingConfig,
    ) -> SttResult<Vec<PartialTranscript>>;

    /// Flush any buffered audio and return final results
    ///
    /// Called when the audio stream ends to ensure all audio is processed.
    async fn flush(&self, config: &StreamingConfig) -> SttResult<Vec<PartialTranscript>>;

    /// Reset the backend state
    ///
    /// Called between sessions to clear any accumulated state.
    async fn reset(&self) -> SttResult<()>;

    /// Detect the language of an audio chunk
    ///
    /// Returns the ISO 639-1 language code (e.g., "en", "es", "zh").
    /// Not all backends support this; check capabilities first.
    async fn detect_language(&self, _chunk: &AudioChunk) -> SttResult<String> {
        if !self.capabilities().language_detection {
            return Err(SttError::Internal(
                "Language detection not supported by this backend".to_string(),
            ));
        }
        Err(SttError::Internal("Not implemented".to_string()))
    }

    /// Translate audio to English
    ///
    /// Not all backends support this; check capabilities first.
    async fn translate(
        &self,
        _chunk: &AudioChunk,
        _config: &StreamingConfig,
    ) -> SttResult<Vec<PartialTranscript>> {
        if !self.capabilities().translation {
            return Err(SttError::Internal(
                "Translation not supported by this backend".to_string(),
            ));
        }
        Err(SttError::Internal("Not implemented".to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stt_error_display() {
        let err = SttError::ModelNotLoaded("whisper-tiny".to_string());
        assert!(err.to_string().contains("whisper-tiny"));
    }

    #[test]
    fn test_backend_capabilities_default() {
        let caps = BackendCapabilities::default();
        assert!(!caps.streaming);
        assert!(!caps.language_detection);
    }
}
