//! Wav2Vec2 model implementation using ONNX Runtime
//!
//! Provides speech-to-text transcription using ONNX-exported Wav2Vec2 models.
//! Unlike Whisper (encoder-decoder), Wav2Vec2 is encoder-only with CTC output.
//!
//! # Architecture
//!
//! ```text
//! Raw Audio (16kHz) → CNN Feature Encoder → Transformer → CTC Head → CTC Decode → Text
//! ```
//!
//! # Supported Models
//!
//! Most Wav2Vec2 models on HuggingFace have ONNX exports available:
//! - `facebook/wav2vec2-base-960h` - Base model (95M params)
//! - `facebook/wav2vec2-large-960h` - Large model (317M params)
//! - `jonatasgrosman/wav2vec2-large-xlsr-53-english` - Multilingual fine-tuned
//!
//! # Example
//!
//! ```rust,ignore
//! use antenna::ml::wav2vec2::Wav2Vec2Model;
//!
//! let model = Wav2Vec2Model::from_pretrained("facebook/wav2vec2-base-960h", "cpu")?;
//! let result = model.transcribe(&audio, Default::default())?;
//! println!("Transcription: {}", result.text);
//! ```

use std::fmt::{self, Debug};
use std::path::PathBuf;

use candle_core::Device;
use hf_hub::{api::sync::Api, Repo, RepoType};

use crate::audio::process::{convert_to_mono, resample};
use crate::error::AntennaError;
use crate::ml::backends::{DeviceSpec, ExecutionProvider, OnnxSession};
use crate::ml::decode::ctc::CtcDecoder;
use crate::ml::tokenizers::ctc::CtcCharTokenizer;
use crate::ml::traits::{
    ModelArchitecture, ModelCapabilities, ModelInfo, SpeechModel, SttTokenizer,
    TranscriptionOptions, TranscriptionResult, TranscriptionSegment,
};
use crate::types::AudioData;

/// Wav2Vec2 model using ONNX Runtime for inference
///
/// This model uses CTC (Connectionist Temporal Classification) decoding,
/// which is simpler and faster than autoregressive decoding but typically
/// produces slightly lower quality results than encoder-decoder models.
pub struct Wav2Vec2Model {
    /// ONNX Runtime session
    session: OnnxSession,
    /// CTC character tokenizer
    tokenizer: CtcCharTokenizer,
    /// CTC decoder
    decoder: CtcDecoder,
    /// Device specification
    device_spec: DeviceSpec,
    /// Candle device (for compatibility with SpeechModel trait)
    device: Device,
    /// Model metadata
    model_info: ModelInfo,
    /// Vocabulary (character list)
    vocab: Vec<String>,
}

impl Debug for Wav2Vec2Model {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Wav2Vec2Model")
            .field("name", &self.model_info.name)
            .field("variant", &self.model_info.variant)
            .field("device", &self.device_spec)
            .field("provider", &self.session.provider())
            .finish()
    }
}

impl Wav2Vec2Model {
    /// Load a Wav2Vec2 model from HuggingFace Hub
    ///
    /// # Arguments
    ///
    /// * `model_id` - HuggingFace model ID (e.g., "facebook/wav2vec2-base-960h")
    /// * `device` - Device string ("cpu", "cuda", "cuda:0", etc.)
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// let model = Wav2Vec2Model::from_pretrained("facebook/wav2vec2-base-960h", "cuda")?;
    /// ```
    pub fn from_pretrained(model_id: &str, device: &str) -> Result<Self, AntennaError> {
        let device_spec = DeviceSpec::from_str(device)?;
        Self::from_pretrained_with_device(model_id, device_spec)
    }

