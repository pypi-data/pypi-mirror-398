//! Whisper decoding strategies
//!
//! Implements beam search and greedy decoding for Whisper transcription.

use candle_core::{Device, Tensor};
use candle_transformers::models::whisper as m;

use crate::error::AntennaError;

/// Decoding configuration options
#[derive(Debug, Clone)]
pub struct DecodingOptions {
    /// Beam size for beam search (1 = greedy decoding)
    pub beam_size: usize,
    /// Patience factor for beam search early stopping
    pub patience: f32,
    /// Sampling temperature (0 = greedy)
    pub temperature: f32,
    /// Maximum number of tokens to generate
    pub max_tokens: usize,
}

impl Default for DecodingOptions {
    fn default() -> Self {
        Self {
            beam_size: 5,
            patience: 1.0,
            temperature: 0.0,
            max_tokens: 448,
        }
    }
}

/// A single beam hypothesis
#[derive(Debug, Clone)]
struct Beam {
    tokens: Vec<u32>,
    score: f32,
    finished: bool,
}

impl Beam {
    fn new(tokens: Vec<u32>) -> Self {
        Self {
            tokens,
            score: 0.0,
            finished: false,
        }
    }

    fn with_token(&self, token: u32, log_prob: f32) -> Self {
        let mut new_tokens = self.tokens.clone();
        new_tokens.push(token);
        Self {
            tokens: new_tokens,
            score: self.score + log_prob,
            finished: self.finished,
        }
    }

    fn length_penalty(&self, alpha: f32) -> f32 {
        let length = self.tokens.len() as f32;
        ((5.0 + length) / 6.0).powf(alpha)
    }

    fn normalized_score(&self, alpha: f32) -> f32 {
        self.score / self.length_penalty(alpha)
    }
}

/// Greedy decoding - select the most likely token at each step
pub fn greedy_decode(
    model: &mut m::model::Whisper,
    encoder_output: &Tensor,
    initial_tokens: &[u32],
    options: &DecodingOptions,
    eot_token: u32,
    device: &Device,
) -> Result<Vec<u32>, AntennaError> {
    let mut tokens = initial_tokens.to_vec();

    // Calculate maximum tokens we can generate (accounting for initial prompt)
    // max_tokens is typically 448 (max_target_positions), but we need to reserve
    // space for the initial prompt tokens
    let max_total_tokens = options.max_tokens;
    let max_new_tokens = max_total_tokens.saturating_sub(initial_tokens.len());

    for _step in 0..max_new_tokens {
        // Ensure we don't exceed max sequence length
        if tokens.len() >= max_total_tokens {
            break;
        }

        // Create input tensor with all tokens (simple approach without KV caching)
        let input = Tensor::new(tokens.as_slice(), device)
            .map_err(|e| AntennaError::ModelError(format!("Failed to create input tensor: {}", e)))?
            .unsqueeze(0)
            .map_err(|e| AntennaError::ModelError(format!("Unsqueeze failed: {}", e)))?;

        // Forward pass through decoder (flush cache each time for correctness)
        let hidden_states = model
            .decoder
            .forward(&input, encoder_output, true)
            .map_err(|e| AntennaError::ModelError(format!("Decoder forward failed: {}", e)))?;

        // Project to vocabulary logits
        let logits = model
            .decoder
            .final_linear(&hidden_states)
            .map_err(|e| AntennaError::ModelError(format!("Final linear failed: {}", e)))?;

        // Get logits for the last position
        let seq_len = tokens.len();
        let last_logits = logits
            .squeeze(0)
            .map_err(|e| AntennaError::ModelError(format!("Squeeze failed: {}", e)))?
            .get(seq_len - 1)
            .map_err(|e| AntennaError::ModelError(format!("Get last position failed: {}", e)))?;

        // Apply temperature
        let scaled_logits = if options.temperature > 0.0 && options.temperature != 1.0 {
            (last_logits / options.temperature as f64)
                .map_err(|e| AntennaError::ModelError(format!("Temperature scaling failed: {}", e)))?
        } else {
            last_logits
        };

        // Get argmax
        let next_token = scaled_logits
            .argmax(0)
            .map_err(|e| AntennaError::ModelError(format!("Argmax failed: {}", e)))?
            .to_scalar::<u32>()
            .map_err(|e| AntennaError::ModelError(format!("To scalar failed: {}", e)))?;

        tokens.push(next_token);

        // Check for end of transcript
        if next_token == eot_token {
            break;
        }
    }

    // Remove initial prompt tokens
    let output_tokens = tokens[initial_tokens.len()..].to_vec();
    Ok(output_tokens)
}

