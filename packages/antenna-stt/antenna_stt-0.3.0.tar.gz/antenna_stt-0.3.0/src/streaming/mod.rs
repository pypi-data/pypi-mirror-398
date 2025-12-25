//! Lightweight Streaming Transcription for Python
//!
//! This module provides synchronous, chunk-by-chunk streaming transcription
//! suitable for Python integration. Unlike the async server module, this API
//! is designed for simplicity and direct use from Python code.
//!
//! # Architecture
//!
//! - `StreamingTranscriber` - Main entry point, wraps a speech model
//! - `StreamingConfig` - Configuration for buffering, VAD, and processing
//! - `StreamingEvent` - Events emitted during transcription (partial, final, etc.)
//! - `LocalAgreementPolicy` - Stabilizes partial results to prevent flickering
//! - `AudioRingBuffer` - Efficient circular buffer with overlap support
//!
//! # Example (Rust)
//!
//! ```ignore
//! use antenna::streaming::{StreamingTranscriber, StreamingConfig};
//! use antenna::ml::WhisperModel;
//!
//! let model = WhisperModel::from_size("base", Device::Cpu)?;
//! let mut transcriber = StreamingTranscriber::new(model, StreamingConfig::default());
//!
//! // Process audio chunks
//! for chunk in audio_chunks {
//!     let events = transcriber.process_chunk(&chunk.samples)?;
//!     for event in events {
//!         println!("{:?}", event);
//!     }
//! }
//!
//! // Flush remaining audio
//! let final_events = transcriber.flush()?;
//! ```
//!
//! # Example (Python)
//!
//! ```python
//! import antenna
//!
//! model = antenna.load_model("whisper/base", device="cpu")
//! transcriber = antenna.StreamingTranscriber(model)
//!
//! # Process audio chunks
//! for chunk in audio_chunks:
//!     events = transcriber.process_chunk(chunk)
//!     for event in events:
//!         if event.is_partial:
//!             print(f"[partial] {event.text}", end="\r")
//!         else:
//!             print(f"[final] {event.text}")
//!
//! # Flush remaining
//! final_events = transcriber.flush()
//! ```
//!
//! # Agreement Policy
//!
//! The `LocalAgreementPolicy` helps stabilize streaming transcription output.
//! It works by comparing multiple consecutive transcription runs and only
//! emitting tokens that appear consistently across runs.
//!
//! ```python
//! # Enable agreement policy for smoother output
//! config = antenna.StreamingConfig.realtime()
//! config = config.with_agreement(True)  # Enable stable partials
//! transcriber = antenna.StreamingTranscriber.from_model_id("whisper/tiny", config=config)
//! ```

mod agreement;
mod buffer;
mod config;
mod ring_buffer;
mod transcriber;
mod vad;

pub use agreement::{
    text_to_tokens, tokens_to_text, AgreementConfig, AgreementResult, LocalAgreementPolicy,
    TokenInfo,
};
pub use buffer::AudioBuffer;
pub use config::StreamingConfig;
pub use ring_buffer::{AudioRingBuffer, AudioRingBufferBuilder};
pub use transcriber::{StreamingEvent, StreamingTranscriber};
pub use vad::{SimpleVad, VadConfig, VoiceState};
