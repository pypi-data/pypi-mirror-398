//! Configuration for streaming transcription

use super::agreement::AgreementConfig;

/// Configuration for streaming transcription
#[derive(Debug, Clone)]
pub struct StreamingConfig {
    /// Sample rate expected for audio (Hz)
    pub sample_rate: u32,

    /// Minimum audio duration before attempting transcription (seconds)
    /// Shorter chunks produce lower quality results.
    pub min_chunk_duration: f64,

    /// Maximum audio duration to buffer before forcing transcription (seconds)
    /// Should not exceed model's limit (30s for Whisper).
    pub max_chunk_duration: f64,

    /// Whether to use Voice Activity Detection
    pub use_vad: bool,

    /// VAD threshold in dB (audio below this is silence)
    /// More negative = more sensitive.
    pub vad_threshold_db: f32,

    /// Minimum speech duration to trigger segment (seconds)
    pub vad_min_speech_duration: f64,

    /// Minimum silence duration to end segment (seconds)
    pub vad_min_silence_duration: f64,

    /// Language code for transcription (None for auto-detection)
    pub language: Option<String>,

    /// Beam size for transcription (1 = greedy, higher = better quality)
    pub beam_size: usize,

    /// Whether to use the local agreement policy for stable partial results
    /// When enabled, partial results will only show tokens that have been
    /// confirmed across multiple transcription runs, preventing "flickering".
    pub use_agreement: bool,

    /// Configuration for the local agreement policy
    pub agreement_config: AgreementConfig,
}

impl Default for StreamingConfig {
    fn default() -> Self {
        Self {
            sample_rate: 16000,
            min_chunk_duration: 0.5,       // 500ms minimum
            max_chunk_duration: 30.0,      // 30s maximum (Whisper limit)
            use_vad: true,
            vad_threshold_db: -40.0,       // Fairly sensitive
            vad_min_speech_duration: 0.25, // 250ms speech to trigger
            vad_min_silence_duration: 0.5, // 500ms silence to end
            language: None,
            beam_size: 1,                  // Greedy for speed in streaming
            use_agreement: false,          // Disabled by default for simplicity
            agreement_config: AgreementConfig::default(),
        }
    }
}

impl StreamingConfig {
    /// Create config for real-time, low-latency streaming
    pub fn realtime() -> Self {
        Self {
            min_chunk_duration: 0.3, // 300ms chunks
            max_chunk_duration: 5.0, // 5s max
            beam_size: 1,            // Greedy for speed
            ..Default::default()
        }
    }

    /// Create config for higher quality (more latency)
    pub fn quality() -> Self {
        Self {
            min_chunk_duration: 1.0,  // 1s minimum
            max_chunk_duration: 10.0, // 10s chunks
            beam_size: 3,             // Better quality
            ..Default::default()
        }
    }

    /// Create config without VAD (time-based chunking only)
    pub fn no_vad() -> Self {
        Self {
            use_vad: false,
            ..Default::default()
        }
    }

    /// Create config with stable partial results (agreement policy enabled)
    ///
    /// This is useful for display purposes where you want to avoid
    /// the "flickering" effect of rapidly changing partial results.
    pub fn stable() -> Self {
        Self {
            use_agreement: true,
            agreement_config: AgreementConfig::default(),
            ..Default::default()
        }
    }

    /// Set the language
    pub fn with_language(mut self, lang: impl Into<String>) -> Self {
        self.language = Some(lang.into());
        self
    }

    /// Set the sample rate
    pub fn with_sample_rate(mut self, rate: u32) -> Self {
        self.sample_rate = rate;
        self
    }

    /// Set VAD sensitivity
    pub fn with_vad_threshold(mut self, threshold_db: f32) -> Self {
        self.vad_threshold_db = threshold_db;
        self
    }

    /// Enable or disable the local agreement policy
    ///
    /// When enabled, partial results will only show tokens that have been
    /// confirmed across multiple transcription runs, preventing "flickering".
    pub fn with_agreement(mut self, enabled: bool) -> Self {
        self.use_agreement = enabled;
        self
    }

    /// Set custom agreement configuration
    pub fn with_agreement_config(mut self, config: AgreementConfig) -> Self {
        self.use_agreement = true;
        self.agreement_config = config;
        self
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<(), String> {
        if self.sample_rate == 0 {
            return Err("sample_rate must be > 0".to_string());
        }
        if self.min_chunk_duration <= 0.0 {
            return Err("min_chunk_duration must be > 0".to_string());
        }
        if self.max_chunk_duration <= self.min_chunk_duration {
            return Err("max_chunk_duration must be > min_chunk_duration".to_string());
        }
        if self.max_chunk_duration > 30.0 {
            return Err("max_chunk_duration must be <= 30s (Whisper limit)".to_string());
        }
        if self.use_agreement && self.agreement_config.agreement_count < 2 {
            return Err("agreement_count must be >= 2".to_string());
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = StreamingConfig::default();
        assert_eq!(config.sample_rate, 16000);
        assert!(config.use_vad);
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_realtime_config() {
        let config = StreamingConfig::realtime();
        assert_eq!(config.min_chunk_duration, 0.3);
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_invalid_config() {
        let config = StreamingConfig {
            min_chunk_duration: 5.0,
            max_chunk_duration: 2.0, // Invalid: max < min
            ..Default::default()
        };
        assert!(config.validate().is_err());
    }

    #[test]
    fn test_config_builder() {
        let config = StreamingConfig::default()
            .with_language("en")
            .with_sample_rate(48000)
            .with_vad_threshold(-50.0);

        assert_eq!(config.language, Some("en".to_string()));
        assert_eq!(config.sample_rate, 48000);
        assert_eq!(config.vad_threshold_db, -50.0);
    }
}
