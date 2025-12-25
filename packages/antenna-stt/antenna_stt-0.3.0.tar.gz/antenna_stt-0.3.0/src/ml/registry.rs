//! Unified Model Registry for Antenna
//!
//! This module provides a single entry point for loading any speech-to-text model
//! supported by Antenna. It automatically selects the best backend and handles
//! model configuration.
//!
//! # Model ID Format
//!
//! Models are identified using a `family/variant` format:
//! - `whisper/base` - OpenAI Whisper base model
//! - `whisper/large-v3` - OpenAI Whisper large-v3 model
//! - `distil-whisper/small.en` - Distil-Whisper small English model
//! - `wav2vec2/base-960h` - Facebook Wav2Vec2 base model
//!
//! You can also use full HuggingFace model IDs:
//! - `openai/whisper-base`
//! - `facebook/wav2vec2-base-960h`
//!
//! # Example
//!
//! ```rust,ignore
//! use antenna::ml::registry::{load_model, list_models};
//!
//! // Load model with auto backend selection
//! let model = load_model("whisper/base", "cuda", None)?;
//!
//! // List available models
//! for model in list_models() {
//!     println!("{}: {}", model.id, model.description);
//! }
//! ```

use crate::error::AntennaError;
use crate::ml::backends::{Backend, DeviceSpec, ModelFamily};
use crate::ml::traits::{
    ModelInfo, SpeechModel, TranscriptionOptions, TranscriptionResult,
};
use crate::ml::whisper::WhisperModel;
use crate::ml::distil_whisper::DistilWhisperModel;
use crate::types::AudioData;
use candle_core::Device;

#[cfg(feature = "onnx")]
use crate::ml::wav2vec2::Wav2Vec2Model;

/// Parsed model specification
#[derive(Debug, Clone)]
pub struct ModelSpec {
    /// Model family (whisper, distil-whisper, wav2vec2, etc.)
    pub family: ModelFamily,
    /// Model variant (base, large-v3, small.en, etc.)
    pub variant: String,
    /// Full HuggingFace model ID (if known)
    pub hf_model_id: Option<String>,
    /// Required backend (if explicitly specified)
    pub backend: Option<Backend>,
}

impl ModelSpec {
    /// Parse a model ID string into a ModelSpec
    ///
    /// Supports formats:
    /// - `whisper/base` - family/variant format
    /// - `openai/whisper-base` - HuggingFace format
    /// - `distil-whisper/distil-small.en` - Distil-Whisper
    /// - `wav2vec2/base-960h` - Wav2Vec2
    pub fn parse(model_id: &str) -> Result<Self, AntennaError> {
        let model_id = model_id.trim();

        // Check for HuggingFace-style IDs first
        if model_id.starts_with("openai/whisper-") {
            let variant = model_id.strip_prefix("openai/whisper-")
                .ok_or_else(|| AntennaError::ModelError(format!("Invalid model ID: {}", model_id)))?;
            return Ok(Self {
                family: ModelFamily::Whisper,
                variant: variant.to_string(),
                hf_model_id: Some(model_id.to_string()),
                backend: None,
            });
        }

        if model_id.starts_with("distil-whisper/") {
            let variant = model_id.strip_prefix("distil-whisper/")
                .ok_or_else(|| AntennaError::ModelError(format!("Invalid model ID: {}", model_id)))?;
            return Ok(Self {
                family: ModelFamily::DistilWhisper,
                variant: variant.to_string(),
                hf_model_id: Some(model_id.to_string()),
                backend: None,
            });
        }

        if model_id.starts_with("facebook/wav2vec2-") {
            let variant = model_id.strip_prefix("facebook/wav2vec2-")
                .ok_or_else(|| AntennaError::ModelError(format!("Invalid model ID: {}", model_id)))?;
            return Ok(Self {
                family: ModelFamily::Wav2Vec2,
                variant: variant.to_string(),
                hf_model_id: Some(model_id.to_string()),
                backend: None,
            });
        }

        // Parse family/variant format
        let parts: Vec<&str> = model_id.splitn(2, '/').collect();
        if parts.len() != 2 {
            // Try to infer family from model ID
            if let Some(family) = ModelFamily::from_model_id(model_id) {
                return Ok(Self {
                    family,
                    variant: model_id.to_string(),
                    hf_model_id: None,
                    backend: None,
                });
            }
            return Err(AntennaError::ModelError(format!(
                "Invalid model ID format: '{}'. Use 'family/variant' format (e.g., 'whisper/base', 'wav2vec2/base-960h')",
                model_id
            )));
        }

        let family_str = parts[0].to_lowercase();
        let variant = parts[1].to_string();

        let family = match family_str.as_str() {
            "whisper" => ModelFamily::Whisper,
            "distil-whisper" | "distil_whisper" => ModelFamily::DistilWhisper,
            "wav2vec2" | "wav2vec" => ModelFamily::Wav2Vec2,
            "conformer" => ModelFamily::Conformer,
            "parakeet" => ModelFamily::Parakeet,
            "canary" => ModelFamily::Canary,
            _ => {
                return Err(AntennaError::ModelError(format!(
                    "Unknown model family: '{}'. Supported: whisper, distil-whisper, wav2vec2, conformer, parakeet",
                    family_str
                )));
            }
        };

        // Construct HuggingFace model ID if not already provided
        let hf_model_id = match family {
            ModelFamily::Whisper => Some(format!("openai/whisper-{}", variant)),
            ModelFamily::DistilWhisper => Some(format!("distil-whisper/{}", variant)),
            ModelFamily::Wav2Vec2 => Some(format!("facebook/wav2vec2-{}", variant)),
            _ => None,
        };

        Ok(Self {
            family,
            variant,
            hf_model_id,
            backend: None,
        })
    }

