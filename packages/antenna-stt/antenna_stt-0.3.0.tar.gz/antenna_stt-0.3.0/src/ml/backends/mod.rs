//! Inference backend abstraction layer
//!
//! This module provides a unified interface for different inference backends,
//! allowing Antenna to support multiple execution engines:
//!
//! - **Candle** (default): Native Rust ML framework, best for Whisper/Distil-Whisper
//! - **ONNX Runtime**: Cross-platform inference, supports TensorRT acceleration
//! - **CTranslate2**: Optimized Whisper inference (4x faster)
//! - **sherpa-rs**: Pre-built Conformer/Zipformer models
//! - **parakeet-rs**: NVIDIA Parakeet FastConformer models
//!
//! # Backend Selection
//!
//! Backends are automatically selected based on:
//! 1. Model family (Whisper prefers Candle, Wav2Vec2 requires ONNX)
//! 2. Available features (ONNX only if `onnx` feature enabled)
//! 3. User preference (explicit backend selection)
//!
//! # Example
//!
//! ```rust,ignore
//! use antenna::ml::backends::{Backend, select_backend, DeviceSpec};
//!
//! // Auto-select best backend for Whisper
//! let backend = select_backend("whisper", None, &DeviceSpec::Cuda { device_id: 0 })?;
//!
//! // Force ONNX backend
//! let backend = select_backend("whisper", Some(Backend::Onnx), &DeviceSpec::Cpu)?;
//! ```

pub mod device;

// Conditional backend modules
#[cfg(feature = "onnx")]
pub mod onnx;

#[cfg(feature = "ctranslate2")]
pub mod ctranslate2;

// Re-exports
pub use device::DeviceSpec;

#[cfg(feature = "onnx")]
pub use onnx::{ExecutionProvider, OnnxSession};

use crate::error::AntennaError;

/// Available inference backends
///
/// Each backend has different capabilities, performance characteristics,
/// and model support. Use `select_backend()` for automatic selection.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Backend {
    /// Native Candle implementation (always available)
    ///
    /// Best performance for Whisper and Distil-Whisper models.
    /// Supports CPU and CUDA acceleration.
    Candle,

    /// ONNX Runtime backend
    ///
    /// Cross-platform inference with support for multiple execution providers:
    /// - CPU (always available)
    /// - CUDA (GPU acceleration)
    /// - TensorRT (optimized GPU, requires warmup)
    ///
    /// Required for Wav2Vec2 and other models not in Candle.
    /// Requires `onnx` feature flag.
    Onnx,

    /// CTranslate2 backend (via ct2rs)
    ///
    /// Highly optimized Whisper inference, up to 4x faster than native.
    /// Supports INT8 quantization for additional speedup.
    /// Requires `ctranslate2` feature flag.
    CTranslate2,

    /// sherpa-rs backend
    ///
    /// Pre-built speech recognition models including Conformer,
    /// Zipformer, and Paraformer architectures.
    /// Requires `sherpa` feature flag.
    Sherpa,

    /// parakeet-rs backend
    ///
    /// NVIDIA Parakeet FastConformer models (600M params).
    /// Supports 25 European languages with diarization.
    /// Requires `parakeet` feature flag.
    Parakeet,
}

impl Backend {
    /// Check if this backend is available (feature enabled)
    pub fn is_available(&self) -> bool {
        match self {
            Backend::Candle => true, // Always available
            Backend::Onnx => cfg!(feature = "onnx"),
            Backend::CTranslate2 => cfg!(feature = "ctranslate2"),
            Backend::Sherpa => cfg!(feature = "sherpa"),
            Backend::Parakeet => cfg!(feature = "parakeet"),
        }
    }

