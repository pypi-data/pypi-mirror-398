//! Shared tokenizer implementations
//!
//! This module provides tokenizer implementations for different STT models:
//!
//! - **BPE**: Byte-Pair Encoding (Whisper, Distil-Whisper)
//! - **CTC**: Character/word-piece tokenizer for CTC models (Wav2Vec2)
//! - **SentencePiece**: For models using SentencePiece (Canary)

pub mod bpe;
pub mod ctc;

pub use bpe::BpeTokenizer;
pub use ctc::CtcCharTokenizer;