    /// Set explicit backend
    pub fn with_backend(mut self, backend: Backend) -> Self {
        self.backend = Some(backend);
        self
    }

    /// Get the HuggingFace model ID
    pub fn hf_id(&self) -> String {
        self.hf_model_id.clone().unwrap_or_else(|| {
            match self.family {
                ModelFamily::Whisper => format!("openai/whisper-{}", self.variant),
                ModelFamily::DistilWhisper => format!("distil-whisper/{}", self.variant),
                ModelFamily::Wav2Vec2 => format!("facebook/wav2vec2-{}", self.variant),
                ModelFamily::Conformer => format!("conformer/{}", self.variant),
                ModelFamily::Parakeet => format!("nvidia/parakeet-{}", self.variant),
                ModelFamily::Canary => format!("nvidia/canary-{}", self.variant),
            }
        })
    }
}

/// Dynamic speech model wrapper
///
/// This enum wraps all supported model types and provides a unified interface
/// through the `SpeechModel` trait. Used for the `load_model()` function.
#[derive(Debug)]
pub enum DynSpeechModel {
    /// Whisper model (Candle backend)
    Whisper(WhisperModel),
    /// Distil-Whisper model (Candle backend)
    DistilWhisper(DistilWhisperModel),
    /// Wav2Vec2 model (ONNX backend)
    #[cfg(feature = "onnx")]
    Wav2Vec2(Wav2Vec2Model),
}

impl SpeechModel for DynSpeechModel {
    fn info(&self) -> &ModelInfo {
        match self {
            DynSpeechModel::Whisper(m) => SpeechModel::info(m),
            DynSpeechModel::DistilWhisper(m) => SpeechModel::info(m),
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(m) => SpeechModel::info(m),
        }
    }

    fn device(&self) -> &Device {
        match self {
            DynSpeechModel::Whisper(m) => SpeechModel::device(m),
            DynSpeechModel::DistilWhisper(m) => SpeechModel::device(m),
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(m) => SpeechModel::device(m),
        }
    }

    fn transcribe(
        &mut self,
        audio: &AudioData,
        options: TranscriptionOptions,
    ) -> Result<TranscriptionResult, AntennaError> {
        match self {
            DynSpeechModel::Whisper(m) => SpeechModel::transcribe(m, audio, options),
            DynSpeechModel::DistilWhisper(m) => SpeechModel::transcribe(m, audio, options),
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(m) => SpeechModel::transcribe(m, audio, options),
        }
    }

    fn detect_language(&mut self, audio: &AudioData) -> Result<String, AntennaError> {
        match self {
            DynSpeechModel::Whisper(m) => SpeechModel::detect_language(m, audio),
            DynSpeechModel::DistilWhisper(m) => SpeechModel::detect_language(m, audio),
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(m) => SpeechModel::detect_language(m, audio),
        }
    }

