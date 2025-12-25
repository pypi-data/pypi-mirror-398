//! Whisper model configuration
//!
//! Provides configuration structures for different Whisper model sizes
//! and their associated parameters.

use serde::{Deserialize, Serialize};

/// Model size variants for Whisper
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModelSize {
    Tiny,
    Base,
    Small,
    Medium,
    Large,
    LargeV2,
    LargeV3,
}

impl ModelSize {
    /// Get the HuggingFace model ID for this size
    pub fn model_id(&self) -> &'static str {
        match self {
            ModelSize::Tiny => "openai/whisper-tiny",
            ModelSize::Base => "openai/whisper-base",
            ModelSize::Small => "openai/whisper-small",
            ModelSize::Medium => "openai/whisper-medium",
            ModelSize::Large => "openai/whisper-large",
            ModelSize::LargeV2 => "openai/whisper-large-v2",
            ModelSize::LargeV3 => "openai/whisper-large-v3",
        }
    }

    /// Parse model size from string
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "tiny" => Some(ModelSize::Tiny),
            "base" => Some(ModelSize::Base),
            "small" => Some(ModelSize::Small),
            "medium" => Some(ModelSize::Medium),
            "large" => Some(ModelSize::Large),
            "large-v2" | "largev2" => Some(ModelSize::LargeV2),
            "large-v3" | "largev3" => Some(ModelSize::LargeV3),
            _ => None,
        }
    }
}

/// Whisper model configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WhisperConfig {
    pub vocab_size: usize,
    pub num_mel_bins: usize,
    pub d_model: usize,
    pub encoder_layers: usize,
    pub encoder_attention_heads: usize,
    pub decoder_layers: usize,
    pub decoder_attention_heads: usize,
    pub decoder_ffn_dim: usize,
    pub encoder_ffn_dim: usize,
    pub max_source_positions: usize,
    pub max_target_positions: usize,
    #[serde(default = "default_suppress_tokens")]
    pub suppress_tokens: Vec<i64>,
}

fn default_suppress_tokens() -> Vec<i64> {
    vec![]
}

impl Default for WhisperConfig {
    fn default() -> Self {
        // Default configuration for whisper-base
        Self {
            vocab_size: 51865,
            num_mel_bins: 80,
            d_model: 512,
            encoder_layers: 6,
            encoder_attention_heads: 8,
            decoder_layers: 6,
            decoder_attention_heads: 8,
            decoder_ffn_dim: 2048,
            encoder_ffn_dim: 2048,
            max_source_positions: 1500,
            max_target_positions: 448,
            suppress_tokens: vec![],
        }
    }
}

impl WhisperConfig {
    /// Create configuration for a specific model size
    pub fn for_model_size(size: ModelSize) -> Self {
        match size {
            ModelSize::Tiny => Self {
                vocab_size: 51865,
                num_mel_bins: 80,
                d_model: 384,
                encoder_layers: 4,
                encoder_attention_heads: 6,
                decoder_layers: 4,
                decoder_attention_heads: 6,
                decoder_ffn_dim: 1536,
                encoder_ffn_dim: 1536,
                max_source_positions: 1500,
                max_target_positions: 448,
                suppress_tokens: vec![],
            },
            ModelSize::Base => Self::default(),
            ModelSize::Small => Self {
                vocab_size: 51865,
                num_mel_bins: 80,
                d_model: 768,
                encoder_layers: 12,
                encoder_attention_heads: 12,
                decoder_layers: 12,
                decoder_attention_heads: 12,
                decoder_ffn_dim: 3072,
                encoder_ffn_dim: 3072,
                max_source_positions: 1500,
                max_target_positions: 448,
                suppress_tokens: vec![],
            },
            ModelSize::Medium => Self {
                vocab_size: 51865,
                num_mel_bins: 80,
                d_model: 1024,
                encoder_layers: 24,
                encoder_attention_heads: 16,
                decoder_layers: 24,
                decoder_attention_heads: 16,
                decoder_ffn_dim: 4096,
                encoder_ffn_dim: 4096,
                max_source_positions: 1500,
                max_target_positions: 448,
                suppress_tokens: vec![],
            },
            ModelSize::Large | ModelSize::LargeV2 | ModelSize::LargeV3 => Self {
                vocab_size: 51865,
                num_mel_bins: 128,  // Large models use 128 mel bins
                d_model: 1280,
                encoder_layers: 32,
                encoder_attention_heads: 20,
                decoder_layers: 32,
                decoder_attention_heads: 20,
                decoder_ffn_dim: 5120,
                encoder_ffn_dim: 5120,
                max_source_positions: 1500,
                max_target_positions: 448,
                suppress_tokens: vec![],
            },
        }
    }
}

/// Special token IDs used by Whisper
#[derive(Debug, Clone)]
pub struct SpecialTokens {
    pub sot: u32,                    // Start of transcript
    pub eot: u32,                    // End of transcript
    pub transcribe: u32,             // Transcription task
    pub translate: u32,              // Translation task
    pub no_speech: u32,              // No speech detected
    pub no_timestamps: u32,          // Suppress timestamps
    pub timestamp_begin: u32,        // First timestamp token
    pub language_token_start: u32,   // Start of language tokens
}

