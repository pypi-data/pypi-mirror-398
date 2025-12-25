//! Shared decoding algorithms for speech-to-text models
//!
//! This module provides generic decoding strategies that can be used
//! by different model architectures:
//!
//! - **Beam Search**: For encoder-decoder models (Whisper, Canary)
//! - **Greedy**: Simple argmax decoding
//! - **CTC**: For encoder-only models (Wav2Vec2, Conformer-CTC)

pub mod beam_search;
pub mod ctc;
pub mod greedy;

pub use beam_search::{BeamSearchDecoder, BeamSearchOptions};
pub use ctc::{CtcDecoder, CtcOptions};
pub use greedy::{GreedyDecoder, GreedyOptions};
