//! Whisper model loading and management
//!
//! Provides functionality to download, cache, and load Whisper models
//! from HuggingFace Hub using the Candle ML framework.

use std::fmt::{self, Debug};
use std::fs;
use std::path::PathBuf;

use candle_core::{DType, Device, Tensor};
use candle_nn::VarBuilder;
use candle_transformers::models::whisper::{self as m, Config};
use hf_hub::{api::sync::Api, Repo, RepoType};

use crate::audio::process::{convert_to_mono, resample};
use crate::error::AntennaError;
use crate::ml::tokenizer::WhisperTokenizer;
use crate::ml::traits::{
    ModelArchitecture, ModelCapabilities, ModelInfo, SpeechModel,
    TranscriptionOptions as GenericTranscriptionOptions,
    TranscriptionResult as GenericTranscriptionResult,
    TranscriptionSegment as GenericTranscriptionSegment, TranscriptionTask,
};
use crate::types::AudioData;

use super::config::{ModelSize, SpecialTokens, LANGUAGES};
use super::decode::{beam_search_decode, greedy_decode, DecodingOptions};
use super::inference::{audio_to_mel_spectrogram, Task, TranscriptionOptions};

/// Transcription segment with timing information
#[derive(Debug, Clone)]
pub struct TranscriptionSegment {
    pub start: f32,
    pub end: f32,
    pub text: String,
    pub tokens: Vec<u32>,
    pub avg_logprob: Option<f32>,
    pub no_speech_prob: Option<f32>,
}

/// Complete transcription result
#[derive(Debug, Clone)]
pub struct TranscriptionResult {
    pub text: String,
    pub segments: Vec<TranscriptionSegment>,
    pub language: Option<String>,
    pub language_probability: Option<f32>,
}

/// Whisper model for speech-to-text transcription
pub struct WhisperModel {
    model: m::model::Whisper,
    config: Config,
    tokenizer: WhisperTokenizer,
    device: Device,
    mel_filters: Vec<f32>,
    special_tokens: SpecialTokens,
    model_info: ModelInfo,
}

impl Debug for WhisperModel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("WhisperModel")
            .field("name", &self.model_info.name)
            .field("variant", &self.model_info.variant)
            .field("device", &self.device)
            .finish()
    }
}

impl WhisperModel {
    /// Load a Whisper model from HuggingFace Hub
    pub fn from_pretrained(model_id: &str, device: Device) -> Result<Self, AntennaError> {
        tracing::info!("Loading Whisper model: {}", model_id);

        // Initialize HuggingFace API
        let api = Api::new()
            .map_err(|e| AntennaError::ModelError(format!("Failed to initialize HF API: {}", e)))?;

        let repo = api.repo(Repo::with_revision(
            model_id.to_string(),
            RepoType::Model,
            "main".to_string(),
        ));

        // Download required files
        tracing::info!("Downloading model files...");

        let config_path = repo.get("config.json").map_err(|e| {
            AntennaError::ModelError(format!("Failed to download config.json: {}", e))
        })?;

        let tokenizer_path = repo.get("tokenizer.json").map_err(|e| {
            AntennaError::ModelError(format!("Failed to download tokenizer.json: {}", e))
        })?;

        let weights_path = repo.get("model.safetensors").map_err(|e| {
            AntennaError::ModelError(format!("Failed to download model.safetensors: {}", e))
        })?;

        // Load mel filters
        let mel_bytes = match repo.get("mel_filters.npz") {
            Ok(p) => Some(std::fs::read(p).ok()),
            Err(_) => None,
        }
        .flatten();

        // Load configuration
        let config_str = fs::read_to_string(&config_path)
            .map_err(|e| AntennaError::IoError(format!("Failed to read config: {}", e)))?;

        let config: Config = serde_json::from_str(&config_str)
            .map_err(|e| AntennaError::ModelError(format!("Failed to parse config: {}", e)))?;

        // Load tokenizer
        let tokenizer = WhisperTokenizer::from_file(&tokenizer_path)?;

        // Load model weights
        tracing::info!("Loading model weights...");
        let vb = unsafe {
            VarBuilder::from_mmaped_safetensors(&[weights_path], DType::F32, &device)
                .map_err(|e| AntennaError::ModelError(format!("Failed to load weights: {}", e)))?
        };

        let model = m::model::Whisper::load(&vb, config.clone())
            .map_err(|e| AntennaError::ModelError(format!("Failed to build model: {}", e)))?;

        // Load or generate mel filters
        let mel_filters = Self::load_mel_filters(mel_bytes, config.num_mel_bins)?;

        // Build model info
        let model_info = Self::build_model_info(model_id);

        tracing::info!("Model loaded successfully");

        Ok(Self {
            model,
            config,
            tokenizer,
            device,
            mel_filters,
            special_tokens: SpecialTokens::default(),
            model_info,
        })
    }

