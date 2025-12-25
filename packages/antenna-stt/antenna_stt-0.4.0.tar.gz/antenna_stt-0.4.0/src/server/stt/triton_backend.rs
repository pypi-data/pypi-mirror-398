//! Triton Inference Server STT Backend
//!
//! Provides an `SttBackend` implementation that uses NVIDIA Triton Inference Server
//! for model inference. Ideal for production deployments with:
//! - Dynamic batching
//! - TensorRT optimization
//! - Multi-model serving
//! - Horizontal scaling

use async_trait::async_trait;
use parking_lot::Mutex;
use std::sync::Arc;
use uuid::Uuid;

use super::backend::{BackendCapabilities, BackendInfo, SttBackend, SttError, SttResult};
use super::triton::{TritonClient, TritonConfig};
use crate::server::streaming::types::{AudioChunk, PartialTranscript, StreamingConfig};

/// Triton backend configuration
#[derive(Debug, Clone)]
pub struct TritonBackendConfig {
    /// Triton server URL (e.g., "http://localhost:8001")
    pub url: String,
    /// Model name in Triton repository
    pub model_name: String,
    /// Model version (empty for latest)
    pub model_version: String,
    /// Whether the model supports streaming
    pub streaming: bool,
    /// Expected input tensor name for audio
    pub audio_input_name: String,
    /// Expected output tensor name for text
    pub text_output_name: String,
    /// Expected output tensor name for language (optional)
    pub language_output_name: Option<String>,
}

impl Default for TritonBackendConfig {
    fn default() -> Self {
        Self {
            url: "http://localhost:8001".to_string(),
            model_name: "whisper".to_string(),
            model_version: String::new(),
            streaming: false,
            audio_input_name: "audio".to_string(),
            text_output_name: "text".to_string(),
            language_output_name: Some("language".to_string()),
        }
    }
}

impl TritonBackendConfig {
    /// Create config for a Whisper model
    pub fn whisper(url: &str, model_name: &str) -> Self {
        Self {
            url: url.to_string(),
            model_name: model_name.to_string(),
            ..Default::default()
        }
    }
}

/// Internal state for buffering
struct TritonState {
    buffer: Vec<f32>,
    current_timestamp: f64,
}

/// Triton Inference Server backend
///
/// Uses gRPC to communicate with Triton for model inference.
/// The model should be deployed in Triton with the expected input/output format.
pub struct TritonBackend {
    client: Arc<TritonClient>,
    config: TritonBackendConfig,
    info: BackendInfo,
    state: Mutex<TritonState>,
}

impl std::fmt::Debug for TritonBackend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TritonBackend")
            .field("config", &self.config)
            .field("info", &self.info)
            .finish()
    }
}

impl TritonBackend {
    /// Create a new Triton backend
    pub async fn new(config: TritonBackendConfig) -> SttResult<Self> {
        let triton_config = TritonConfig {
            url: config.url.clone(),
            model_name: config.model_name.clone(),
            model_version: config.model_version.clone(),
            ..Default::default()
        };

        let client = TritonClient::new(triton_config)
            .await
            .map_err(|e| SttError::InitializationFailed(format!("Triton connection failed: {}", e)))?;

        // Check if server is ready
        let server_ready = client.server_ready().await.unwrap_or(false);
        if !server_ready {
            return Err(SttError::InitializationFailed(
                "Triton server is not ready".to_string(),
            ));
        }

        // Check if model is ready
        let model_ready = client
            .model_ready(&config.model_name, &config.model_version)
            .await
            .unwrap_or(false);
        if !model_ready {
            return Err(SttError::InitializationFailed(format!(
                "Model '{}' is not ready in Triton",
                config.model_name
            )));
        }

        // Get model metadata for capabilities
        let capabilities = Self::build_capabilities(&client, &config).await;

        let info = BackendInfo {
            name: "triton".to_string(),
            model: config.model_name.clone(),
            device: format!("triton:{}", config.url),
            capabilities,
        };

        Ok(Self {
            client: Arc::new(client),
            config,
            info,
            state: Mutex::new(TritonState {
                buffer: Vec::new(),
                current_timestamp: 0.0,
            }),
        })
    }

