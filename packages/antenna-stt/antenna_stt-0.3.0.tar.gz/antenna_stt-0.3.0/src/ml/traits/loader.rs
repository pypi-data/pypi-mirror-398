//! Model loading traits
//!
//! Abstractions for loading models from different sources:
//! - HuggingFace Hub
//! - Local directories
//! - NeMo format (.nemo files for NVIDIA models)

use candle_core::Device;

use crate::error::AntennaError;

use super::SpeechModel;

/// Source from which to load a model
#[derive(Debug, Clone)]
pub enum ModelSource {
    /// HuggingFace Hub model ID (e.g., "openai/whisper-base")
    HuggingFace {
        /// Model ID on HuggingFace Hub
        model_id: String,
        /// Revision/branch (default: "main")
        revision: Option<String>,
    },
    /// Local directory containing model files
    Local {
        /// Path to the model directory
        path: String,
    },
    /// NeMo format model file (.nemo)
    /// Used for NVIDIA models like Canary
    Nemo {
        /// Path to the .nemo file
        path: String,
    },
    /// ONNX model file
    Onnx {
        /// Path to the .onnx file
        path: String,
    },
}

impl ModelSource {
    /// Create a HuggingFace source
    pub fn huggingface(model_id: impl Into<String>) -> Self {
        Self::HuggingFace {
            model_id: model_id.into(),
            revision: None,
        }
    }

    /// Create a HuggingFace source with a specific revision
    pub fn huggingface_revision(model_id: impl Into<String>, revision: impl Into<String>) -> Self {
        Self::HuggingFace {
            model_id: model_id.into(),
            revision: Some(revision.into()),
        }
    }

    /// Create a local source
    pub fn local(path: impl Into<String>) -> Self {
        Self::Local { path: path.into() }
    }

    /// Create a NeMo source
    pub fn nemo(path: impl Into<String>) -> Self {
        Self::Nemo { path: path.into() }
    }

    /// Create an ONNX source
    pub fn onnx(path: impl Into<String>) -> Self {
        Self::Onnx { path: path.into() }
    }

    /// Get a display string for this source
    pub fn display(&self) -> String {
        match self {
            Self::HuggingFace { model_id, revision } => {
                if let Some(rev) = revision {
                    format!("{}@{}", model_id, rev)
                } else {
                    model_id.clone()
                }
            }
            Self::Local { path } => format!("local:{}", path),
            Self::Nemo { path } => format!("nemo:{}", path),
            Self::Onnx { path } => format!("onnx:{}", path),
        }
    }
}

/// Trait for loading speech models
///
/// Each model family implements its own loader that knows how to
/// download/load and initialize models from various sources.
pub trait ModelLoader: Send + Sync {
    /// The type of model this loader produces
    type Model: SpeechModel;

    /// Load a model from a source
    ///
    /// # Arguments
    /// * `source` - Where to load the model from
    /// * `device` - Device to load the model onto
    fn load(&self, source: ModelSource, device: Device) -> Result<Self::Model, AntennaError>;

    /// Check if a model is cached locally
    fn is_cached(&self, source: &ModelSource) -> bool;

    /// List available model variants for this loader
    fn available_variants(&self) -> Vec<ModelVariant>;

    /// Get the model family name (e.g., "whisper", "wav2vec2")
    fn family(&self) -> &str;
}

/// Information about a model variant
#[derive(Debug, Clone)]
pub struct ModelVariant {
    /// Variant name (e.g., "tiny", "base", "large-v3")
    pub name: String,
    /// HuggingFace model ID
    pub model_id: String,
    /// Approximate model size in bytes
    pub size_bytes: Option<u64>,
    /// Brief description
    pub description: Option<String>,
}

impl ModelVariant {
    /// Create a new model variant
    pub fn new(name: impl Into<String>, model_id: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            model_id: model_id.into(),
            size_bytes: None,
            description: None,
        }
    }

    /// Set the size
    pub fn with_size(mut self, size_bytes: u64) -> Self {
        self.size_bytes = Some(size_bytes);
        self
    }

    /// Set the description
    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Parse a model ID string into family and variant
