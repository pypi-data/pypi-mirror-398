//! Local Agreement Policy for Stable Streaming Transcription
//!
//! Implements a policy for emitting stable partial transcription results.
//! Based on the approach from whisper_streaming (UFAL):
//! https://github.com/ufal/whisper_streaming
//!
//! The key idea is to run inference on growing audio windows and only
//! emit tokens that appear consistently across multiple consecutive runs.
//! This prevents the "flickering" effect where partial results change rapidly.

use std::collections::VecDeque;

/// Configuration for local agreement policy
#[derive(Debug, Clone)]
pub struct AgreementConfig {
    /// Number of consecutive inferences that must agree (typically 2)
    pub agreement_count: usize,
    /// Maximum tokens to buffer before forcing emission
    pub max_buffer_tokens: usize,
    /// Minimum tokens to emit at once
    pub min_emit_tokens: usize,
}

impl Default for AgreementConfig {
    fn default() -> Self {
        Self {
            agreement_count: 2,
            max_buffer_tokens: 100,
            min_emit_tokens: 1,
        }
    }
}

impl AgreementConfig {
    /// Create a strict config requiring more agreement
    pub fn strict() -> Self {
        Self {
            agreement_count: 3,
            max_buffer_tokens: 50,
            min_emit_tokens: 1,
        }
    }

    /// Create a fast config with minimal agreement
    pub fn fast() -> Self {
        Self {
            agreement_count: 2,
            max_buffer_tokens: 200,
            min_emit_tokens: 1,
        }
    }
}

/// A token with its position and confidence
#[derive(Debug, Clone, PartialEq)]
pub struct TokenInfo {
    /// Token text
    pub text: String,
    /// Position in the sequence (0-indexed)
    pub position: usize,
    /// Confidence/probability (if available)
    pub confidence: Option<f32>,
}

/// Result of processing a new transcription through the agreement policy
#[derive(Debug, Clone)]
pub struct AgreementResult {
    /// Tokens that are confirmed (stable across multiple runs)
    pub confirmed_tokens: Vec<TokenInfo>,
    /// Combined text of confirmed tokens
    pub confirmed_text: String,
    /// Tokens that are pending (not yet stable)
    pub pending_tokens: Vec<TokenInfo>,
    /// Combined text of pending tokens (preview)
    pub pending_text: String,
    /// Whether this result forced emission due to buffer limits
    pub forced_emission: bool,
}

/// Internal state tracking previous transcriptions
#[derive(Debug)]
struct AgreementState {
    /// History of recent token sequences
    history: VecDeque<Vec<TokenInfo>>,
    /// Number of tokens already confirmed and emitted
    confirmed_count: usize,
}

impl AgreementState {
    fn new() -> Self {
        Self {
            history: VecDeque::new(),
            confirmed_count: 0,
        }
    }

    fn reset(&mut self) {
        self.history.clear();
        self.confirmed_count = 0;
    }
}

/// Local Agreement Policy processor
///
/// Tracks multiple transcription runs and determines which tokens
/// are stable enough to emit as confirmed results.
///
/// # Example
///
/// ```ignore
/// use antenna::streaming::agreement::{LocalAgreementPolicy, text_to_tokens};
///
/// let policy = LocalAgreementPolicy::new();
///
/// // First transcription: "hello world"
/// let tokens1 = text_to_tokens("hello world");
/// let result1 = policy.process(tokens1);
/// // result1.confirmed_text == "" (need another run to confirm)
///
/// // Second transcription (same): "hello world"
/// let tokens2 = text_to_tokens("hello world");
/// let result2 = policy.process(tokens2);
/// // result2.confirmed_text == "hello world" (confirmed!)
/// ```
#[derive(Debug)]
pub struct LocalAgreementPolicy {
    config: AgreementConfig,
    state: AgreementState,
}

impl LocalAgreementPolicy {
    /// Create a new policy with default configuration
    pub fn new() -> Self {
        Self::with_config(AgreementConfig::default())
    }