    fn preprocess_audio(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        match self {
            DynSpeechModel::Whisper(m) => SpeechModel::preprocess_audio(m, audio),
            DynSpeechModel::DistilWhisper(m) => SpeechModel::preprocess_audio(m, audio),
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(m) => SpeechModel::preprocess_audio(m, audio),
        }
    }
}

impl DynSpeechModel {
    /// Get the model family
    pub fn family(&self) -> ModelFamily {
        match self {
            DynSpeechModel::Whisper(_) => ModelFamily::Whisper,
            DynSpeechModel::DistilWhisper(_) => ModelFamily::DistilWhisper,
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(_) => ModelFamily::Wav2Vec2,
        }
    }

    /// Get the backend used by this model
    pub fn backend(&self) -> Backend {
        match self {
            DynSpeechModel::Whisper(_) => Backend::Candle,
            DynSpeechModel::DistilWhisper(_) => Backend::Candle,
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(_) => Backend::Onnx,
        }
    }

    /// Check if this model supports translation
    pub fn supports_translation(&self) -> bool {
        self.info().capabilities.supports_translation
    }

    /// Check if this model supports language detection
    pub fn supports_language_detection(&self) -> bool {
        self.info().capabilities.supports_language_detection
    }

    /// Translate audio to English (convenience method)
    pub fn translate(&mut self, audio: &AudioData) -> Result<TranscriptionResult, AntennaError> {
        match self {
            DynSpeechModel::Whisper(m) => SpeechModel::translate(m, audio),
            DynSpeechModel::DistilWhisper(m) => SpeechModel::translate(m, audio),
            #[cfg(feature = "onnx")]
            DynSpeechModel::Wav2Vec2(m) => SpeechModel::translate(m, audio),
        }
    }

    /// Try to get the underlying WhisperModel
    pub fn as_whisper(&self) -> Option<&WhisperModel> {
        match self {
            DynSpeechModel::Whisper(m) => Some(m),
            _ => None,
        }
    }

    /// Try to get the underlying WhisperModel mutably
    pub fn as_whisper_mut(&mut self) -> Option<&mut WhisperModel> {
        match self {
            DynSpeechModel::Whisper(m) => Some(m),
            _ => None,
        }
    }

    /// Try to get the underlying DistilWhisperModel
    pub fn as_distil_whisper(&self) -> Option<&DistilWhisperModel> {
        match self {
            DynSpeechModel::DistilWhisper(m) => Some(m),
            _ => None,
        }
    }

    /// Try to get the underlying DistilWhisperModel mutably
    pub fn as_distil_whisper_mut(&mut self) -> Option<&mut DistilWhisperModel> {
        match self {
            DynSpeechModel::DistilWhisper(m) => Some(m),
            _ => None,
        }
    }

    /// Try to get the underlying Wav2Vec2Model
    #[cfg(feature = "onnx")]
    pub fn as_wav2vec2(&self) -> Option<&Wav2Vec2Model> {
        match self {
            DynSpeechModel::Wav2Vec2(m) => Some(m),
            _ => None,
        }
    }

    /// Try to get the underlying Wav2Vec2Model mutably
    #[cfg(feature = "onnx")]
    pub fn as_wav2vec2_mut(&mut self) -> Option<&mut Wav2Vec2Model> {
        match self {
            DynSpeechModel::Wav2Vec2(m) => Some(m),
            _ => None,
        }
    }
}

