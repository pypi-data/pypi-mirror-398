//! ONNX Runtime backend for cross-platform inference
//!
//! This module provides a wrapper around ONNX Runtime via the `ort` crate,
//! enabling inference of ONNX models with various execution providers:
//!
//! - **CPU**: Always available, good for portable deployments
//! - **CUDA**: GPU acceleration on NVIDIA hardware
//! - **TensorRT**: Optimized GPU inference (requires warmup)
//!
//! # Example
//!
//! ```rust,ignore
//! use antenna::ml::backends::onnx::{OnnxSession, ExecutionProvider};
//!
//! // Load a model with CUDA acceleration
//! let session = OnnxSession::from_file("model.onnx", ExecutionProvider::Cuda)?;
//!
//! // Run inference using the underlying session
//! let outputs = session.inner().run(ort::inputs![input_tensor]?)?;
//! ```

use crate::error::AntennaError;
use crate::ml::backends::DeviceSpec;
use ort::execution_providers::{CPUExecutionProvider, CUDAExecutionProvider};
use ort::session::Session;
use std::path::Path;

/// ONNX Runtime execution providers
///
/// Determines which hardware/software backend is used for inference.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ExecutionProvider {
    /// CPU execution (always available)
    #[default]
    Cpu,
    /// CUDA GPU acceleration
    Cuda,
    /// TensorRT optimized inference (NVIDIA only)
    /// Falls back to CUDA if TensorRT is not available
    TensorRT,
    /// DirectML (Windows GPU acceleration)
    DirectML,
    /// CoreML (macOS/iOS acceleration)
    CoreML,
}

impl ExecutionProvider {
    /// Create from DeviceSpec
    pub fn from_device_spec(spec: &DeviceSpec) -> Self {
        match spec {
            DeviceSpec::Cpu => ExecutionProvider::Cpu,
            DeviceSpec::Cuda { .. } => ExecutionProvider::Cuda,
            DeviceSpec::TensorRT { .. } => ExecutionProvider::TensorRT,
            DeviceSpec::Metal { .. } => ExecutionProvider::CoreML,
        }
    }

    /// Check if this provider requires a GPU
    pub fn requires_gpu(&self) -> bool {
        matches!(
            self,
            ExecutionProvider::Cuda
                | ExecutionProvider::TensorRT
                | ExecutionProvider::DirectML
                | ExecutionProvider::CoreML
        )
    }
}

impl std::fmt::Display for ExecutionProvider {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExecutionProvider::Cpu => write!(f, "CPU"),
            ExecutionProvider::Cuda => write!(f, "CUDA"),
            ExecutionProvider::TensorRT => write!(f, "TensorRT"),
            ExecutionProvider::DirectML => write!(f, "DirectML"),
            ExecutionProvider::CoreML => write!(f, "CoreML"),
        }
    }
}

/// ONNX Runtime session wrapper
///
/// Manages an ONNX Runtime inference session with the configured
/// execution provider. Provides a simplified interface for running
/// inference on ONNX models.
pub struct OnnxSession {
    session: Session,
    provider: ExecutionProvider,
}

impl std::fmt::Debug for OnnxSession {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("OnnxSession")
            .field("provider", &self.provider)
            .finish_non_exhaustive()
    }
}

impl OnnxSession {
    /// Create a new ONNX session from a model file
    ///
    /// # Arguments
    ///
    /// * `model_path` - Path to the ONNX model file
    /// * `provider` - Execution provider to use
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// let session = OnnxSession::from_file("model.onnx", ExecutionProvider::Cuda)?;
    /// ```
    pub fn from_file<P: AsRef<Path>>(
        model_path: P,
        provider: ExecutionProvider,
    ) -> Result<Self, AntennaError> {
        let path = model_path.as_ref();

        if !path.exists() {
            return Err(AntennaError::IoError(format!(
                "ONNX model file not found: {}",
                path.display()
            )));
        }

        let session = Self::build_session_from_file(path, provider)?;

        Ok(Self { session, provider })
    }

    /// Create a new ONNX session from model bytes
    ///
    /// # Arguments
    ///
    /// * `model_bytes` - Raw ONNX model data
    /// * `provider` - Execution provider to use
    pub fn from_bytes(model_bytes: &[u8], provider: ExecutionProvider) -> Result<Self, AntennaError> {
        let session = Self::build_session_from_bytes(model_bytes, provider)?;

        Ok(Self { session, provider })
    }

