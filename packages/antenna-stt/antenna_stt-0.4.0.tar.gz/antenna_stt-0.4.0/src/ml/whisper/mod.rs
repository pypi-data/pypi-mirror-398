//! Whisper speech-to-text implementation
//!
//! This module provides Whisper model loading, inference, and transcription
//! capabilities using the Candle ML framework.

pub mod config;
pub mod decode;
pub mod inference;
pub mod model;

pub use config::WhisperConfig;
pub use decode::{DecodingOptions, beam_search_decode, greedy_decode};
pub use inference::{audio_to_mel_spectrogram, TranscriptionOptions, Task};
pub use model::WhisperModel;
