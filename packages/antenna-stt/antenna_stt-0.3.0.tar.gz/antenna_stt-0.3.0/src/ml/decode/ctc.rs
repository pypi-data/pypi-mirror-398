//! CTC (Connectionist Temporal Classification) decoding
//!
//! Used for encoder-only models like Wav2Vec2 and Conformer-CTC.
//! CTC handles alignment between input frames and output tokens
//! by introducing a blank token and collapsing repeated characters.

use candle_core::{Device, Tensor};

use crate::error::AntennaError;

/// Options for CTC decoding
#[derive(Debug, Clone)]
pub struct CtcOptions {
    /// Blank token ID (typically 0)
    pub blank_id: u32,
    /// Whether to merge repeated tokens (standard CTC behavior)
    pub merge_repeated: bool,
    /// Beam width for CTC beam search (1 = greedy)
    pub beam_width: usize,
    /// Minimum log probability to consider a token
    pub log_prob_threshold: f32,
}

impl Default for CtcOptions {
    fn default() -> Self {
        Self {
            blank_id: 0,
            merge_repeated: true,
            beam_width: 1,
            log_prob_threshold: f32::NEG_INFINITY,
        }
    }
}

/// Result of CTC decoding
#[derive(Debug, Clone)]
pub struct CtcResult {
    /// Decoded token IDs (after collapsing blanks and repeats)
    pub tokens: Vec<u32>,
    /// Frame-level alignments (which frame each token came from)
    pub alignments: Vec<usize>,
    /// Confidence scores per token
    pub confidences: Vec<f32>,
}

impl CtcResult {
    /// Get average confidence
    pub fn average_confidence(&self) -> f32 {
        if self.confidences.is_empty() {
            0.0
        } else {
            self.confidences.iter().sum::<f32>() / self.confidences.len() as f32
        }
    }
}

/// CTC decoder for encoder-only models
///
/// Handles frame-level predictions from models like Wav2Vec2 and Conformer,
/// collapsing repeated tokens and removing blanks to produce the final text.
pub struct CtcDecoder {
    options: CtcOptions,
}

impl CtcDecoder {
    /// Create a new CTC decoder with default options
    pub fn new() -> Self {
        Self {
            options: CtcOptions::default(),
        }
    }

    /// Create with custom options
    pub fn with_options(options: CtcOptions) -> Self {
        Self { options }
    }

    /// Set the blank token ID
    pub fn blank_id(mut self, id: u32) -> Self {
        self.options.blank_id = id;
        self
    }

    /// Set whether to merge repeated tokens
    pub fn merge_repeated(mut self, merge: bool) -> Self {
        self.options.merge_repeated = merge;
        self
    }

    /// Set beam width (1 = greedy)
    pub fn beam_width(mut self, width: usize) -> Self {
        self.options.beam_width = width;
        self
    }

    /// Decode encoder output using CTC greedy decoding
    ///
    /// # Arguments
    /// * `logits` - Frame-level logits [time_steps, vocab_size]
    /// * `device` - Device (unused but kept for API consistency)
    ///
    /// # Returns
    /// Decoded tokens with alignments
    pub fn decode(&self, logits: &Tensor, _device: &Device) -> Result<CtcResult, AntennaError> {
        if self.options.beam_width > 1 {
            self.decode_beam(logits)
        } else {
            self.decode_greedy(logits)
        }
    }

    /// Greedy CTC decoding
    fn decode_greedy(&self, logits: &Tensor) -> Result<CtcResult, AntennaError> {
        let dims = logits.dims();
        if dims.len() != 2 {
            return Err(AntennaError::ModelError(format!(
                "Expected 2D logits [time, vocab], got {:?}",
                dims
            )));
        }

        let time_steps = dims[0];
        let _vocab_size = dims[1];

        let mut tokens = Vec::new();
        let mut alignments = Vec::new();
        let mut confidences = Vec::new();
        let mut prev_token: Option<u32> = None;

        for t in 0..time_steps {
            // Get logits for this frame
            let frame_logits = logits
                .get(t)
                .map_err(|e| AntennaError::ModelError(format!("Get frame failed: {}", e)))?;

            // Get softmax probabilities
            let probs = candle_nn::ops::softmax(&frame_logits, 0)
                .map_err(|e| AntennaError::ModelError(format!("Softmax failed: {}", e)))?;

            // Get argmax
            let best_token = frame_logits
                .argmax(0)
                .map_err(|e| AntennaError::ModelError(format!("Argmax failed: {}", e)))?
                .to_scalar::<u32>()
                .map_err(|e| AntennaError::ModelError(format!("To scalar failed: {}", e)))?;

            // Get confidence for best token
            let confidence = probs
                .get(best_token as usize)
                .map_err(|e| AntennaError::ModelError(format!("Get prob failed: {}", e)))?
                .to_scalar::<f32>()
                .map_err(|e| AntennaError::ModelError(format!("To scalar failed: {}", e)))?;

            // Skip blanks
            if best_token == self.options.blank_id {
                prev_token = Some(best_token);
                continue;
            }

            // Skip repeated tokens if configured
            if self.options.merge_repeated && Some(best_token) == prev_token {
                continue;
            }

            // Check confidence threshold
            if confidence.ln() < self.options.log_prob_threshold {
                prev_token = Some(best_token);
                continue;
            }

            tokens.push(best_token);
            alignments.push(t);
            confidences.push(confidence);
            prev_token = Some(best_token);
        }

        Ok(CtcResult {
            tokens,
            alignments,
            confidences,
        })
    }