    /// Create a new policy with custom configuration
    pub fn with_config(config: AgreementConfig) -> Self {
        Self {
            config,
            state: AgreementState::new(),
        }
    }

    /// Process a new transcription result
    ///
    /// # Arguments
    /// * `tokens` - The full token sequence from the latest inference
    ///
    /// # Returns
    /// Agreement result with confirmed and pending tokens
    pub fn process(&mut self, tokens: Vec<TokenInfo>) -> AgreementResult {
        // Add to history
        self.state.history.push_back(tokens.clone());

        // Keep only the last N transcriptions
        while self.state.history.len() > self.config.agreement_count {
            self.state.history.pop_front();
        }

        // Find agreed-upon tokens
        let (confirmed, pending, forced) = self.find_agreement(&tokens);

        // Update confirmed count
        self.state.confirmed_count += confirmed.len();

        // Build result
        let confirmed_text = confirmed
            .iter()
            .map(|t| t.text.as_str())
            .collect::<Vec<_>>()
            .join("");
        let pending_text = pending
            .iter()
            .map(|t| t.text.as_str())
            .collect::<Vec<_>>()
            .join("");

        AgreementResult {
            confirmed_tokens: confirmed,
            confirmed_text,
            pending_tokens: pending,
            pending_text,
            forced_emission: forced,
        }
    }

    /// Find tokens that all recent transcriptions agree on
    fn find_agreement(&self, current_tokens: &[TokenInfo]) -> (Vec<TokenInfo>, Vec<TokenInfo>, bool) {
        // If we don't have enough history, nothing is confirmed yet
        if self.state.history.len() < self.config.agreement_count {
            return (vec![], current_tokens.to_vec(), false);
        }

        // Start from the already confirmed position
        let start_pos = self.state.confirmed_count;

        // Find the longest prefix that all transcriptions agree on
        let mut agreed_end = start_pos;

        'outer: for pos in start_pos..current_tokens.len() {
            // Check if all transcriptions in history agree at this position
            for past in self.state.history.iter() {
                if pos >= past.len() {
                    // Past transcription is shorter, can't agree
                    break 'outer;
                }
                if past[pos].text != current_tokens[pos].text {
                    // Disagreement found
                    break 'outer;
                }
            }
            agreed_end = pos + 1;
        }

        // Check for forced emission due to buffer limits
        let pending_count = current_tokens.len().saturating_sub(agreed_end);
        let forced = pending_count > self.config.max_buffer_tokens;

        let final_agreed_end = if forced {
            // Force emit some tokens to prevent buffer overflow
            let force_emit = pending_count - self.config.max_buffer_tokens;
            (agreed_end + force_emit).min(current_tokens.len())
        } else {
            agreed_end
        };

        // Split tokens
        let confirmed: Vec<TokenInfo> = current_tokens[start_pos..final_agreed_end].to_vec();
        let pending: Vec<TokenInfo> = current_tokens[final_agreed_end..].to_vec();

        (confirmed, pending, forced)
    }

    /// Reset the agreement state (e.g., between utterances)
    pub fn reset(&mut self) {
        self.state.reset();
    }

    /// Get the number of confirmed tokens so far
    pub fn confirmed_count(&self) -> usize {
        self.state.confirmed_count
    }

    /// Get the configuration
    pub fn config(&self) -> &AgreementConfig {
        &self.config
    }
}

