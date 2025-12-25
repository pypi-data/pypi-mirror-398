//! Distil-Whisper model implementation
//!
//! Distil-Whisper shares the same architecture as Whisper but with fewer
//! decoder layers, resulting in faster inference with minimal quality loss.

use std::fmt::{self, Debug};
use std::fs;

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
use crate::ml::whisper::config::{SpecialTokens, LANGUAGES};
use crate::ml::whisper::decode::{beam_search_decode, greedy_decode, DecodingOptions};
use crate::ml::whisper::inference::{audio_to_mel_spectrogram, Task, TranscriptionOptions};
use crate::ml::whisper::model::{TranscriptionResult, TranscriptionSegment, WhisperModel};
use crate::types::AudioData;

use super::config::DistilWhisperSize;

/// Distil-Whisper model for fast speech-to-text transcription
///
/// This model uses the same underlying architecture as Whisper but with
/// a distilled (compressed) decoder for faster inference.
pub struct DistilWhisperModel {
    model: m::model::Whisper,
    config: Config,
    tokenizer: WhisperTokenizer,
    device: Device,
    mel_filters: Vec<f32>,
    special_tokens: SpecialTokens,
    model_info: ModelInfo,
    is_english_only: bool,
}

impl Debug for DistilWhisperModel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("DistilWhisperModel")
            .field("name", &self.model_info.name)
            .field("variant", &self.model_info.variant)
            .field("device", &self.device)
            .field("english_only", &self.is_english_only)
            .finish()
    }
}

