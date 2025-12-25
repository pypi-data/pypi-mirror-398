//! Whisper tokenizer implementation
//!
//! Provides tokenization for Whisper input/output, including special token handling
//! and timestamp token processing.

use crate::AntennaError;
use std::collections::HashMap;
use std::fs;
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
    ///
    /// This method reads the tokenizer.json file and parses special token IDs
    /// from the added_tokens section, ensuring compatibility with both
    /// OpenAI Whisper and Distil-Whisper tokenizers.
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError> {
        let path = path.as_ref();

        let tokenizer = Tokenizer::from_file(path)
            .map_err(|e| AntennaError::ModelError(format!("Failed to load tokenizer: {}", e)))?;

        // Parse special tokens from the tokenizer.json file
        let special_tokens = Self::parse_special_tokens(path)?;

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

    /// Parse special token IDs from tokenizer.json
    ///
    /// Reads the added_tokens section to find the correct IDs for special tokens.
    /// Falls back to default values if parsing fails.
    fn parse_special_tokens(path: &Path) -> Result<SpecialTokens, AntennaError> {
        let content = fs::read_to_string(path)
            .map_err(|e| AntennaError::IoError(format!("Failed to read tokenizer file: {}", e)))?;

        let json: serde_json::Value = serde_json::from_str(&content)
            .map_err(|e| AntennaError::ModelError(format!("Failed to parse tokenizer JSON: {}", e)))?;

        let added_tokens = json
            .get("added_tokens")
            .and_then(|v| v.as_array())
            .ok_or_else(|| {
                tracing::warn!("No added_tokens found in tokenizer, using defaults");
                AntennaError::ModelError("No added_tokens section in tokenizer".to_string())
            })?;

        // Build a map of token content -> id
        let mut token_map: HashMap<String, u32> = HashMap::new();
        for token_entry in added_tokens {
            if let (Some(content), Some(id)) = (
                token_entry.get("content").and_then(|v| v.as_str()),
                token_entry.get("id").and_then(|v| v.as_u64()),
            ) {
                token_map.insert(content.to_string(), id as u32);
            }
        }

        // Helper to get token ID with fallback
        let get_token = |name: &str, default: u32| -> u32 {
            token_map.get(name).copied().unwrap_or_else(|| {
                tracing::warn!("Token '{}' not found, using default: {}", name, default);
                default
            })
        };

        // Parse each special token
        let eot = get_token("<|endoftext|>", 50257);
        let sot = get_token("<|startoftranscript|>", 50258);
        let transcribe = get_token("<|transcribe|>", 50359);
        let translate = get_token("<|translate|>", 50358);
        let no_timestamps = get_token("<|notimestamps|>", 50363);
        let no_speech = get_token("<|nospeech|>", 50362);

        // Find language token start by looking for <|en|>
        let language_token_start = get_token("<|en|>", 50259);

        // Find timestamp_begin by looking for <|0.00|>
        let timestamp_begin = get_token("<|0.00|>", 50364);

        tracing::debug!(
            "Parsed special tokens: sot={}, eot={}, transcribe={}, translate={}, no_timestamps={}, timestamp_begin={}, lang_start={}",
            sot, eot, transcribe, translate, no_timestamps, timestamp_begin, language_token_start
        );

        Ok(SpecialTokens {
            sot,
            eot,
            transcribe,
            translate,
            no_speech,
            no_timestamps,
            timestamp_begin,
            language_token_start,
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