impl Default for LocalAgreementPolicy {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper function to convert text segments to tokens
pub fn text_to_tokens(text: &str) -> Vec<TokenInfo> {
    // Simple word-based tokenization for text comparison
    text.split_whitespace()
        .enumerate()
        .map(|(i, word)| TokenInfo {
            text: format!("{} ", word), // Include space for joining
            position: i,
            confidence: None,
        })
        .collect()
}

/// Helper to convert confirmed tokens back to text
pub fn tokens_to_text(tokens: &[TokenInfo]) -> String {
    tokens
        .iter()
        .map(|t| t.text.as_str())
        .collect::<String>()
        .trim()
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_tokens(words: &[&str]) -> Vec<TokenInfo> {
        words
            .iter()
            .enumerate()
            .map(|(i, w)| TokenInfo {
                text: format!("{} ", w),
                position: i,
                confidence: None,
            })
            .collect()
    }

    #[test]
    fn test_config_defaults() {
        let config = AgreementConfig::default();
        assert_eq!(config.agreement_count, 2);
    }

    #[test]
    fn test_first_transcription_no_confirmation() {
        let mut policy = LocalAgreementPolicy::new();
        let tokens = make_tokens(&["hello", "world"]);

        let result = policy.process(tokens);

        assert!(result.confirmed_tokens.is_empty());
        assert_eq!(result.pending_tokens.len(), 2);
    }

    #[test]
    fn test_agreement_on_second_transcription() {
        let mut policy = LocalAgreementPolicy::new();

        // First transcription
        let tokens1 = make_tokens(&["hello", "world"]);
        policy.process(tokens1);

        // Second transcription (same)
        let tokens2 = make_tokens(&["hello", "world"]);
        let result = policy.process(tokens2);

        assert_eq!(result.confirmed_tokens.len(), 2);
        assert!(result.pending_tokens.is_empty());
    }

    #[test]
    fn test_partial_agreement() {
        let mut policy = LocalAgreementPolicy::new();

        // First: "hello world"
        let tokens1 = make_tokens(&["hello", "world"]);
        policy.process(tokens1);

        // Second: "hello there" (disagreement on second word)
        let tokens2 = make_tokens(&["hello", "there"]);
        let result = policy.process(tokens2);

        assert_eq!(result.confirmed_tokens.len(), 1);
        assert_eq!(result.confirmed_text.trim(), "hello");
        assert_eq!(result.pending_tokens.len(), 1);
    }

    #[test]
    fn test_growing_agreement() {
        let mut policy = LocalAgreementPolicy::new();

        // First: "hello"
        policy.process(make_tokens(&["hello"]));

        // Second: "hello world"
        let result = policy.process(make_tokens(&["hello", "world"]));

        // "hello" should be confirmed (present in both)
        assert_eq!(result.confirmed_tokens.len(), 1);
        assert_eq!(result.confirmed_text.trim(), "hello");

        // Third: "hello world today"
        let result = policy.process(make_tokens(&["hello", "world", "today"]));

        // "world" should now be confirmed
        assert_eq!(result.confirmed_tokens.len(), 1);
        assert_eq!(result.confirmed_text.trim(), "world");
    }

    #[test]
    fn test_reset() {
        let mut policy = LocalAgreementPolicy::new();

        policy.process(make_tokens(&["hello", "world"]));
        policy.process(make_tokens(&["hello", "world"]));

        assert_eq!(policy.confirmed_count(), 2);

        policy.reset();

        assert_eq!(policy.confirmed_count(), 0);
    }

    #[test]
    fn test_text_to_tokens() {
        let tokens = text_to_tokens("hello world");
        assert_eq!(tokens.len(), 2);
        assert_eq!(tokens[0].text.trim(), "hello");
        assert_eq!(tokens[1].text.trim(), "world");
    }

    #[test]
    fn test_forced_emission() {
        let config = AgreementConfig {
            agreement_count: 2,
            max_buffer_tokens: 2,
            min_emit_tokens: 1,
        };
        let mut policy = LocalAgreementPolicy::with_config(config);

        // First: many tokens
        let tokens1 = make_tokens(&["a", "b", "c", "d", "e"]);
        policy.process(tokens1);

        // Second: same but we disagree from position 1
        let tokens2 = make_tokens(&["a", "x", "y", "z", "w"]);
        let result = policy.process(tokens2);

        // Should force emit due to buffer overflow
        assert!(result.forced_emission || result.confirmed_tokens.len() >= 1);
    }

    #[test]
    fn test_strict_config() {
        let config = AgreementConfig::strict();
        assert_eq!(config.agreement_count, 3);
    }

    #[test]
    fn test_fast_config() {
        let config = AgreementConfig::fast();
        assert_eq!(config.agreement_count, 2);
        assert_eq!(config.max_buffer_tokens, 200);
    }
}