    /// Load a Wav2Vec2 model with explicit DeviceSpec
    pub fn from_pretrained_with_device(
        model_id: &str,
        device_spec: DeviceSpec,
    ) -> Result<Self, AntennaError> {
        tracing::info!("Loading Wav2Vec2 model: {} on {:?}", model_id, device_spec);

        // Initialize HuggingFace API
        let api = Api::new()
            .map_err(|e| AntennaError::ModelError(format!("Failed to initialize HF API: {}", e)))?;

        let repo = api.repo(Repo::with_revision(
            model_id.to_string(),
            RepoType::Model,
            "main".to_string(),
        ));

        // Download ONNX model file
        // HuggingFace ONNX models can be in different locations
        let onnx_path = Self::download_onnx_model(&repo, model_id)?;

        // Download vocabulary
        let vocab = Self::download_vocab(&repo)?;

        // Create ONNX session
        let provider = ExecutionProvider::from_device_spec(&device_spec);
        tracing::info!("Creating ONNX session with {:?} provider", provider);

        let session = OnnxSession::from_file(&onnx_path, provider)?;

        // Log model input/output info
        tracing::debug!("Model inputs: {:?}", session.input_names());
        tracing::debug!("Model outputs: {:?}", session.output_names());

        // Create tokenizer from vocabulary
        let tokenizer = Self::create_tokenizer(&vocab);

        // Create CTC decoder
        let decoder = CtcDecoder::new().blank_id(0).merge_repeated(true);

        // Create Candle device for trait compatibility
        let device = device_spec.to_candle_device()?;

        // Build model info
        let model_info = Self::build_model_info(model_id);

        tracing::info!("Wav2Vec2 model loaded successfully");

        Ok(Self {
            session,
            tokenizer,
            decoder,
            device_spec,
            device,
            model_info,
            vocab,
        })
    }

    /// Download ONNX model from HuggingFace
    fn download_onnx_model(repo: &hf_hub::api::sync::ApiRepo, model_id: &str) -> Result<PathBuf, AntennaError> {
        // Try different common ONNX file locations
        let onnx_paths = [
            "onnx/model.onnx",
            "model.onnx",
            "onnx/model_quantized.onnx",
            "model_quantized.onnx",
        ];

        for path in &onnx_paths {
            match repo.get(path) {
                Ok(p) => {
                    tracing::info!("Found ONNX model at: {}", path);
                    return Ok(p);
                }
                Err(_) => continue,
            }
        }

        Err(AntennaError::ModelError(format!(
            "No ONNX model found for {}. Tried: {:?}. \
            Please ensure the model has an ONNX export, or use `optimum-cli export onnx` to convert.",
            model_id, onnx_paths
        )))
    }

    /// Download vocabulary from HuggingFace
    fn download_vocab(repo: &hf_hub::api::sync::ApiRepo) -> Result<Vec<String>, AntennaError> {
        // Try vocab.json first (most common for Wav2Vec2)
        if let Ok(vocab_path) = repo.get("vocab.json") {
            let vocab_str = std::fs::read_to_string(&vocab_path)
                .map_err(|e| AntennaError::IoError(format!("Failed to read vocab.json: {}", e)))?;

            // vocab.json is typically {"<pad>": 0, "a": 1, ...}
            let vocab_map: std::collections::HashMap<String, usize> =
                serde_json::from_str(&vocab_str).map_err(|e| {
                    AntennaError::ModelError(format!("Failed to parse vocab.json: {}", e))
                })?;

            // Convert to ordered list
            let mut vocab: Vec<(String, usize)> = vocab_map.into_iter().collect();
            vocab.sort_by_key(|(_, idx)| *idx);
            let vocab: Vec<String> = vocab.into_iter().map(|(s, _)| s).collect();

            tracing::info!("Loaded vocabulary with {} tokens", vocab.len());
            return Ok(vocab);
        }

        // Try tokenizer.json (HuggingFace tokenizers format)
        if let Ok(tokenizer_path) = repo.get("tokenizer.json") {
            let tokenizer_str = std::fs::read_to_string(&tokenizer_path)
                .map_err(|e| AntennaError::IoError(format!("Failed to read tokenizer.json: {}", e)))?;

            let tokenizer_json: serde_json::Value = serde_json::from_str(&tokenizer_str)
                .map_err(|e| AntennaError::ModelError(format!("Failed to parse tokenizer.json: {}", e)))?;

            // Extract vocab from tokenizer.json structure
            if let Some(model) = tokenizer_json.get("model") {
                if let Some(vocab) = model.get("vocab") {
                    if let Some(vocab_map) = vocab.as_object() {
                        let mut vocab: Vec<(String, i64)> = vocab_map
                            .iter()
                            .filter_map(|(k, v)| v.as_i64().map(|idx| (k.clone(), idx)))
                            .collect();
                        vocab.sort_by_key(|(_, idx)| *idx);
                        let vocab: Vec<String> = vocab.into_iter().map(|(s, _)| s).collect();

                        tracing::info!("Loaded vocabulary with {} tokens from tokenizer.json", vocab.len());
                        return Ok(vocab);
                    }
                }
            }
        }

        // Fall back to standard English alphabet
        tracing::warn!("No vocabulary file found, using default English alphabet");
        Ok(Self::default_english_vocab())
    }