    /// Get the feature flag name required for this backend
    pub fn feature_flag(&self) -> Option<&'static str> {
        match self {
            Backend::Candle => None,
            Backend::Onnx => Some("onnx"),
            Backend::CTranslate2 => Some("ctranslate2"),
            Backend::Sherpa => Some("sherpa"),
            Backend::Parakeet => Some("parakeet"),
        }
    }

    /// Get a human-readable description of this backend
    pub fn description(&self) -> &'static str {
        match self {
            Backend::Candle => "Native Candle (Rust ML framework)",
            Backend::Onnx => "ONNX Runtime (cross-platform inference)",
            Backend::CTranslate2 => "CTranslate2 (optimized Whisper, 4x faster)",
            Backend::Sherpa => "sherpa-rs (Conformer/Zipformer models)",
            Backend::Parakeet => "parakeet-rs (NVIDIA FastConformer)",
        }
    }

    /// Parse backend from string
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "candle" | "native" => Some(Backend::Candle),
            "onnx" | "onnxruntime" | "ort" => Some(Backend::Onnx),
            "ctranslate2" | "ct2" | "faster-whisper" => Some(Backend::CTranslate2),
            "sherpa" | "sherpa-onnx" => Some(Backend::Sherpa),
            "parakeet" => Some(Backend::Parakeet),
            _ => None,
        }
    }
}

impl std::fmt::Display for Backend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Backend::Candle => write!(f, "candle"),
            Backend::Onnx => write!(f, "onnx"),
            Backend::CTranslate2 => write!(f, "ctranslate2"),
            Backend::Sherpa => write!(f, "sherpa"),
            Backend::Parakeet => write!(f, "parakeet"),
        }
    }
}

/// Model family for backend selection
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModelFamily {
    /// OpenAI Whisper models
    Whisper,
    /// Distil-Whisper (distilled Whisper)
    DistilWhisper,
    /// Meta Wav2Vec2 models
    Wav2Vec2,
    /// Conformer-based models
    Conformer,
    /// NVIDIA Parakeet models
    Parakeet,
    /// NVIDIA Canary models
    Canary,
}

impl ModelFamily {
    /// Parse model family from model ID
    pub fn from_model_id(model_id: &str) -> Option<Self> {
        let id = model_id.to_lowercase();

        if id.contains("distil-whisper") || id.contains("distil_whisper") {
            Some(ModelFamily::DistilWhisper)
        } else if id.contains("whisper") {
            Some(ModelFamily::Whisper)
        } else if id.contains("wav2vec2") || id.contains("wav2vec") {
            Some(ModelFamily::Wav2Vec2)
        } else if id.contains("conformer") {
            Some(ModelFamily::Conformer)
        } else if id.contains("parakeet") {
            Some(ModelFamily::Parakeet)
        } else if id.contains("canary") {
            Some(ModelFamily::Canary)
        } else {
            None
        }
    }

    /// Get the default (preferred) backend for this model family
    pub fn default_backend(&self) -> Backend {
        match self {
            ModelFamily::Whisper | ModelFamily::DistilWhisper => Backend::Candle,
            ModelFamily::Wav2Vec2 => Backend::Onnx,
            ModelFamily::Conformer => Backend::Sherpa,
            ModelFamily::Parakeet => Backend::Parakeet,
            ModelFamily::Canary => Backend::Onnx, // NeMo models via ONNX
        }
    }

    /// Get all supported backends for this model family (in priority order)
    pub fn supported_backends(&self) -> Vec<Backend> {
        match self {
            ModelFamily::Whisper => vec![Backend::Candle, Backend::CTranslate2, Backend::Onnx],
            ModelFamily::DistilWhisper => vec![Backend::Candle, Backend::Onnx],
            ModelFamily::Wav2Vec2 => vec![Backend::Onnx],
            ModelFamily::Conformer => vec![Backend::Sherpa, Backend::Onnx],
            ModelFamily::Parakeet => vec![Backend::Parakeet],
            ModelFamily::Canary => vec![Backend::Onnx],
        }
    }
}

