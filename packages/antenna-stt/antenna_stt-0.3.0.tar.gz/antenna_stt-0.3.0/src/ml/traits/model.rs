//! Core SpeechModel trait for speech-to-text models
//!
//! This trait provides a unified interface for all STT models regardless of
//! their underlying architecture (encoder-decoder, encoder-only, etc.).

use candle_core::Device;
use std::fmt::Debug;

use crate::error::AntennaError;
use crate::types::AudioData;

/// Transcription task type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum TranscriptionTask {
    /// Transcribe audio to text in the same language
    #[default]
    Transcribe,
    /// Translate audio to English
    Translate,
}

impl TranscriptionTask {
    /// Convert from string representation
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "transcribe" => Some(Self::Transcribe),
            "translate" => Some(Self::Translate),
            _ => None,
        }
    }
}

/// Model architecture type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModelArchitecture {
    /// Encoder-Decoder architecture (Whisper, Canary)
    /// Uses autoregressive decoding with cross-attention
    EncoderDecoder,
    /// Encoder-only architecture with CTC (Wav2Vec2, Conformer-CTC)
    /// Uses Connectionist Temporal Classification for alignment-free decoding
    EncoderOnly,
    /// Hybrid architecture (Conformer with both CTC and attention)
    /// Can use either decoding method
    Hybrid,
}

/// Capabilities of a speech model
#[derive(Debug, Clone)]
pub struct ModelCapabilities {
    /// Model architecture type
    pub architecture: ModelArchitecture,
    /// Whether the model supports translation to English
    pub supports_translation: bool,
    /// Whether the model can detect the language of audio
    pub supports_language_detection: bool,
    /// Whether the model outputs timestamps for segments
    pub supports_timestamps: bool,
    /// Maximum audio duration in seconds the model can process
    pub max_audio_duration: f32,
    /// List of supported language codes
    pub supported_languages: Vec<String>,
}

impl Default for ModelCapabilities {
    fn default() -> Self {
        Self {
            architecture: ModelArchitecture::EncoderDecoder,
            supports_translation: false,
            supports_language_detection: false,
            supports_timestamps: false,
            max_audio_duration: 30.0,
            supported_languages: vec!["en".to_string()],
        }
    }
}

/// Model metadata and identification
#[derive(Debug, Clone)]
pub struct ModelInfo {
    /// Human-readable model name
    pub name: String,
    /// Model family identifier (e.g., "whisper", "wav2vec2", "conformer", "canary")
    pub family: String,
    /// Model variant (e.g., "tiny", "base", "large-v3", "1b")
    pub variant: String,
    /// Model capabilities
    pub capabilities: ModelCapabilities,
}

impl ModelInfo {
    /// Create a new ModelInfo
    pub fn new(name: impl Into<String>, family: impl Into<String>, variant: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            family: family.into(),
            variant: variant.into(),
            capabilities: ModelCapabilities::default(),
        }
    }

    /// Set capabilities
    pub fn with_capabilities(mut self, capabilities: ModelCapabilities) -> Self {
        self.capabilities = capabilities;
        self
    }
}

/// Common transcription options applicable to all models
#[derive(Debug, Clone)]
pub struct TranscriptionOptions {
    /// Language code (None for auto-detection)
    pub language: Option<String>,
    /// Task (transcribe or translate)
    pub task: TranscriptionTask,
    /// Whether to include timestamps in output
    pub timestamps: bool,
    /// Beam size for decoding (1 = greedy, higher = better quality but slower)
    pub beam_size: usize,
    /// Temperature for sampling (0.0 = deterministic)
    pub temperature: f32,
}

impl Default for TranscriptionOptions {
    fn default() -> Self {
        Self {
            language: None,
            task: TranscriptionTask::Transcribe,
            timestamps: true,
            beam_size: 5,
            temperature: 0.0,
        }
    }
}

impl TranscriptionOptions {
    /// Create options for simple transcription
    pub fn transcribe() -> Self {
        Self::default()
    }

    /// Create options for translation to English
    pub fn translate() -> Self {
        Self {
            task: TranscriptionTask::Translate,
            ..Self::default()
        }
    }

    /// Set the language
    pub fn with_language(mut self, lang: impl Into<String>) -> Self {
        self.language = Some(lang.into());
        self
    }

    /// Set beam size
    pub fn with_beam_size(mut self, beam_size: usize) -> Self {
        self.beam_size = beam_size;
        self
    }

    /// Use greedy decoding (beam_size = 1)
    pub fn greedy(mut self) -> Self {
        self.beam_size = 1;
        self
    }
}