/// Beam search decoding - maintain multiple hypotheses
/// Note: Beam search doesn't use KV caching (each beam needs independent forward pass)
/// so we limit total sequence length to max_tokens
pub fn beam_search_decode(
    model: &mut m::model::Whisper,
    encoder_output: &Tensor,
    initial_tokens: &[u32],
    options: &DecodingOptions,
    eot_token: u32,
    device: &Device,
) -> Result<Vec<u32>, AntennaError> {
    let beam_size = options.beam_size;
    let length_penalty_alpha = 0.6;

    // Calculate maximum tokens we can generate (accounting for initial prompt)
    let max_total_tokens = options.max_tokens;
    let max_new_tokens = max_total_tokens.saturating_sub(initial_tokens.len());

    // Initialize beams
    let mut beams = vec![Beam::new(initial_tokens.to_vec())];
    let mut finished_beams: Vec<Beam> = Vec::new();

    for _step in 0..max_new_tokens {
        if beams.is_empty() {
            break;
        }

        let mut all_candidates: Vec<Beam> = Vec::new();

        for beam in &beams {
            if beam.finished {
                finished_beams.push(beam.clone());
                continue;
            }

            // Check if beam has reached max length
            if beam.tokens.len() >= max_total_tokens {
                let mut finished_beam = beam.clone();
                finished_beam.finished = true;
                finished_beams.push(finished_beam);
                continue;
            }

            // Create input tensor for this beam
            let input = Tensor::new(beam.tokens.as_slice(), device)
                .map_err(|e| AntennaError::ModelError(format!("Failed to create input tensor: {}", e)))?
                .unsqueeze(0)
                .map_err(|e| AntennaError::ModelError(format!("Unsqueeze failed: {}", e)))?;

            // Forward pass (flush cache since each beam is independent)
            let hidden_states = model
                .decoder
                .forward(&input, encoder_output, true)
                .map_err(|e| AntennaError::ModelError(format!("Decoder forward failed: {}", e)))?;

            // Project to vocabulary logits
            let logits = model
                .decoder
                .final_linear(&hidden_states)
                .map_err(|e| AntennaError::ModelError(format!("Final linear failed: {}", e)))?;

            // Get logits for last position
            let seq_len = beam.tokens.len();
            let last_logits = logits
                .squeeze(0)
                .map_err(|e| AntennaError::ModelError(format!("Squeeze failed: {}", e)))?
                .get(seq_len - 1)
                .map_err(|e| AntennaError::ModelError(format!("Get failed: {}", e)))?;

            // Apply temperature
            let scaled_logits = if options.temperature > 0.0 && options.temperature != 1.0 {
                (last_logits.clone() / options.temperature as f64)
                    .map_err(|e| AntennaError::ModelError(format!("Temperature scaling failed: {}", e)))?
            } else {
                last_logits.clone()
            };

            // Convert to log probabilities
            let log_probs = candle_nn::ops::log_softmax(&scaled_logits, 0)
                .map_err(|e| AntennaError::ModelError(format!("Log softmax failed: {}", e)))?;

            // Get top-k tokens
            let log_probs_vec: Vec<f32> = log_probs
                .to_vec1()
                .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

            // Find top beam_size tokens
            let mut indexed: Vec<(usize, f32)> = log_probs_vec.iter().enumerate().map(|(i, &p)| (i, p)).collect();
            indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

            for (token_idx, log_prob) in indexed.iter().take(beam_size * 2) {
                let token = *token_idx as u32;
                let mut new_beam = beam.with_token(token, *log_prob);

                if token == eot_token {
                    new_beam.finished = true;
                    finished_beams.push(new_beam);
                } else {
                    all_candidates.push(new_beam);
                }
            }
        }

        // Select top beams
        all_candidates.sort_by(|a, b| {
            b.normalized_score(length_penalty_alpha)
                .partial_cmp(&a.normalized_score(length_penalty_alpha))
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        beams = all_candidates.into_iter().take(beam_size).collect();

        // Early stopping with patience
        if !finished_beams.is_empty() {
            let best_finished_score = finished_beams
                .iter()
                .map(|b| b.normalized_score(length_penalty_alpha))
                .fold(f32::NEG_INFINITY, f32::max);

            let best_active_score = beams
                .iter()
                .map(|b| b.normalized_score(length_penalty_alpha))
                .fold(f32::NEG_INFINITY, f32::max);

            if best_finished_score >= best_active_score * options.patience {
                break;
            }
        }
    }

    // Get best finished beam, or best active beam if none finished
    let all_beams: Vec<&Beam> = finished_beams
        .iter()
        .chain(beams.iter())
        .collect();

    let best_beam = all_beams
        .iter()
        .max_by(|a, b| {
            a.normalized_score(length_penalty_alpha)
                .partial_cmp(&b.normalized_score(length_penalty_alpha))
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .ok_or_else(|| AntennaError::ModelError("No beams found".to_string()))?;

    // Return tokens after initial prompt
    let output_tokens = best_beam.tokens[initial_tokens.len()..].to_vec();
    Ok(output_tokens)
}

/// Sample from probability distribution with temperature
pub fn sample_with_temperature(
    logits: &Tensor,
    temperature: f32,
    _device: &Device,
) -> Result<u32, AntennaError> {
    if temperature == 0.0 {
        // Greedy
        return logits
            .argmax(0)
            .map_err(|e| AntennaError::ModelError(format!("Argmax failed: {}", e)))?
            .to_scalar::<u32>()
            .map_err(|e| AntennaError::ModelError(format!("To scalar failed: {}", e)));
    }

    // Apply temperature
    let scaled = (logits.clone() / temperature as f64)
        .map_err(|e| AntennaError::ModelError(format!("Temperature scaling failed: {}", e)))?;

    // Convert to probabilities
    let probs = candle_nn::ops::softmax(&scaled, 0)
        .map_err(|e| AntennaError::ModelError(format!("Softmax failed: {}", e)))?;

    let probs_vec: Vec<f32> = probs
        .to_vec1()
        .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

    // Sample from distribution
    let random: f32 = rand_sample();
    let mut cumsum = 0.0f32;

    for (idx, &prob) in probs_vec.iter().enumerate() {
        cumsum += prob;
        if cumsum >= random {
            return Ok(idx as u32);
        }
    }

    // Fallback to last token
    Ok((probs_vec.len() - 1) as u32)
}

/// Simple random number generator for sampling
fn rand_sample() -> f32 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let seed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);

    // Simple LCG
    let a: u128 = 1103515245;
    let c: u128 = 12345;
    let m: u128 = 2u128.pow(31);

    let value = (a.wrapping_mul(seed).wrapping_add(c)) % m;
    (value as f32) / (m as f32)
}

/// Suppress specific tokens during decoding
pub fn suppress_tokens(
    logits: &Tensor,
    suppress_token_ids: &[u32],
) -> Result<Tensor, AntennaError> {
    let mut logits_vec: Vec<f32> = logits
        .to_vec1()
        .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

    for &token_id in suppress_token_ids {
        if (token_id as usize) < logits_vec.len() {
            logits_vec[token_id as usize] = f32::NEG_INFINITY;
        }
    }

    Tensor::from_vec(logits_vec, logits.shape(), logits.device())
        .map_err(|e| AntennaError::ModelError(format!("Tensor creation failed: {}", e)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_beam_scoring() {
        let beam = Beam::new(vec![1, 2, 3]);
        let beam = beam.with_token(4, -1.0);
        let beam = beam.with_token(5, -0.5);

        assert_eq!(beam.tokens.len(), 5);
        assert!((beam.score - (-1.5)).abs() < 1e-6);
    }

    #[test]
    fn test_beam_length_penalty() {
        let beam = Beam::new(vec![1, 2, 3, 4, 5]);
        let penalty = beam.length_penalty(0.6);
        assert!(penalty > 1.0);
    }

    #[test]
    fn test_random_sample_range() {
        for _ in 0..100 {
            let r = rand_sample();
            assert!(r >= 0.0 && r < 1.0);
        }
    }
}
