//! Canary model configuration

/// Canary model size variants
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CanarySize {
    /// Canary 1B - Original 1 billion parameter model
    Canary1B,
    /// Canary 1B v2 - Improved version
    Canary1BV2,
}

impl CanarySize {
    /// Get the HuggingFace/NVIDIA model ID
    pub fn model_id(&self) -> &'static str {
        match self {
            CanarySize::Canary1B => "nvidia/canary-1b",
            CanarySize::Canary1BV2 => "nvidia/canary-1b-v2",
        }
    }

    /// Parse from string
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "canary-1b" | "1b" => Some(CanarySize::Canary1B),
            "canary-1b-v2" | "1b-v2" => Some(CanarySize::Canary1BV2),
            _ => None,
        }
    }

    /// Get approximate model size in bytes
    pub fn model_size_bytes(&self) -> u64 {
        match self {
            CanarySize::Canary1B => 4_000_000_000,  // ~4GB
            CanarySize::Canary1BV2 => 4_000_000_000,
        }
    }
}

/// Canary model configuration
#[derive(Debug, Clone)]
pub struct CanaryConfig {
    /// FastConformer encoder layers
    pub encoder_layers: usize,
    /// Encoder hidden dimension
    pub encoder_dim: usize,
    /// Encoder attention heads
    pub encoder_heads: usize,
    /// Transformer decoder layers
    pub decoder_layers: usize,
    /// Decoder hidden dimension
    pub decoder_dim: usize,
    /// Decoder attention heads
    pub decoder_heads: usize,
    /// Vocabulary size (SentencePiece)
    pub vocab_size: usize,
    /// Mel spectrogram bins
    pub num_mel_bins: usize,
    /// Subsampling factor
    pub subsampling_factor: usize,
}

impl Default for CanaryConfig {
    fn default() -> Self {
        // Canary-1B configuration
        Self {
            encoder_layers: 24,
            encoder_dim: 1024,
            encoder_heads: 8,
            decoder_layers: 24,
            decoder_dim: 1024,
            decoder_heads: 16,
            vocab_size: 1024,  // SentencePiece vocab
            num_mel_bins: 80,
            subsampling_factor: 8,
        }
    }
}

/// Supported languages for Canary
pub const CANARY_LANGUAGES: &[(&str, &str)] = &[
    ("en", "English"),
    ("de", "German"),
    ("es", "Spanish"),
    ("fr", "French"),
];

/// Planned Canary model variants
pub const CANARY_MODELS: &[(&str, &str, &str)] = &[
    (
        "canary-1b",
        "nvidia/canary-1b",
        "1B param FastConformer, multilingual ASR",
    ),
    (
        "canary-1b-v2",
        "nvidia/canary-1b-v2",
        "Improved 1B param model",
    ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_size_parsing() {
        assert_eq!(CanarySize::from_str("canary-1b"), Some(CanarySize::Canary1B));
        assert_eq!(CanarySize::from_str("1b-v2"), Some(CanarySize::Canary1BV2));
        assert_eq!(CanarySize::from_str("invalid"), None);
    }

    #[test]
    fn test_config_default() {
        let config = CanaryConfig::default();
        assert_eq!(config.encoder_layers, 24);
        assert_eq!(config.num_mel_bins, 80);
    }

    #[test]
    fn test_models_listed() {
        assert_eq!(CANARY_MODELS.len(), 2);
    }
}
