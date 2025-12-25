//! ParakeetModel implementation using sherpa-rs

use std::fmt::{self, Debug};
use std::path::PathBuf;

use candle_core::Device;
use sherpa_rs::transducer::{TransducerConfig, TransducerRecognizer};

use crate::audio::process::{convert_to_mono, resample};
use crate::error::AntennaError;
use crate::ml::backends::DeviceSpec;
use crate::ml::traits::{
    ModelArchitecture, ModelCapabilities, ModelInfo, SpeechModel,
    TranscriptionOptions, TranscriptionResult, TranscriptionSegment,
};
use crate::types::AudioData;

use super::config::{ParakeetConfig, ParakeetSize};

/// Parakeet model using sherpa-rs for inference
///
/// Wraps NVIDIA's Parakeet FastConformer-TDT model via sherpa-onnx.
/// Provides extremely fast and accurate speech recognition.
pub struct ParakeetModel {
    /// Sherpa transducer recognizer
    recognizer: TransducerRecognizer,
    /// Model configuration
    config: ParakeetConfig,
    /// Device specification
    device_spec: DeviceSpec,
    /// Candle device (for compatibility with SpeechModel trait)
    device: Device,
    /// Model metadata
    model_info: ModelInfo,
}

impl Debug for ParakeetModel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ParakeetModel")
            .field("variant", &self.config.size)
            .field("device", &self.device_spec)
            .field("num_threads", &self.config.num_threads)
            .finish()
    }
}

impl ParakeetModel {
    /// Load a Parakeet model by variant name
    ///
    /// # Arguments
    ///
    /// * `variant` - Model variant (e.g., "tdt-0.6b-v2", "v3", "multilingual")
    /// * `device` - Device string ("cpu", "cuda", "cuda:0")
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// let model = ParakeetModel::from_size("tdt-0.6b-v2", "cpu")?;
    /// ```
    pub fn from_size(variant: &str, device: &str) -> Result<Self, AntennaError> {
        let size = ParakeetSize::from_variant(variant).ok_or_else(|| {
            AntennaError::ModelError(format!(
                "Unknown Parakeet variant: '{}'. Available: tdt-0.6b-v2, tdt-0.6b-v3, tdt-0.6b-en",
                variant
            ))
        })?;

        let config = ParakeetConfig::default().with_size(size);
        let device_spec = DeviceSpec::from_str(device)?;

        Self::from_config(config, device_spec)
    }

    /// Load a Parakeet model with explicit configuration
    pub fn from_config(config: ParakeetConfig, device_spec: DeviceSpec) -> Result<Self, AntennaError> {
        tracing::info!("Loading Parakeet model: {:?} on {:?}", config.size, device_spec);

        // Get or download model files
        let model_dir = Self::get_model_dir(&config)?;

        // Build TransducerConfig for sherpa-rs
        let transducer_config = Self::build_transducer_config(&config, &model_dir, &device_spec)?;

        // Create recognizer
        let recognizer = TransducerRecognizer::new(transducer_config)
            .map_err(|e| AntennaError::ModelError(format!("Failed to create Parakeet recognizer: {}", e)))?;

        // Create Candle device for trait compatibility
        let device = device_spec.to_candle_device()?;

        // Build model info
        let model_info = Self::build_model_info(&config);

        tracing::info!("Parakeet model loaded successfully");

        Ok(Self {
            recognizer,
            config,
            device_spec,
            device,
            model_info,
        })
    }

    /// Get or download model directory
    fn get_model_dir(config: &ParakeetConfig) -> Result<PathBuf, AntennaError> {
        // If custom model dir specified, use that
        if let Some(ref dir) = config.model_dir {
            let path = PathBuf::from(dir);
            if path.exists() {
                return Ok(path);
            }
            return Err(AntennaError::ModelError(format!(
                "Custom model directory not found: {}",
                dir
            )));
        }

        // Use HuggingFace cache directory for model storage
        let cache_dir = dirs::cache_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("antenna")
            .join("parakeet")
            .join(config.size.model_name());

        // Check if model already downloaded (try int8 first, then regular ONNX)
        if cache_dir.exists() {
            let encoder_int8 = cache_dir.join("encoder.int8.onnx");
            let encoder_onnx = cache_dir.join("encoder.onnx");
            if encoder_int8.exists() || encoder_onnx.exists() {
                tracing::info!("Using cached model from: {:?}", cache_dir);
                return Ok(cache_dir);
            }
        }

        // Download model
        tracing::info!(
            "Parakeet model not found in cache. Please download manually from:\n  {}\n\
            Extract to: {:?}",
            config.size.download_url(),
            cache_dir
        );

        Err(AntennaError::ModelError(format!(
            "Parakeet model not found. Download from: {}\n\
            Then extract to: {:?}\n\n\
            Example:\n  \
            wget {}\n  \
            tar xvf {}.tar.bz2 -C {:?}",
            config.size.download_url(),
            cache_dir,
            config.size.download_url(),
            config.size.model_name(),
            cache_dir.parent().unwrap_or(&cache_dir)
        )))
    }

