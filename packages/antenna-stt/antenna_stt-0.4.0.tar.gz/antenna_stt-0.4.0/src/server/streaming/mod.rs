//! Streaming audio processing
//!
//! This module provides components for real-time audio streaming:
//! - Ring buffer for efficient audio accumulation
//! - Types for audio chunks and partial transcripts
//! - Streaming configuration
//! - Voice Activity Detection (VAD)
//! - Local agreement policy for stable partial results
//! - Streaming engine orchestration

pub mod agreement;
pub mod buffer;
pub mod engine;
pub mod types;
pub mod vad;

pub use agreement::{AgreementConfig, AgreementResult, LocalAgreementPolicy, TokenInfo};
pub use buffer::{AudioRingBuffer, AudioRingBufferBuilder};
pub use engine::{EngineConfig, StreamingEngine, StreamingEvent};
pub use types::{AudioChunk, PartialTranscript, StreamingConfig};
pub use vad::{StreamingVad, VadConfig, VadFrame, VoiceState};