/// Load a speech model by ID
///
/// This is the main entry point for loading any speech-to-text model supported
/// by Antenna. It automatically selects the best backend for the model family.
///
/// # Arguments
///
/// * `model_id` - Model identifier. Supports formats:
///   - `family/variant`: "whisper/base", "distil-whisper/small.en", "wav2vec2/base-960h"
///   - HuggingFace ID: "openai/whisper-base", "facebook/wav2vec2-base-960h"
/// * `device` - Device string: "cpu", "cuda", "cuda:0", "cuda:1"
/// * `backend` - Optional explicit backend selection. If None, auto-selects best.
///
/// # Returns
///
/// A `DynSpeechModel` wrapping the loaded model.
///
/// # Example
///
/// ```rust,ignore
/// // Load Whisper (uses Candle backend)
/// let model = load_model("whisper/base", "cuda", None)?;
///
/// // Load Wav2Vec2 (uses ONNX backend)
/// let model = load_model("wav2vec2/base-960h", "cpu", None)?;
///
/// // Force specific backend
/// let model = load_model("whisper/base", "cpu", Some("onnx"))?;
/// ```
pub fn load_model(
    model_id: &str,
    device: &str,
    backend: Option<&str>,
) -> Result<DynSpeechModel, AntennaError> {
    // Parse model specification
    let mut spec = ModelSpec::parse(model_id)?;

    // Parse backend if specified
    if let Some(backend_str) = backend {
        let backend = Backend::from_str(backend_str).ok_or_else(|| {
            AntennaError::ModelError(format!(
                "Unknown backend: '{}'. Supported: candle, onnx, ctranslate2, sherpa, parakeet",
                backend_str
            ))
        })?;
        spec = spec.with_backend(backend);
    }

    // Parse device
    let device_spec = DeviceSpec::from_str(device)?;

    // Select backend (explicit or auto)
    let selected_backend = if let Some(b) = spec.backend {
        // Validate explicit backend
        if !b.is_available() {
            return Err(AntennaError::ModelError(format!(
                "Backend '{}' requires the '{}' feature. Rebuild with: cargo build --features {}",
                b,
                b.feature_flag().unwrap_or("unknown"),
                b.feature_flag().unwrap_or("unknown")
            )));
        }
        b
    } else {
        // Auto-select based on model family
        spec.family.default_backend()
    };

    // Validate backend supports this model family
    let supported = spec.family.supported_backends();
    if !supported.contains(&selected_backend) {
        return Err(AntennaError::ModelError(format!(
            "Backend '{}' does not support {} models. Supported backends: {:?}",
            selected_backend,
            spec.family.default_backend(), // Use default as family name
            supported.iter().map(|b| b.to_string()).collect::<Vec<_>>()
        )));
    }

    // Load the model based on family and backend
    match (spec.family, selected_backend) {
        (ModelFamily::Whisper, Backend::Candle) => {
            let candle_device = device_spec.to_candle_device()?;
            let model = WhisperModel::from_size(&spec.variant, candle_device)?;
            Ok(DynSpeechModel::Whisper(model))
        }

        (ModelFamily::DistilWhisper, Backend::Candle) => {
            let candle_device = device_spec.to_candle_device()?;
            let model = DistilWhisperModel::from_size(&spec.variant, candle_device)?;
            Ok(DynSpeechModel::DistilWhisper(model))
        }

        #[cfg(feature = "onnx")]
        (ModelFamily::Wav2Vec2, Backend::Onnx) => {
            let hf_id = spec.hf_id();
            let model = Wav2Vec2Model::from_pretrained(&hf_id, device)?;
            Ok(DynSpeechModel::Wav2Vec2(model))
        }

        #[cfg(not(feature = "onnx"))]
        (ModelFamily::Wav2Vec2, _) => {
            Err(AntennaError::ModelError(
                "Wav2Vec2 models require the 'onnx' feature. Rebuild with: cargo build --features onnx".to_string()
            ))
        }

        (family, backend) => {
            Err(AntennaError::ModelError(format!(
                "Combination {:?} + {:?} is not yet implemented",
                family, backend
            )))
        }
    }
}

/// Model registry entry
#[derive(Debug, Clone)]
pub struct ModelEntry {
    /// Short model ID (family/variant format)
    pub id: String,
    /// Full HuggingFace model ID
    pub hf_id: String,
    /// Human-readable description
    pub description: String,
    /// Model family
    pub family: ModelFamily,
    /// Default backend
    pub default_backend: Backend,
    /// Required feature flag (if any)
    pub feature_flag: Option<String>,
}