impl DistilWhisperModel {
    /// Load a Distil-Whisper model from HuggingFace Hub
    pub fn from_pretrained(model_id: &str, device: Device) -> Result<Self, AntennaError> {
        tracing::info!("Loading Distil-Whisper model: {}", model_id);

        // Determine if English-only
        let is_english_only = model_id.ends_with(".en");

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

        // Load mel filters (optional, we generate them if not available)
        let _mel_bytes = match repo.get("mel_filters.npz") {
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
        let mel_filters =
            WhisperModel::generate_mel_filters(config.num_mel_bins, 201, 16000);

        // Build model info
        let model_info = Self::build_model_info(model_id, is_english_only);

        tracing::info!("Model loaded successfully");

        Ok(Self {
            model,
            config,
            tokenizer,
            device,
            mel_filters,
            special_tokens: SpecialTokens::default(),
            model_info,
            is_english_only,
        })
    }

    /// Load model by size name
    pub fn from_size(size: &str, device: Device) -> Result<Self, AntennaError> {
        let model_size = DistilWhisperSize::from_str(size).ok_or_else(|| {
            AntennaError::ModelError(format!(
                "Unknown Distil-Whisper model size: '{}'. Valid sizes: distil-small.en, distil-medium.en, distil-large-v2, distil-large-v3",
                size
            ))
        })?;

        Self::from_pretrained(model_size.model_id(), device)
    }

    /// Build ModelInfo for a given model ID
    fn build_model_info(model_id: &str, is_english_only: bool) -> ModelInfo {
        let variant = model_id
            .split('/')
            .last()
            .unwrap_or(model_id)
            .to_string();

        let supported_languages: Vec<String> = if is_english_only {
            vec!["en".to_string()]
        } else {
            LANGUAGES.iter().map(|(code, _)| code.to_string()).collect()
        };

        let capabilities = ModelCapabilities {
            architecture: ModelArchitecture::EncoderDecoder,
            supports_translation: !is_english_only, // English-only can't translate
            supports_language_detection: !is_english_only,
            supports_timestamps: true,
            max_audio_duration: 30.0,
            supported_languages,
        };

        ModelInfo::new(format!("Distil-Whisper {}", variant), "distil-whisper", variant)
            .with_capabilities(capabilities)
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
                "Audio must be 16kHz. Use preprocess_audio() first.".to_string(),
            ));
        }

        if audio.channels != 1 {
            return Err(AntennaError::PreprocessingError(
                "Audio must be mono. Use preprocess_audio() first.".to_string(),
            ));
        }

        // Convert to mel spectrogram
        let mel = audio_to_mel_spectrogram(audio, &self.mel_filters, &self.config, &self.device)?;

        // For English-only models, force English language
        let language = if self.is_english_only {
            Some("en".to_string())
        } else if options.language.is_some() {
            options.language.clone()
        } else {
            Some(self.detect_language_internal(&mel)?)
        };

        // Transcribe in chunks
        let chunk_duration = 30.0;
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

            for mut segment in segments {
                segment.start += current_time;
                segment.end += current_time;
                all_segments.push(segment);
            }

            current_time += chunk_duration;
        }

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
        let encoder_output = self
            .model
            .encoder
            .forward(mel, true)
            .map_err(|e| AntennaError::ModelError(format!("Encoder forward failed: {}", e)))?;

        let mut prompt_tokens = vec![self.special_tokens.sot];

        if let Some(lang) = language {
            if let Some(lang_token) = self.tokenizer.get_language_token(lang) {
                prompt_tokens.push(lang_token);
            }
        }

        match options.task {
            Task::Translate => prompt_tokens.push(self.special_tokens.translate),
            Task::Transcribe => prompt_tokens.push(self.special_tokens.transcribe),
        }

        if !options.timestamps {
            prompt_tokens.push(self.special_tokens.no_timestamps);
        }

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

        if options.timestamps {
            self.extract_segments_with_timestamps(&decoded_tokens)
        } else {
            let text = self.tokenizer.decode(&decoded_tokens, true)?;
            Ok(vec![TranscriptionSegment {
                start: 0.0,
                end: 30.0,
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

    /// Detect language from mel spectrogram
    fn detect_language_internal(&mut self, mel: &Tensor) -> Result<String, AntennaError> {
        if self.is_english_only {
            return Ok("en".to_string());
        }

        let encoder_output = self
            .model
            .encoder
            .forward(mel, true)
            .map_err(|e| AntennaError::ModelError(format!("Encoder forward failed: {}", e)))?;

        let sot_tensor = Tensor::new(&[self.special_tokens.sot], &self.device)
            .map_err(|e| AntennaError::ModelError(format!("Failed to create SOT tensor: {}", e)))?
            .unsqueeze(0)
            .map_err(|e| AntennaError::ModelError(format!("Failed to unsqueeze: {}", e)))?;

        let hidden_states = self
            .model
            .decoder
            .forward(&sot_tensor, &encoder_output, true)
            .map_err(|e| AntennaError::ModelError(format!("Decoder forward failed: {}", e)))?;

        let logits = self
            .model
            .decoder
            .final_linear(&hidden_states)
            .map_err(|e| AntennaError::ModelError(format!("Final linear failed: {}", e)))?;

        let logits = logits
            .squeeze(0)
            .map_err(|e| AntennaError::ModelError(format!("Squeeze failed: {}", e)))?;
        let logits = logits
            .get(0)
            .map_err(|e| AntennaError::ModelError(format!("Get failed: {}", e)))?;

        let lang_start = self.special_tokens.language_token_start as usize;
        let lang_end = lang_start + LANGUAGES.len();

        let lang_logits = logits
            .narrow(0, lang_start, lang_end - lang_start)
            .map_err(|e| AntennaError::ModelError(format!("Narrow failed: {}", e)))?;

        let lang_probs = candle_nn::ops::softmax(&lang_logits, 0)
            .map_err(|e| AntennaError::ModelError(format!("Softmax failed: {}", e)))?;

        let lang_probs_vec: Vec<f32> = lang_probs
            .to_vec1()
            .map_err(|e| AntennaError::ModelError(format!("To vec failed: {}", e)))?;

        let (max_idx, _) = lang_probs_vec
            .iter()
            .enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
            .unwrap_or((0, &0.0));

        let language = LANGUAGES
            .get(max_idx)
            .map(|(code, _)| code.to_string())
            .unwrap_or_else(|| "en".to_string());

        Ok(language)
    }

    /// Translate audio to English
    pub fn translate(&mut self, audio: &AudioData) -> Result<TranscriptionResult, AntennaError> {
        if self.is_english_only {
            return Err(AntennaError::ModelError(
                "English-only models cannot translate. Use a multilingual model.".to_string(),
            ));
        }

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

    /// Get model info
    pub fn info(&self) -> &ModelInfo {
        &self.model_info
    }

    /// Check if this model is English-only
    pub fn is_english_only(&self) -> bool {
        self.is_english_only
    }
}

// ============================================================================
// SpeechModel Trait Implementation
// ============================================================================

impl SpeechModel for DistilWhisperModel {
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

        let result = DistilWhisperModel::transcribe(self, audio, whisper_options)?;

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
        if self.is_english_only {
            return Ok("en".to_string());
        }

        let mel = audio_to_mel_spectrogram(audio, &self.mel_filters, &self.config, &self.device)?;
        self.detect_language_internal(&mel)
    }

    fn preprocess_audio(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        let mut processed = audio.clone();

        if processed.channels > 1 {
            processed = convert_to_mono(&processed);
        }

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
    fn test_model_info_english_only() {
        let info = DistilWhisperModel::build_model_info("distil-whisper/distil-small.en", true);
        assert_eq!(info.family, "distil-whisper");
        assert!(!info.capabilities.supports_translation);
        assert_eq!(info.capabilities.supported_languages, vec!["en"]);
    }

    #[test]
    fn test_model_info_multilingual() {
        let info = DistilWhisperModel::build_model_info("distil-whisper/distil-large-v3", false);
        assert_eq!(info.family, "distil-whisper");
        assert!(info.capabilities.supports_translation);
        assert!(info.capabilities.supported_languages.len() > 50);
    }
}
