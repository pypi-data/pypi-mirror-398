//! Raw waveform feature extraction
//!
//! Provides raw waveform preprocessing for models like Wav2Vec2 that
//! learn their own audio representations from raw audio samples.

use candle_core::{DType, Device, Tensor};

use crate::audio;
use crate::error::AntennaError;
use crate::ml::traits::{FeatureConfig, FeatureExtractor, FeatureType};
use crate::types::AudioData;

/// Configuration for raw waveform features
#[derive(Debug, Clone)]
pub struct WaveformConfig {
    /// Expected sample rate (typically 16000 Hz)
    pub sample_rate: u32,
    /// Whether to normalize waveform to [-1, 1]
    pub normalize: bool,
    /// Maximum duration in seconds (None for unlimited)
    pub max_duration: Option<f32>,
    /// Whether to pad shorter audio
    pub pad_to_max: bool,
}

impl WaveformConfig {
    /// Create a Wav2Vec2-compatible waveform config
    pub fn wav2vec2() -> Self {
        Self {
            sample_rate: 16000,
            normalize: true,
            max_duration: Some(30.0),
            pad_to_max: false,
        }
    }
}

impl Default for WaveformConfig {
    fn default() -> Self {
        Self::wav2vec2()
    }
}

impl FeatureConfig for WaveformConfig {
    fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    fn feature_type(&self) -> FeatureType {
        FeatureType::RawWaveform
    }

    fn normalize_audio(&self) -> bool {
        self.normalize
    }
}

/// Raw waveform feature extractor
///
/// Prepares raw audio waveforms for models that learn their own
/// audio representations (like Wav2Vec2).
#[derive(Debug, Clone)]
pub struct WaveformExtractor {
    config: WaveformConfig,
}

impl WaveformExtractor {
    /// Create a new waveform extractor with the given configuration
    pub fn new(config: WaveformConfig) -> Self {
        Self { config }
    }

    /// Create a Wav2Vec2-compatible extractor
    pub fn wav2vec2() -> Self {
        Self::new(WaveformConfig::wav2vec2())
    }

    /// Extract waveform tensor from audio samples
    pub fn extract_from_samples(
        &self,
        samples: &[f32],
        device: &Device,
    ) -> Result<Tensor, AntennaError> {
        let mut processed = samples.to_vec();

        // Normalize if configured
        if self.config.normalize {
            let max_abs = processed
                .iter()
                .map(|x| x.abs())
                .fold(0.0f32, f32::max);

            if max_abs > 0.0 {
                for sample in &mut processed {
                    *sample /= max_abs;
                }
            }
        }

        // Handle max duration
        if let Some(max_duration) = self.config.max_duration {
            let max_samples = (max_duration * self.config.sample_rate as f32) as usize;

            if processed.len() > max_samples {
                processed.truncate(max_samples);
            } else if self.config.pad_to_max && processed.len() < max_samples {
                processed.resize(max_samples, 0.0);
            }
        }

        // Create tensor with shape [1, samples]
        let n_samples = processed.len();
        Tensor::from_vec(processed, (1, n_samples), device)
            .map_err(|e| {
                AntennaError::PreprocessingError(format!("Failed to create waveform tensor: {}", e))
            })?
            .to_dtype(DType::F32)
            .map_err(|e| AntennaError::PreprocessingError(format!("Failed to convert dtype: {}", e)))
    }
}

impl FeatureExtractor for WaveformExtractor {
    type Config = WaveformConfig;

    fn config(&self) -> &Self::Config {
        &self.config
    }

    fn extract(&self, audio: &AudioData, device: &Device) -> Result<Tensor, AntennaError> {
        let processed = self.preprocess(audio)?;
        self.extract_from_samples(&processed.samples, device)
    }

    fn preprocess(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        let mut processed = audio.clone();

        // Convert to mono if needed
        if processed.channels != 1 {
            processed = audio::convert_to_mono(&processed);
        }

        // Resample if needed
        if processed.sample_rate != self.config.sample_rate {
            processed = audio::resample(&processed, self.config.sample_rate)?;
        }

        Ok(processed)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_waveform_config() {
        let cfg = WaveformConfig::wav2vec2();
        assert_eq!(cfg.sample_rate, 16000);
        assert!(cfg.normalize);
        assert_eq!(cfg.max_duration, Some(30.0));
    }

    #[test]
    fn test_waveform_extraction() {
        let extractor = WaveformExtractor::wav2vec2();

        // Create 1 second of audio
        let samples: Vec<f32> = (0..16000)
            .map(|i| (i as f32 / 16000.0 * 2.0 * std::f32::consts::PI * 440.0).sin() * 0.5)
            .collect();

        let device = Device::Cpu;
        let waveform = extractor.extract_from_samples(&samples, &device).unwrap();

        let shape = waveform.dims();
        assert_eq!(shape[0], 1); // Batch size
        assert_eq!(shape[1], 16000); // Samples
    }

    #[test]
    fn test_waveform_normalization() {
        let extractor = WaveformExtractor::wav2vec2();

        // Create audio with values > 1.0
        let samples = vec![2.0f32; 1000];

        let device = Device::Cpu;
        let waveform = extractor.extract_from_samples(&samples, &device).unwrap();

        // After normalization, max should be 1.0
        let data: Vec<f32> = waveform.flatten_all().unwrap().to_vec1().unwrap();
        let max_val = data.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        assert!((max_val - 1.0).abs() < 0.001);
    }
}
