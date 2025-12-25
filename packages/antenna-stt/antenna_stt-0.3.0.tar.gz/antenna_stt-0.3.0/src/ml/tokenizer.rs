//! Whisper tokenizer implementation
//!
//! Provides tokenization for Whisper input/output, including special token handling
//! and timestamp token processing.

use crate::AntennaError;
use std::collections::HashMap;
use std::path::Path;
use tokenizers::Tokenizer;

use super::whisper::config::{SpecialTokens, LANGUAGES, get_language_token};

/// Whisper tokenizer wrapper
pub struct WhisperTokenizer {
    tokenizer: Tokenizer,
    special_tokens: SpecialTokens,
    language_tokens: HashMap<String, u32>,
}

impl WhisperTokenizer {
    /// Load tokenizer from file
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError> {
        let tokenizer = Tokenizer::from_file(path)
            .map_err(|e| AntennaError::ModelError(format!("Failed to load tokenizer: {}", e)))?;

        let special_tokens = SpecialTokens::default();

        // Build language token lookup
        let mut language_tokens = HashMap::new();
        for (i, (code, _)) in LANGUAGES.iter().enumerate() {
            language_tokens.insert(
                code.to_string(),
                special_tokens.language_token_start + i as u32,
            );
        }

        Ok(Self {
            tokenizer,
            special_tokens,
            language_tokens,
        })
    }

    /// Create a tokenizer with default Whisper vocabulary
    pub fn new() -> Result<Self, AntennaError> {
        // For now, we'll rely on the HuggingFace tokenizer file
        // This method can be extended to support embedded vocabulary
        Err(AntennaError::ModelError(
            "Default tokenizer requires tokenizer.json file".to_string(),
        ))
    }

    /// Get special tokens
    pub fn special_tokens(&self) -> &SpecialTokens {
        &self.special_tokens
    }

    /// Encode text to token IDs
    pub fn encode(&self, text: &str) -> Result<Vec<u32>, AntennaError> {
        let encoding = self
            .tokenizer
            .encode(text, false)
            .map_err(|e| AntennaError::ModelError(format!("Encoding failed: {}", e)))?;

        Ok(encoding.get_ids().to_vec())
    }

    /// Decode token IDs to text
    pub fn decode(&self, tokens: &[u32], skip_special: bool) -> Result<String, AntennaError> {
        let tokens_filtered: Vec<u32> = if skip_special {
            tokens
                .iter()
                .copied()
                .filter(|&t| !self.is_special_token(t))
                .collect()
        } else {
            tokens.to_vec()
        };

        self.tokenizer
            .decode(&tokens_filtered, skip_special)
            .map_err(|e| AntennaError::ModelError(format!("Decoding failed: {}", e)))
    }

    /// Check if a token is a special token
    pub fn is_special_token(&self, token: u32) -> bool {
        token == self.special_tokens.sot
            || token == self.special_tokens.eot
            || token == self.special_tokens.transcribe
            || token == self.special_tokens.translate
            || token == self.special_tokens.no_speech
            || token == self.special_tokens.no_timestamps
            || self.is_timestamp_token(token)
            || self.is_language_token(token)
    }

    /// Check if a token is a timestamp token
    pub fn is_timestamp_token(&self, token: u32) -> bool {
        token >= self.special_tokens.timestamp_begin
    }

    /// Check if a token is a language token
    pub fn is_language_token(&self, token: u32) -> bool {
        let start = self.special_tokens.language_token_start;
        let end = start + LANGUAGES.len() as u32;
        token >= start && token < end
    }

    /// Convert timestamp token to seconds
    pub fn timestamp_to_seconds(&self, token: u32) -> f32 {
        if token < self.special_tokens.timestamp_begin {
            return 0.0;
        }
        ((token - self.special_tokens.timestamp_begin) as f32) * 0.02 // 20ms per timestamp
    }

    /// Convert seconds to timestamp token
    pub fn seconds_to_timestamp(&self, seconds: f32) -> u32 {
        let token_offset = (seconds / 0.02).round() as u32;
        self.special_tokens.timestamp_begin + token_offset
    }

