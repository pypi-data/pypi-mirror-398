//! Unified device abstraction across all inference backends
//!
//! This module provides a backend-agnostic device specification that can be
//! translated to each backend's native device type (Candle Device, ONNX
//! ExecutionProvider, etc.).

use crate::error::AntennaError;
use candle_core::Device as CandleDevice;
use std::fmt;

/// Unified device specification for all backends
///
/// This enum abstracts away backend-specific device handling, providing a
/// consistent interface for specifying where inference should run.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DeviceSpec {
    /// CPU execution (always available)
    Cpu,
    /// CUDA GPU execution
    Cuda {
        /// GPU device index (0-based)
        device_id: usize,
    },
    /// TensorRT-accelerated execution (ONNX backend only)
    /// Falls back to CUDA if TensorRT is not available
    TensorRT {
        /// GPU device index (0-based)
        device_id: usize,
    },
    /// Metal GPU execution (macOS only)
    Metal {
        /// GPU device index (0-based)
        device_id: usize,
    },
}

impl Default for DeviceSpec {
    fn default() -> Self {
        DeviceSpec::Cpu
    }
}

impl fmt::Display for DeviceSpec {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DeviceSpec::Cpu => write!(f, "cpu"),
            DeviceSpec::Cuda { device_id } => write!(f, "cuda:{}", device_id),
            DeviceSpec::TensorRT { device_id } => write!(f, "tensorrt:{}", device_id),
            DeviceSpec::Metal { device_id } => write!(f, "metal:{}", device_id),
        }
    }
}

impl DeviceSpec {
    /// Parse a device specification string
    ///
    /// Supported formats:
    /// - "cpu" - CPU execution
    /// - "cuda" or "cuda:0" - CUDA GPU (default device 0)
    /// - "gpu" - Alias for "cuda"
    /// - "tensorrt" or "tensorrt:0" - TensorRT acceleration
    /// - "metal" or "metal:0" - Metal GPU (macOS)
    pub fn from_str(s: &str) -> Result<Self, AntennaError> {
        let s = s.to_lowercase();
        let s = s.trim();

        if s == "cpu" {
            return Ok(DeviceSpec::Cpu);
        }

        // Handle cuda/gpu variants
        if s == "cuda" || s == "gpu" {
            return Ok(DeviceSpec::Cuda { device_id: 0 });
        }

        if let Some(id_str) = s.strip_prefix("cuda:") {
            let device_id = id_str
                .parse::<usize>()
                .map_err(|_| AntennaError::InvalidAudio(format!("Invalid CUDA device ID: {}", id_str)))?;
            return Ok(DeviceSpec::Cuda { device_id });
        }

        if let Some(id_str) = s.strip_prefix("gpu:") {
            let device_id = id_str
                .parse::<usize>()
                .map_err(|_| AntennaError::InvalidAudio(format!("Invalid GPU device ID: {}", id_str)))?;
            return Ok(DeviceSpec::Cuda { device_id });
        }

        // Handle tensorrt variants
        if s == "tensorrt" || s == "trt" {
            return Ok(DeviceSpec::TensorRT { device_id: 0 });
        }

        if let Some(id_str) = s.strip_prefix("tensorrt:") {
            let device_id = id_str
                .parse::<usize>()
                .map_err(|_| AntennaError::InvalidAudio(format!("Invalid TensorRT device ID: {}", id_str)))?;
            return Ok(DeviceSpec::TensorRT { device_id });
        }

        if let Some(id_str) = s.strip_prefix("trt:") {
            let device_id = id_str
                .parse::<usize>()
                .map_err(|_| AntennaError::InvalidAudio(format!("Invalid TensorRT device ID: {}", id_str)))?;
            return Ok(DeviceSpec::TensorRT { device_id });
        }

        // Handle metal variants
        if s == "metal" || s == "mps" {
            return Ok(DeviceSpec::Metal { device_id: 0 });
        }

        if let Some(id_str) = s.strip_prefix("metal:") {
            let device_id = id_str
                .parse::<usize>()
                .map_err(|_| AntennaError::InvalidAudio(format!("Invalid Metal device ID: {}", id_str)))?;
            return Ok(DeviceSpec::Metal { device_id });
        }

        Err(AntennaError::InvalidAudio(format!(
            "Unknown device specification: '{}'. Valid options: cpu, cuda, cuda:N, gpu, tensorrt, metal",
            s
        )))
    }

    /// Check if this is a GPU device (CUDA, TensorRT, or Metal)
    pub fn is_gpu(&self) -> bool {
        matches!(
            self,
            DeviceSpec::Cuda { .. } | DeviceSpec::TensorRT { .. } | DeviceSpec::Metal { .. }
        )
    }

