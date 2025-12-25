//! Wav2Vec2 model implementation using ONNX Runtime
//!
//! Wav2Vec2 is Meta's self-supervised speech representation model that uses
//! contrastive learning. When fine-tuned for ASR, it uses CTC decoding.
//!
//! # Status: Implemented via ONNX Runtime
//!
//! This module provides Wav2Vec2 speech recognition using ONNX-exported models
//! from HuggingFace. Uses CTC decoding for alignment-free transcription.
//!
//! # Architecture Overview
//!
//! ```text
//! Raw Audio (16kHz)
//!     │
//!     ▼
//! CNN Feature Encoder (7 layers, ~25ms windows)
//!     │
//!     ▼
//! Transformer Encoder (12-24 layers)
//!     │
//!     ▼
//! CTC Projection Head
//!     │
//!     ▼
//! CTC Decoding → Text
//! ```
//!
//! # Supported Models
//!
//! Most Wav2Vec2 models on HuggingFace have ONNX exports:
//! - `facebook/wav2vec2-base-960h` - Base model, 95M params
//! - `facebook/wav2vec2-large-960h` - Large model, 317M params
//! - `jonatasgrosman/wav2vec2-large-xlsr-53-english` - Multilingual fine-tuned
//!
//! # Example
//!
//! ```rust,ignore
//! use antenna::ml::wav2vec2::Wav2Vec2Model;
//!
//! // Load model from HuggingFace (downloads ONNX version)
//! let mut model = Wav2Vec2Model::from_pretrained("facebook/wav2vec2-base-960h", "cuda")?;
//!
//! // Transcribe audio
//! let result = model.transcribe(&audio, Default::default())?;
//! println!("{}", result.text);
//! ```
//!
//! # Implementation Notes
//!
//! Unlike Whisper (encoder-decoder), Wav2Vec2 is encoder-only with CTC:
//! - No autoregressive decoding - single forward pass
//! - Uses our `CtcDecoder` from `ml::decode::ctc`
//! - Uses our `CtcCharTokenizer` from `ml::tokenizers::ctc`
//! - Implements `SpeechModel` trait for unified interface
//!
//! # References
//!
//! - Paper: "wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations"
//! - HuggingFace: https://huggingface.co/facebook/wav2vec2-base-960h

#[cfg(feature = "onnx")]
mod model;

#[cfg(feature = "onnx")]
pub use model::Wav2Vec2Model;

/// Placeholder for Wav2Vec2 configuration
#[derive(Debug, Clone)]
pub struct Wav2Vec2Config {
    /// Number of CNN feature encoder layers
    pub num_feat_extract_layers: usize,
    /// Number of transformer encoder layers
    pub num_hidden_layers: usize,
    /// Hidden size
    pub hidden_size: usize,
    /// Number of attention heads
    pub num_attention_heads: usize,
    /// Vocabulary size for CTC
    pub vocab_size: usize,
}

impl Default for Wav2Vec2Config {
    fn default() -> Self {
        // Base model configuration
        Self {
            num_feat_extract_layers: 7,
            num_hidden_layers: 12,
            hidden_size: 768,
            num_attention_heads: 12,
            vocab_size: 32,
        }
    }
}

/// Planned Wav2Vec2 model variants
pub const WAV2VEC2_MODELS: &[(&str, &str, &str)] = &[
    (
        "base-960h",
        "facebook/wav2vec2-base-960h",
        "Base model, 95M params, trained on LibriSpeech 960h",
    ),
    (
        "large-960h",
        "facebook/wav2vec2-large-960h",
        "Large model, 317M params, trained on LibriSpeech 960h",
    ),
    (
        "large-960h-lv60-self",
        "facebook/wav2vec2-large-960h-lv60-self",
        "Large model with self-training on LibriLight 60k",
    ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_default() {
        let config = Wav2Vec2Config::default();
        assert_eq!(config.num_feat_extract_layers, 7);
        assert_eq!(config.num_hidden_layers, 12);
    }

    #[test]
    fn test_models_listed() {
        assert!(!WAV2VEC2_MODELS.is_empty());
    }
}
