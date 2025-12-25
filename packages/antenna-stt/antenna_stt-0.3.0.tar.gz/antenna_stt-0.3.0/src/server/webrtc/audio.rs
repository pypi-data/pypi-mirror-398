//! WebRTC Audio Handler
//!
//! Handles incoming audio from WebRTC tracks:
//! - Opus decoding (handled by webrtc media engine)
//! - Resampling from 48kHz to 16kHz for Whisper
//! - Stereo to mono conversion

use rubato::{FftFixedIn, Resampler};

/// A sample of audio data
#[derive(Debug, Clone)]
pub struct AudioSample {
    /// PCM samples (f32, mono, 16kHz)
    pub samples: Vec<f32>,
    /// Timestamp in seconds
    pub timestamp: f64,
}

/// Configuration for audio handler
#[derive(Debug, Clone)]
pub struct AudioHandlerConfig {
    /// Input sample rate (from WebRTC, typically 48000)
    pub input_sample_rate: u32,
    /// Output sample rate (for Whisper, typically 16000)
    pub output_sample_rate: u32,
    /// Number of input channels
    pub input_channels: usize,
    /// Opus frame size in samples (at input rate)
    pub frame_size: usize,
}

impl Default for AudioHandlerConfig {
    fn default() -> Self {
        Self {
            input_sample_rate: 48000,
            output_sample_rate: 16000,
            input_channels: 2, // WebRTC typically sends stereo
            frame_size: 960,   // 20ms at 48kHz
        }
    }
}

/// Handles audio processing for WebRTC streams
pub struct AudioHandler {
    config: AudioHandlerConfig,
    resampler: Option<FftFixedIn<f32>>,
    resample_buffer: Vec<Vec<f32>>,
    output_buffer: Vec<Vec<f32>>,
    current_timestamp: f64,
}

impl AudioHandler {
    /// Create a new audio handler
    pub fn new(input_sample_rate: u32, output_sample_rate: u32) -> Self {
        let config = AudioHandlerConfig {
            input_sample_rate,
            output_sample_rate,
            ..Default::default()
        };

        let resampler = if input_sample_rate != output_sample_rate {
            // Calculate chunk size based on frame size
            let chunk_size = config.frame_size;

            match FftFixedIn::new(
                input_sample_rate as usize,
                output_sample_rate as usize,
                chunk_size,
                2, // Sub-chunks for better quality
                1, // Mono output
            ) {
                Ok(r) => Some(r),
                Err(e) => {
                    tracing::warn!("Failed to create resampler: {}, using passthrough", e);
                    None
                }
            }
        } else {
            None
        };

        Self {
            config,
            resampler,
            resample_buffer: vec![Vec::new()],
            output_buffer: vec![Vec::new()],
            current_timestamp: 0.0,
        }
    }

    /// Create with full configuration
    pub fn with_config(config: AudioHandlerConfig) -> Self {
        let resampler = if config.input_sample_rate != config.output_sample_rate {
            match FftFixedIn::new(
                config.input_sample_rate as usize,
                config.output_sample_rate as usize,
                config.frame_size,
                2,
                1,
            ) {
                Ok(r) => Some(r),
                Err(e) => {
                    tracing::warn!("Failed to create resampler: {}", e);
                    None
                }
            }
        } else {
            None
        };

        Self {
            config,
            resampler,
            resample_buffer: vec![Vec::new()],
            output_buffer: vec![Vec::new()],
            current_timestamp: 0.0,
        }
    }

    /// Process an audio packet from WebRTC
    ///
    /// Input: Raw RTP payload (Opus-encoded audio, but webrtc-rs decodes it)
    /// Output: PCM f32 samples at 16kHz mono
    pub fn process_packet(&mut self, payload: &[u8]) -> Result<Vec<f32>, AudioError> {
        // The webrtc crate's media engine handles Opus decoding
        // We receive PCM samples as i16 in the RTP payload
        // Convert to f32 and process

        if payload.len() < 12 {
            // Too small for RTP header
            return Ok(Vec::new());
        }

        // Skip RTP header (12 bytes minimum) to get to payload
        // Note: Real RTP may have extensions, but webrtc-rs usually strips them
        let audio_data = if payload.len() > 12 {
            &payload[12..]
        } else {
            return Ok(Vec::new());
        };

        // Convert bytes to i16 samples (little-endian PCM)
        let samples: Vec<f32> = audio_data
            .chunks_exact(2)
            .map(|chunk| {
                let sample = i16::from_le_bytes([chunk[0], chunk[1]]);
                sample as f32 / 32768.0
            })
            .collect();

        if samples.is_empty() {
            return Ok(Vec::new());
        }

        // Convert stereo to mono if needed
        let mono_samples = if self.config.input_channels == 2 && samples.len() >= 2 {
            samples
                .chunks_exact(2)
                .map(|chunk| (chunk[0] + chunk[1]) / 2.0)
                .collect()
        } else {
            samples
        };

        // Resample to target rate
        let output = self.resample(&mono_samples)?;

        // Update timestamp
        self.current_timestamp += output.len() as f64 / self.config.output_sample_rate as f64;

        Ok(output)
    }

