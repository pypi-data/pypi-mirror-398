//! Tokenizer traits for text encoding/decoding
//!
//! Different STT models use different tokenization schemes:
//! - Whisper: BPE with special tokens for language, task, timestamps
//! - Wav2Vec2-CTC: Character-level or word-piece
//! - Canary: SentencePiece with special tokens

use std::path::Path;

use crate::error::AntennaError;

/// Information about a supported language
#[derive(Debug, Clone)]
pub struct LanguageInfo {
    /// ISO 639-1 language code (e.g., "en", "es", "zh")
    pub code: String,
    /// Human-readable language name
    pub name: String,
    /// Token ID for this language (if model uses language tokens)
    pub token_id: Option<u32>,
}

impl LanguageInfo {
    /// Create a new language info
    pub fn new(code: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            name: name.into(),
            token_id: None,
        }
    }

    /// Set the token ID
    pub fn with_token_id(mut self, token_id: u32) -> Self {
        self.token_id = Some(token_id);
        self
    }
}

/// Trait for STT tokenizers
///
/// This trait abstracts tokenization for different model types.
/// Each model family may have different special tokens and encoding schemes.
///
/// # Special Tokens
///
/// - **Whisper**: Language tokens, task tokens (transcribe/translate), timestamps
/// - **Wav2Vec2-CTC**: Blank token, word boundary token
/// - **Canary**: Language tokens, punctuation tokens
pub trait SttTokenizer: Send + Sync {
    /// Load tokenizer from a file
    fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError>
    where
        Self: Sized;

    /// Encode text to token IDs
    fn encode(&self, text: &str) -> Result<Vec<u32>, AntennaError>;

    /// Decode token IDs to text
    ///
    /// # Arguments
    /// * `tokens` - Token IDs to decode
    /// * `skip_special` - Whether to skip special tokens in output
    fn decode(&self, tokens: &[u32], skip_special: bool) -> Result<String, AntennaError>;

    /// Get vocabulary size
    fn vocab_size(&self) -> usize;

    /// Check if a token is a special token
    fn is_special_token(&self, token: u32) -> bool;

    /// Get the end-of-sequence token
    fn eos_token(&self) -> u32;

    /// Get the beginning-of-sequence token (if applicable)
    fn bos_token(&self) -> Option<u32> {
        None
    }

    /// Get the padding token (if applicable)
    fn pad_token(&self) -> Option<u32> {
        None
    }

    /// Get the blank token for CTC (if applicable)
    fn blank_token(&self) -> Option<u32> {
        None
    }

    /// Get the unknown token
    fn unk_token(&self) -> Option<u32> {
        None
    }

    /// Get supported languages
    fn supported_languages(&self) -> Vec<LanguageInfo> {
        vec![]
    }

    /// Get the token ID for a language code
    fn get_language_token(&self, _lang_code: &str) -> Option<u32> {
        None
    }

    /// Check if the tokenizer supports a language
    fn supports_language(&self, lang_code: &str) -> bool {
        self.supported_languages()
            .iter()
            .any(|l| l.code == lang_code)
    }

    /// Convert token ID to its string representation
    fn token_to_string(&self, token: u32) -> Option<String> {
        self.decode(&[token], false).ok()
    }
}

/// Trait for tokenizers with timestamp support (Whisper-style)
pub trait TimestampTokenizer: SttTokenizer {
    /// Get the first timestamp token ID
    fn timestamp_begin(&self) -> u32;

    /// Check if a token is a timestamp token
    fn is_timestamp_token(&self, token: u32) -> bool;

    /// Convert a timestamp token to seconds
    fn token_to_timestamp(&self, token: u32) -> Option<f32>;

    /// Convert seconds to the nearest timestamp token
    fn timestamp_to_token(&self, seconds: f32) -> u32;

    /// Extract timestamps from a token sequence
    fn extract_timestamps(&self, tokens: &[u32]) -> Vec<(f32, f32, String)> {
        let mut result = Vec::new();
        let mut current_start: Option<f32> = None;
        let mut current_text = String::new();

        for &token in tokens {
            if self.is_timestamp_token(token) {
                if let Some(ts) = self.token_to_timestamp(token) {
                    if current_start.is_none() {
                        current_start = Some(ts);
                    } else if let Some(start) = current_start {
                        if !current_text.is_empty() {
                            result.push((start, ts, current_text.trim().to_string()));
                        }
                        current_start = Some(ts);
                        current_text.clear();
                    }
                }
            } else if !self.is_special_token(token) {
                if let Ok(text) = self.decode(&[token], true) {
                    current_text.push_str(&text);
                }
            }
        }

        result
    }
}

/// Trait for tokenizers with task tokens (Whisper-style)
pub trait TaskTokenizer: SttTokenizer {
    /// Get the transcribe task token
    fn transcribe_token(&self) -> u32;

    /// Get the translate task token
    fn translate_token(&self) -> u32;

    /// Get the no-timestamps token
    fn no_timestamps_token(&self) -> Option<u32> {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_language_info() {
        let lang = LanguageInfo::new("en", "English").with_token_id(50259);
        assert_eq!(lang.code, "en");
        assert_eq!(lang.name, "English");
        assert_eq!(lang.token_id, Some(50259));
    }
}
