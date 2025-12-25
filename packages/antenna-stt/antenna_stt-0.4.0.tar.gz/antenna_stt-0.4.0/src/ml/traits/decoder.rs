//! Decoder traits for sequence generation
//!
//! Different models use different decoding strategies:
//! - Autoregressive: Beam search, greedy (Whisper, Canary)
//! - CTC: Connectionist Temporal Classification (Wav2Vec2, Conformer-CTC)
//! - Hybrid: Both CTC and attention (some Conformer variants)

use candle_core::{Device, Tensor};

use crate::error::AntennaError;

/// Decoding strategy used by the model
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DecodingStrategy {
    /// Autoregressive decoding with attention
    /// Generates tokens one at a time, attending to encoder output
    Autoregressive,
    /// Connectionist Temporal Classification
    /// Produces frame-level predictions, then collapses repeats
    Ctc,
    /// Hybrid approach using both CTC and attention
    Hybrid,
}

/// Common options for all decoding strategies
#[derive(Debug, Clone)]
pub struct CommonDecodingOptions {
    /// Temperature for sampling (0.0 = greedy/deterministic)
    pub temperature: f32,
    /// Maximum output sequence length
    pub max_length: usize,
    /// Minimum output sequence length
    pub min_length: usize,
    /// Whether to suppress blank/padding tokens in output
    pub suppress_blank: bool,
}

impl Default for CommonDecodingOptions {
    fn default() -> Self {
        Self {
            temperature: 0.0,
            max_length: 448,
            min_length: 0,
            suppress_blank: true,
        }
    }
}

/// Options specific to beam search decoding
#[derive(Debug, Clone)]
pub struct BeamSearchOptions {
    /// Number of beams to maintain
    pub beam_size: usize,
    /// Length penalty (alpha): positive values favor longer sequences
    pub length_penalty: f32,
    /// Early stopping when all beams reach EOS
    pub early_stopping: bool,
    /// Number of best sequences to return
    pub num_return_sequences: usize,
}

impl Default for BeamSearchOptions {
    fn default() -> Self {
        Self {
            beam_size: 5,
            length_penalty: 1.0,
            early_stopping: true,
            num_return_sequences: 1,
        }
    }
}

/// Options specific to CTC decoding
#[derive(Debug, Clone)]
pub struct CtcDecodingOptions {
    /// Blank token ID (typically 0)
    pub blank_id: u32,
    /// Whether to merge repeated tokens
    pub merge_repeated: bool,
    /// Beam width for CTC beam search (1 = greedy)
    pub beam_width: usize,
}

impl Default for CtcDecodingOptions {
    fn default() -> Self {
        Self {
            blank_id: 0,
            merge_repeated: true,
            beam_width: 1,
        }
    }
}

/// Result from decoding
#[derive(Debug, Clone)]
pub struct DecodingResult {
    /// Decoded token IDs
    pub tokens: Vec<u32>,
    /// Log probability of the sequence (if available)
    pub score: Option<f32>,
    /// Per-token timestamps (if available)
    pub timestamps: Option<Vec<(f32, f32)>>,
}

impl DecodingResult {
    /// Create a simple result with just tokens
    pub fn from_tokens(tokens: Vec<u32>) -> Self {
        Self {
            tokens,
            score: None,
            timestamps: None,
        }
    }

    /// Add a score to the result
    pub fn with_score(mut self, score: f32) -> Self {
        self.score = Some(score);
        self
    }
}

/// Trait for model decoders
///
/// This trait abstracts the decoding step, allowing different strategies
/// to be used with different model architectures.
///
/// # Implementations
///
/// - **Autoregressive**: For encoder-decoder models (Whisper, Canary)
///   - Greedy: Always pick highest probability token
///   - Beam search: Maintain multiple hypotheses
///
/// - **CTC**: For encoder-only models (Wav2Vec2, Conformer-CTC)
///   - Greedy: Collapse repeated tokens, remove blanks
///   - Beam search: Search over possible alignments
pub trait Decoder: Send + Sync {
    /// The type of model-specific decoding options
    type Options: Clone + Default;

    /// Get the decoding strategy this decoder uses
    fn strategy(&self) -> DecodingStrategy;

    /// Decode encoder output to token IDs
    ///
    /// # Arguments
    /// * `encoder_output` - Hidden states from encoder [batch, seq_len, hidden_dim]
    /// * `options` - Model-specific decoding options
    /// * `device` - Device for computation
    ///
    /// # Returns
    /// Decoded token sequence with optional metadata
    fn decode(
        &mut self,
        encoder_output: &Tensor,
        options: &Self::Options,
        device: &Device,
    ) -> Result<DecodingResult, AntennaError>;

    /// Decode with common options applied
    fn decode_with_common(
        &mut self,
        encoder_output: &Tensor,
        options: &Self::Options,
        common: &CommonDecodingOptions,
        device: &Device,
    ) -> Result<DecodingResult, AntennaError> {
        // Default implementation ignores common options
        // Specific decoders should override if they support these options
        let _ = common;
        self.decode(encoder_output, options, device)
    }

    /// Check if this decoder supports timestamps
    fn supports_timestamps(&self) -> bool {
        false
    }
}

/// Marker trait for autoregressive decoders
pub trait AutoregressiveDecoder: Decoder {
    /// Get the end-of-sequence token ID
    fn eos_token(&self) -> u32;

    /// Get the beginning-of-sequence token ID
    fn bos_token(&self) -> u32;

    /// Get initial tokens to start decoding (language, task tokens, etc.)
    fn initial_tokens(&self) -> Vec<u32> {
        vec![self.bos_token()]
    }
}

/// Marker trait for CTC decoders
pub trait CtcDecoder: Decoder {
    /// Get the blank token ID
    fn blank_token(&self) -> u32;

    /// Collapse CTC output (remove blanks and repeated tokens)
    fn collapse_ctc(&self, tokens: &[u32]) -> Vec<u32> {
        let blank = self.blank_token();
        let mut result = Vec::new();
        let mut prev_token = None;

        for &token in tokens {
            if token != blank && Some(token) != prev_token {
                result.push(token);
            }
            prev_token = Some(token);
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decoding_result() {
        let result = DecodingResult::from_tokens(vec![1, 2, 3]).with_score(-0.5);
        assert_eq!(result.tokens, vec![1, 2, 3]);
        assert_eq!(result.score, Some(-0.5));
    }

    #[test]
    fn test_beam_search_options() {
        let opts = BeamSearchOptions::default();
        assert_eq!(opts.beam_size, 5);
        assert!(opts.early_stopping);
    }

    #[test]
    fn test_ctc_options() {
        let opts = CtcDecodingOptions::default();
        assert_eq!(opts.blank_id, 0);
        assert!(opts.merge_repeated);
    }
}