    /// Build ModelInfo for a given model ID
    fn build_model_info(model_id: &str) -> ModelInfo {
        // Extract variant from model ID (e.g., "openai/whisper-base" -> "base")
        let variant = model_id
            .split('/')
            .last()
            .unwrap_or(model_id)
            .strip_prefix("whisper-")
            .unwrap_or(model_id)
            .to_string();

        // Build language list from LANGUAGES constant
        let supported_languages: Vec<String> = LANGUAGES.iter().map(|(code, _)| code.to_string()).collect();

        let capabilities = ModelCapabilities {
            architecture: ModelArchitecture::EncoderDecoder,
            supports_translation: true,
            supports_language_detection: true,
            supports_timestamps: true,
            max_audio_duration: 30.0, // Whisper processes 30s chunks
            supported_languages,
        };

        ModelInfo::new(
            format!("Whisper {}", variant),
            "whisper",
            variant,
        )
        .with_capabilities(capabilities)
    }

    /// Load model by size name (e.g., "tiny", "base", "small")
    pub fn from_size(size: &str, device: Device) -> Result<Self, AntennaError> {
        let model_size = ModelSize::from_str(size)
            .ok_or_else(|| AntennaError::ModelError(format!("Unknown model size: {}", size)))?;

        Self::from_pretrained(model_size.model_id(), device)
    }

    /// Load mel filter bank
    fn load_mel_filters(
        mel_bytes: Option<Vec<u8>>,
        num_mel_bins: usize,
    ) -> Result<Vec<f32>, AntennaError> {
        if let Some(bytes) = mel_bytes {
            // Parse NPZ format (simplified)
            // For now, generate standard mel filters if parsing fails
            if bytes.len() >= num_mel_bins * 201 * 4 {
                let filters: Vec<f32> = bytes[..num_mel_bins * 201 * 4]
                    .chunks_exact(4)
                    .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
                    .collect();
                return Ok(filters);
            }
        }

        // Generate standard mel filters
        Ok(Self::generate_mel_filters(num_mel_bins, 201, 16000))
    }

    /// Generate mel filter bank
    pub fn generate_mel_filters(num_mels: usize, num_freqs: usize, sample_rate: u32) -> Vec<f32> {
        let fmin = 0.0f32;
        let fmax = (sample_rate / 2) as f32;

        // Convert to mel scale
        let mel_min = 2595.0 * (1.0 + fmin / 700.0).log10();
        let mel_max = 2595.0 * (1.0 + fmax / 700.0).log10();

        // Create mel points
        let mel_points: Vec<f32> = (0..=num_mels + 1)
            .map(|i| mel_min + (mel_max - mel_min) * (i as f32) / ((num_mels + 1) as f32))
            .collect();

        // Convert back to Hz
        let hz_points: Vec<f32> = mel_points
            .iter()
            .map(|m| 700.0 * (10.0f32.powf(m / 2595.0) - 1.0))
            .collect();

        // Convert to FFT bins
        let fft_size = (num_freqs - 1) * 2;
        let bin_points: Vec<usize> = hz_points
            .iter()
            .map(|f| ((fft_size as f32 + 1.0) * f / sample_rate as f32).floor() as usize)
            .collect();

        // Create filter bank
        let mut filters = vec![0.0f32; num_mels * num_freqs];

        for m in 0..num_mels {
            for k in bin_points[m]..bin_points[m + 1] {
                if k < num_freqs {
                    let denom = (bin_points[m + 1] - bin_points[m]) as f32;
                    if denom > 0.0 {
                        filters[m * num_freqs + k] = (k - bin_points[m]) as f32 / denom;
                    }
                }
            }
            for k in bin_points[m + 1]..bin_points[m + 2] {
                if k < num_freqs {
                    let denom = (bin_points[m + 2] - bin_points[m + 1]) as f32;
                    if denom > 0.0 {
                        filters[m * num_freqs + k] = (bin_points[m + 2] - k) as f32 / denom;
                    }
                }
            }
        }

        filters
    }

