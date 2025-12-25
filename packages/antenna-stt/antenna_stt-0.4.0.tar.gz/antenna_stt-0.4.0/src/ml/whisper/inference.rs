//! Whisper inference and audio preprocessing
//!
//! Provides audio-to-mel spectrogram conversion and inference utilities
//! for Whisper speech-to-text transcription.

use candle_core::{Device, Tensor, DType};
use candle_transformers::models::whisper::Config;

use crate::error::AntennaError;
use crate::types::AudioData;

/// Transcription task type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Task {
    /// Transcribe audio in original language
    Transcribe,
    /// Translate audio to English
    Translate,
}

impl Default for Task {
    fn default() -> Self {
        Task::Transcribe
    }
}

/// Options for transcription
#[derive(Debug, Clone)]
pub struct TranscriptionOptions {
    /// Language code (e.g., "en", "es", "zh"). None for auto-detection.
    pub language: Option<String>,
    /// Transcription or translation task
    pub task: Task,
    /// Beam size for beam search decoding (1 = greedy)
    pub beam_size: usize,
    /// Patience factor for beam search
    pub patience: f32,
    /// Temperature for sampling (0 = greedy)
    pub temperature: f32,
    /// Threshold for detecting no speech
    pub no_speech_threshold: f32,
    /// Whether to include word-level timestamps
    pub timestamps: bool,
    /// Initial prompt to condition the model
    pub initial_prompt: Option<String>,
    /// Suppress blank outputs at beginning
    pub suppress_blank: bool,
}

impl Default for TranscriptionOptions {
    fn default() -> Self {
        Self {
            language: None,
            task: Task::Transcribe,
            beam_size: 5,
            patience: 1.0,
            temperature: 0.0,
            no_speech_threshold: 0.6,
            timestamps: true,
            initial_prompt: None,
            suppress_blank: true,
        }
    }
}

/// Convert audio samples to mel spectrogram for Whisper
pub fn audio_to_mel_spectrogram(
    audio: &AudioData,
    mel_filters: &[f32],
    config: &Config,
    device: &Device,
) -> Result<Tensor, AntennaError> {
    let samples = &audio.samples;
    let n_mels = config.num_mel_bins;

    // Whisper uses 400 sample window (25ms at 16kHz) and 160 sample hop (10ms)
    let n_fft = 400;
    let hop_length = 160;

    // Pad or truncate to 30 seconds (480000 samples at 16kHz)
    let target_samples = 480000;
    let padded_samples: Vec<f32> = if samples.len() >= target_samples {
        samples[..target_samples].to_vec()
    } else {
        let mut padded = samples.clone();
        padded.resize(target_samples, 0.0);
        padded
    };

    // Compute STFT
    let stft = compute_stft(&padded_samples, n_fft, hop_length)?;

    // Convert to power spectrogram
    let power_spec: Vec<f32> = stft.iter().map(|(re, im)| re * re + im * im).collect();

    // Number of frequency bins and frames
    let n_freqs = n_fft / 2 + 1; // 201
    let n_frames = power_spec.len() / n_freqs;

    // Apply mel filter bank
    let mut mel_spec = vec![0.0f32; n_mels * n_frames];

    for frame in 0..n_frames {
        for mel in 0..n_mels {
            let mut sum = 0.0f32;
            for freq in 0..n_freqs {
                let filter_val = mel_filters.get(mel * n_freqs + freq).copied().unwrap_or(0.0);
                let power_val = power_spec.get(frame * n_freqs + freq).copied().unwrap_or(0.0);
                sum += filter_val * power_val;
            }
            mel_spec[mel * n_frames + frame] = sum;
        }
    }

    // Convert to log scale
    let log_spec: Vec<f32> = mel_spec
        .iter()
        .map(|&x| {
            let clamped = x.max(1e-10);
            clamped.log10().max(-10.0)
        })
        .collect();

    // Normalize
    let max_val = log_spec.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
    let normalized: Vec<f32> = log_spec
        .iter()
        .map(|&x| (x.max(max_val - 8.0) + 4.0) / 4.0)
        .collect();

    // Create tensor with shape [1, n_mels, n_frames]
    let mel_tensor = Tensor::from_vec(normalized, (1, n_mels, n_frames), device)
        .map_err(|e| AntennaError::PreprocessingError(format!("Failed to create mel tensor: {}", e)))?
        .to_dtype(DType::F32)
        .map_err(|e| AntennaError::PreprocessingError(format!("Failed to convert dtype: {}", e)))?;

    Ok(mel_tensor)
}

/// Compute Short-Time Fourier Transform
fn compute_stft(samples: &[f32], n_fft: usize, hop_length: usize) -> Result<Vec<(f32, f32)>, AntennaError> {
    let n_freqs = n_fft / 2 + 1;
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

        // Apply window and prepare for FFT
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

/// Prepare audio chunk for processing
pub fn prepare_audio_chunk(
    audio: &AudioData,
    start_sample: usize,
    duration_seconds: f32,
) -> AudioData {
    let sample_count = (duration_seconds * audio.sample_rate as f32) as usize;
    let end = (start_sample + sample_count).min(audio.samples.len());

    let chunk = if start_sample < end {
        audio.samples[start_sample..end].to_vec()
    } else {
        vec![]
    };

    AudioData::new(chunk, audio.sample_rate, audio.channels)
}

/// Pad audio to specified duration
pub fn pad_audio(audio: &AudioData, target_duration: f32) -> AudioData {
    let target_samples = (target_duration * audio.sample_rate as f32) as usize;

    let padded = if audio.samples.len() >= target_samples {
        audio.samples[..target_samples].to_vec()
    } else {
        let mut padded = audio.samples.clone();
        padded.resize(target_samples, 0.0);
        padded
    };

    AudioData::new(padded, audio.sample_rate, audio.channels)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stft_computation() {
        // Generate a simple sine wave
        let sample_rate = 16000;
        let duration = 0.1; // 100ms
        let freq = 440.0; // A4

        let samples: Vec<f32> = (0..(sample_rate as f32 * duration) as usize)
            .map(|i| {
                let t = i as f32 / sample_rate as f32;
                (2.0 * std::f32::consts::PI * freq * t).sin()
            })
            .collect();

        let stft = compute_stft(&samples, 400, 160).unwrap();
        assert!(!stft.is_empty());
    }

    #[test]
    fn test_pad_audio() {
        let audio = AudioData::new(vec![0.1, 0.2, 0.3], 16000, 1);
        let padded = pad_audio(&audio, 1.0);
        assert_eq!(padded.samples.len(), 16000);
    }

    #[test]
    fn test_prepare_chunk() {
        let samples: Vec<f32> = (0..48000).map(|i| i as f32 / 48000.0).collect();
        let audio = AudioData::new(samples, 16000, 1);

        let chunk = prepare_audio_chunk(&audio, 0, 1.0);
        assert_eq!(chunk.samples.len(), 16000);
    }
}
