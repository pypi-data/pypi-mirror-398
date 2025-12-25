//! Greedy decoding
//!
//! Simple argmax decoding that selects the most likely token at each step.
//! Fast but may not produce optimal sequences.

use candle_core::{Device, Tensor};

use crate::error::AntennaError;

/// Options for greedy decoding
#[derive(Debug, Clone)]
pub struct GreedyOptions {
    /// Maximum number of tokens to generate
    pub max_tokens: usize,
    /// Temperature for sampling (0.0 = pure greedy)
    pub temperature: f32,
    /// Token IDs to suppress (never generate)
    pub suppress_tokens: Vec<u32>,
}

impl Default for GreedyOptions {
    fn default() -> Self {
        Self {
            max_tokens: 448,
            temperature: 0.0,
            suppress_tokens: vec![],
        }
    }
}

/// Result of greedy decoding
#[derive(Debug, Clone)]
pub struct GreedyResult {
    /// Generated token IDs
    pub tokens: Vec<u32>,
    /// Log probabilities for each token
    pub log_probs: Vec<f32>,
}

impl GreedyResult {
    /// Get the total log probability (sum of log probs)
    pub fn total_log_prob(&self) -> f32 {
        self.log_probs.iter().sum()
    }
}

/// Greedy decoder for autoregressive models
///
/// This decoder works with any model that provides a `forward` function
/// that takes tokens and returns logits.
pub struct GreedyDecoder {
    options: GreedyOptions,
    eos_token: u32,
}

impl GreedyDecoder {
    /// Create a new greedy decoder
    pub fn new(eos_token: u32) -> Self {
        Self {
            options: GreedyOptions::default(),
            eos_token,
        }
    }

    /// Create with custom options
    pub fn with_options(eos_token: u32, options: GreedyOptions) -> Self {
        Self { options, eos_token }
    }

    /// Set the maximum tokens to generate
    pub fn max_tokens(mut self, max: usize) -> Self {
        self.options.max_tokens = max;
        self
    }

    /// Set the temperature
    pub fn temperature(mut self, temp: f32) -> Self {
        self.options.temperature = temp;
        self
    }

    /// Decode using a model forward function
    ///
    /// # Arguments
    /// * `initial_tokens` - Starting tokens (e.g., BOS, language, task tokens)
    /// * `forward_fn` - Function that takes tokens and returns logits [vocab_size]
    /// * `device` - Device for tensor operations
    ///
    /// # Returns
    /// Generated tokens (not including initial tokens)
    pub fn decode<F>(
        &self,
        initial_tokens: &[u32],
        mut forward_fn: F,
        device: &Device,
    ) -> Result<GreedyResult, AntennaError>
    where
        F: FnMut(&[u32]) -> Result<Tensor, AntennaError>,
    {
        let mut tokens = initial_tokens.to_vec();
        let mut log_probs = Vec::new();

        let max_total = self.options.max_tokens;
        let max_new = max_total.saturating_sub(initial_tokens.len());

        for _ in 0..max_new {
            if tokens.len() >= max_total {
                break;
            }

            // Get logits for current sequence
            let logits = forward_fn(&tokens)?;

            // Apply temperature
            let scaled_logits = if self.options.temperature > 0.0 && self.options.temperature != 1.0
            {
                (&logits / self.options.temperature as f64).map_err(|e| {
                    AntennaError::ModelError(format!("Temperature scaling failed: {}", e))
                })?
            } else {
                logits
            };

            // Suppress tokens if configured
            let final_logits = if !self.options.suppress_tokens.is_empty() {
                self.suppress_tokens(&scaled_logits, device)?
            } else {
                scaled_logits
            };

            // Get softmax probabilities for log prob calculation
            let probs = candle_nn::ops::softmax(&final_logits, 0).map_err(|e| {
                AntennaError::ModelError(format!("Softmax failed: {}", e))
            })?;

            // Get argmax
            let next_token = final_logits
                .argmax(0)
                .map_err(|e| AntennaError::ModelError(format!("Argmax failed: {}", e)))?
                .to_scalar::<u32>()
                .map_err(|e| AntennaError::ModelError(format!("To scalar failed: {}", e)))?;

            // Get log probability of selected token
            let token_prob = probs
                .get(next_token as usize)
                .map_err(|e| AntennaError::ModelError(format!("Get prob failed: {}", e)))?
                .to_scalar::<f32>()
                .map_err(|e| AntennaError::ModelError(format!("To scalar failed: {}", e)))?;

            log_probs.push(token_prob.ln());
            tokens.push(next_token);

            // Check for end of sequence
            if next_token == self.eos_token {
                break;
            }
        }

        // Remove initial tokens from result
        let output_tokens = tokens[initial_tokens.len()..].to_vec();

        Ok(GreedyResult {
            tokens: output_tokens,
            log_probs,
        })
    }

    /// Suppress specified tokens by setting their logits to -inf
    fn suppress_tokens(&self, logits: &Tensor, device: &Device) -> Result<Tensor, AntennaError> {
        let vocab_size = logits.dims()[0];
        let mut mask = vec![0.0f32; vocab_size];

        for &token in &self.options.suppress_tokens {
            if (token as usize) < vocab_size {
                mask[token as usize] = f32::NEG_INFINITY;
            }
        }

        let mask_tensor = Tensor::from_vec(mask, vocab_size, device)
            .map_err(|e| AntennaError::ModelError(format!("Create mask failed: {}", e)))?;

        (logits + &mask_tensor)
            .map_err(|e| AntennaError::ModelError(format!("Apply mask failed: {}", e)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_greedy_options_default() {
        let opts = GreedyOptions::default();
        assert_eq!(opts.max_tokens, 448);
        assert_eq!(opts.temperature, 0.0);
    }

    #[test]
    fn test_greedy_result() {
        let result = GreedyResult {
            tokens: vec![1, 2, 3],
            log_probs: vec![-0.1, -0.2, -0.3],
        };
        assert!((result.total_log_prob() - (-0.6)).abs() < 0.001);
    }
}