/// A single transcription segment with timing information
#[derive(Debug, Clone)]
pub struct TranscriptionSegment {
    /// Start time in seconds
    pub start: f32,
    /// End time in seconds
    pub end: f32,
    /// Transcribed text for this segment
    pub text: String,
    /// Token IDs for this segment
    pub tokens: Vec<u32>,
    /// Average log probability (confidence indicator)
    pub avg_logprob: Option<f32>,
    /// Probability that this segment contains no speech
    pub no_speech_prob: Option<f32>,
}

/// Complete transcription result
#[derive(Debug, Clone)]
pub struct TranscriptionResult {
    /// Full transcribed text
    pub text: String,
    /// Individual segments with timing
    pub segments: Vec<TranscriptionSegment>,
    /// Detected or specified language code
    pub language: Option<String>,
    /// Probability of the detected language
    pub language_probability: Option<f32>,
}

impl TranscriptionResult {
    /// Create a simple result with just text
    pub fn from_text(text: impl Into<String>) -> Self {
        Self {
            text: text.into(),
            segments: vec![],
            language: None,
            language_probability: None,
        }
    }

    /// Set the language
    pub fn with_language(mut self, lang: impl Into<String>) -> Self {
        self.language = Some(lang.into());
        self
    }
}

/// Core trait for speech-to-text models
///
/// This is the main abstraction that all STT models implement.
/// It provides a unified interface regardless of the underlying
/// architecture (encoder-decoder, encoder-only, etc.).
///
/// # Example
///
/// ```ignore
/// use antenna::ml::traits::SpeechModel;
///
/// fn transcribe_with_any_model(model: &mut dyn SpeechModel, audio: &AudioData) {
///     let result = model.transcribe(audio, TranscriptionOptions::default()).unwrap();
///     println!("Transcription: {}", result.text);
/// }
/// ```
pub trait SpeechModel: Send + Sync + Debug {
    /// Get model information and metadata
    fn info(&self) -> &ModelInfo;

    /// Get the device this model is running on
    fn device(&self) -> &Device;

    /// Transcribe audio to text
    ///
    /// This is the main entry point for transcription. The audio should be
    /// preprocessed appropriately for the model (use `preprocess_audio`).
    ///
    /// # Arguments
    /// * `audio` - Input audio data
    /// * `options` - Transcription options (language, beam size, etc.)
    ///
    /// # Returns
    /// Complete transcription result with text, segments, and metadata
    fn transcribe(
        &mut self,
        audio: &AudioData,
        options: TranscriptionOptions,
    ) -> Result<TranscriptionResult, AntennaError>;

    /// Translate audio to English
    ///
    /// Convenience method that calls `transcribe` with translate task.
    /// Returns an error if the model doesn't support translation.
    fn translate(&mut self, audio: &AudioData) -> Result<TranscriptionResult, AntennaError> {
        if !self.info().capabilities.supports_translation {
            return Err(AntennaError::ModelError(
                "This model does not support translation".to_string(),
            ));
        }
        self.transcribe(audio, TranscriptionOptions::translate())
    }

    /// Detect the language of audio
    ///
    /// Returns the language code (e.g., "en", "es", "zh").
    /// Returns an error if the model doesn't support language detection.
    fn detect_language(&mut self, audio: &AudioData) -> Result<String, AntennaError>;

    /// Preprocess audio to the format expected by this model
    ///
    /// This typically involves resampling to the correct sample rate
    /// and converting to mono. Each model may have different requirements.
    fn preprocess_audio(&self, audio: &AudioData) -> Result<AudioData, AntennaError>;

    /// Get the expected sample rate for this model
    fn expected_sample_rate(&self) -> u32 {
        16000 // Most STT models use 16kHz
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_transcription_options_default() {
        let opts = TranscriptionOptions::default();
        assert_eq!(opts.task, TranscriptionTask::Transcribe);
        assert_eq!(opts.beam_size, 5);
        assert!(opts.timestamps);
    }

    #[test]
    fn test_transcription_options_builder() {
        let opts = TranscriptionOptions::transcribe()
            .with_language("en")
            .with_beam_size(3)
            .greedy();

        assert_eq!(opts.language, Some("en".to_string()));
        assert_eq!(opts.beam_size, 1); // greedy overrides
    }

    #[test]
    fn test_transcription_task_from_str() {
        assert_eq!(
            TranscriptionTask::from_str("transcribe"),
            Some(TranscriptionTask::Transcribe)
        );
        assert_eq!(
            TranscriptionTask::from_str("TRANSLATE"),
            Some(TranscriptionTask::Translate)
        );
        assert_eq!(TranscriptionTask::from_str("invalid"), None);
    }
}