/// Select the best available backend for a model
///
/// # Arguments
///
/// * `model_family` - The model family string (e.g., "whisper", "wav2vec2")
/// * `preferred` - Optional preferred backend (overrides auto-selection)
/// * `device` - Target device specification
///
/// # Returns
///
/// The selected backend, or an error if no suitable backend is available.
///
/// # Example
///
/// ```rust,ignore
/// // Auto-select for Whisper on GPU
/// let backend = select_backend("whisper", None, &DeviceSpec::Cuda { device_id: 0 })?;
/// assert_eq!(backend, Backend::Candle);
///
/// // Force ONNX backend
/// let backend = select_backend("whisper", Some(Backend::Onnx), &DeviceSpec::Cpu)?;
/// assert_eq!(backend, Backend::Onnx);
/// ```
pub fn select_backend(
    model_family: &str,
    preferred: Option<Backend>,
    _device: &DeviceSpec,
) -> Result<Backend, AntennaError> {
    // If user explicitly requested a backend, validate and use it
    if let Some(backend) = preferred {
        if !backend.is_available() {
            return Err(AntennaError::ModelError(format!(
                "Backend '{}' requires the '{}' feature. Rebuild with: cargo build --features {}",
                backend,
                backend.feature_flag().unwrap_or("unknown"),
                backend.feature_flag().unwrap_or("unknown")
            )));
        }
        return Ok(backend);
    }

    // Parse model family
    let family = ModelFamily::from_model_id(model_family).ok_or_else(|| {
        AntennaError::ModelError(format!(
            "Unknown model family: '{}'. Supported: whisper, distil-whisper, wav2vec2, conformer, parakeet",
            model_family
        ))
    })?;

    // Get supported backends and find first available
    let backends = family.supported_backends();
    for backend in backends {
        if backend.is_available() {
            return Ok(backend);
        }
    }

    // No available backend found
    let required_features: Vec<_> = family
        .supported_backends()
        .iter()
        .filter_map(|b| b.feature_flag())
        .collect();

    Err(AntennaError::ModelError(format!(
        "No backend available for '{}'. Enable one of these features: {}",
        model_family,
        required_features.join(", ")
    )))
}

/// List all available backends (with features enabled)
pub fn available_backends() -> Vec<Backend> {
    [
        Backend::Candle,
        Backend::Onnx,
        Backend::CTranslate2,
        Backend::Sherpa,
        Backend::Parakeet,
    ]
    .into_iter()
    .filter(|b| b.is_available())
    .collect()
}

/// Backend capabilities for a specific model
#[derive(Debug, Clone)]
pub struct BackendInfo {
    /// The backend type
    pub backend: Backend,
    /// Whether this backend is currently available
    pub available: bool,
    /// Human-readable description
    pub description: String,
    /// Required feature flag (if any)
    pub feature_flag: Option<String>,
}

/// Get information about all backends for a model family
pub fn backend_info(model_family: &str) -> Vec<BackendInfo> {
    let family = match ModelFamily::from_model_id(model_family) {
        Some(f) => f,
        None => return vec![],
    };

    family
        .supported_backends()
        .into_iter()
        .map(|backend| BackendInfo {
            backend,
            available: backend.is_available(),
            description: backend.description().to_string(),
            feature_flag: backend.feature_flag().map(|s| s.to_string()),
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_backend_availability() {
        // Candle is always available
        assert!(Backend::Candle.is_available());
    }

    #[test]
    fn test_model_family_parsing() {
        assert_eq!(
            ModelFamily::from_model_id("openai/whisper-base"),
            Some(ModelFamily::Whisper)
        );
        assert_eq!(
            ModelFamily::from_model_id("distil-whisper/distil-small.en"),
            Some(ModelFamily::DistilWhisper)
        );
        assert_eq!(
            ModelFamily::from_model_id("facebook/wav2vec2-base-960h"),
            Some(ModelFamily::Wav2Vec2)
        );
    }

    #[test]
    fn test_backend_selection_whisper() {
        // Whisper should default to Candle
        let backend = select_backend("whisper/base", None, &DeviceSpec::Cpu).unwrap();
        assert_eq!(backend, Backend::Candle);
    }

    #[test]
    fn test_backend_display() {
        assert_eq!(Backend::Candle.to_string(), "candle");
        assert_eq!(Backend::Onnx.to_string(), "onnx");
    }

    #[test]
    fn test_backend_from_str() {
        assert_eq!(Backend::from_str("candle"), Some(Backend::Candle));
        assert_eq!(Backend::from_str("ONNX"), Some(Backend::Onnx));
        assert_eq!(Backend::from_str("ct2"), Some(Backend::CTranslate2));
        assert_eq!(Backend::from_str("invalid"), None);
    }
}
