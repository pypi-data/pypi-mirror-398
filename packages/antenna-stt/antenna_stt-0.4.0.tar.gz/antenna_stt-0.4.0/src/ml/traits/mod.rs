//! Core traits for speech-to-text models
//!
//! This module defines the trait abstractions that allow Antenna to support
//! multiple STT model architectures (Whisper, Wav2Vec2, Conformer, Canary, etc.)
//! through a unified interface.

pub mod decoder;
pub mod feature_extractor;
pub mod loader;
pub mod model;
pub mod tokenizer;

// Re-export all traits for convenience
pub use decoder::{CommonDecodingOptions, Decoder, DecodingStrategy};
pub use feature_extractor::{FeatureConfig, FeatureExtractor, FeatureType};
pub use loader::{ModelLoader, ModelSource};
pub use model::{
    ModelArchitecture, ModelCapabilities, ModelInfo, SpeechModel, TranscriptionOptions,
    TranscriptionResult, TranscriptionSegment, TranscriptionTask,
};
pub use tokenizer::{LanguageInfo, SttTokenizer};
