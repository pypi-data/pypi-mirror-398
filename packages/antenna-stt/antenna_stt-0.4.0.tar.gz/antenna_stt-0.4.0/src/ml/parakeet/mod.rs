//! Parakeet model implementation using sherpa-rs
//!
//! NVIDIA Parakeet is a state-of-the-art ASR model based on FastConformer-TDT
//! architecture with 600 million parameters. It achieves low Word Error Rates
//! while maintaining fast inference speeds.
//!
//! # Features
//!
//! - **Fast Inference**: Can transcribe 60 minutes of audio in ~1 second
//! - **High Accuracy**: Low WER on common benchmarks
//! - **Multilingual**: v3 supports 25 European languages
//! - **Punctuation & Capitalization**: Built-in formatting
//!
//! # Example
//!
//! ```rust,ignore
//! use antenna::ml::parakeet::ParakeetModel;
//!
//! let model = ParakeetModel::from_size("tdt-0.6b-v2", "cpu")?;
//! let result = model.transcribe(&audio, Default::default())?;
//! println!("Transcription: {}", result.text);
//! ```
//!
//! # Model Variants
//!
//! | Variant | Languages | Description |
//! |---------|-----------|-------------|
//! | tdt-0.6b-v2 | English | Improved English model |
//! | tdt-0.6b-v3 | 25 langs | Multilingual (European) |
//! | tdt-0.6b-en | English | Original English model |

mod config;

pub use config::{ParakeetConfig, ParakeetSize, PARAKEET_MODELS};

#[cfg(feature = "sherpa")]
mod model;

#[cfg(feature = "sherpa")]
pub use model::ParakeetModel;

// Provide a stub when sherpa feature is not enabled
#[cfg(not(feature = "sherpa"))]
pub struct ParakeetModel;

#[cfg(not(feature = "sherpa"))]
impl ParakeetModel {
    pub fn from_size(_variant: &str, _device: &str) -> Result<Self, crate::error::AntennaError> {
        Err(crate::error::AntennaError::ModelError(
            "Parakeet models require the 'sherpa' feature. Rebuild with: cargo build --features sherpa".to_string()
        ))
    }
}