    /// Create with default URL (localhost:8001)
    pub async fn with_model(model_name: &str) -> SttResult<Self> {
        let config = TritonBackendConfig {
            model_name: model_name.to_string(),
            ..Default::default()
        };
        Self::new(config).await
    }

    /// Build capabilities from model metadata
    async fn build_capabilities(
        client: &TritonClient,
        config: &TritonBackendConfig,
    ) -> BackendCapabilities {
        // Try to get model metadata
        let metadata = client
            .model_metadata(&config.model_name, &config.model_version)
            .await;

        let mut capabilities = BackendCapabilities {
            streaming: config.streaming,
            language_detection: config.language_output_name.is_some(),
            translation: true, // Assume Whisper models support translation
            word_timestamps: false, // Depends on model config
            supported_languages: Self::whisper_languages(),
            max_audio_duration: 30.0,
            recommended_chunk_duration: 5.0,
        };

        // Check outputs from metadata
        if let Ok(meta) = metadata {
            for output in &meta.outputs {
                if output.name == "timestamps" || output.name == "word_timestamps" {
                    capabilities.word_timestamps = true;
                }
            }
        }

        capabilities
    }

    /// Get list of Whisper-supported languages
    fn whisper_languages() -> Vec<String> {
        vec![
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
        ]
        .into_iter()
        .map(String::from)
        .collect()
    }

    /// Parse transcription response from Triton
    fn parse_response(
        &self,
        response: &super::triton::ModelInferResponse,
        start_time: f64,
        end_time: f64,
    ) -> SttResult<Vec<PartialTranscript>> {
        let mut transcripts = Vec::new();

        // Find text output
        let text_idx = response
            .outputs
            .iter()
            .position(|o| o.name == self.config.text_output_name);

        if let Some(idx) = text_idx {
            if idx < response.raw_output_contents.len() {
                let text_bytes = &response.raw_output_contents[idx];

                // Parse as UTF-8 string (Triton returns bytes)
                // Handle both direct string and length-prefixed formats
                let text = Self::parse_string_tensor(text_bytes)?;

                if !text.is_empty() {
                    let mut transcript = PartialTranscript::partial(text, start_time, end_time);

                    // Try to get language if available
                    if let Some(lang_name) = &self.config.language_output_name {
                        if let Some(lang_idx) = response.outputs.iter().position(|o| &o.name == lang_name) {
                            if lang_idx < response.raw_output_contents.len() {
                                if let Ok(lang) = Self::parse_string_tensor(&response.raw_output_contents[lang_idx]) {
                                    transcript = transcript.with_language(lang);
                                }
                            }
                        }
                    }

                    transcripts.push(transcript);
                }
            }
        }

        Ok(transcripts)
    }

    /// Parse a string tensor from Triton output bytes
    fn parse_string_tensor(bytes: &[u8]) -> SttResult<String> {
        if bytes.is_empty() {
            return Ok(String::new());
        }

        // Triton string format: 4-byte length prefix (little-endian) + string bytes
        if bytes.len() >= 4 {
            let len = u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]) as usize;
            if bytes.len() >= 4 + len {
                return String::from_utf8(bytes[4..4 + len].to_vec())
                    .map_err(|e| SttError::TranscriptionFailed(format!("Invalid UTF-8: {}", e)));
            }
        }

        // Fallback: try as raw UTF-8
        String::from_utf8(bytes.to_vec())
            .map_err(|e| SttError::TranscriptionFailed(format!("Invalid UTF-8: {}", e)))
    }
}

#[async_trait]
impl SttBackend for TritonBackend {
    fn info(&self) -> &BackendInfo {
        &self.info
    }

