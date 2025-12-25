//! Mel spectrogram feature extraction
//!
//! Provides mel spectrogram computation for models like Whisper, Canary, and Conformer.
//! The mel spectrogram is a time-frequency representation that mimics human auditory
//! perception by using mel-scaled frequency bins.

use candle_core::{DType, Device, Tensor};

use crate::audio;
use crate::error::AntennaError;
use crate::ml::traits::{FeatureConfig, FeatureExtractor, FeatureType};
use crate::types::AudioData;

/// Configuration for mel spectrogram extraction
#[derive(Debug, Clone)]
pub struct MelConfig {
    /// Expected sample rate (typically 16000 Hz for STT models)
    pub sample_rate: u32,
    /// Number of mel frequency bins
    pub n_mels: usize,
    /// FFT window size in samples
    pub n_fft: usize,
    /// Hop length (stride) in samples
    pub hop_length: usize,
    /// Target duration in seconds (audio will be padded/truncated)
    pub target_duration: Option<f32>,
    /// Whether to apply log scaling
    pub log_scale: bool,
    /// Whether to normalize the output
    pub normalize: bool,
}

impl MelConfig {
    /// Create a Whisper-compatible mel config
    ///
    /// Whisper uses:
    /// - 16kHz sample rate
    /// - 80 mel bins
    /// - 400 sample FFT window (25ms)
    /// - 160 sample hop (10ms)
    /// - 30 second target duration
    pub fn whisper() -> Self {
        Self {
            sample_rate: 16000,
            n_mels: 80,
            n_fft: 400,
            hop_length: 160,
            target_duration: Some(30.0),
            log_scale: true,
            normalize: true,
        }
    }

    /// Create a Canary-compatible mel config
    ///
    /// Canary (FastConformer) typically uses similar settings to Whisper
    pub fn canary() -> Self {
        Self {
            sample_rate: 16000,
            n_mels: 80,
            n_fft: 512,
            hop_length: 160,
            target_duration: None, // Canary handles variable length
            log_scale: true,
            normalize: true,
        }
    }

    /// Create a generic Conformer mel config
    pub fn conformer() -> Self {
        Self {
            sample_rate: 16000,
            n_mels: 80,
            n_fft: 512,
            hop_length: 160,
            target_duration: None,
            log_scale: true,
            normalize: true,
        }
    }
}

impl Default for MelConfig {
    fn default() -> Self {
        Self::whisper()
    }
}

impl FeatureConfig for MelConfig {
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

/// Mel spectrogram feature extractor
///
/// Converts raw audio waveforms into mel-scaled spectrograms suitable
/// for speech recognition models.
#[derive(Debug, Clone)]
pub struct MelExtractor {
    config: MelConfig,
    /// Pre-computed mel filter bank
    mel_filters: Vec<f32>,
}

impl MelExtractor {
    /// Create a new mel extractor with the given configuration
    pub fn new(config: MelConfig) -> Self {
        let mel_filters = Self::create_mel_filters(config.n_mels, config.n_fft, config.sample_rate);
        Self { config, mel_filters }
    }

    /// Create a Whisper-compatible extractor
    pub fn whisper() -> Self {
        Self::new(MelConfig::whisper())
    }

    /// Create a Canary-compatible extractor
    pub fn canary() -> Self {
        Self::new(MelConfig::canary())
    }

    /// Create a Conformer-compatible extractor
    pub fn conformer() -> Self {
        Self::new(MelConfig::conformer())
    }

    /// Create extractor with pre-computed mel filters (for Whisper models with custom filters)
    pub fn with_filters(config: MelConfig, mel_filters: Vec<f32>) -> Self {
        Self { config, mel_filters }
    }

    /// Get the mel filter bank
    pub fn mel_filters(&self) -> &[f32] {
        &self.mel_filters
    }

