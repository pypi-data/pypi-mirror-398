//! Beam search decoding
//!
//! Maintains multiple hypotheses to find better overall sequences.
//! Higher quality than greedy but slower.

use candle_core::{Device, Tensor};

use crate::error::AntennaError;

/// Options for beam search decoding
#[derive(Debug, Clone)]
pub struct BeamSearchOptions {
    /// Number of beams to maintain
    pub beam_size: usize,
    /// Maximum number of tokens to generate
    pub max_tokens: usize,
    /// Length penalty alpha (positive = favor longer, negative = favor shorter)
    pub length_penalty: f32,
    /// Temperature for sampling
    pub temperature: f32,
    /// Early stopping when best beam is finished
    pub early_stopping: bool,
    /// Patience factor for early stopping
    pub patience: f32,
    /// Token IDs to suppress
    pub suppress_tokens: Vec<u32>,
}

impl Default for BeamSearchOptions {
    fn default() -> Self {
        Self {
            beam_size: 5,
            max_tokens: 448,
            length_penalty: 1.0,
            temperature: 0.0,
            early_stopping: true,
            patience: 1.0,
            suppress_tokens: vec![],
        }
    }
}

/// A single beam hypothesis
#[derive(Debug, Clone)]
pub struct Beam {
    /// Token sequence
    pub tokens: Vec<u32>,
    /// Cumulative log probability
    pub score: f32,
    /// Whether this beam has finished (hit EOS)
    pub finished: bool,
}

impl Beam {
    /// Create a new beam with initial tokens
    pub fn new(tokens: Vec<u32>) -> Self {
        Self {
            tokens,
            score: 0.0,
            finished: false,
        }
    }

    /// Extend beam with a new token
    pub fn extend(&self, token: u32, log_prob: f32, eos_token: u32) -> Self {
        let mut new_tokens = self.tokens.clone();
        new_tokens.push(token);
        Self {
            tokens: new_tokens,
            score: self.score + log_prob,
            finished: token == eos_token,
        }
    }

    /// Calculate length penalty
    fn length_penalty(&self, alpha: f32) -> f32 {
        let length = self.tokens.len() as f32;
        ((5.0 + length) / 6.0).powf(alpha)
    }

    /// Get normalized score with length penalty
    pub fn normalized_score(&self, alpha: f32) -> f32 {
        self.score / self.length_penalty(alpha)
    }
}

/// Result of beam search decoding
#[derive(Debug, Clone)]
pub struct BeamSearchResult {
    /// Best hypothesis tokens
    pub tokens: Vec<u32>,
    /// Score of best hypothesis
    pub score: f32,
    /// All beam hypotheses (sorted by score)
    pub all_beams: Vec<Beam>,
}

/// Beam search decoder for autoregressive models
pub struct BeamSearchDecoder {
    options: BeamSearchOptions,
    eos_token: u32,
}

impl BeamSearchDecoder {
    /// Create a new beam search decoder
    pub fn new(eos_token: u32) -> Self {
        Self {
            options: BeamSearchOptions::default(),
            eos_token,
        }
    }

    /// Create with custom options
    pub fn with_options(eos_token: u32, options: BeamSearchOptions) -> Self {
        Self { options, eos_token }
    }

    /// Set beam size
    pub fn beam_size(mut self, size: usize) -> Self {
        self.options.beam_size = size;
        self
    }

    /// Set length penalty
    pub fn length_penalty(mut self, alpha: f32) -> Self {
        self.options.length_penalty = alpha;
        self
    }

