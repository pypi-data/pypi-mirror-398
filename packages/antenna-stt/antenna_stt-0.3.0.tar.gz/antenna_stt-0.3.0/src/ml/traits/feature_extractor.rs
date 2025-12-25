//! Feature extraction traits for audio preprocessing
//!
//! Different STT models use different audio representations:
//! - Whisper/Canary/Conformer: Mel spectrograms
//! - Wav2Vec2: Raw waveform or learned features
//! - Some models: MFCC features

use candle_core::{Device, Tensor};

use crate::audio;
use crate::error::AntennaError;
use crate::types::AudioData;

/// Type of features produced by an extractor
#[derive(Debug, Clone, PartialEq)]
pub enum FeatureType {
    /// Mel spectrogram features
    /// Used by Whisper, Canary, most Conformer variants
    MelSpectrogram {
        /// Number of mel frequency bins
        n_mels: usize,
        /// Hop length in samples (stride between frames)
        hop_length: usize,
        /// FFT window size
        n_fft: usize,
    },
    /// Mel-frequency cepstral coefficients
    /// Alternative for some Conformer/traditional ASR
    Mfcc {
        /// Number of MFCC coefficients
        n_mfcc: usize,
        /// Number of mel bins used to compute MFCCs
        n_mels: usize,
    },
    /// Raw waveform input
    /// Used by Wav2Vec2 and similar self-supervised models
    RawWaveform,
    /// Pre-computed filterbank features
    Filterbank {
        /// Number of filterbank channels
        n_filters: usize,
    },
}

/// Configuration for feature extraction
pub trait FeatureConfig: Send + Sync + Clone {
    /// Expected sample rate for this extractor
    fn sample_rate(&self) -> u32;

    /// Type of features produced
    fn feature_type(&self) -> FeatureType;

    /// Whether input audio should be converted to mono
    fn requires_mono(&self) -> bool {
        true
    }

    /// Whether to normalize audio before extraction
    fn normalize_audio(&self) -> bool {
        false
    }
}

/// Trait for audio feature extraction
///
/// This trait abstracts the conversion of raw audio into the features
/// expected by different model architectures.
///
/// # Feature Types
///
/// - **Mel Spectrogram**: Time-frequency representation using mel scale.
///   Output shape: `[batch, n_mels, time_frames]`
///
/// - **MFCC**: Mel-frequency cepstral coefficients, compact representation.
///   Output shape: `[batch, n_mfcc, time_frames]`
///
/// - **Raw Waveform**: Direct audio samples for models with learned frontends.
///   Output shape: `[batch, samples]`
pub trait FeatureExtractor: Send + Sync {
    /// The configuration type for this extractor
    type Config: FeatureConfig;

    /// Get the configuration for this extractor
    fn config(&self) -> &Self::Config;

    /// Extract features from audio data
    ///
    /// # Arguments
    /// * `audio` - Input audio (should be preprocessed to correct sample rate/channels)
    /// * `device` - Target device for output tensor
    ///
    /// # Returns
    /// Tensor with shape depending on feature type
    fn extract(&self, audio: &AudioData, device: &Device) -> Result<Tensor, AntennaError>;

    /// Preprocess audio to the expected format
    ///
    /// This method handles resampling and mono conversion based on the config.
    fn preprocess(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        let cfg = self.config();
        let mut processed = audio.clone();

        // Convert to mono if required
        if cfg.requires_mono() && processed.channels != 1 {
            processed = audio::convert_to_mono(&processed);
        }

        // Resample if needed
        if processed.sample_rate != cfg.sample_rate() {
            processed = audio::resample(&processed, cfg.sample_rate())?;
        }

        Ok(processed)
    }

    /// Get the expected sample rate
    fn sample_rate(&self) -> u32 {
        self.config().sample_rate()
    }

    /// Get the feature type produced
    fn feature_type(&self) -> FeatureType {
        self.config().feature_type()
    }
}

/// Standard mel spectrogram configuration used by Whisper
#[derive(Debug, Clone)]
pub struct WhisperMelConfig {
    /// Sample rate (16000 Hz for Whisper)
    pub sample_rate: u32,
    /// Number of mel bins (80 for Whisper)
    pub n_mels: usize,
    /// FFT window size (400 samples = 25ms at 16kHz)
    pub n_fft: usize,
    /// Hop length (160 samples = 10ms at 16kHz)
    pub hop_length: usize,
}

impl Default for WhisperMelConfig {
    fn default() -> Self {
        Self {
            sample_rate: 16000,
            n_mels: 80,
            n_fft: 400,
            hop_length: 160,
        }
    }
}

impl FeatureConfig for WhisperMelConfig {
    fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    fn feature_type(&self) -> FeatureType {
        FeatureType::MelSpectrogram {
            n_mels: self.n_mels,
            hop_length: self.hop_length,
            n_fft: self.n_fft,
        }
    }
}

/// Configuration for raw waveform features (Wav2Vec2)
#[derive(Debug, Clone)]
pub struct WaveformConfig {
    /// Sample rate (16000 Hz typical)
    pub sample_rate: u32,
    /// Whether to normalize waveform to [-1, 1]
    pub normalize: bool,
}

impl Default for WaveformConfig {
    fn default() -> Self {
        Self {
            sample_rate: 16000,
            normalize: true,
        }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_whisper_mel_config() {
        let cfg = WhisperMelConfig::default();
        assert_eq!(cfg.sample_rate(), 16000);
        assert!(matches!(
            cfg.feature_type(),
            FeatureType::MelSpectrogram { n_mels: 80, .. }
        ));
    }

    #[test]
    fn test_waveform_config() {
        let cfg = WaveformConfig::default();
        assert_eq!(cfg.sample_rate(), 16000);
        assert_eq!(cfg.feature_type(), FeatureType::RawWaveform);
    }
}