    /// Transcribe audio to text
    pub fn transcribe(
        &mut self,
        audio: &AudioData,
        options: TranscriptionOptions,
    ) -> Result<TranscriptionResult, AntennaError> {
        // Validate audio format
        if audio.sample_rate != 16000 {
            return Err(AntennaError::PreprocessingError(
                "Audio must be 16kHz for Whisper. Use preprocess_audio() first.".to_string(),
            ));
        }

        if audio.channels != 1 {
            return Err(AntennaError::PreprocessingError(
                "Audio must be mono for Whisper. Use preprocess_audio() first.".to_string(),
            ));
        }

        // Convert to mel spectrogram
        let mel = audio_to_mel_spectrogram(audio, &self.mel_filters, &self.config, &self.device)?;

        // Detect language if not specified
        let language = if options.language.is_some() {
            options.language.clone()
        } else {
            Some(self.detect_language(&mel)?)
        };

        // Transcribe in chunks
        let chunk_duration = 30.0; // Whisper's optimal chunk size
        let total_duration = audio.duration();
        let mut all_segments = Vec::new();
        let mut current_time = 0.0;

        while current_time < total_duration {
            let chunk_start = (current_time * audio.sample_rate as f32) as usize;
            let chunk_samples = (chunk_duration * audio.sample_rate as f32) as usize;
            let chunk_end = (chunk_start + chunk_samples).min(audio.samples.len());

            if chunk_start >= chunk_end {
                break;
            }

            let chunk_audio = AudioData::new(
                audio.samples[chunk_start..chunk_end].to_vec(),
                audio.sample_rate,
                audio.channels,
            );

            let chunk_mel =
                audio_to_mel_spectrogram(&chunk_audio, &self.mel_filters, &self.config, &self.device)?;

            let segments = self.transcribe_chunk(&chunk_mel, language.as_deref(), &options)?;

            // Adjust timestamps and add segments
            for mut segment in segments {
                segment.start += current_time;
                segment.end += current_time;
                all_segments.push(segment);
            }

            current_time += chunk_duration;
        }

        // Combine all text
        let full_text = all_segments
            .iter()
            .map(|s| s.text.trim())
            .collect::<Vec<_>>()
            .join(" ");

        Ok(TranscriptionResult {
            text: full_text,
            segments: all_segments,
            language,
            language_probability: None,
        })
    }

    /// Transcribe a single mel spectrogram chunk
    fn transcribe_chunk(
        &mut self,
        mel: &Tensor,
        language: Option<&str>,
        options: &TranscriptionOptions,
    ) -> Result<Vec<TranscriptionSegment>, AntennaError> {
        // Encode audio
        let encoder_output = self
            .model
            .encoder
            .forward(mel, true)
            .map_err(|e| AntennaError::ModelError(format!("Encoder forward failed: {}", e)))?;

        // Build initial prompt
        let mut prompt_tokens = vec![self.special_tokens.sot];

        // Add language token
        if let Some(lang) = language {
            if let Some(lang_token) = self.tokenizer.get_language_token(lang) {
                prompt_tokens.push(lang_token);
            }
        }

        // Add task token
        match options.task {
            Task::Translate => prompt_tokens.push(self.special_tokens.translate),
            Task::Transcribe => prompt_tokens.push(self.special_tokens.transcribe),
        }

        // Add timestamp control
        if !options.timestamps {
            prompt_tokens.push(self.special_tokens.no_timestamps);
        }

        // Decode
        let decoding_opts = DecodingOptions {
            beam_size: options.beam_size,
            patience: options.patience,
            temperature: options.temperature,
            max_tokens: self.config.max_target_positions,
        };

        let decoded_tokens = if options.beam_size > 1 {
            beam_search_decode(
                &mut self.model,
                &encoder_output,
                &prompt_tokens,
                &decoding_opts,
                self.special_tokens.eot,
                &self.device,
            )?
        } else {
            greedy_decode(
                &mut self.model,
                &encoder_output,
                &prompt_tokens,
                &decoding_opts,
                self.special_tokens.eot,
                &self.device,
            )?
        };

        // Extract segments with timestamps
        if options.timestamps {
            let segments = self.extract_segments_with_timestamps(&decoded_tokens)?;
            Ok(segments)
        } else {
            // Single segment without timestamps
            let text = self.tokenizer.decode(&decoded_tokens, true)?;
            Ok(vec![TranscriptionSegment {
                start: 0.0,
                end: 30.0, // Chunk duration
                text,
                tokens: decoded_tokens,
                avg_logprob: None,
                no_speech_prob: None,
            }])
        }
    }

