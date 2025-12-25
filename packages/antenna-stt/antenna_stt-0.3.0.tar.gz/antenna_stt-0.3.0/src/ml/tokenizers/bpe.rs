//! BPE (Byte-Pair Encoding) tokenizer
//!
//! Wrapper around HuggingFace tokenizers for models that use BPE,
//! such as Whisper and GPT-style models.

use std::path::Path;
use tokenizers::Tokenizer;

use crate::error::AntennaError;
use crate::ml::traits::{LanguageInfo, SttTokenizer};

/// BPE tokenizer for speech models
///
/// This wraps the HuggingFace tokenizers library and provides
/// the SttTokenizer interface.
pub struct BpeTokenizer {
    tokenizer: Tokenizer,
    eos_token_id: u32,
    bos_token_id: Option<u32>,
    pad_token_id: Option<u32>,
    unk_token_id: Option<u32>,
    special_token_ids: Vec<u32>,
}

impl BpeTokenizer {
    /// Create a BPE tokenizer from a tokenizer.json file
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError> {
        let tokenizer = Tokenizer::from_file(path.as_ref()).map_err(|e| {
            AntennaError::ModelError(format!("Failed to load tokenizer: {}", e))
        })?;

        // Try to find special tokens
        let eos_token_id = tokenizer
            .token_to_id("<|endoftext|>")
            .or_else(|| tokenizer.token_to_id("</s>"))
            .or_else(|| tokenizer.token_to_id("<eos>"))
            .unwrap_or(0);

        let bos_token_id = tokenizer
            .token_to_id("<|startoftext|>")
            .or_else(|| tokenizer.token_to_id("<s>"))
            .or_else(|| tokenizer.token_to_id("<bos>"));

        let pad_token_id = tokenizer
            .token_to_id("<pad>")
            .or_else(|| tokenizer.token_to_id("<|pad|>"));

        let unk_token_id = tokenizer
            .token_to_id("<unk>")
            .or_else(|| tokenizer.token_to_id("<|unk|>"));

        Ok(Self {
            tokenizer,
            eos_token_id,
            bos_token_id,
            pad_token_id,
            unk_token_id,
            special_token_ids: vec![],
        })
    }

    /// Create with explicit special token IDs
    pub fn with_special_tokens(
        mut self,
        eos: u32,
        bos: Option<u32>,
        pad: Option<u32>,
        special_ids: Vec<u32>,
    ) -> Self {
        self.eos_token_id = eos;
        self.bos_token_id = bos;
        self.pad_token_id = pad;
        self.special_token_ids = special_ids;
        self
    }

    /// Get the underlying tokenizer
    pub fn inner(&self) -> &Tokenizer {
        &self.tokenizer
    }

    /// Get token ID for a token string
    pub fn token_to_id(&self, token: &str) -> Option<u32> {
        self.tokenizer.token_to_id(token)
    }

    /// Get token string for a token ID
    pub fn id_to_token(&self, id: u32) -> Option<String> {
        self.tokenizer.id_to_token(id)
    }
}

impl SttTokenizer for BpeTokenizer {
    fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, AntennaError>
    where
        Self: Sized,
    {
        BpeTokenizer::from_file(path)
    }

    fn encode(&self, text: &str) -> Result<Vec<u32>, AntennaError> {
        let encoding = self
            .tokenizer
            .encode(text, false)
            .map_err(|e| AntennaError::ModelError(format!("Encoding failed: {}", e)))?;

        Ok(encoding.get_ids().to_vec())
    }

    fn decode(&self, tokens: &[u32], skip_special: bool) -> Result<String, AntennaError> {
        let tokens_to_decode = if skip_special {
            tokens
                .iter()
                .filter(|&&t| !self.is_special_token(t))
                .copied()
                .collect::<Vec<_>>()
        } else {
            tokens.to_vec()
        };

        self.tokenizer
            .decode(&tokens_to_decode, skip_special)
            .map_err(|e| AntennaError::ModelError(format!("Decoding failed: {}", e)))
    }

    fn vocab_size(&self) -> usize {
        self.tokenizer.get_vocab_size(true)
    }

    fn is_special_token(&self, token: u32) -> bool {
        if self.special_token_ids.contains(&token) {
            return true;
        }
        if Some(token) == self.bos_token_id {
            return true;
        }
        if token == self.eos_token_id {
            return true;
        }
        if Some(token) == self.pad_token_id {
            return true;
        }
        false
    }

    fn eos_token(&self) -> u32 {
        self.eos_token_id
    }

    fn bos_token(&self) -> Option<u32> {
        self.bos_token_id
    }

    fn pad_token(&self) -> Option<u32> {
        self.pad_token_id
    }

    fn unk_token(&self) -> Option<u32> {
        self.unk_token_id
    }

    fn supported_languages(&self) -> Vec<LanguageInfo> {
        // BPE tokenizers don't inherently have language info
        // Subclasses (like WhisperTokenizer) should override this
        vec![]
    }
}

#[cfg(test)]
mod tests {
    // Tests would require a tokenizer file
}