impl Default for SpecialTokens {
    fn default() -> Self {
        Self {
            sot: 50258,
            eot: 50257,
            transcribe: 50359,
            translate: 50358,
            no_speech: 50362,
            no_timestamps: 50363,
            timestamp_begin: 50364,
            language_token_start: 50259,
        }
    }
}

/// Language codes supported by Whisper (99 languages)
pub const LANGUAGES: &[(&str, &str)] = &[
    ("en", "english"),
    ("zh", "chinese"),
    ("de", "german"),
    ("es", "spanish"),
    ("ru", "russian"),
    ("ko", "korean"),
    ("fr", "french"),
    ("ja", "japanese"),
    ("pt", "portuguese"),
    ("tr", "turkish"),
    ("pl", "polish"),
    ("ca", "catalan"),
    ("nl", "dutch"),
    ("ar", "arabic"),
    ("sv", "swedish"),
    ("it", "italian"),
    ("id", "indonesian"),
    ("hi", "hindi"),
    ("fi", "finnish"),
    ("vi", "vietnamese"),
    ("he", "hebrew"),
    ("uk", "ukrainian"),
    ("el", "greek"),
    ("ms", "malay"),
    ("cs", "czech"),
    ("ro", "romanian"),
    ("da", "danish"),
    ("hu", "hungarian"),
    ("ta", "tamil"),
    ("no", "norwegian"),
    ("th", "thai"),
    ("ur", "urdu"),
    ("hr", "croatian"),
    ("bg", "bulgarian"),
    ("lt", "lithuanian"),
    ("la", "latin"),
    ("mi", "maori"),
    ("ml", "malayalam"),
    ("cy", "welsh"),
    ("sk", "slovak"),
    ("te", "telugu"),
    ("fa", "persian"),
    ("lv", "latvian"),
    ("bn", "bengali"),
    ("sr", "serbian"),
    ("az", "azerbaijani"),
    ("sl", "slovenian"),
    ("kn", "kannada"),
    ("et", "estonian"),
    ("mk", "macedonian"),
    ("br", "breton"),
    ("eu", "basque"),
    ("is", "icelandic"),
    ("hy", "armenian"),
    ("ne", "nepali"),
    ("mn", "mongolian"),
    ("bs", "bosnian"),
    ("kk", "kazakh"),
    ("sq", "albanian"),
    ("sw", "swahili"),
    ("gl", "galician"),
    ("mr", "marathi"),
    ("pa", "punjabi"),
    ("si", "sinhala"),
    ("km", "khmer"),
    ("sn", "shona"),
    ("yo", "yoruba"),
    ("so", "somali"),
    ("af", "afrikaans"),
    ("oc", "occitan"),
    ("ka", "georgian"),
    ("be", "belarusian"),
    ("tg", "tajik"),
    ("sd", "sindhi"),
    ("gu", "gujarati"),
    ("am", "amharic"),
    ("yi", "yiddish"),
    ("lo", "lao"),
    ("uz", "uzbek"),
    ("fo", "faroese"),
    ("ht", "haitian creole"),
    ("ps", "pashto"),
    ("tk", "turkmen"),
    ("nn", "nynorsk"),
    ("mt", "maltese"),
    ("sa", "sanskrit"),
    ("lb", "luxembourgish"),
    ("my", "myanmar"),
    ("bo", "tibetan"),
    ("tl", "tagalog"),
    ("mg", "malagasy"),
    ("as", "assamese"),
    ("tt", "tatar"),
    ("haw", "hawaiian"),
    ("ln", "lingala"),
    ("ha", "hausa"),
    ("ba", "bashkir"),
    ("jw", "javanese"),
    ("su", "sundanese"),
];

/// Get language token ID from language code
pub fn get_language_token(lang_code: &str) -> Option<u32> {
    let tokens = SpecialTokens::default();
    LANGUAGES
        .iter()
        .position(|(code, _)| *code == lang_code)
        .map(|idx| tokens.language_token_start + idx as u32)
}

/// Get language code from token ID
pub fn get_language_from_token(token: u32) -> Option<&'static str> {
    let tokens = SpecialTokens::default();
    if token < tokens.language_token_start {
        return None;
    }
    let idx = (token - tokens.language_token_start) as usize;
    LANGUAGES.get(idx).map(|(code, _)| *code)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_model_size_parsing() {
        assert_eq!(ModelSize::from_str("tiny"), Some(ModelSize::Tiny));
        assert_eq!(ModelSize::from_str("LARGE-V3"), Some(ModelSize::LargeV3));
        assert_eq!(ModelSize::from_str("invalid"), None);
    }

    #[test]
    fn test_language_tokens() {
        assert_eq!(get_language_token("en"), Some(50259));
        assert_eq!(get_language_token("zh"), Some(50260));
        assert_eq!(get_language_from_token(50259), Some("en"));
    }
}