    /// Extract segments with timestamps from decoded tokens
    fn extract_segments_with_timestamps(
        &self,
        tokens: &[u32],
    ) -> Result<Vec<TranscriptionSegment>, AntennaError> {
        let timestamp_segments = self.tokenizer.extract_timestamps(tokens);

        let segments = timestamp_segments
            .into_iter()
            .map(|(start, end, text)| TranscriptionSegment {
                start,
                end,
                text,
                tokens: vec![],
                avg_logprob: None,
                no_speech_prob: None,
            })
            .collect();

        Ok(segments)
    }

    /// Detect language from audio features
    pub fn detect_language(&mut self, mel: &Tensor) -> Result<String, AntennaError> {
        // Encode audio
        let encoder_output = self
            .model
            .encoder
            .forward(mel, true)
            .map_err(|e| AntennaError::ModelError(format!("Encoder forward failed: {}", e)))?;

        // Get decoder with SOT token
        let sot_tensor = Tensor::new(&[self.special_tokens.sot], &self.device)
            .map_err(|e| AntennaError::ModelError(format!("Failed to create SOT tensor: {}", e)))?
            .unsqueeze(0)
            .map_err(|e| AntennaError::ModelError(format!("Failed to unsqueeze: {}", e)))?;

        // Get decoder hidden states
        let hidden_states = self
            .model
            .decoder
            .forward(&sot_tensor, &encoder_output, true)
            .map_err(|e| AntennaError::ModelError(format!("Decoder forward failed: {}", e)))?;

        // Project to vocabulary logits using final_linear
        let logits = self
            .model
            .decoder
            .final_linear(&hidden_states)
            .map_err(|e| AntennaError::ModelError(format!("Final linear failed: {}", e)))?;

        // Get probabilities for language tokens
        // logits shape: [batch, seq_len, vocab_size]
        let logits = logits
            .squeeze(0)
            .map_err(|e| AntennaError::ModelError(format!("Squeeze failed: {}", e)))?;
        let logits = logits
            .get(0)
            .map_err(|e| AntennaError::ModelError(format!("Get failed: {}", e)))?;

        // Find most likely language token
        let lang_start = self.special_tokens.language_token_start as usize;
        let lang_end = lang_start + super::config::LANGUAGES.len();

        let lang_logits = logits
            .narrow(0, lang_start, lang_end - lang_start)
            .map_err(|e| AntennaError::ModelError(format!("Narrow failed: {}", e)))?;

        let lang_probs = candle_nn::ops::softmax(&lang_logits, 0)
            .map_err(|e| AntennaError::ModelError(format!("Softmax failed: {}", e)))?;

        let lang_probs_vec: Vec<f32> = lang_probs
            .to_vec1()
            .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

        let (max_idx, _max_prob) = lang_probs_vec
            .iter()
            .enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
            .unwrap_or((0, &0.0));

        let language = super::config::LANGUAGES
            .get(max_idx)
            .map(|(code, _)| code.to_string())
            .unwrap_or_else(|| "en".to_string());

        Ok(language)
    }

    /// Translate audio to English
    pub fn translate(&mut self, audio: &AudioData) -> Result<TranscriptionResult, AntennaError> {
        let options = TranscriptionOptions {
            task: Task::Translate,
            ..Default::default()
        };
        self.transcribe(audio, options)
    }

    /// Get model configuration
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// Get device
    pub fn device(&self) -> &Device {
        &self.device
    }