    /// Create mel filter bank
    ///
    /// Creates triangular mel-scaled filters that convert FFT bins to mel bins.
    fn create_mel_filters(n_mels: usize, n_fft: usize, sample_rate: u32) -> Vec<f32> {
        let n_freqs = n_fft / 2 + 1;
        let mut filters = vec![0.0f32; n_mels * n_freqs];

        // Convert Hz to mel scale
        let hz_to_mel = |hz: f32| 2595.0 * (1.0 + hz / 700.0).log10();
        let mel_to_hz = |mel: f32| 700.0 * (10.0f32.powf(mel / 2595.0) - 1.0);

        let mel_min = hz_to_mel(0.0);
        let mel_max = hz_to_mel(sample_rate as f32 / 2.0);

        // Create mel points
        let mel_points: Vec<f32> = (0..=n_mels + 1)
            .map(|i| mel_min + (mel_max - mel_min) * (i as f32) / ((n_mels + 1) as f32))
            .collect();

        // Convert mel points to FFT bin indices
        let bin_points: Vec<usize> = mel_points
            .iter()
            .map(|&mel| {
                let hz = mel_to_hz(mel);
                let bin = (n_fft as f32 * hz / sample_rate as f32).round() as usize;
                bin.min(n_freqs - 1)
            })
            .collect();

        // Create triangular filters
        for m in 0..n_mels {
            let left = bin_points[m];
            let center = bin_points[m + 1];
            let right = bin_points[m + 2];

            // Rising edge
            for k in left..center {
                if center > left {
                    filters[m * n_freqs + k] = (k - left) as f32 / (center - left) as f32;
                }
            }

            // Falling edge
            for k in center..right {
                if right > center {
                    filters[m * n_freqs + k] = (right - k) as f32 / (right - center) as f32;
                }
            }
        }

        filters
    }

    /// Compute Short-Time Fourier Transform
    fn compute_stft(&self, samples: &[f32]) -> Result<Vec<(f32, f32)>, AntennaError> {
        let n_fft = self.config.n_fft;
        let hop_length = self.config.hop_length;
        let n_freqs = n_fft / 2 + 1;

        if samples.len() < n_fft {
            return Err(AntennaError::PreprocessingError(
                "Audio too short for STFT".to_string(),
            ));
        }

        let n_frames = (samples.len() - n_fft) / hop_length + 1;

        // Create Hann window
        let window: Vec<f32> = (0..n_fft)
            .map(|i| {
                let t = std::f32::consts::PI * 2.0 * (i as f32) / (n_fft as f32);
                0.5 * (1.0 - t.cos())
            })
            .collect();

        let mut stft = Vec::with_capacity(n_frames * n_freqs);

        for frame_idx in 0..n_frames {
            let start = frame_idx * hop_length;

            // Apply window
            let windowed: Vec<f32> = (0..n_fft)
                .map(|i| {
                    let sample = samples.get(start + i).copied().unwrap_or(0.0);
                    sample * window[i]
                })
                .collect();

            // Compute DFT (real FFT)
            for k in 0..n_freqs {
                let mut real = 0.0f32;
                let mut imag = 0.0f32;

                for (n, &sample) in windowed.iter().enumerate() {
                    let angle = -2.0 * std::f32::consts::PI * (k as f32) * (n as f32) / (n_fft as f32);
                    real += sample * angle.cos();
                    imag += sample * angle.sin();
                }

                stft.push((real, imag));
            }
        }

        Ok(stft)
    }

