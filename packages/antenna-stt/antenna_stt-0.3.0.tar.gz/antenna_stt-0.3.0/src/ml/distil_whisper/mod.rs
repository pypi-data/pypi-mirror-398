//! Distil-Whisper model implementation
//!
//! Distil-Whisper is a distilled (compressed) version of Whisper that maintains
//! high accuracy while being significantly faster. It uses the same architecture
//! as Whisper but with fewer decoder layers.
//!
//! # Supported Models
//!
//! - `distil-whisper/distil-small.en` - English-only, fastest
//! - `distil-whisper/distil-medium.en` - English-only, balanced
//! - `distil-whisper/distil-large-v2` - Multilingual, based on large-v2
//! - `distil-whisper/distil-large-v3` - Multilingual, based on large-v3

mod config;
mod model;

pub use config::{DistilWhisperSize, DISTIL_WHISPER_MODELS};
pub use model::DistilWhisperModel;