    /// Get language token for a language code
    pub fn get_language_token(&self, lang_code: &str) -> Option<u32> {
        self.language_tokens.get(lang_code).copied()
    }

    /// Get start of transcript token
    pub fn sot_token(&self) -> u32 {
        self.special_tokens.sot
    }

    /// Get end of transcript token
    pub fn eot_token(&self) -> u32 {
        self.special_tokens.eot
    }

    /// Get transcribe task token
    pub fn transcribe_token(&self) -> u32 {
        self.special_tokens.transcribe
    }

    /// Get translate task token
    pub fn translate_token(&self) -> u32 {
        self.special_tokens.translate
    }

    /// Get no timestamps token
    pub fn no_timestamps_token(&self) -> u32 {
        self.special_tokens.no_timestamps
    }

    /// Build initial decoder prompt tokens
    pub fn build_prompt_tokens(
        &self,
        language: Option<&str>,
        task: &str,
        timestamps: bool,
    ) -> Vec<u32> {
        let mut tokens = vec![self.special_tokens.sot];

        // Add language token
        if let Some(lang) = language {
            if let Some(lang_token) = get_language_token(lang) {
                tokens.push(lang_token);
            }
        }

        // Add task token
        match task {
            "translate" => tokens.push(self.special_tokens.translate),
            _ => tokens.push(self.special_tokens.transcribe),
        }

        // Add no_timestamps token if not using timestamps
        if !timestamps {
            tokens.push(self.special_tokens.no_timestamps);
        }

        tokens
    }

    /// Extract timestamps from decoded tokens
    pub fn extract_timestamps(&self, tokens: &[u32]) -> Vec<(f32, f32, String)> {
        let mut segments = Vec::new();
        let mut current_start: Option<f32> = None;
        let mut current_tokens: Vec<u32> = Vec::new();

        for &token in tokens {
            if self.is_timestamp_token(token) {
                let time = self.timestamp_to_seconds(token);

                if current_start.is_none() {
                    // First timestamp - this is the start
                    current_start = Some(time);
                } else if let Some(start) = current_start {
                    // Second timestamp - this is the end, create segment
                    if !current_tokens.is_empty() {
                        if let Ok(text) = self.decode(&current_tokens, true) {
                            let trimmed = text.trim().to_string();
                            if !trimmed.is_empty() {
                                segments.push((start, time, trimmed));
                            }
                        }
                    }
                    current_tokens.clear();
                    current_start = None; // Reset for next segment
                }
            } else if !self.is_special_token(token) {
                current_tokens.push(token);
            }
        }

        // Handle remaining tokens without closing timestamp
        if !current_tokens.is_empty() {
            if let Ok(text) = self.decode(&current_tokens, true) {
                let trimmed = text.trim().to_string();
                if !trimmed.is_empty() {
                    let start = current_start.unwrap_or(0.0);
                    // Use 30.0 as default end time (chunk duration)
                    segments.push((start, 30.0, trimmed));
                }
            }
        }

        // If no segments were found but we have tokens, decode all non-special tokens
        if segments.is_empty() && !tokens.is_empty() {
            let text_tokens: Vec<u32> = tokens
                .iter()
                .copied()
                .filter(|&t| !self.is_special_token(t))
                .collect();

            if !text_tokens.is_empty() {
                if let Ok(text) = self.decode(&text_tokens, true) {
                    let trimmed = text.trim().to_string();
                    if !trimmed.is_empty() {
                        segments.push((0.0, 30.0, trimmed));
                    }
                }
            }
        }

        segments
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_timestamp_conversion() {
        let special_tokens = SpecialTokens::default();

        // Test timestamp at 1 second (50 * 20ms)
        let token = special_tokens.timestamp_begin + 50;
        let seconds = ((token - special_tokens.timestamp_begin) as f32) * 0.02;
        assert!((seconds - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_special_tokens() {
        let special_tokens = SpecialTokens::default();
        assert_eq!(special_tokens.sot, 50258);
        assert_eq!(special_tokens.eot, 50257);
    }
}