/// List all available models
///
/// Returns a list of all models that can be loaded with `load_model()`.
/// Models requiring unavailable features are included but marked.
pub fn list_models() -> Vec<ModelEntry> {
    let mut models = Vec::new();

    // Whisper models
    for (size, hf_id) in [
        ("tiny", "openai/whisper-tiny"),
        ("base", "openai/whisper-base"),
        ("small", "openai/whisper-small"),
        ("medium", "openai/whisper-medium"),
        ("large", "openai/whisper-large"),
        ("large-v2", "openai/whisper-large-v2"),
        ("large-v3", "openai/whisper-large-v3"),
    ] {
        models.push(ModelEntry {
            id: format!("whisper/{}", size),
            hf_id: hf_id.to_string(),
            description: format!("OpenAI Whisper {} - Multilingual speech recognition", size),
            family: ModelFamily::Whisper,
            default_backend: Backend::Candle,
            feature_flag: None,
        });
    }

    // Distil-Whisper models
    for (size, hf_id, desc) in [
        ("distil-small.en", "distil-whisper/distil-small.en", "English-only, 2x faster"),
        ("distil-medium.en", "distil-whisper/distil-medium.en", "English-only, 2x faster"),
        ("distil-large-v2", "distil-whisper/distil-large-v2", "Multilingual, 2x faster"),
        ("distil-large-v3", "distil-whisper/distil-large-v3", "Multilingual, 2x faster"),
    ] {
        models.push(ModelEntry {
            id: format!("distil-whisper/{}", size),
            hf_id: hf_id.to_string(),
            description: format!("Distil-Whisper {} - {}", size, desc),
            family: ModelFamily::DistilWhisper,
            default_backend: Backend::Candle,
            feature_flag: None,
        });
    }

    // Wav2Vec2 models (require ONNX)
    for (size, hf_id, desc) in [
        ("base-960h", "facebook/wav2vec2-base-960h", "Base model, 960h training"),
        ("large-960h", "facebook/wav2vec2-large-960h", "Large model, 960h training"),
        ("large-960h-lv60-self", "facebook/wav2vec2-large-960h-lv60-self", "Large with self-training"),
    ] {
        models.push(ModelEntry {
            id: format!("wav2vec2/{}", size),
            hf_id: hf_id.to_string(),
            description: format!("Wav2Vec2 {} - {}", size, desc),
            family: ModelFamily::Wav2Vec2,
            default_backend: Backend::Onnx,
            feature_flag: Some("onnx".to_string()),
        });
    }

    models
}

/// Get models for a specific family
pub fn models_for_family(family: ModelFamily) -> Vec<ModelEntry> {
    list_models()
        .into_iter()
        .filter(|m| m.family == family)
        .collect()
}

/// Check if a model is available (all required features enabled)
pub fn is_model_available(model_id: &str) -> bool {
    let spec = match ModelSpec::parse(model_id) {
        Ok(s) => s,
        Err(_) => return false,
    };

    let backend = spec.backend.unwrap_or_else(|| spec.family.default_backend());
    backend.is_available()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_model_spec_parse_family_variant() {
        let spec = ModelSpec::parse("whisper/base").unwrap();
        assert_eq!(spec.family, ModelFamily::Whisper);
        assert_eq!(spec.variant, "base");
        assert_eq!(spec.hf_id(), "openai/whisper-base");
    }

    #[test]
    fn test_model_spec_parse_hf_format() {
        let spec = ModelSpec::parse("openai/whisper-large-v3").unwrap();
        assert_eq!(spec.family, ModelFamily::Whisper);
        assert_eq!(spec.variant, "large-v3");
        assert_eq!(spec.hf_id(), "openai/whisper-large-v3");
    }

    #[test]
    fn test_model_spec_parse_distil_whisper() {
        let spec = ModelSpec::parse("distil-whisper/distil-small.en").unwrap();
        assert_eq!(spec.family, ModelFamily::DistilWhisper);
        assert_eq!(spec.variant, "distil-small.en");
    }

    #[test]
    fn test_model_spec_parse_wav2vec2() {
        let spec = ModelSpec::parse("wav2vec2/base-960h").unwrap();
        assert_eq!(spec.family, ModelFamily::Wav2Vec2);
        assert_eq!(spec.variant, "base-960h");
    }

    #[test]
    fn test_model_spec_parse_invalid() {
        assert!(ModelSpec::parse("invalid").is_err());
        assert!(ModelSpec::parse("unknown/model").is_err());
    }

    #[test]
    fn test_list_models_not_empty() {
        let models = list_models();
        assert!(!models.is_empty());

        // Should have Whisper models
        assert!(models.iter().any(|m| m.family == ModelFamily::Whisper));

        // Should have Distil-Whisper models
        assert!(models.iter().any(|m| m.family == ModelFamily::DistilWhisper));
    }

    #[test]
    fn test_is_model_available() {
        // Whisper models are always available (Candle is default)
        assert!(is_model_available("whisper/base"));

        // Wav2Vec2 depends on ONNX feature
        #[cfg(feature = "onnx")]
        assert!(is_model_available("wav2vec2/base-960h"));

        #[cfg(not(feature = "onnx"))]
        assert!(!is_model_available("wav2vec2/base-960h"));
    }
}