    /// Get cache directory for models
    pub fn cache_dir() -> PathBuf {
        let home = std::env::var("HOME")
            .or_else(|_| std::env::var("USERPROFILE"))
            .unwrap_or_else(|_| ".".to_string());
        PathBuf::from(home)
            .join(".cache")
            .join("antenna")
            .join("models")
    }

    /// Check if a model is cached
    pub fn is_model_cached(model_id: &str) -> bool {
        let api = match Api::new() {
            Ok(api) => api,
            Err(_) => return false,
        };

        let repo = api.repo(Repo::with_revision(
            model_id.to_string(),
            RepoType::Model,
            "main".to_string(),
        ));

        // Check if main files exist in cache
        repo.get("config.json").is_ok()
            && repo.get("model.safetensors").is_ok()
            && repo.get("tokenizer.json").is_ok()
    }

    /// List cached models
    pub fn list_cached_models() -> Vec<String> {
        let cache_dir = hf_hub::Cache::default().path().to_path_buf();
        let models_dir = cache_dir.join("models--openai--whisper-*");

        glob::glob(models_dir.to_str().unwrap_or(""))
            .ok()
            .map(|paths| {
                paths
                    .filter_map(|p| p.ok())
                    .filter_map(|p| {
                        p.file_name()
                            .and_then(|n| n.to_str())
                            .map(|s| s.replace("models--", "").replace("--", "/"))
                    })
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Clear model cache
    pub fn clear_cache() -> Result<(), AntennaError> {
        let cache_dir = Self::cache_dir();
        if cache_dir.exists() {
            fs::remove_dir_all(&cache_dir)
                .map_err(|e| AntennaError::IoError(format!("Failed to clear cache: {}", e)))?;
        }
        Ok(())
    }

    /// Get model info
    pub fn info(&self) -> &ModelInfo {
        &self.model_info
    }
}

// ============================================================================
// SpeechModel Trait Implementation
// ============================================================================

impl SpeechModel for WhisperModel {
    fn info(&self) -> &ModelInfo {
        &self.model_info
    }

    fn device(&self) -> &Device {
        &self.device
    }

    fn transcribe(
        &mut self,
        audio: &AudioData,
        options: GenericTranscriptionOptions,
    ) -> Result<GenericTranscriptionResult, AntennaError> {
        // Convert generic options to Whisper-specific options
        let whisper_task = match options.task {
            TranscriptionTask::Transcribe => Task::Transcribe,
            TranscriptionTask::Translate => Task::Translate,
        };

        let whisper_options = TranscriptionOptions {
            task: whisper_task,
            language: options.language,
            timestamps: options.timestamps,
            beam_size: options.beam_size,
            temperature: options.temperature,
            ..Default::default()
        };

        // Call the existing Whisper transcribe method
        let result = WhisperModel::transcribe(self, audio, whisper_options)?;

        // Convert Whisper result to generic result
        let segments: Vec<GenericTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| GenericTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
                tokens: s.tokens,
                avg_logprob: s.avg_logprob,
                no_speech_prob: s.no_speech_prob,
            })
            .collect();

        Ok(GenericTranscriptionResult {
            text: result.text,
            segments,
            language: result.language,
            language_probability: result.language_probability,
        })
    }

    fn detect_language(&mut self, audio: &AudioData) -> Result<String, AntennaError> {
        // Convert audio to mel spectrogram first
        let mel = audio_to_mel_spectrogram(audio, &self.mel_filters, &self.config, &self.device)?;

        // Use the internal detect_language method that takes a mel tensor
        WhisperModel::detect_language(self, &mel)
    }

    fn preprocess_audio(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        // Whisper expects 16kHz mono audio
        let mut processed = audio.clone();

        // Convert to mono if needed
        if processed.channels > 1 {
            processed = convert_to_mono(&processed);
        }

        // Resample to 16kHz if needed
        if processed.sample_rate != 16000 {
            processed = resample(&processed, 16000)?;
        }

        Ok(processed)
    }

    fn expected_sample_rate(&self) -> u32 {
        16000
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mel_filter_generation() {
        let filters = WhisperModel::generate_mel_filters(80, 201, 16000);
        assert_eq!(filters.len(), 80 * 201);
    }

    #[test]
    fn test_cache_dir() {
        let cache_dir = WhisperModel::cache_dir();
        assert!(cache_dir.to_string_lossy().contains("antenna"));
    }
}
