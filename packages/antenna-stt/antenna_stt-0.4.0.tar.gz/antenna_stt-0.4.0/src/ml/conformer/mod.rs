//! Conformer model implementation (Planned)
//!
//! Conformer is a convolution-augmented transformer architecture that combines
//! the strengths of CNNs (local features) and transformers (global context).
//!
//! # Status: Not Yet Implemented
//!
//! This module is a placeholder for future Conformer support. Implementation
//! requires:
//!
//! 1. **Mel Spectrogram Frontend**: Similar to Whisper
//! 2. **Conformer Encoder Blocks**: Alternating self-attention and convolution
//! 3. **CTC Head**: For encoder-only variants
//! 4. **Decoder** (optional): For encoder-decoder variants
//!
//! # Architecture Overview
//!
//! ```text
//! Audio → Mel Spectrogram
//!     │
//!     ▼
//! ┌─────────────────────────────────────┐
//! │        Conformer Block (×N)         │
//! │  ┌─────────────────────────────┐    │
//! │  │ Feed Forward Module (½)     │    │
//! │  └─────────────────────────────┘    │
//! │  ┌─────────────────────────────┐    │
//! │  │ Multi-Head Self-Attention   │    │
//! │  └─────────────────────────────┘    │
//! │  ┌─────────────────────────────┐    │
//! │  │ Convolution Module          │    │
//! │  └─────────────────────────────┘    │
//! │  ┌─────────────────────────────┐    │
//! │  │ Feed Forward Module (½)     │    │
//! │  └─────────────────────────────┘    │
//! └─────────────────────────────────────┘
//!     │
//!     ▼
//! CTC/Attention Decoder → Text
//! ```
//!
//! # Planned Models
//!
//! - Conformer-CTC (encoder-only with CTC)
//! - Conformer-Transducer (with RNN-T decoder)
//!
//! # Implementation Notes
//!
//! Conformer can be used in multiple configurations:
//! - **CTC**: Encoder-only, uses our `CtcDecoder`
//! - **Attention**: Encoder-decoder, similar to Whisper
//! - **Hybrid**: Both CTC and attention heads
//!
//! # References
//!
//! - Paper: "Conformer: Convolution-augmented Transformer for Speech Recognition"
//! - NeMo Implementation: Used as reference for FastConformer in Canary

/// Placeholder for Conformer configuration
#[derive(Debug, Clone)]
pub struct ConformerConfig {
    /// Number of encoder layers
    pub num_layers: usize,
    /// Hidden size (d_model)
    pub hidden_size: usize,
    /// Number of attention heads
    pub num_attention_heads: usize,
    /// Convolution kernel size
    pub conv_kernel_size: usize,
    /// Feed-forward dimension
    pub ff_dim: usize,
    /// Dropout probability
    pub dropout: f32,
}

impl Default for ConformerConfig {
    fn default() -> Self {
        Self {
            num_layers: 12,
            hidden_size: 512,
            num_attention_heads: 8,
            conv_kernel_size: 31,
            ff_dim: 2048,
            dropout: 0.1,
        }
    }
}

/// Conformer encoder block components
#[derive(Debug, Clone, Copy)]
pub enum ConformerBlockComponent {
    /// Feed-forward half module
    FeedForwardHalf,
    /// Multi-head self-attention
    SelfAttention,
    /// Convolution module (pointwise + depthwise + pointwise)
    Convolution,
}

/// Planned Conformer model variants
pub const CONFORMER_MODELS: &[(&str, &str)] = &[
    ("conformer-ctc-small", "Conformer-CTC small (~30M params)"),
    ("conformer-ctc-medium", "Conformer-CTC medium (~100M params)"),
    ("conformer-ctc-large", "Conformer-CTC large (~300M params)"),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_default() {
        let config = ConformerConfig::default();
        assert_eq!(config.num_layers, 12);
        assert_eq!(config.conv_kernel_size, 31);
    }

    #[test]
    fn test_models_listed() {
        assert!(!CONFORMER_MODELS.is_empty());
    }
}
