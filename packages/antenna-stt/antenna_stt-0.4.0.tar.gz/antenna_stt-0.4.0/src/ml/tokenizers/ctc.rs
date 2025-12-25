//! CTC character tokenizer
//!
//! Simple character-level tokenizer for CTC-based models like Wav2Vec2.
//! These models typically output frame-level predictions over a character
//! vocabulary plus a blank token.

use std::collections::HashMap;
use std::path::Path;

use crate::error::AntennaError;
use crate::ml::traits::{LanguageInfo, SttTokenizer};

/// Character-level tokenizer for CTC models
///
/// Maps characters to token IDs and vice versa.
/// Token 0 is typically reserved for the CTC blank.
pub struct CtcCharTokenizer {
    /// Character to ID mapping
    char_to_id: HashMap<char, u32>,
    /// ID to character mapping
    id_to_char: HashMap<u32, char>,
    /// Blank token ID (typically 0)
    blank_id: u32,
    /// Padding token ID
    pad_id: Option<u32>,
    /// Unknown token ID
    unk_id: Option<u32>,
    /// Word separator character (typically space or |)
    word_separator: char,
    /// Word separator token ID
    word_separator_id: Option<u32>,
}

impl CtcCharTokenizer {
    /// Create a new CTC tokenizer with a character vocabulary
    ///
    /// # Arguments
    /// * `vocab` - Characters in vocabulary order (blank should be first)
    /// * `blank_char` - Character representing blank (e.g., '<pad>' or first char)
    pub fn new(vocab: &[char], blank_id: u32) -> Self {
        let mut char_to_id = HashMap::new();
        let mut id_to_char = HashMap::new();

        for (i, &c) in vocab.iter().enumerate() {
            char_to_id.insert(c, i as u32);
            id_to_char.insert(i as u32, c);
        }

        let word_separator = ' ';
        let word_separator_id = char_to_id.get(&word_separator).copied();

        Self {
            char_to_id,
            id_to_char,
            blank_id,
            pad_id: Some(blank_id), // Often same as blank
            unk_id: None,
            word_separator,
            word_separator_id,
        }
    }

    /// Create a standard English alphabet tokenizer
    ///
    /// Vocabulary: <blank>, a-z, space, apostrophe
    pub fn english() -> Self {
        let mut vocab = vec!['<']; // Placeholder for blank (index 0)

        // Add lowercase letters
        for c in 'a'..='z' {
            vocab.push(c);
        }

        // Add common punctuation
        vocab.push(' ');  // Space (word separator)
        vocab.push('\''); // Apostrophe

        let mut tokenizer = Self::new(&vocab, 0);
        tokenizer.word_separator = ' ';
        tokenizer.word_separator_id = tokenizer.char_to_id.get(&' ').copied();
        tokenizer
    }

    /// Create from a vocab file (one character per line)
    pub fn from_vocab_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError> {
        let content = std::fs::read_to_string(path.as_ref())
            .map_err(|e| AntennaError::IoError(format!("Failed to read vocab file: {}", e)))?;

        let vocab: Vec<char> = content
            .lines()
            .filter_map(|line| {
                let trimmed = line.trim();
                if trimmed.is_empty() {
                    None
                } else if trimmed.starts_with("<") {
                    // Special token like <pad>, <blank>, etc.
                    Some('<') // Placeholder
                } else {
                    trimmed.chars().next()
                }
            })
            .collect();

        Ok(Self::new(&vocab, 0))
    }

    /// Set the word separator
    pub fn with_word_separator(mut self, sep: char) -> Self {
        self.word_separator = sep;
        self.word_separator_id = self.char_to_id.get(&sep).copied();
        self
    }

    /// Get the blank token ID
    pub fn blank_id(&self) -> u32 {
        self.blank_id
    }

    /// Get the word separator token ID
    pub fn word_separator_id(&self) -> Option<u32> {
        self.word_separator_id
    }

    /// Encode a single character
    pub fn encode_char(&self, c: char) -> Option<u32> {
        // Try lowercase first
        self.char_to_id
            .get(&c.to_lowercase().next().unwrap_or(c))
            .or_else(|| self.char_to_id.get(&c))
            .copied()
    }

    /// Decode a single token
    pub fn decode_token(&self, id: u32) -> Option<char> {
        self.id_to_char.get(&id).copied()
    }
}

impl SttTokenizer for CtcCharTokenizer {
    fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError>
    where
        Self: Sized,
    {
        Self::from_vocab_file(path)
    }

    fn encode(&self, text: &str) -> Result<Vec<u32>, AntennaError> {
        let mut tokens = Vec::new();

        for c in text.chars() {
            if let Some(id) = self.encode_char(c) {
                tokens.push(id);
            } else if let Some(unk) = self.unk_id {
                tokens.push(unk);
            }
            // Skip unknown characters if no UNK token
        }

        Ok(tokens)
    }

    fn decode(&self, tokens: &[u32], skip_special: bool) -> Result<String, AntennaError> {
        let mut result = String::new();

        for &token in tokens {
            if skip_special && token == self.blank_id {
                continue;
            }
            if skip_special && Some(token) == self.pad_id {
                continue;
            }

            if let Some(c) = self.decode_token(token) {
                if c != '<' {
                    // Skip placeholder for special tokens
                    result.push(c);
                }
            }
        }

        Ok(result)
    }

    fn vocab_size(&self) -> usize {
        self.char_to_id.len()
    }

    fn is_special_token(&self, token: u32) -> bool {
        token == self.blank_id || Some(token) == self.pad_id
    }

    fn eos_token(&self) -> u32 {
        // CTC doesn't typically have EOS
        self.blank_id
    }

    fn blank_token(&self) -> Option<u32> {
        Some(self.blank_id)
    }

    fn pad_token(&self) -> Option<u32> {
        self.pad_id
    }

    fn unk_token(&self) -> Option<u32> {
        self.unk_id
    }

    fn supported_languages(&self) -> Vec<LanguageInfo> {
        // CTC tokenizers are typically language-specific
        vec![]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_english_tokenizer() {
        let tokenizer = CtcCharTokenizer::english();

        // Should have blank + 26 letters + space + apostrophe
        assert_eq!(tokenizer.vocab_size(), 29);

        // Blank should be 0
        assert_eq!(tokenizer.blank_id(), 0);
    }

    #[test]
    fn test_encode_decode() {
        let tokenizer = CtcCharTokenizer::english();

        let text = "hello";
        let encoded = tokenizer.encode(text).unwrap();
        assert_eq!(encoded.len(), 5);

        let decoded = tokenizer.decode(&encoded, false).unwrap();
        assert_eq!(decoded, "hello");
    }

    #[test]
    fn test_skip_blank() {
        let tokenizer = CtcCharTokenizer::english();

        // Simulate CTC output with blanks
        let tokens = vec![0, 8, 0, 5, 0, 12, 12, 0, 15]; // _h_e_ll_o (with blanks)

        let decoded = tokenizer.decode(&tokens, true).unwrap();
        // Note: This doesn't collapse repeated chars, just skips blanks
        assert_eq!(decoded, "hello");
    }

    #[test]
    fn test_case_insensitive() {
        let tokenizer = CtcCharTokenizer::english();

        let encoded_lower = tokenizer.encode("abc").unwrap();
        let encoded_upper = tokenizer.encode("ABC").unwrap();

        // Should encode to same IDs (lowercase)
        assert_eq!(encoded_lower, encoded_upper);
    }
}