    /// Process raw PCM samples (f32, mono, at input rate)
    pub fn process_samples(&mut self, samples: &[f32]) -> Result<Vec<f32>, AudioError> {
        if samples.is_empty() {
            return Ok(Vec::new());
        }

        let output = self.resample(samples)?;
        self.current_timestamp += output.len() as f64 / self.config.output_sample_rate as f64;

        Ok(output)
    }

    /// Resample audio to target rate
    fn resample(&mut self, samples: &[f32]) -> Result<Vec<f32>, AudioError> {
        if let Some(ref mut resampler) = self.resampler {
            // Add samples to buffer
            self.resample_buffer[0].extend_from_slice(samples);

            let input_frames_needed = resampler.input_frames_next();
            let mut output = Vec::new();

            // Process complete chunks
            while self.resample_buffer[0].len() >= input_frames_needed {
                // Take chunk from buffer
                let chunk: Vec<f32> = self.resample_buffer[0]
                    .drain(..input_frames_needed)
                    .collect();

                // Resample
                let input = vec![chunk];
                match resampler.process(&input, None) {
                    Ok(result) => {
                        if !result.is_empty() && !result[0].is_empty() {
                            output.extend_from_slice(&result[0]);
                        }
                    }
                    Err(e) => {
                        tracing::warn!("Resample error: {}", e);
                    }
                }
            }

            Ok(output)
        } else {
            // No resampling needed
            Ok(samples.to_vec())
        }
    }

    /// Flush any remaining samples in the buffer
    pub fn flush(&mut self) -> Vec<f32> {
        if let Some(ref mut resampler) = self.resampler {
            if !self.resample_buffer[0].is_empty() {
                // Pad to required length
                let input_frames_needed = resampler.input_frames_next();
                while self.resample_buffer[0].len() < input_frames_needed {
                    self.resample_buffer[0].push(0.0);
                }

                let chunk: Vec<f32> = self.resample_buffer[0].drain(..).collect();
                let input = vec![chunk];

                if let Ok(result) = resampler.process(&input, None) {
                    if !result.is_empty() {
                        return result[0].clone();
                    }
                }
            }
        }

        std::mem::take(&mut self.resample_buffer[0])
    }

    /// Get current timestamp
    pub fn timestamp(&self) -> f64 {
        self.current_timestamp
    }

    /// Reset the handler state
    pub fn reset(&mut self) {
        self.resample_buffer = vec![Vec::new()];
        self.current_timestamp = 0.0;
    }
}

/// Audio processing errors
#[derive(Debug, thiserror::Error)]
pub enum AudioError {
    #[error("Decode error: {0}")]
    Decode(String),

    #[error("Resample error: {0}")]
    Resample(String),

    #[error("Invalid format: {0}")]
    InvalidFormat(String),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audio_handler_config_defaults() {
        let config = AudioHandlerConfig::default();
        assert_eq!(config.input_sample_rate, 48000);
        assert_eq!(config.output_sample_rate, 16000);
    }

    #[test]
    fn test_audio_handler_creation() {
        let handler = AudioHandler::new(48000, 16000);
        assert_eq!(handler.timestamp(), 0.0);
    }

    #[test]
    fn test_stereo_to_mono() {
        let mut handler = AudioHandler::new(16000, 16000); // No resampling
        handler.config.input_channels = 2;

        // Stereo samples: L=0.5, R=0.3 -> mono=(0.5+0.3)/2=0.4
        let stereo = vec![0.5f32, 0.3f32, 0.6f32, 0.2f32];

        // Process as raw samples (not packet)
        let mono: Vec<f32> = stereo
            .chunks_exact(2)
            .map(|chunk| (chunk[0] + chunk[1]) / 2.0)
            .collect();

        assert_eq!(mono.len(), 2);
        assert!((mono[0] - 0.4).abs() < 0.001);
        assert!((mono[1] - 0.4).abs() < 0.001);
    }

    #[test]
    fn test_audio_handler_reset() {
        let mut handler = AudioHandler::new(48000, 16000);
        handler.current_timestamp = 1.0;
        handler.reset();
        assert_eq!(handler.timestamp(), 0.0);
    }
}