    /// Find a model file, trying int8 version first, then regular ONNX
    fn find_model_file(model_dir: &PathBuf, name: &str) -> Result<PathBuf, AntennaError> {
        // Try int8 quantized model first (smaller, faster)
        let int8_path = model_dir.join(format!("{}.int8.onnx", name));
        if int8_path.exists() {
            return Ok(int8_path);
        }

        // Try regular ONNX model
        let onnx_path = model_dir.join(format!("{}.onnx", name));
        if onnx_path.exists() {
            return Ok(onnx_path);
        }

        Err(AntennaError::ModelError(format!(
            "Missing {} model file. Looked for: {:?} or {:?}",
            name, int8_path, onnx_path
        )))
    }

    /// Build sherpa-rs TransducerConfig
    fn build_transducer_config(
        config: &ParakeetConfig,
        model_dir: &PathBuf,
        device_spec: &DeviceSpec,
    ) -> Result<TransducerConfig, AntennaError> {
        // Try int8 models first (smaller, faster), then regular ONNX
        let encoder = Self::find_model_file(model_dir, "encoder")?;
        let decoder = Self::find_model_file(model_dir, "decoder")?;
        let joiner = Self::find_model_file(model_dir, "joiner")?;
        let tokens = model_dir.join("tokens.txt");

        // Verify tokens file exists
        if !tokens.exists() {
            return Err(AntennaError::ModelError(format!(
                "Missing tokens file: {:?}",
                tokens
            )));
        }

        let provider = match device_spec {
            DeviceSpec::Cpu => None,
            DeviceSpec::Cuda { .. } => Some("cuda".to_string()),
            DeviceSpec::TensorRT { .. } => Some("tensorrt".to_string()),
            DeviceSpec::Metal { .. } => Some("coreml".to_string()),
        };

        Ok(TransducerConfig {
            encoder: encoder.to_string_lossy().into_owned(),
            decoder: decoder.to_string_lossy().into_owned(),
            joiner: joiner.to_string_lossy().into_owned(),
            tokens: tokens.to_string_lossy().into_owned(),
            num_threads: config.num_threads as i32,
            sample_rate: 16000,
            feature_dim: 80,
            decoding_method: "greedy_search".to_string(),
            model_type: "nemo_transducer".to_string(),
            provider,
            debug: false,
            ..Default::default()
        })
    }

    /// Build model info from config
    fn build_model_info(config: &ParakeetConfig) -> ModelInfo {
        let languages: Vec<String> = config.size.languages()
            .into_iter()
            .map(String::from)
            .collect();

        let capabilities = ModelCapabilities {
            architecture: ModelArchitecture::Hybrid,
            supports_translation: false,
            supports_language_detection: config.size == ParakeetSize::Tdt06BV3,
            supports_timestamps: true,
            max_audio_duration: 600.0, // Can handle very long audio
            supported_languages: languages,
        };

        ModelInfo::new(
            format!("NVIDIA Parakeet {}", config.size.model_name()),
            "parakeet",
            config.size.model_name(),
        ).with_capabilities(capabilities)
    }

    /// Get the model size
    pub fn size(&self) -> ParakeetSize {
        self.config.size
    }
}

impl SpeechModel for ParakeetModel {
    fn info(&self) -> &ModelInfo {
        &self.model_info
    }

    fn device(&self) -> &Device {
        &self.device
    }

    fn transcribe(
        &mut self,
        audio: &AudioData,
        _options: TranscriptionOptions,
    ) -> Result<TranscriptionResult, AntennaError> {
        // Preprocess audio
        let processed = self.preprocess_audio(audio)?;

        tracing::debug!(
            "Processing audio: {} samples, {}Hz, {:.2}s",
            processed.samples.len(),
            processed.sample_rate,
            processed.duration()
        );

        // Run sherpa-rs transcription
        let text = self.recognizer.transcribe(processed.sample_rate, &processed.samples);

        // Clean up text (trim, normalize)
        let text = text.trim().to_lowercase();

        tracing::debug!("Transcribed: {}", text);

        // Build result
        let duration = processed.duration();
        let segment = TranscriptionSegment {
            start: 0.0,
            end: duration,
            text: text.clone(),
            tokens: vec![], // Sherpa doesn't expose tokens
            avg_logprob: None,
            no_speech_prob: None,
        };

        Ok(TranscriptionResult {
            text,
            segments: vec![segment],
            language: Some("en".to_string()), // TODO: language detection for v3
            language_probability: None,
        })
    }

    fn detect_language(&mut self, _audio: &AudioData) -> Result<String, AntennaError> {
        if !self.model_info.capabilities.supports_language_detection {
            return Err(AntennaError::ModelError(
                "This Parakeet variant does not support language detection. Use tdt-0.6b-v3 for multilingual support.".to_string(),
            ));
        }
        // TODO: Implement language detection using sherpa-rs language_id module
        Err(AntennaError::ModelError(
            "Language detection not yet implemented for Parakeet".to_string()
        ))
    }

    fn preprocess_audio(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        // Convert to mono
        let mono = convert_to_mono(audio);

        // Resample to 16kHz
        let resampled = resample(&mono, 16000)?;

        Ok(resampled)
    }

    fn expected_sample_rate(&self) -> u32 {
        16000
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_model_info() {
        let config = ParakeetConfig::default();
        let info = ParakeetModel::build_model_info(&config);

        assert_eq!(info.family, "parakeet");
        assert_eq!(info.capabilities.architecture, ModelArchitecture::Hybrid);
        assert!(!info.capabilities.supports_translation);
    }

    #[test]
    fn test_from_size_invalid() {
        let result = ParakeetModel::from_size("invalid-variant", "cpu");
        assert!(result.is_err());
    }
}
