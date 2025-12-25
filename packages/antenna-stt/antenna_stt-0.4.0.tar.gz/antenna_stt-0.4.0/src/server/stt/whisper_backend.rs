//! Whisper STT Backend
//!
//! This module provides an `SttBackend` implementation that wraps the native
//! Antenna Whisper model for use in the streaming server.

use async_trait::async_trait;
use parking_lot::Mutex;
use std::sync::Arc;

use candle_core::Device;

use crate::ml::whisper::inference::{Task, TranscriptionOptions};
use crate::ml::WhisperModel;
use crate::types::AudioData;

use super::backend::{
    BackendCapabilities, BackendInfo, SttBackend, SttError, SttResult,
};
use crate::server::streaming::types::{AudioChunk, PartialTranscript, StreamingConfig};

/// Whisper backend configuration
#[derive(Debug, Clone)]
pub struct WhisperBackendConfig {
    /// Model size (e.g., "tiny", "base", "small", "medium", "large")
    pub model_size: String,
    /// Device to run on (e.g., "cpu", "cuda", "cuda:0")
    pub device: String,
    /// Beam size for decoding (1 = greedy, 5 = beam search)
    pub beam_size: usize,
    /// Whether to generate timestamps
    pub timestamps: bool,
}

impl Default for WhisperBackendConfig {
    fn default() -> Self {
        Self {
            model_size: "base".to_string(),
            device: "cpu".to_string(),
            beam_size: 5,
            timestamps: true,
        }
    }
}

/// Whisper STT backend
///
/// Wraps the native Antenna Whisper model to implement the `SttBackend` trait.
/// Uses interior mutability to allow shared access across async tasks.
pub struct WhisperBackend {
    /// The Whisper model (wrapped in Mutex for interior mutability)
    model: Arc<Mutex<WhisperModel>>,
    /// Backend info
    info: BackendInfo,
    /// Configuration
    config: WhisperBackendConfig,
    /// Audio buffer for accumulating samples between calls
    buffer: Mutex<Vec<f32>>,
    /// Current timestamp in the stream
    current_timestamp: Mutex<f64>,
    /// Whether the backend was successfully initialized
    initialized: bool,
}

impl std::fmt::Debug for WhisperBackend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("WhisperBackend")
            .field("info", &self.info)
            .field("config", &self.config)
            .field("buffer_len", &self.buffer.lock().len())
            .field("initialized", &self.initialized)
            .finish()
    }
}

impl WhisperBackend {
    /// Create a new Whisper backend
    pub fn new(config: WhisperBackendConfig) -> SttResult<Self> {
        let device = Self::parse_device(&config.device)?;

        let model = WhisperModel::from_size(&config.model_size, device).map_err(|e| {
            SttError::InitializationFailed(format!("Failed to load Whisper model: {}", e))
        })?;

        let info = BackendInfo {
            name: "whisper".to_string(),
            model: config.model_size.clone(),
            device: config.device.clone(),
            capabilities: BackendCapabilities {
                streaming: false, // Native Whisper doesn't support true streaming
                language_detection: true,
                translation: true,
                word_timestamps: true,
                supported_languages: Self::supported_languages(),
                max_audio_duration: 30.0, // Whisper's optimal chunk size
                recommended_chunk_duration: 5.0, // Good balance for streaming
            },
        };

        Ok(Self {
            model: Arc::new(Mutex::new(model)),
            info,
            config,
            buffer: Mutex::new(Vec::new()),
            current_timestamp: Mutex::new(0.0),
            initialized: true,
        })
    }

    /// Create with specific model size and device
    pub fn with_model(model_size: &str, device: &str) -> SttResult<Self> {
        Self::new(WhisperBackendConfig {
            model_size: model_size.to_string(),
            device: device.to_string(),
            ..Default::default()
        })
    }