    /// Decode using a model forward function
    ///
    /// # Arguments
    /// * `initial_tokens` - Starting tokens
    /// * `forward_fn` - Function that takes tokens and returns logits [vocab_size]
    /// * `device` - Device for tensor operations
    ///
    /// # Returns
    /// Best beam and all hypotheses
    pub fn decode<F>(
        &self,
        initial_tokens: &[u32],
        mut forward_fn: F,
        device: &Device,
    ) -> Result<BeamSearchResult, AntennaError>
    where
        F: FnMut(&[u32]) -> Result<Tensor, AntennaError>,
    {
        let beam_size = self.options.beam_size;
        let max_tokens = self.options.max_tokens;
        let alpha = self.options.length_penalty;

        // Initialize with a single beam
        let mut beams = vec![Beam::new(initial_tokens.to_vec())];
        let mut finished_beams: Vec<Beam> = Vec::new();

        let max_new = max_tokens.saturating_sub(initial_tokens.len());

        for _step in 0..max_new {
            if beams.is_empty() {
                break;
            }

            // Early stopping check
            if self.options.early_stopping && !finished_beams.is_empty() {
                let best_finished = finished_beams
                    .iter()
                    .map(|b| b.normalized_score(alpha))
                    .fold(f32::NEG_INFINITY, f32::max);

                let best_active = beams
                    .iter()
                    .map(|b| b.normalized_score(alpha))
                    .fold(f32::NEG_INFINITY, f32::max);

                // If best finished beam is better than all active beams can possibly be
                if best_finished > best_active * self.options.patience {
                    break;
                }
            }

            let mut all_candidates: Vec<Beam> = Vec::new();

            // Expand each beam
            for beam in &beams {
                if beam.tokens.len() >= max_tokens {
                    finished_beams.push(beam.clone());
                    continue;
                }

                // Get logits for this beam
                let logits = forward_fn(&beam.tokens)?;

                // Apply temperature
                let scaled_logits =
                    if self.options.temperature > 0.0 && self.options.temperature != 1.0 {
                        (&logits / self.options.temperature as f64).map_err(|e| {
                            AntennaError::ModelError(format!("Temperature scaling failed: {}", e))
                        })?
                    } else {
                        logits
                    };

                // Get log softmax
                let log_probs = candle_nn::ops::log_softmax(&scaled_logits, 0).map_err(|e| {
                    AntennaError::ModelError(format!("Log softmax failed: {}", e))
                })?;

                // Get top-k tokens
                let (top_probs, top_indices) = self.top_k(&log_probs, beam_size * 2, device)?;

                // Create new candidates
                for i in 0..top_indices.len().min(beam_size * 2) {
                    let token = top_indices[i];
                    let log_prob = top_probs[i];

                    // Skip suppressed tokens
                    if self.options.suppress_tokens.contains(&token) {
                        continue;
                    }

                    let new_beam = beam.extend(token, log_prob, self.eos_token);

                    if new_beam.finished {
                        finished_beams.push(new_beam);
                    } else {
                        all_candidates.push(new_beam);
                    }
                }
            }

            // Keep top beam_size candidates
            all_candidates.sort_by(|a, b| {
                b.normalized_score(alpha)
                    .partial_cmp(&a.normalized_score(alpha))
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
            beams = all_candidates.into_iter().take(beam_size).collect();
        }

        // Add remaining active beams to finished
        finished_beams.extend(beams);

        // Sort all beams by normalized score
        finished_beams.sort_by(|a, b| {
            b.normalized_score(alpha)
                .partial_cmp(&a.normalized_score(alpha))
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        // Get best beam
        let best = finished_beams
            .first()
            .cloned()
            .unwrap_or_else(|| Beam::new(initial_tokens.to_vec()));

        // Remove initial tokens from result
        let output_tokens = if best.tokens.len() > initial_tokens.len() {
            best.tokens[initial_tokens.len()..].to_vec()
        } else {
            vec![]
        };

        Ok(BeamSearchResult {
            tokens: output_tokens,
            score: best.score,
            all_beams: finished_beams,
        })
    }

    /// Get top-k values and indices from a tensor
    fn top_k(
        &self,
        tensor: &Tensor,
        k: usize,
        _device: &Device,
    ) -> Result<(Vec<f32>, Vec<u32>), AntennaError> {
        let values: Vec<f32> = tensor
            .to_vec1()
            .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

        // Create (value, index) pairs and sort
        let mut indexed: Vec<(f32, u32)> = values
            .iter()
            .enumerate()
            .map(|(i, &v)| (v, i as u32))
            .collect();

        indexed.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

        let top: Vec<(f32, u32)> = indexed.into_iter().take(k).collect();

        let probs: Vec<f32> = top.iter().map(|(p, _)| *p).collect();
        let indices: Vec<u32> = top.iter().map(|(_, i)| *i).collect();

        Ok((probs, indices))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_beam_new() {
        let beam = Beam::new(vec![1, 2, 3]);
        assert_eq!(beam.tokens, vec![1, 2, 3]);
        assert_eq!(beam.score, 0.0);
        assert!(!beam.finished);
    }

    #[test]
    fn test_beam_extend() {
        let beam = Beam::new(vec![1, 2]);
        let extended = beam.extend(3, -0.5, 99);
        assert_eq!(extended.tokens, vec![1, 2, 3]);
        assert_eq!(extended.score, -0.5);
        assert!(!extended.finished);
    }

    #[test]
    fn test_beam_extend_eos() {
        let beam = Beam::new(vec![1, 2]);
        let extended = beam.extend(99, -0.3, 99);
        assert!(extended.finished);
    }

    #[test]
    fn test_beam_normalized_score() {
        let beam = Beam {
            tokens: vec![1, 2, 3, 4, 5],
            score: -5.0,
            finished: false,
        };
        // With length penalty alpha=1.0
        let normalized = beam.normalized_score(1.0);
        assert!(normalized < 0.0); // Should be negative (normalized negative score)
    }

    #[test]
    fn test_beam_search_options_default() {
        let opts = BeamSearchOptions::default();
        assert_eq!(opts.beam_size, 5);
        assert_eq!(opts.length_penalty, 1.0);
        assert!(opts.early_stopping);
    }
}