    /// Build session from file with the specified execution provider
    fn build_session_from_file<P: AsRef<Path>>(
        model_path: P,
        provider: ExecutionProvider,
    ) -> Result<Session, AntennaError> {
        match provider {
            ExecutionProvider::TensorRT => {
                #[cfg(feature = "onnx-tensorrt")]
                {
                    use ort::execution_providers::TensorRTExecutionProvider;
                    Session::builder()
                        .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                        .with_execution_providers([
                            TensorRTExecutionProvider::default().build(),
                            CUDAExecutionProvider::default().build(),
                            CPUExecutionProvider::default().build(),
                        ])
                        .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                        .commit_from_file(model_path)
                        .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
                }
                #[cfg(not(feature = "onnx-tensorrt"))]
                {
                    Err(AntennaError::ModelError(
                        "TensorRT requires 'onnx-tensorrt' feature".into(),
                    ))
                }
            }
            ExecutionProvider::Cuda => {
                Session::builder()
                    .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                    .with_execution_providers([
                        CUDAExecutionProvider::default().build(),
                        CPUExecutionProvider::default().build(),
                    ])
                    .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                    .commit_from_file(model_path)
                    .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
            }
            ExecutionProvider::DirectML => {
                #[cfg(target_os = "windows")]
                {
                    use ort::execution_providers::DirectMLExecutionProvider;
                    Session::builder()
                        .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                        .with_execution_providers([
                            DirectMLExecutionProvider::default().build(),
                            CPUExecutionProvider::default().build(),
                        ])
                        .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                        .commit_from_file(model_path)
                        .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
                }
                #[cfg(not(target_os = "windows"))]
                {
                    Err(AntennaError::ModelError(
                        "DirectML is only available on Windows".into(),
                    ))
                }
            }
            ExecutionProvider::CoreML => {
                #[cfg(target_os = "macos")]
                {
                    use ort::execution_providers::CoreMLExecutionProvider;
                    Session::builder()
                        .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                        .with_execution_providers([
                            CoreMLExecutionProvider::default().build(),
                            CPUExecutionProvider::default().build(),
                        ])
                        .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                        .commit_from_file(model_path)
                        .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
                }
                #[cfg(not(target_os = "macos"))]
                {
                    Err(AntennaError::ModelError(
                        "CoreML is only available on macOS".into(),
                    ))
                }
            }
            ExecutionProvider::Cpu => {
                Session::builder()
                    .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                    .with_execution_providers([CPUExecutionProvider::default().build()])
                    .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                    .commit_from_file(model_path)
                    .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
            }
        }
    }

    /// Build session from bytes with the specified execution provider
    fn build_session_from_bytes(
        model_bytes: &[u8],
        provider: ExecutionProvider,
    ) -> Result<Session, AntennaError> {
        match provider {
            ExecutionProvider::Cuda => {
                Session::builder()
                    .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                    .with_execution_providers([
                        CUDAExecutionProvider::default().build(),
                        CPUExecutionProvider::default().build(),
                    ])
                    .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                    .commit_from_memory(model_bytes)
                    .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
            }
            ExecutionProvider::Cpu | _ => {
                Session::builder()
                    .map_err(|e| AntennaError::ModelError(format!("Session builder error: {}", e)))?
                    .with_execution_providers([CPUExecutionProvider::default().build()])
                    .map_err(|e| AntennaError::ModelError(format!("Provider error: {}", e)))?
                    .commit_from_memory(model_bytes)
                    .map_err(|e| AntennaError::ModelError(format!("Failed to load ONNX model: {}", e)))
            }
        }
    }

    /// Get the execution provider used by this session
    pub fn provider(&self) -> ExecutionProvider {
        self.provider
    }

    /// Get the input names for this model
    pub fn input_names(&self) -> Vec<String> {
        self.session
            .inputs
            .iter()
            .map(|input| input.name.clone())
            .collect()
    }

    /// Get the output names for this model
    pub fn output_names(&self) -> Vec<String> {
        self.session
            .outputs
            .iter()
            .map(|output| output.name.clone())
            .collect()
    }

    /// Get a reference to the underlying ort Session
    ///
    /// Use this to run inference directly:
    /// ```rust,ignore
    /// let outputs = session.inner().run(ort::inputs![tensor]?)?;
    /// ```
    pub fn inner(&self) -> &Session {
        &self.session
    }

    /// Get a mutable reference to the underlying ort Session
    pub fn inner_mut(&mut self) -> &mut Session {
        &mut self.session
    }
}

/// Check if ONNX Runtime CUDA support is available at compile time
pub fn is_cuda_available() -> bool {
    cfg!(feature = "onnx-cuda") || cfg!(feature = "onnx-tensorrt")
}

/// Get the ONNX Runtime version string
pub fn ort_version() -> &'static str {
    "2.0.0-rc"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_execution_provider_display() {
        assert_eq!(ExecutionProvider::Cpu.to_string(), "CPU");
        assert_eq!(ExecutionProvider::Cuda.to_string(), "CUDA");
        assert_eq!(ExecutionProvider::TensorRT.to_string(), "TensorRT");
    }

    #[test]
    fn test_execution_provider_from_device_spec() {
        assert_eq!(
            ExecutionProvider::from_device_spec(&DeviceSpec::Cpu),
            ExecutionProvider::Cpu
        );
        assert_eq!(
            ExecutionProvider::from_device_spec(&DeviceSpec::Cuda { device_id: 0 }),
            ExecutionProvider::Cuda
        );
        assert_eq!(
            ExecutionProvider::from_device_spec(&DeviceSpec::TensorRT { device_id: 0 }),
            ExecutionProvider::TensorRT
        );
    }

    #[test]
    fn test_execution_provider_requires_gpu() {
        assert!(!ExecutionProvider::Cpu.requires_gpu());
        assert!(ExecutionProvider::Cuda.requires_gpu());
        assert!(ExecutionProvider::TensorRT.requires_gpu());
    }

    #[test]
    fn test_session_missing_file() {
        let result = OnnxSession::from_file("nonexistent.onnx", ExecutionProvider::Cpu);
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert!(err.to_string().contains("not found"));
    }
}