    /// Create default English vocabulary
    fn default_english_vocab() -> Vec<String> {
        let mut vocab = vec!["<pad>".to_string()]; // Blank token at index 0

        // Lowercase letters
        for c in 'a'..='z' {
            vocab.push(c.to_string());
        }

        // Common tokens
        vocab.push(" ".to_string());  // Space
        vocab.push("'".to_string());  // Apostrophe
        vocab.push("|".to_string());  // Word separator (some models use this)

        vocab
    }

    /// Create tokenizer from vocabulary
    fn create_tokenizer(vocab: &[String]) -> CtcCharTokenizer {
        let chars: Vec<char> = vocab
            .iter()
            .map(|s| {
                if s.len() == 1 {
                    s.chars().next().unwrap()
                } else {
                    // Special token placeholder
                    '<'
                }
            })
            .collect();

        CtcCharTokenizer::new(&chars, 0)
    }

    /// Build model info from model ID
    fn build_model_info(model_id: &str) -> ModelInfo {
        let variant = model_id
            .split('/')
            .last()
            .unwrap_or("unknown")
            .to_string();

        let capabilities = ModelCapabilities {
            architecture: ModelArchitecture::EncoderOnly,
            supports_translation: false,
            supports_language_detection: false,
            supports_timestamps: true, // CTC provides frame alignments
            max_audio_duration: 60.0,  // Can handle longer audio than Whisper
            supported_languages: vec!["en".to_string()], // Most Wav2Vec2 are English-only
        };

        ModelInfo::new(model_id, "wav2vec2", variant).with_capabilities(capabilities)
    }

    /// Run inference on preprocessed audio
    fn run_inference(&mut self, audio_samples: &[f32]) -> Result<Vec<Vec<f32>>, AntennaError> {
        // Prepare input tensor: [batch_size, sequence_length]
        let input_len = audio_samples.len();

        // Use ort's ndarray integration
        let input_array = ort::value::Tensor::from_array((
            vec![1, input_len],
            audio_samples.to_vec(),
        ))
        .map_err(|e| AntennaError::ModelError(format!("Failed to create input tensor: {}", e)))?;

        // Get input and output names (before borrowing session mutably)
        let input_names = self.session.input_names();
        let input_name = input_names
            .first()
            .ok_or_else(|| AntennaError::ModelError("Model has no inputs".to_string()))?
            .clone();

        let output_names = self.session.output_names();
        let output_name = output_names
            .first()
            .ok_or_else(|| AntennaError::ModelError("Model has no outputs".to_string()))?
            .clone();

        // Run inference
        let outputs = self.session.inner_mut()
            .run(ort::inputs![input_name.as_str() => input_array])
            .map_err(|e| AntennaError::ModelError(format!("ONNX inference failed: {}", e)))?;

        // Get output tensor
        let output = outputs
            .get(output_name.as_str())
            .ok_or_else(|| AntennaError::ModelError(format!("Output '{}' not found", output_name)))?;

        // Extract logits: typically [batch, time, vocab_size]
        // try_extract_tensor returns (&Shape, &[T]) tuple
        let (shape, logits_data) = output
            .try_extract_tensor::<f32>()
            .map_err(|e| AntennaError::ModelError(format!("Failed to extract tensor: {}", e)))?;

        // Shape is a wrapper around dimensions
        let dims: Vec<i64> = shape.iter().copied().collect();

        if dims.len() != 3 {
            return Err(AntennaError::ModelError(format!(
                "Expected 3D output [batch, time, vocab], got {:?}",
                dims
            )));
        }

        let _batch_size = dims[0] as usize;
        let time_steps = dims[1] as usize;
        let vocab_size = dims[2] as usize;

        // Convert to Vec<Vec<f32>> for CTC decoder
        let mut result = Vec::with_capacity(time_steps);
        for t in 0..time_steps {
            let start_idx = t * vocab_size;
            let end_idx = start_idx + vocab_size;
            let frame: Vec<f32> = logits_data[start_idx..end_idx].to_vec();
            result.push(frame);
        }

        Ok(result)
    }