    /// Check if this is a CUDA-based device (CUDA or TensorRT)
    pub fn is_cuda(&self) -> bool {
        matches!(self, DeviceSpec::Cuda { .. } | DeviceSpec::TensorRT { .. })
    }

    /// Get the device ID for GPU devices
    pub fn device_id(&self) -> Option<usize> {
        match self {
            DeviceSpec::Cpu => None,
            DeviceSpec::Cuda { device_id }
            | DeviceSpec::TensorRT { device_id }
            | DeviceSpec::Metal { device_id } => Some(*device_id),
        }
    }

    /// Convert to Candle Device
    ///
    /// Note: TensorRT falls back to CUDA since Candle doesn't support TensorRT.
    /// Metal is only available on macOS with the metal feature.
    pub fn to_candle_device(&self) -> Result<CandleDevice, AntennaError> {
        match self {
            DeviceSpec::Cpu => Ok(CandleDevice::Cpu),
            DeviceSpec::Cuda { device_id } | DeviceSpec::TensorRT { device_id } => {
                #[cfg(feature = "cuda")]
                {
                    CandleDevice::new_cuda(*device_id)
                        .map_err(|e| AntennaError::ModelError(format!("Failed to create CUDA device: {}", e)))
                }
                #[cfg(not(feature = "cuda"))]
                {
                    let _ = device_id;
                    Err(AntennaError::ModelError(
                        "CUDA support not enabled. Rebuild with --features cuda".into(),
                    ))
                }
            }
            DeviceSpec::Metal { device_id } => {
                #[cfg(feature = "metal")]
                {
                    CandleDevice::new_metal(*device_id)
                        .map_err(|e| AntennaError::ModelError(format!("Failed to create Metal device: {}", e)))
                }
                #[cfg(not(feature = "metal"))]
                {
                    let _ = device_id;
                    Err(AntennaError::ModelError(
                        "Metal support not enabled. Rebuild with --features metal".into(),
                    ))
                }
            }
        }
    }
}

/// Convert from Candle Device to DeviceSpec
///
/// Note: Candle's CudaDevice doesn't expose its ordinal directly,
/// so we default to device 0 for CUDA devices. Use DeviceSpec::from_str()
/// if you need to specify a specific device.
impl From<&CandleDevice> for DeviceSpec {
    fn from(device: &CandleDevice) -> Self {
        match device {
            CandleDevice::Cpu => DeviceSpec::Cpu,
            // Candle doesn't expose the ordinal, default to 0
            CandleDevice::Cuda(_) => DeviceSpec::Cuda { device_id: 0 },
            CandleDevice::Metal(_) => DeviceSpec::Metal { device_id: 0 },
        }
    }
}

impl From<CandleDevice> for DeviceSpec {
    fn from(device: CandleDevice) -> Self {
        DeviceSpec::from(&device)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_device_spec_parsing() {
        assert_eq!(DeviceSpec::from_str("cpu").unwrap(), DeviceSpec::Cpu);
        assert_eq!(
            DeviceSpec::from_str("cuda").unwrap(),
            DeviceSpec::Cuda { device_id: 0 }
        );
        assert_eq!(
            DeviceSpec::from_str("cuda:1").unwrap(),
            DeviceSpec::Cuda { device_id: 1 }
        );
        assert_eq!(
            DeviceSpec::from_str("gpu").unwrap(),
            DeviceSpec::Cuda { device_id: 0 }
        );
        assert_eq!(
            DeviceSpec::from_str("tensorrt").unwrap(),
            DeviceSpec::TensorRT { device_id: 0 }
        );
        assert_eq!(
            DeviceSpec::from_str("metal").unwrap(),
            DeviceSpec::Metal { device_id: 0 }
        );
    }

    #[test]
    fn test_device_spec_display() {
        assert_eq!(DeviceSpec::Cpu.to_string(), "cpu");
        assert_eq!(DeviceSpec::Cuda { device_id: 0 }.to_string(), "cuda:0");
        assert_eq!(DeviceSpec::TensorRT { device_id: 1 }.to_string(), "tensorrt:1");
    }

    #[test]
    fn test_is_gpu() {
        assert!(!DeviceSpec::Cpu.is_gpu());
        assert!(DeviceSpec::Cuda { device_id: 0 }.is_gpu());
        assert!(DeviceSpec::TensorRT { device_id: 0 }.is_gpu());
        assert!(DeviceSpec::Metal { device_id: 0 }.is_gpu());
    }

    #[test]
    fn test_case_insensitive() {
        assert_eq!(DeviceSpec::from_str("CPU").unwrap(), DeviceSpec::Cpu);
        assert_eq!(
            DeviceSpec::from_str("CUDA").unwrap(),
            DeviceSpec::Cuda { device_id: 0 }
        );
    }
}
