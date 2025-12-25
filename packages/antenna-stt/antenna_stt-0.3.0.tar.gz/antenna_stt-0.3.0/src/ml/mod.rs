//! Machine Learning module for Antenna
//!
//! This module provides ML-based audio processing capabilities,
//! supporting multiple speech-to-text model architectures through
//! a unified trait-based interface.
//!
//! # Architecture
//!
//! The module is organized into:
//! - `traits`: Core trait definitions for models, decoders, tokenizers
//! - `backends`: Inference backend abstraction (Candle, ONNX, CTranslate2, etc.)
//! - `features`: Shared feature extraction (mel spectrogram, waveform)
//! - `decode`: Shared decoding algorithms (beam search, CTC)
//! - `tokenizers`: Shared tokenizer implementations
//! - `whisper`: Whisper model implementation
//!
//! # Supported Backends
//!
//! - **Candle** (default): Native Rust ML framework, best for Whisper
//! - **ONNX Runtime**: Cross-platform inference (requires `onnx` feature)
//! - **CTranslate2**: Optimized Whisper, 4x faster (requires `ctranslate2` feature)
//! - **sherpa-rs**: Conformer/Zipformer models (requires `sherpa` feature)
//! - **parakeet-rs**: NVIDIA Parakeet models (requires `parakeet` feature)
//!
//! # Supported Models
//!
//! - **Whisper**: OpenAI's encoder-decoder model (transcribe, translate)
//! - **Distil-Whisper**: Faster/smaller Whisper variants
//! - **Wav2Vec2**: Meta's encoder-only model with CTC (requires `onnx` feature)
//! - **Conformer**: Convolution-augmented transformer (requires `sherpa` or `onnx`)
//! - **Parakeet**: NVIDIA FastConformer model (requires `parakeet` feature)

// Backend abstraction layer
pub mod backends;

// Core trait definitions
pub mod traits;

// Unified model registry
pub mod registry;

// Shared components
pub mod decode;
pub mod features;
pub mod tokenizers;

// Model implementations
pub mod tokenizer; // Legacy Whisper tokenizer (will be moved to tokenizers/)
pub mod whisper;
pub mod distil_whisper;

// Planned model implementations (stubs)
pub mod wav2vec2;   // Encoder-only with CTC
pub mod conformer;  // Conformer-CTC
pub mod canary;     // FastConformer (NeMo format)

// Re-export traits for convenience (with distinct names to avoid conflicts)
pub use traits::{
    ModelArchitecture, ModelCapabilities, ModelInfo, SpeechModel,
    TranscriptionOptions as GenericTranscriptionOptions,
    TranscriptionTask,
};

// Re-export Whisper types (backward compatibility)
pub use tokenizer::WhisperTokenizer;
pub use whisper::{Task, TranscriptionOptions, WhisperModel};

// Re-export Distil-Whisper types
pub use distil_whisper::{DistilWhisperModel, DistilWhisperSize};

// Re-export backend types
pub use backends::{Backend, DeviceSpec, ModelFamily};

#[cfg(feature = "onnx")]
pub use backends::{ExecutionProvider, OnnxSession};

// Re-export registry types
pub use registry::{DynSpeechModel, ModelSpec, ModelEntry, load_model, list_models, is_model_available};

// Re-export Wav2Vec2 types (requires onnx feature)
#[cfg(feature = "onnx")]
pub use wav2vec2::Wav2Vec2Model;