    /// Extract mel spectrogram from audio samples
    pub fn extract_from_samples(
        &self,
        samples: &[f32],
        device: &Device,
    ) -> Result<Tensor, AntennaError> {
        let n_mels = self.config.n_mels;
        let n_fft = self.config.n_fft;
        let n_freqs = n_fft / 2 + 1;

        // Pad or truncate to target duration if specified
        let processed_samples = if let Some(target_duration) = self.config.target_duration {
            let target_samples = (target_duration * self.config.sample_rate as f32) as usize;
            if samples.len() >= target_samples {
                samples[..target_samples].to_vec()
            } else {
                let mut padded = samples.to_vec();
                padded.resize(target_samples, 0.0);
                padded
            }
        } else {
            samples.to_vec()
        };

        // Compute STFT
        let stft = self.compute_stft(&processed_samples)?;

        // Convert to power spectrogram
        let power_spec: Vec<f32> = stft.iter().map(|(re, im)| re * re + im * im).collect();
        let n_frames = power_spec.len() / n_freqs;

        // Apply mel filter bank
        let mut mel_spec = vec![0.0f32; n_mels * n_frames];

        for frame in 0..n_frames {
            for mel in 0..n_mels {
                let mut sum = 0.0f32;
                for freq in 0..n_freqs {
                    let filter_val = self.mel_filters.get(mel * n_freqs + freq).copied().unwrap_or(0.0);
                    let power_val = power_spec.get(frame * n_freqs + freq).copied().unwrap_or(0.0);
                    sum += filter_val * power_val;
                }
                mel_spec[mel * n_frames + frame] = sum;
            }
        }

        // Apply log scaling if configured
        let processed_spec = if self.config.log_scale {
            mel_spec
                .iter()
                .map(|&x| {
                    let clamped = x.max(1e-10);
                    clamped.log10().max(-10.0)
                })
                .collect::<Vec<_>>()
        } else {
            mel_spec
        };

        // Normalize if configured
        let final_spec = if self.config.normalize {
            let max_val = processed_spec.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
            processed_spec
                .iter()
                .map(|&x| (x.max(max_val - 8.0) + 4.0) / 4.0)
                .collect::<Vec<_>>()
        } else {
            processed_spec
        };

        // Create tensor with shape [1, n_mels, n_frames]
        Tensor::from_vec(final_spec, (1, n_mels, n_frames), device)
            .map_err(|e| AntennaError::PreprocessingError(format!("Failed to create mel tensor: {}", e)))?
            .to_dtype(DType::F32)
            .map_err(|e| AntennaError::PreprocessingError(format!("Failed to convert dtype: {}", e)))
    }
}

impl FeatureExtractor for MelExtractor {
    type Config = MelConfig;

    fn config(&self) -> &Self::Config {
        &self.config
    }

    fn extract(&self, audio: &AudioData, device: &Device) -> Result<Tensor, AntennaError> {
        // Preprocess audio first
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
    fn test_mel_config_whisper() {
        let cfg = MelConfig::whisper();
        assert_eq!(cfg.sample_rate, 16000);
        assert_eq!(cfg.n_mels, 80);
        assert_eq!(cfg.n_fft, 400);
        assert_eq!(cfg.hop_length, 160);
        assert_eq!(cfg.target_duration, Some(30.0));
    }

    #[test]
    fn test_mel_filter_creation() {
        let extractor = MelExtractor::whisper();
        let filters = extractor.mel_filters();

        // 80 mel bins * 201 frequency bins
        assert_eq!(filters.len(), 80 * 201);

        // Filters should sum to approximately 1.0 for each frequency bin
        // (within the mel range)
    }

    #[test]
    fn test_stft_computation() {
        let extractor = MelExtractor::whisper();

        // Generate a simple sine wave
        let sample_rate = 16000;
        let duration = 0.1; // 100ms
        let freq = 440.0;

        let samples: Vec<f32> = (0..(sample_rate as f32 * duration) as usize)
            .map(|i| {
                let t = i as f32 / sample_rate as f32;
                (2.0 * std::f32::consts::PI * freq * t).sin()
            })
            .collect();

        let stft = extractor.compute_stft(&samples).unwrap();
        assert!(!stft.is_empty());
    }

    #[test]
    fn test_mel_extraction() {
        let extractor = MelExtractor::whisper();

        // Create 1 second of silence
        let samples = vec![0.0f32; 16000];
        let device = Device::Cpu;

        let mel = extractor.extract_from_samples(&samples, &device).unwrap();
        let shape = mel.dims();

        assert_eq!(shape[0], 1); // Batch size
        assert_eq!(shape[1], 80); // Mel bins
        // Frame count depends on padding
    }
}
