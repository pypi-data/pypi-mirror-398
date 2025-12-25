//! Shared audio feature extraction
//!
//! This module provides reusable feature extractors that can be used
//! by multiple STT model architectures.
//!
//! # Feature Types
//!
//! - **Mel Spectrogram**: Used by Whisper, Canary, Conformer
//! - **Raw Waveform**: Used by Wav2Vec2

pub mod mel;
pub mod waveform;

pub use mel::{MelConfig, MelExtractor};
pub use waveform::{WaveformConfig as RawWaveformConfig, WaveformExtractor};