    /// Parse device string into Candle Device
    fn parse_device(device: &str) -> SttResult<Device> {
        match device {
            "cpu" => Ok(Device::Cpu),
            "cuda" | "gpu" => Device::new_cuda(0).map_err(|e| {
                SttError::InitializationFailed(format!("CUDA not available: {}", e))
            }),
            s if s.starts_with("cuda:") || s.starts_with("gpu:") => {
                let idx: usize = s
                    .split(':')
                    .nth(1)
                    .and_then(|s| s.parse().ok())
                    .ok_or_else(|| {
                        SttError::InitializationFailed(format!("Invalid device index in '{}'", s))
                    })?;
                Device::new_cuda(idx).map_err(|e| {
                    SttError::InitializationFailed(format!("CUDA device {} not available: {}", idx, e))
                })
            }
            _ => Err(SttError::InitializationFailed(format!(
                "Unknown device: {}",
                device
            ))),
        }
    }

    /// Get list of supported languages
    fn supported_languages() -> Vec<String> {
        // Whisper supports 99 languages
        vec![
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl", "ar",
            "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro", "da", "hu",
            "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa",
            "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne", "mn",
            "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
            "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo", "ht", "ps", "tk", "nn",
            "mt", "sa", "lb", "my", "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw",
            "su",
        ]
        .into_iter()
        .map(String::from)
        .collect()
    }

    /// Process buffered audio and return transcripts
    fn process_buffer(
        &self,
        samples: &[f32],
        sample_rate: u32,
        language: Option<&str>,
        is_final: bool,
    ) -> SttResult<Vec<PartialTranscript>> {
        if samples.is_empty() {
            return Ok(vec![]);
        }

        // Create AudioData from samples
        let audio = AudioData::new(samples.to_vec(), sample_rate, 1);

        // Get current timestamp
        let start_time = *self.current_timestamp.lock();
        let duration = samples.len() as f64 / sample_rate as f64;

        // Build transcription options
        let options = TranscriptionOptions {
            language: language.map(String::from),
            task: Task::Transcribe,
            beam_size: self.config.beam_size,
            timestamps: self.config.timestamps,
            ..Default::default()
        };

        // Lock the model and transcribe
        let result = {
            let mut model = self.model.lock();
            model.transcribe(&audio, options)
        };

        match result {
            Ok(transcription) => {
                let transcripts: Vec<PartialTranscript> = transcription
                    .segments
                    .into_iter()
                    .map(|seg| {
                        let mut transcript = PartialTranscript::final_result(
                            seg.text,
                            start_time + seg.start as f64,
                            start_time + seg.end as f64,
                        );
                        transcript.is_final = is_final;
                        if let Some(lang) = &transcription.language {
                            transcript = transcript.with_language(lang.clone());
                        }
                        transcript
                    })
                    .collect();

                // Update timestamp for next chunk
                *self.current_timestamp.lock() = start_time + duration;

                Ok(transcripts)
            }
            Err(e) => Err(SttError::TranscriptionFailed(e.to_string())),
        }
    }
}

#[async_trait]
impl SttBackend for WhisperBackend {
    fn info(&self) -> &BackendInfo {
        &self.info
    }

    fn is_ready(&self) -> bool {
        // Backend is ready if it was successfully initialized
        // We don't use try_lock() here because the model may be busy with inference
        self.initialized
    }

    async fn transcribe(
        &self,
        chunk: &AudioChunk,
        config: &StreamingConfig,
    ) -> SttResult<Vec<PartialTranscript>> {
        // Validate sample rate
        if chunk.sample_rate != config.sample_rate {
            return Err(SttError::InvalidAudioFormat(format!(
                "Expected {}Hz, got {}Hz",
                config.sample_rate, chunk.sample_rate
            )));
        }

        // Add samples to buffer
        {
            let mut buffer = self.buffer.lock();
            buffer.extend_from_slice(&chunk.samples);
        }

        // Check if we have enough audio to process
        let buffer_duration = {
            let buffer = self.buffer.lock();
            buffer.len() as f64 / config.sample_rate as f64
        };

        // Process if we have enough audio or it's the final chunk
        let should_process = chunk.is_final
            || buffer_duration >= config.max_chunk_duration
            || (buffer_duration >= config.min_chunk_duration && chunk.is_final);

        if !should_process && buffer_duration < config.min_chunk_duration {
            return Ok(vec![]);
        }

        // Take samples from buffer for processing
        let samples_to_process: Vec<f32> = {
            let mut buffer = self.buffer.lock();
            if chunk.is_final {
                // Process all remaining audio
                std::mem::take(&mut *buffer)
            } else {
                // Keep some overlap for context
                let process_samples =
                    (config.max_chunk_duration * config.sample_rate as f64) as usize;
                if buffer.len() <= process_samples {
                    std::mem::take(&mut *buffer)
                } else {
                    let samples = buffer[..process_samples].to_vec();
                    *buffer = buffer[process_samples..].to_vec();
                    samples
                }
            }
        };

        // Process the audio (blocking operation wrapped for async)
        let language = config.language.as_deref();
        self.process_buffer(&samples_to_process, config.sample_rate, language, chunk.is_final)
    }