    /// Decode CTC output to text
    fn decode_ctc(&self, logits: Vec<Vec<f32>>) -> Result<(String, Vec<u32>), AntennaError> {
        use candle_core::Tensor;

        let time_steps = logits.len();
        let vocab_size = logits.first().map(|v| v.len()).unwrap_or(0);

        if time_steps == 0 || vocab_size == 0 {
            return Ok((String::new(), vec![]));
        }

        // Convert to Candle tensor for CTC decoder
        let flat: Vec<f32> = logits.into_iter().flatten().collect();
        let tensor = Tensor::from_vec(flat, (time_steps, vocab_size), &self.device)
            .map_err(|e| AntennaError::ModelError(format!("Failed to create logits tensor: {}", e)))?;

        // Run CTC decoding
        let ctc_result = self.decoder.decode(&tensor, &self.device)?;

        // Convert token IDs to text
        let text = self.tokenizer.decode(&ctc_result.tokens, true)?;

        // Clean up text (normalize whitespace, trim)
        let text = text
            .replace("|", " ")  // Some models use | as word separator
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ");

        Ok((text, ctc_result.tokens))
    }

    /// Get the vocabulary
    pub fn vocab(&self) -> &[String] {
        &self.vocab
    }

    /// Get the execution provider being used
    pub fn execution_provider(&self) -> ExecutionProvider {
        self.session.provider()
    }
}

impl SpeechModel for Wav2Vec2Model {
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
            "Processing audio: {} samples, {}Hz",
            processed.samples.len(),
            processed.sample_rate
        );

        // Run ONNX inference
        let logits = self.run_inference(&processed.samples)?;

        tracing::debug!("Got {} time steps from encoder", logits.len());

        // Decode with CTC
        let (text, tokens) = self.decode_ctc(logits)?;

        tracing::debug!("Transcribed: {}", text);

        // Build result
        let duration = processed.duration();
        let segment = TranscriptionSegment {
            start: 0.0,
            end: duration,
            text: text.clone(),
            tokens,
            avg_logprob: None,
            no_speech_prob: None,
        };

        Ok(TranscriptionResult {
            text,
            segments: vec![segment],
            language: Some("en".to_string()),
            language_probability: None,
        })
    }

    fn detect_language(&mut self, _audio: &AudioData) -> Result<String, AntennaError> {
        // Wav2Vec2 models are typically monolingual
        if !self.model_info.capabilities.supports_language_detection {
            return Err(AntennaError::ModelError(
                "Wav2Vec2 does not support language detection".to_string(),
            ));
        }
        Ok("en".to_string())
    }

    fn preprocess_audio(&self, audio: &AudioData) -> Result<AudioData, AntennaError> {
        // Convert to mono
        let mono = convert_to_mono(audio);

        // Resample to 16kHz (Wav2Vec2 expected sample rate)
        let resampled = resample(&mono, 16000)?;

        // Normalize to [-1, 1] range
        let max_abs = resampled
            .samples
            .iter()
            .map(|s| s.abs())
            .fold(0.0f32, f32::max);

        let normalized = if max_abs > 0.0 && max_abs != 1.0 {
            AudioData::new(
                resampled.samples.iter().map(|s| s / max_abs).collect(),
                resampled.sample_rate,
                resampled.channels,
            )
        } else {
            resampled
        };

        Ok(normalized)
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
        let info = Wav2Vec2Model::build_model_info("facebook/wav2vec2-base-960h");
        assert_eq!(info.family, "wav2vec2");
        assert_eq!(info.variant, "wav2vec2-base-960h");
        assert_eq!(info.capabilities.architecture, ModelArchitecture::EncoderOnly);
    }

    #[test]
    fn test_default_english_vocab() {
        let vocab = Wav2Vec2Model::default_english_vocab();
        assert_eq!(vocab[0], "<pad>"); // Blank token
        assert_eq!(vocab[1], "a");
        assert_eq!(vocab[26], "z");
        assert!(vocab.contains(&" ".to_string())); // Space
    }

    #[test]
    fn test_create_tokenizer() {
        let vocab = Wav2Vec2Model::default_english_vocab();
        let tokenizer = Wav2Vec2Model::create_tokenizer(&vocab);

        assert_eq!(tokenizer.blank_id(), 0);
        assert_eq!(tokenizer.vocab_size(), vocab.len());
    }
}
