//! Speech-to-Text backends
//!
//! This module provides pluggable STT backends for the streaming server.
//!
//! ## Available Backends
//!
//! - `WhisperBackend`: Native Whisper model via Candle (local inference)
//! - `TritonBackend`: NVIDIA Triton Inference Server (production, requires `triton` feature)
//!
//! ## Backend Selection
//!
//! Use the `BackendSelector` to automatically choose the best backend:
//!
//! ```ignore
//! use antenna::server::stt::{BackendSelector, BackendType};
//!
//! // Auto-select: Triton if available, fallback to Candle
//! let backend = BackendSelector::auto()
//!     .triton_url("http://triton:8001")
//!     .model("whisper_base")
//!     .device("cuda")
//!     .build()
//!     .await?;
//!
//! // Or explicitly choose:
//! let backend = BackendSelector::new(BackendType::Candle)
//!     .model("base")
//!     .device("cuda")
//!     .build()
//!     .await?;
//! ```

pub mod backend;
pub mod whisper_backend;

#[cfg(feature = "triton")]
pub mod triton;
#[cfg(feature = "triton")]
pub mod triton_backend;

pub use backend::{BackendCapabilities, BackendInfo, SttBackend, SttError, SttResult};
pub use whisper_backend::{WhisperBackend, WhisperBackendConfig};

#[cfg(feature = "triton")]
pub use triton::{TritonClient, TritonConfig};
#[cfg(feature = "triton")]
pub use triton_backend::{TritonBackend, TritonBackendConfig};

use std::sync::Arc;

/// Backend type selection
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BackendType {
    /// Native Candle-based Whisper (local inference)
    Candle,
    /// NVIDIA Triton Inference Server (production)
    #[cfg(feature = "triton")]
    Triton,
    /// Auto-select: try Triton first, fallback to Candle
    Auto,
}

impl Default for BackendType {
    fn default() -> Self {
        Self::Auto
    }
}

/// Builder for selecting and configuring STT backends
#[derive(Debug, Clone)]
pub struct BackendSelector {
    backend_type: BackendType,
    model: String,
    device: String,
    #[cfg(feature = "triton")]
    triton_url: Option<String>,
}

impl BackendSelector {
    /// Create a new selector with explicit backend type
    pub fn new(backend_type: BackendType) -> Self {
        Self {
            backend_type,
            model: "base".to_string(),
            device: "cpu".to_string(),
            #[cfg(feature = "triton")]
            triton_url: None,
        }
    }

    /// Auto-select backend (Triton if available, else Candle)
    pub fn auto() -> Self {
        Self::new(BackendType::Auto)
    }

    /// Use Candle backend
    pub fn candle() -> Self {
        Self::new(BackendType::Candle)
    }

    /// Use Triton backend
    #[cfg(feature = "triton")]
    pub fn triton() -> Self {
        Self::new(BackendType::Triton)
    }

    /// Set model name/size
    pub fn model(mut self, model: &str) -> Self {
        self.model = model.to_string();
        self
    }

    /// Set device (for Candle: "cpu", "cuda", "cuda:0")
    pub fn device(mut self, device: &str) -> Self {
        self.device = device.to_string();
        self
    }

    /// Set Triton server URL
    #[cfg(feature = "triton")]
    pub fn triton_url(mut self, url: &str) -> Self {
        self.triton_url = Some(url.to_string());
        self
    }

    /// Build the backend
    ///
    /// Returns a boxed trait object for flexibility.
    pub async fn build(self) -> SttResult<Arc<dyn SttBackend>> {
        match self.backend_type {
            BackendType::Candle => self.build_candle(),

            #[cfg(feature = "triton")]
            BackendType::Triton => self.build_triton().await,

            BackendType::Auto => self.build_auto().await,
        }
    }

    /// Build Candle backend
    fn build_candle(self) -> SttResult<Arc<dyn SttBackend>> {
        let config = WhisperBackendConfig {
            model_size: self.model,
            device: self.device,
            ..Default::default()
        };
        let backend = WhisperBackend::new(config)?;
        Ok(Arc::new(backend))
    }

    /// Build Triton backend
    #[cfg(feature = "triton")]
    async fn build_triton(self) -> SttResult<Arc<dyn SttBackend>> {
        let url = self.triton_url.unwrap_or_else(|| "http://localhost:8001".to_string());
        let config = TritonBackendConfig {
            url,
            model_name: self.model,
            ..Default::default()
        };
        let backend = TritonBackend::new(config).await?;
        Ok(Arc::new(backend))
    }

    /// Auto-select backend
    async fn build_auto(self) -> SttResult<Arc<dyn SttBackend>> {
        #[cfg(feature = "triton")]
        {
            // Try Triton first
            if let Some(url) = &self.triton_url {
                let config = TritonBackendConfig {
                    url: url.clone(),
                    model_name: self.model.clone(),
                    ..Default::default()
                };

                match TritonBackend::new(config).await {
                    Ok(backend) => {
                        tracing::info!("Using Triton backend at {}", url);
                        return Ok(Arc::new(backend));
                    }
                    Err(e) => {
                        tracing::warn!("Triton not available ({}), falling back to Candle", e);
                    }
                }
            }
        }

        // Fallback to Candle
        tracing::info!("Using Candle backend with model '{}' on '{}'", self.model, self.device);
        self.build_candle()
    }
}

/// Quick helper to create a Candle backend
pub fn candle_backend(model: &str, device: &str) -> SttResult<Arc<dyn SttBackend>> {
    let config = WhisperBackendConfig {
        model_size: model.to_string(),
        device: device.to_string(),
        ..Default::default()
    };
    let backend = WhisperBackend::new(config)?;
    Ok(Arc::new(backend))
}

/// Quick helper to create a Triton backend
#[cfg(feature = "triton")]
pub async fn triton_backend(url: &str, model: &str) -> SttResult<Arc<dyn SttBackend>> {
    let config = TritonBackendConfig {
        url: url.to_string(),
        model_name: model.to_string(),
        ..Default::default()
    };
    let backend = TritonBackend::new(config).await?;
    Ok(Arc::new(backend))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_backend_type_default() {
        assert_eq!(BackendType::default(), BackendType::Auto);
    }

    #[test]
    fn test_selector_builder() {
        let selector = BackendSelector::candle()
            .model("tiny")
            .device("cpu");

        assert_eq!(selector.model, "tiny");
        assert_eq!(selector.device, "cpu");
    }

    #[cfg(feature = "triton")]
    #[test]
    fn test_triton_selector() {
        let selector = BackendSelector::triton()
            .triton_url("http://triton:8001")
            .model("whisper_base");

        assert_eq!(selector.triton_url, Some("http://triton:8001".to_string()));
    }
}