    async fn flush(&self, config: &StreamingConfig) -> SttResult<Vec<PartialTranscript>> {
        let samples: Vec<f32> = {
            let mut buffer = self.buffer.lock();
            std::mem::take(&mut *buffer)
        };

        if samples.is_empty() {
            return Ok(vec![]);
        }

        let language = config.language.as_deref();
        self.process_buffer(&samples, config.sample_rate, language, true)
    }

    async fn reset(&self) -> SttResult<()> {
        let mut buffer = self.buffer.lock();
        buffer.clear();
        *self.current_timestamp.lock() = 0.0;
        Ok(())
    }

    async fn detect_language(&self, chunk: &AudioChunk) -> SttResult<String> {
        // Create AudioData for language detection
        let audio = AudioData::new(chunk.samples.clone(), chunk.sample_rate, 1);

        // Lock model and get config for mel generation
        let result = {
            let mut model = self.model.lock();
            let config = model.config().clone();
            let mel_filters =
                WhisperModel::generate_mel_filters(config.num_mel_bins, 201, chunk.sample_rate);

            let mel = crate::ml::whisper::inference::audio_to_mel_spectrogram(
                &audio,
                &mel_filters,
                &config,
                model.device(),
            )
            .map_err(|e| SttError::TranscriptionFailed(format!("Mel conversion failed: {}", e)))?;

            model
                .detect_language(&mel)
                .map_err(|e| SttError::TranscriptionFailed(format!("Language detection failed: {}", e)))
        };

        result
    }

    async fn translate(
        &self,
        chunk: &AudioChunk,
        config: &StreamingConfig,
    ) -> SttResult<Vec<PartialTranscript>> {
        // Create AudioData
        let audio = AudioData::new(chunk.samples.clone(), chunk.sample_rate, 1);

        let start_time = chunk.timestamp;

        // Build translation options
        let options = TranscriptionOptions {
            language: config.language.clone(),
            task: Task::Translate,
            beam_size: self.config.beam_size,
            timestamps: self.config.timestamps,
            ..Default::default()
        };

        // Lock and translate
        let result = {
            let mut model = self.model.lock();
            model.transcribe(&audio, options)
        };

        match result {
            Ok(transcription) => {
                let transcripts: Vec<PartialTranscript> = transcription
                    .segments
                    .into_iter()
                    .map(|seg| {
                        let mut transcript = PartialTranscript::final_result(
                            seg.text,
                            start_time + seg.start as f64,
                            start_time + seg.end as f64,
                        );
                        // Translation is always to English
                        transcript = transcript.with_language("en".to_string());
                        transcript
                    })
                    .collect();
                Ok(transcripts)
            }
            Err(e) => Err(SttError::TranscriptionFailed(e.to_string())),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_whisper_backend_config_default() {
        let config = WhisperBackendConfig::default();
        assert_eq!(config.model_size, "base");
        assert_eq!(config.device, "cpu");
        assert_eq!(config.beam_size, 5);
    }

    #[test]
    fn test_parse_device_cpu() {
        let device = WhisperBackend::parse_device("cpu").unwrap();
        assert!(matches!(device, Device::Cpu));
    }

    #[test]
    fn test_supported_languages() {
        let languages = WhisperBackend::supported_languages();
        assert!(languages.contains(&"en".to_string()));
        assert!(languages.contains(&"es".to_string()));
        assert!(languages.contains(&"zh".to_string()));
    }
}