///
/// Supports formats:
/// - "whisper/base" -> ("whisper", "base")
/// - "openai/whisper-base" -> ("whisper", "base")
/// - "facebook/wav2vec2-base-960h" -> ("wav2vec2", "base-960h")
/// - "nvidia/canary-1b" -> ("canary", "1b")
pub fn parse_model_id(model_id: &str) -> Result<(String, String), AntennaError> {
    // Handle short format: "family/variant"
    if !model_id.contains('/') {
        return Err(AntennaError::ModelError(format!(
            "Invalid model ID format: '{}'. Expected 'family/variant' or HuggingFace ID.",
            model_id
        )));
    }

    let parts: Vec<&str> = model_id.split('/').collect();

    if parts.len() != 2 {
        return Err(AntennaError::ModelError(format!(
            "Invalid model ID format: '{}'. Expected 'org/model' format.",
            model_id
        )));
    }

    let org = parts[0].to_lowercase();
    let model = parts[1].to_lowercase();

    // Short format: whisper/base, wav2vec2/base - return directly
    if matches!(
        org.as_str(),
        "whisper" | "distil-whisper" | "wav2vec2" | "conformer" | "canary"
    ) {
        return Ok((org, model));
    }

    // Map organization to family
    let family = match org.as_str() {
        "openai" => {
            if model.starts_with("whisper") {
                "whisper"
            } else {
                return Err(AntennaError::ModelError(format!(
                    "Unknown OpenAI model: {}",
                    model
                )));
            }
        }
        "facebook" | "meta" => {
            if model.starts_with("wav2vec2") {
                "wav2vec2"
            } else {
                return Err(AntennaError::ModelError(format!(
                    "Unknown Facebook model: {}",
                    model
                )));
            }
        }
        "nvidia" => {
            if model.starts_with("canary") {
                "canary"
            } else if model.starts_with("conformer") {
                "conformer"
            } else {
                return Err(AntennaError::ModelError(format!(
                    "Unknown NVIDIA model: {}",
                    model
                )));
            }
        }
        _ => {
            return Err(AntennaError::ModelError(format!(
                "Unknown model organization: {}",
                org
            )));
        }
    };

    // Extract variant from model name
    let variant = if model.starts_with(family) {
        model
            .strip_prefix(family)
            .unwrap_or(&model)
            .trim_start_matches('-')
            .to_string()
    } else {
        model
    };

    Ok((family.to_string(), variant))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_model_source_display() {
        let source = ModelSource::huggingface("openai/whisper-base");
        assert_eq!(source.display(), "openai/whisper-base");

        let source = ModelSource::local("/path/to/model");
        assert_eq!(source.display(), "local:/path/to/model");

        let source = ModelSource::nemo("/path/to/model.nemo");
        assert_eq!(source.display(), "nemo:/path/to/model.nemo");
    }

    #[test]
    fn test_parse_model_id() {
        let (family, variant) = parse_model_id("openai/whisper-base").unwrap();
        assert_eq!(family, "whisper");
        assert_eq!(variant, "base");

        let (family, variant) = parse_model_id("whisper/tiny").unwrap();
        assert_eq!(family, "whisper");
        assert_eq!(variant, "tiny");

        let (family, variant) = parse_model_id("facebook/wav2vec2-base-960h").unwrap();
        assert_eq!(family, "wav2vec2");
        assert_eq!(variant, "base-960h");

        let (family, variant) = parse_model_id("nvidia/canary-1b").unwrap();
        assert_eq!(family, "canary");
        assert_eq!(variant, "1b");
    }

    #[test]
    fn test_model_variant() {
        let variant = ModelVariant::new("base", "openai/whisper-base")
            .with_size(74_000_000)
            .with_description("Base model, good balance of speed and accuracy");

        assert_eq!(variant.name, "base");
        assert_eq!(variant.size_bytes, Some(74_000_000));
    }
}
