//! Configuration for Parakeet models

/// Parakeet model size/variant
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ParakeetSize {
    /// Parakeet TDT 0.6B (English)
    Tdt06BEn,
    /// Parakeet TDT 0.6B v2 (English, improved)
    Tdt06BV2,
    /// Parakeet TDT 0.6B v3 (Multilingual, 25 languages)
    Tdt06BV3,
}

impl ParakeetSize {
    /// Get the sherpa-onnx model name for this variant
    pub fn model_name(&self) -> &'static str {
        match self {
            Self::Tdt06BEn => "sherpa-onnx-nemo-parakeet-tdt-0.6b-en-int8",
            Self::Tdt06BV2 => "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8",
            Self::Tdt06BV3 => "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8",
        }
    }

    /// Get human-readable description
    pub fn description(&self) -> &'static str {
        match self {
            Self::Tdt06BEn => "Parakeet TDT 0.6B English (int8 quantized)",
            Self::Tdt06BV2 => "Parakeet TDT 0.6B v2 English (int8, improved)",
            Self::Tdt06BV3 => "Parakeet TDT 0.6B v3 Multilingual (25 languages)",
        }
    }

    /// Get supported languages
    pub fn languages(&self) -> Vec<&'static str> {
        match self {
            Self::Tdt06BEn | Self::Tdt06BV2 => vec!["en"],
            Self::Tdt06BV3 => vec![
                "en", "de", "es", "fr", "it", "nl", "pl", "pt", "ro", "sv",
                "cs", "da", "fi", "hu", "no", "sk", "sl", "bg", "hr", "lt",
                "lv", "et", "el", "uk", "ru",
            ],
        }
    }

    /// Get download URL for this model
    pub fn download_url(&self) -> String {
        format!(
            "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{}.tar.bz2",
            self.model_name()
        )
    }

    /// Parse from variant string
    pub fn from_variant(variant: &str) -> Option<Self> {
        match variant.to_lowercase().as_str() {
            "tdt-0.6b" | "tdt-0.6b-en" | "en" => Some(Self::Tdt06BEn),
            "tdt-0.6b-v2" | "v2" => Some(Self::Tdt06BV2),
            "tdt-0.6b-v3" | "v3" | "multilingual" => Some(Self::Tdt06BV3),
            _ => None,
        }
    }
}

impl Default for ParakeetSize {
    fn default() -> Self {
        Self::Tdt06BV2 // Best English model
    }
}

/// Configuration for Parakeet model loading
#[derive(Debug, Clone)]
pub struct ParakeetConfig {
    /// Model size/variant
    pub size: ParakeetSize,
    /// Number of threads for inference
    pub num_threads: usize,
    /// Whether to use int8 quantized model
    pub use_int8: bool,
    /// Custom model directory (None = use HF cache)
    pub model_dir: Option<String>,
}

impl Default for ParakeetConfig {
    fn default() -> Self {
        Self {
            size: ParakeetSize::default(),
            num_threads: 4,
            use_int8: true,
            model_dir: None,
        }
    }
}

impl ParakeetConfig {
    /// Create config for specific model variant
    pub fn with_size(mut self, size: ParakeetSize) -> Self {
        self.size = size;
        self
    }

    /// Set number of threads
    pub fn with_threads(mut self, num_threads: usize) -> Self {
        self.num_threads = num_threads;
        self
    }

    /// Set custom model directory
    pub fn with_model_dir(mut self, dir: impl Into<String>) -> Self {
        self.model_dir = Some(dir.into());
        self
    }
}

/// List of available Parakeet models
pub const PARAKEET_MODELS: &[(&str, &str)] = &[
    ("tdt-0.6b-v2", "Parakeet TDT 0.6B v2 - English, int8 quantized (~600M params)"),
    ("tdt-0.6b-v3", "Parakeet TDT 0.6B v3 - Multilingual, 25 languages"),
    ("tdt-0.6b-en", "Parakeet TDT 0.6B - English, original version"),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parakeet_size_from_variant() {
        assert_eq!(ParakeetSize::from_variant("v2"), Some(ParakeetSize::Tdt06BV2));
        assert_eq!(ParakeetSize::from_variant("multilingual"), Some(ParakeetSize::Tdt06BV3));
        assert_eq!(ParakeetSize::from_variant("invalid"), None);
    }

    #[test]
    fn test_parakeet_size_languages() {
        assert_eq!(ParakeetSize::Tdt06BV2.languages(), vec!["en"]);
        assert!(ParakeetSize::Tdt06BV3.languages().len() > 20);
    }

    #[test]
    fn test_config_builder() {
        let config = ParakeetConfig::default()
            .with_size(ParakeetSize::Tdt06BV3)
            .with_threads(8);

        assert_eq!(config.size, ParakeetSize::Tdt06BV3);
        assert_eq!(config.num_threads, 8);
    }
}