    /// Beam search CTC decoding (prefix beam search)
    fn decode_beam(&self, logits: &Tensor) -> Result<CtcResult, AntennaError> {
        // For simplicity, we implement a basic prefix beam search
        // Full implementation would be more complex

        let dims = logits.dims();
        if dims.len() != 2 {
            return Err(AntennaError::ModelError(format!(
                "Expected 2D logits [time, vocab], got {:?}",
                dims
            )));
        }

        let time_steps = dims[0];
        let vocab_size = dims[1];
        let beam_width = self.options.beam_width;
        let blank_id = self.options.blank_id as usize;

        // Beam: (prefix, p_blank, p_non_blank)
        // p_blank: probability of prefix ending in blank
        // p_non_blank: probability of prefix not ending in blank
        type BeamState = (Vec<u32>, f32, f32);

        let mut beams: Vec<BeamState> = vec![(vec![], 1.0, 0.0)];

        for t in 0..time_steps {
            let frame_logits = logits
                .get(t)
                .map_err(|e| AntennaError::ModelError(format!("Get frame failed: {}", e)))?;

            let probs = candle_nn::ops::softmax(&frame_logits, 0)
                .map_err(|e| AntennaError::ModelError(format!("Softmax failed: {}", e)))?;

            let prob_vec: Vec<f32> = probs
                .to_vec1()
                .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

            let mut new_beams: std::collections::HashMap<Vec<u32>, (f32, f32)> =
                std::collections::HashMap::new();

            for (prefix, p_blank, p_non_blank) in &beams {
                let p_total = p_blank + p_non_blank;

                // Extend with blank
                let blank_prob = prob_vec[blank_id];
                let entry = new_beams.entry(prefix.clone()).or_insert((0.0, 0.0));
                entry.0 += p_total * blank_prob;

                // Extend with each non-blank token
                for c in 0..vocab_size {
                    if c == blank_id {
                        continue;
                    }

                    let c_prob = prob_vec[c];
                    let c_u32 = c as u32;

                    let last_token = prefix.last().copied();

                    if Some(c_u32) == last_token {
                        // Same as last character: only extend if we had a blank
                        let mut new_prefix = prefix.clone();
                        new_prefix.push(c_u32);
                        let entry = new_beams.entry(new_prefix).or_insert((0.0, 0.0));
                        entry.1 += p_blank * c_prob;

                        // Also keep original prefix (repeated char absorbed)
                        let entry = new_beams.entry(prefix.clone()).or_insert((0.0, 0.0));
                        entry.1 += p_non_blank * c_prob;
                    } else {
                        // Different character: extend with new token
                        let mut new_prefix = prefix.clone();
                        new_prefix.push(c_u32);
                        let entry = new_beams.entry(new_prefix).or_insert((0.0, 0.0));
                        entry.1 += p_total * c_prob;
                    }
                }
            }

            // Prune to top beams
            let mut beam_vec: Vec<BeamState> = new_beams
                .into_iter()
                .map(|(prefix, (p_b, p_nb))| (prefix, p_b, p_nb))
                .collect();

            beam_vec.sort_by(|a, b| {
                let score_a = a.1 + a.2;
                let score_b = b.1 + b.2;
                score_b
                    .partial_cmp(&score_a)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });

            beams = beam_vec.into_iter().take(beam_width).collect();
        }

        // Get best beam
        let (best_prefix, _, _) = beams
            .into_iter()
            .max_by(|a, b| {
                let score_a = a.1 + a.2;
                let score_b = b.1 + b.2;
                score_a
                    .partial_cmp(&score_b)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .unwrap_or((vec![], 0.0, 0.0));

        Ok(CtcResult {
            tokens: best_prefix,
            alignments: vec![], // Beam search doesn't preserve alignments easily
            confidences: vec![],
        })
    }

    /// Collapse CTC output (remove blanks and repeated tokens)
    ///
    /// This is a standalone function that can be used without full decoding.
    pub fn collapse(&self, tokens: &[u32]) -> Vec<u32> {
        let mut result = Vec::new();
        let mut prev: Option<u32> = None;

        for &token in tokens {
            if token == self.options.blank_id {
                prev = Some(token);
                continue;
            }

            if self.options.merge_repeated && Some(token) == prev {
                continue;
            }

            result.push(token);
            prev = Some(token);
        }

        result
    }
}

impl Default for CtcDecoder {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ctc_options_default() {
        let opts = CtcOptions::default();
        assert_eq!(opts.blank_id, 0);
        assert!(opts.merge_repeated);
        assert_eq!(opts.beam_width, 1);
    }

    #[test]
    fn test_ctc_collapse() {
        let decoder = CtcDecoder::new().blank_id(0);

        // Input: blank, a, a, blank, b, b, b, blank, c
        // Tokens: 0, 1, 1, 0, 2, 2, 2, 0, 3
        let tokens = vec![0, 1, 1, 0, 2, 2, 2, 0, 3];
        let collapsed = decoder.collapse(&tokens);

        // After collapse: a, b, c
        assert_eq!(collapsed, vec![1, 2, 3]);
    }

    #[test]
    fn test_ctc_collapse_no_merge() {
        let decoder = CtcDecoder::new().blank_id(0).merge_repeated(false);

        let tokens = vec![0, 1, 1, 0, 2];
        let collapsed = decoder.collapse(&tokens);

        // Without merge: a, a, b
        assert_eq!(collapsed, vec![1, 1, 2]);
    }

    #[test]
    fn test_ctc_result() {
        let result = CtcResult {
            tokens: vec![1, 2, 3],
            alignments: vec![0, 5, 10],
            confidences: vec![0.9, 0.8, 0.95],
        };

        let avg = result.average_confidence();
        assert!((avg - 0.883).abs() < 0.01);
    }
}