    fn is_ready(&self) -> bool {
        // Check client availability (could ping server in production)
        true
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

        // Add to buffer
        {
            let mut state = self.state.lock();
            state.buffer.extend_from_slice(&chunk.samples);
        }

        // Check if we have enough audio
        let buffer_duration = {
            let state = self.state.lock();
            state.buffer.len() as f64 / config.sample_rate as f64
        };

        if buffer_duration < config.min_chunk_duration && !chunk.is_final {
            return Ok(vec![]);
        }

        // Get samples for processing
        let (samples, start_time) = {
            let mut state = self.state.lock();
            let samples = if chunk.is_final {
                std::mem::take(&mut state.buffer)
            } else {
                let max_samples = (config.max_chunk_duration * config.sample_rate as f64) as usize;
                if state.buffer.len() <= max_samples {
                    std::mem::take(&mut state.buffer)
                } else {
                    let samples = state.buffer[..max_samples].to_vec();
                    state.buffer = state.buffer[max_samples..].to_vec();
                    samples
                }
            };
            let start = state.current_timestamp;
            state.current_timestamp += samples.len() as f64 / config.sample_rate as f64;
            (samples, start)
        };

        if samples.is_empty() {
            return Ok(vec![]);
        }

        let end_time = start_time + samples.len() as f64 / config.sample_rate as f64;
        let request_id = Uuid::new_v4().to_string();

        // Call Triton
        let response = self
            .client
            .infer_audio(&samples, &request_id)
            .await
            .map_err(|e| SttError::TranscriptionFailed(format!("Triton inference failed: {}", e)))?;

        self.parse_response(&response, start_time, end_time)
    }

    async fn flush(&self, config: &StreamingConfig) -> SttResult<Vec<PartialTranscript>> {
        let (samples, start_time) = {
            let mut state = self.state.lock();
            let samples = std::mem::take(&mut state.buffer);
            let start = state.current_timestamp;
            (samples, start)
        };

        if samples.is_empty() {
            return Ok(vec![]);
        }

        let end_time = start_time + samples.len() as f64 / config.sample_rate as f64;
        let request_id = Uuid::new_v4().to_string();

        let response = self
            .client
            .infer_audio(&samples, &request_id)
            .await
            .map_err(|e| SttError::TranscriptionFailed(format!("Triton inference failed: {}", e)))?;

        let mut transcripts = self.parse_response(&response, start_time, end_time)?;

        // Mark as final
        for t in &mut transcripts {
            t.is_final = true;
        }

        Ok(transcripts)
    }

    async fn reset(&self) -> SttResult<()> {
        let mut state = self.state.lock();
        state.buffer.clear();
        state.current_timestamp = 0.0;
        Ok(())
    }

    async fn detect_language(&self, chunk: &AudioChunk) -> SttResult<String> {
        if self.config.language_output_name.is_none() {
            return Err(SttError::Internal(
                "Language detection not configured for this model".to_string(),
            ));
        }

        let request_id = Uuid::new_v4().to_string();
        let response = self
            .client
            .infer_audio(&chunk.samples, &request_id)
            .await
            .map_err(|e| SttError::TranscriptionFailed(format!("Triton inference failed: {}", e)))?;

        // Find language output
        if let Some(lang_name) = &self.config.language_output_name {
            if let Some(lang_idx) = response.outputs.iter().position(|o| &o.name == lang_name) {
                if lang_idx < response.raw_output_contents.len() {
                    return Self::parse_string_tensor(&response.raw_output_contents[lang_idx]);
                }
            }
        }

        Err(SttError::TranscriptionFailed(
            "Language not found in response".to_string(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_defaults() {
        let config = TritonBackendConfig::default();
        assert_eq!(config.url, "http://localhost:8001");
        assert_eq!(config.model_name, "whisper");
        assert_eq!(config.audio_input_name, "audio");
    }

    #[test]
    fn test_whisper_config() {
        let config = TritonBackendConfig::whisper("http://triton:8001", "whisper_large");
        assert_eq!(config.url, "http://triton:8001");
        assert_eq!(config.model_name, "whisper_large");
    }

    #[test]
    fn test_parse_string_tensor() {
        // Length-prefixed format
        let bytes = [5, 0, 0, 0, b'h', b'e', b'l', b'l', b'o'];
        let result = TritonBackend::parse_string_tensor(&bytes).unwrap();
        assert_eq!(result, "hello");
    }

    #[test]
    fn test_parse_raw_string() {
        // Raw UTF-8
        let bytes = b"hello world";
        let result = TritonBackend::parse_string_tensor(bytes).unwrap();
        assert_eq!(result, "hello world");
    }
}
