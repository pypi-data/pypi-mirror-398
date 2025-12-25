use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use candle_core::Device;
use std::sync::Arc;
use parking_lot::Mutex as ParkingMutex;

mod error;
mod types;
pub mod audio;
pub mod ml;
pub mod streaming;

// Server module (enabled by "server" feature)
#[cfg(feature = "server")]
pub mod server;

pub use error::AntennaError;
pub use types::{AudioData, PyAudioData, PyTranscriptionResult, PyTranscriptionSegment};

// ============================================================================
// Device Utilities
// ============================================================================

/// Parse device string into candle Device
///
/// Supports: "cpu", "cuda", "cuda:0", "gpu", "metal", "metal:0", "mps"
fn parse_device(device: Option<&str>) -> PyResult<Device> {
    match device {
        Some("cpu") | None => Ok(Device::Cpu),
        Some("cuda") | Some("gpu") => {
            Device::new_cuda(0).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "CUDA not available: {}. Use device='cpu' instead.",
                    e
                ))
            })
        }
        Some(s) if s.starts_with("cuda:") || s.starts_with("gpu:") => {
            let idx_str = s.split(':').nth(1).ok_or_else(|| {
                pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid device format '{}'. Use 'cuda:0', 'cuda:1', etc.",
                    s
                ))
            })?;
            let idx: usize = idx_str.parse().map_err(|_| {
                pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid GPU index '{}'. Must be a non-negative integer.",
                    idx_str
                ))
            })?;
            Device::new_cuda(idx).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "CUDA device {} not available: {}. Use device='cpu' instead.",
                    idx, e
                ))
            })
        }
        Some("metal") | Some("mps") => {
            Device::new_metal(0).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Metal not available: {}. Use device='cpu' instead.",
                    e
                ))
            })
        }
        Some(s) if s.starts_with("metal:") || s.starts_with("mps:") => {
            let idx_str = s.split(':').nth(1).ok_or_else(|| {
                pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid device format '{}'. Use 'metal:0', etc.",
                    s
                ))
            })?;
            let idx: usize = idx_str.parse().map_err(|_| {
                pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid Metal device index '{}'. Must be a non-negative integer.",
                    idx_str
                ))
            })?;
            Device::new_metal(idx).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Metal device {} not available: {}. Use device='cpu' instead.",
                    idx, e
                ))
            })
        }
        Some(other) => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Invalid device '{}'. Use 'cpu', 'cuda', 'cuda:N', 'metal', 'metal:N', etc.",
            other
        ))),
    }
}

/// Check if CUDA is available
#[pyfunction]
fn is_cuda_available() -> bool {
    Device::new_cuda(0).is_ok()
}

/// Get the number of available CUDA devices
#[pyfunction]
fn cuda_device_count() -> usize {
    let mut count = 0;
    while Device::new_cuda(count).is_ok() {
        count += 1;
        // Safety limit to prevent infinite loop
        if count > 16 {
            break;
        }
    }
    count
}

/// Check if Metal GPU is available (macOS only)
#[pyfunction]
fn is_metal_available() -> bool {
    Device::new_metal(0).is_ok()
}

/// Get the number of available Metal devices (macOS only)
#[pyfunction]
fn metal_device_count() -> usize {
    let mut count = 0;
    while Device::new_metal(count).is_ok() {
        count += 1;
        // Safety limit - typically only 1 Metal device on macOS
        if count > 4 {
            break;
        }
    }
    count
}

/// Check if any GPU is available (CUDA or Metal)
#[pyfunction]
fn is_gpu_available() -> bool {
    is_cuda_available() || is_metal_available()
}

/// Check if ONNX Runtime CUDA support is available
///
/// Returns True if built with 'onnx-cuda' or 'onnx-tensorrt' features.
#[pyfunction]
fn is_onnx_cuda_available() -> bool {
    cfg!(feature = "onnx-cuda") || cfg!(feature = "onnx-tensorrt")
}

/// Check if ONNX Runtime TensorRT support is available
#[pyfunction]
fn is_onnx_tensorrt_available() -> bool {
    cfg!(feature = "onnx-tensorrt")
}

/// Audio statistics for Python
#[pyclass]
pub struct PyAudioStats {
    #[pyo3(get)]
    pub rms: f32,
    #[pyo3(get)]
    pub peak: f32,
    #[pyo3(get)]
    pub peak_db: f32,
    #[pyo3(get)]
    pub rms_db: f32,
    #[pyo3(get)]
    pub zero_crossing_rate: f32,
    #[pyo3(get)]
    pub energy: f32,
}

#[pymethods]
impl PyAudioStats {
    fn __repr__(&self) -> String {
        format!(
            "AudioStats(rms={:.4}, peak={:.4}, rms_db={:.2}, peak_db={:.2}, zcr={:.4})",
            self.rms, self.peak, self.rms_db, self.peak_db, self.zero_crossing_rate
        )
    }
}

#[pyfunction]
fn load_audio(path: String) -> PyResult<PyAudioData> {
    let audio = audio::load_audio(&path)?;
    Ok(PyAudioData::from(audio))
}

#[pyfunction]
#[pyo3(signature = (audio, target_sample_rate=None, mono=None))]
fn preprocess_audio(
    audio: &PyAudioData,
    target_sample_rate: Option<u32>,
    mono: Option<bool>,
) -> PyResult<PyAudioData> {
    let mut processed = audio.inner.clone();
    
    if mono.unwrap_or(false) {
        processed = audio::convert_to_mono(&processed);
    }
    
    if let Some(rate) = target_sample_rate {
        processed = audio::resample(&processed, rate)?;
    }
    
    Ok(PyAudioData::from(processed))
}

#[pyfunction]
fn analyze_audio(audio: &PyAudioData) -> PyResult<PyAudioStats> {
    let stats = audio::analyze(&audio.inner);
    Ok(PyAudioStats {
        rms: stats.rms,
        peak: stats.peak,
        peak_db: stats.peak_db,
        rms_db: stats.rms_db,
        zero_crossing_rate: stats.zero_crossing_rate,
        energy: stats.energy,
    })
}

#[pyfunction]
fn trim_silence(audio: &PyAudioData, threshold_db: f32) -> PyResult<PyAudioData> {
    let trimmed = audio::trim_silence(&audio.inner, threshold_db);
    Ok(PyAudioData::from(trimmed))
}

#[pyfunction]
fn detect_silence(
    audio: &PyAudioData,
    threshold_db: f32,
    min_duration: f32,
) -> PyResult<Vec<(f32, f32)>> {
    let segments = audio::detect_silence(&audio.inner, threshold_db, min_duration);
    Ok(segments.into_iter().map(|s| (s.start, s.end)).collect())
}

#[pyfunction]
fn split_on_silence(
    audio: &PyAudioData,
    threshold_db: f32,
    min_silence_duration: f32,
) -> PyResult<Vec<PyAudioData>> {
    let chunks = audio::split_on_silence(&audio.inner, threshold_db, min_silence_duration);
    Ok(chunks.into_iter().map(PyAudioData::from).collect())
}

#[pyfunction]
fn normalize_audio(
    audio: &PyAudioData,
    method: String,
    target_db: f32,
) -> PyResult<PyAudioData> {
    let norm_method = match method.as_str() {
        "peak" => audio::NormalizationMethod::Peak,
        "rms" => audio::NormalizationMethod::Rms,
        "lufs" => audio::NormalizationMethod::Lufs,
        _ => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Invalid normalization method '{}'. Use 'peak', 'rms', or 'lufs'", method),
            ))
        }
    };

    let normalized = audio::normalize(&audio.inner, norm_method, target_db);
    Ok(PyAudioData::from(normalized))
}

#[pyfunction]
fn save_audio(audio: &PyAudioData, path: String) -> PyResult<()> {
    audio::save_audio(&audio.inner, &path)?;
    Ok(())
}

// ============================================================================
// Whisper Speech-to-Text API
// ============================================================================

/// Model capabilities exposed to Python
#[pyclass]
pub struct PyModelCapabilities {
    #[pyo3(get)]
    pub supports_translation: bool,
    #[pyo3(get)]
    pub supports_language_detection: bool,
    #[pyo3(get)]
    pub supports_timestamps: bool,
    #[pyo3(get)]
    pub max_audio_duration: f32,
    #[pyo3(get)]
    pub supported_languages: Vec<String>,
}

#[pymethods]
impl PyModelCapabilities {
    fn __repr__(&self) -> String {
        format!(
            "ModelCapabilities(translation={}, language_detection={}, timestamps={}, max_duration={}s, languages={})",
            self.supports_translation,
            self.supports_language_detection,
            self.supports_timestamps,
            self.max_audio_duration,
            self.supported_languages.len()
        )
    }
}

/// Model information exposed to Python
#[pyclass]
pub struct PyModelInfo {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub family: String,
    #[pyo3(get)]
    pub variant: String,
}

#[pymethods]
impl PyModelInfo {
    fn __repr__(&self) -> String {
        format!(
            "ModelInfo(name='{}', family='{}', variant='{}')",
            self.name, self.family, self.variant
        )
    }
}

/// Whisper model for speech-to-text transcription
#[pyclass]
pub struct PyWhisperModel {
    inner: ml::WhisperModel,
}

#[pymethods]
impl PyWhisperModel {
    /// Load a Whisper model from HuggingFace Hub
    ///
    /// Args:
    ///     model_id: HuggingFace model ID (e.g., "openai/whisper-tiny", "openai/whisper-base")
    ///     device: Device to run on. Options: "cpu", "cuda", "cuda:0", "cuda:1", "gpu", "gpu:0".
    ///             Defaults to "cpu".
    ///
    /// Returns:
    ///     WhisperModel instance ready for transcription
    #[staticmethod]
    #[pyo3(signature = (model_id, device=None))]
    fn from_pretrained(model_id: String, device: Option<String>) -> PyResult<Self> {
        let device = parse_device(device.as_deref())?;
        let model = ml::WhisperModel::from_pretrained(&model_id, device)?;
        Ok(Self { inner: model })
    }

    /// Load a Whisper model by size name
    ///
    /// Args:
    ///     size: Model size ("tiny", "base", "small", "medium", "large", "large-v2", "large-v3")
    ///     device: Device to run on. Options: "cpu", "cuda", "cuda:0", "cuda:1", "gpu", "gpu:0".
    ///             Defaults to "cpu".
    ///
    /// Returns:
    ///     WhisperModel instance ready for transcription
    #[staticmethod]
    #[pyo3(signature = (size, device=None))]
    fn from_size(size: String, device: Option<String>) -> PyResult<Self> {
        let device = parse_device(device.as_deref())?;
        let model = ml::WhisperModel::from_size(&size, device)?;
        Ok(Self { inner: model })
    }

    /// Transcribe audio to text
    ///
    /// Args:
    ///     audio: AudioData to transcribe (must be 16kHz mono)
    ///     language: Language code (e.g., "en", "es"). None for auto-detection.
    ///     task: "transcribe" or "translate" (translate to English)
    ///     beam_size: Beam size for decoding (default: 5, use 1 for greedy)
    ///     timestamps: Whether to include word-level timestamps (default: True)
    ///
    /// Returns:
    ///     TranscriptionResult with text, segments, and detected language
    #[pyo3(signature = (audio, language=None, task=None, beam_size=None, timestamps=None))]
    fn transcribe(
        &mut self,
        audio: &PyAudioData,
        language: Option<String>,
        task: Option<String>,
        beam_size: Option<usize>,
        timestamps: Option<bool>,
    ) -> PyResult<PyTranscriptionResult> {
        let task_enum = match task.as_deref() {
            Some("translate") => ml::Task::Translate,
            Some("transcribe") | None => ml::Task::Transcribe,
            Some(other) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid task '{}'. Use 'transcribe' or 'translate'",
                    other
                )))
            }
        };

        let options = ml::TranscriptionOptions {
            language,
            task: task_enum,
            beam_size: beam_size.unwrap_or(5),
            timestamps: timestamps.unwrap_or(true),
            ..Default::default()
        };

        let result = self.inner.transcribe(&audio.inner, options)?;

        // Convert to Python types
        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Translate audio to English
    ///
    /// Args:
    ///     audio: AudioData to translate (must be 16kHz mono)
    ///
    /// Returns:
    ///     TranscriptionResult with English translation
    fn translate(&mut self, audio: &PyAudioData) -> PyResult<PyTranscriptionResult> {
        let result = self.inner.translate(&audio.inner)?;

        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Detect the language of audio
    ///
    /// Args:
    ///     audio: AudioData to analyze (must be 16kHz mono)
    ///
    /// Returns:
    ///     Detected language code (e.g., "en", "es", "zh")
    fn detect_language(&mut self, audio: &PyAudioData) -> PyResult<String> {
        // Convert to mel for language detection
        let config = self.inner.config().clone();
        let mel_filters = ml::whisper::model::WhisperModel::generate_mel_filters(
            config.num_mel_bins,
            201,
            16000,
        );

        let mel = ml::whisper::inference::audio_to_mel_spectrogram(
            &audio.inner,
            &mel_filters,
            &config,
            self.inner.device(),
        )?;

        let language = self.inner.detect_language(&mel)?;
        Ok(language)
    }

    /// Get model information
    ///
    /// Returns:
    ///     ModelInfo with name, family, and variant
    fn info(&self) -> PyModelInfo {
        let info = self.inner.info();
        PyModelInfo {
            name: info.name.clone(),
            family: info.family.clone(),
            variant: info.variant.clone(),
        }
    }

    /// Get model capabilities
    ///
    /// Returns:
    ///     ModelCapabilities describing what the model can do
    fn capabilities(&self) -> PyModelCapabilities {
        let caps = &self.inner.info().capabilities;
        PyModelCapabilities {
            supports_translation: caps.supports_translation,
            supports_language_detection: caps.supports_language_detection,
            supports_timestamps: caps.supports_timestamps,
            max_audio_duration: caps.max_audio_duration,
            supported_languages: caps.supported_languages.clone(),
        }
    }

    /// Get the device this model is running on
    ///
    /// Returns:
    ///     Device string ("cpu", "cuda", "metal")
    fn device(&self) -> String {
        match self.inner.device() {
            candle_core::Device::Cpu => "cpu".to_string(),
            candle_core::Device::Cuda(_) => "cuda".to_string(),
            candle_core::Device::Metal(_) => "metal".to_string(),
        }
    }

    /// Preprocess audio to the format expected by this model
    ///
    /// Automatically converts to 16kHz mono if needed.
    ///
    /// Args:
    ///     audio: Audio data to preprocess
    ///
    /// Returns:
    ///     Preprocessed AudioData ready for transcription
    fn preprocess(&self, audio: &PyAudioData) -> PyResult<PyAudioData> {
        use ml::SpeechModel;
        let processed = self.inner.preprocess_audio(&audio.inner)?;
        Ok(PyAudioData::from(processed))
    }

    fn __repr__(&self) -> String {
        let info = self.inner.info();
        format!(
            "WhisperModel(name='{}', variant='{}', device='{}')",
            info.name,
            info.variant,
            self.device()
        )
    }
}

/// Helper function to preprocess audio for Whisper (16kHz mono)
#[pyfunction]
fn preprocess_for_whisper(audio: &PyAudioData) -> PyResult<PyAudioData> {
    let mut processed = audio.inner.clone();

    // Convert to mono if needed
    if processed.channels != 1 {
        processed = audio::convert_to_mono(&processed);
    }

    // Resample to 16kHz if needed
    if processed.sample_rate != 16000 {
        processed = audio::resample(&processed, 16000)?;
    }

    Ok(PyAudioData::from(processed))
}

/// Check if a model is cached locally
#[pyfunction]
fn is_model_cached(model_id: String) -> bool {
    ml::WhisperModel::is_model_cached(&model_id)
}

/// List available Whisper model sizes
#[pyfunction]
fn list_whisper_models() -> Vec<(&'static str, &'static str)> {
    vec![
        ("tiny", "openai/whisper-tiny"),
        ("base", "openai/whisper-base"),
        ("small", "openai/whisper-small"),
        ("medium", "openai/whisper-medium"),
        ("large", "openai/whisper-large"),
        ("large-v2", "openai/whisper-large-v2"),
        ("large-v3", "openai/whisper-large-v3"),
    ]
}

// ============================================================================
// Distil-Whisper Speech-to-Text API
// ============================================================================

/// Distil-Whisper model for fast speech-to-text transcription
///
/// Distil-Whisper is a distilled (compressed) version of Whisper that maintains
/// high accuracy while being significantly faster.
#[pyclass]
pub struct PyDistilWhisperModel {
    inner: ml::DistilWhisperModel,
}

#[pymethods]
impl PyDistilWhisperModel {
    /// Load a Distil-Whisper model from HuggingFace Hub
    ///
    /// Args:
    ///     model_id: HuggingFace model ID (e.g., "distil-whisper/distil-small.en")
    ///     device: Device to run on. Options: "cpu", "cuda", "gpu". Defaults to "cpu".
    ///
    /// Returns:
    ///     DistilWhisperModel instance ready for transcription
    #[staticmethod]
    #[pyo3(signature = (model_id, device=None))]
    fn from_pretrained(model_id: String, device: Option<String>) -> PyResult<Self> {
        let device = parse_device(device.as_deref())?;
        let model = ml::DistilWhisperModel::from_pretrained(&model_id, device)?;
        Ok(Self { inner: model })
    }

    /// Load a Distil-Whisper model by size name
    ///
    /// Args:
    ///     size: Model size ("distil-small.en", "distil-medium.en", "distil-large-v2", "distil-large-v3")
    ///     device: Device to run on. Options: "cpu", "cuda", "gpu". Defaults to "cpu".
    ///
    /// Returns:
    ///     DistilWhisperModel instance ready for transcription
    #[staticmethod]
    #[pyo3(signature = (size, device=None))]
    fn from_size(size: String, device: Option<String>) -> PyResult<Self> {
        let device = parse_device(device.as_deref())?;
        let model = ml::DistilWhisperModel::from_size(&size, device)?;
        Ok(Self { inner: model })
    }

    /// Transcribe audio to text
    ///
    /// Args:
    ///     audio: AudioData to transcribe (must be 16kHz mono)
    ///     language: Language code (e.g., "en", "es"). None for auto-detection.
    ///     task: "transcribe" or "translate" (translate to English)
    ///     beam_size: Beam size for decoding (default: 5)
    ///     timestamps: Whether to include timestamps (default: True)
    ///
    /// Returns:
    ///     TranscriptionResult with text, segments, and detected language
    #[pyo3(signature = (audio, language=None, task=None, beam_size=None, timestamps=None))]
    fn transcribe(
        &mut self,
        audio: &PyAudioData,
        language: Option<String>,
        task: Option<String>,
        beam_size: Option<usize>,
        timestamps: Option<bool>,
    ) -> PyResult<PyTranscriptionResult> {
        let task_enum = match task.as_deref() {
            Some("translate") => ml::Task::Translate,
            Some("transcribe") | None => ml::Task::Transcribe,
            Some(other) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid task '{}'. Use 'transcribe' or 'translate'",
                    other
                )))
            }
        };

        let options = ml::TranscriptionOptions {
            language,
            task: task_enum,
            beam_size: beam_size.unwrap_or(5),
            timestamps: timestamps.unwrap_or(true),
            ..Default::default()
        };

        let result = self.inner.transcribe(&audio.inner, options)?;

        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Translate audio to English
    ///
    /// Note: Only works with multilingual models (distil-large-v2, distil-large-v3).
    /// English-only models will return an error.
    fn translate(&mut self, audio: &PyAudioData) -> PyResult<PyTranscriptionResult> {
        let result = self.inner.translate(&audio.inner)?;

        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Detect the language of audio
    fn detect_language(&mut self, audio: &PyAudioData) -> PyResult<String> {
        use ml::SpeechModel;
        let language = self.inner.detect_language(&audio.inner)?;
        Ok(language)
    }

    /// Get model information
    fn info(&self) -> PyModelInfo {
        let info = self.inner.info();
        PyModelInfo {
            name: info.name.clone(),
            family: info.family.clone(),
            variant: info.variant.clone(),
        }
    }

    /// Get model capabilities
    fn capabilities(&self) -> PyModelCapabilities {
        let caps = &self.inner.info().capabilities;
        PyModelCapabilities {
            supports_translation: caps.supports_translation,
            supports_language_detection: caps.supports_language_detection,
            supports_timestamps: caps.supports_timestamps,
            max_audio_duration: caps.max_audio_duration,
            supported_languages: caps.supported_languages.clone(),
        }
    }

    /// Get the device this model is running on
    fn device(&self) -> String {
        match self.inner.device() {
            candle_core::Device::Cpu => "cpu".to_string(),
            candle_core::Device::Cuda(_) => "cuda".to_string(),
            candle_core::Device::Metal(_) => "metal".to_string(),
        }
    }

    /// Check if this is an English-only model
    fn is_english_only(&self) -> bool {
        self.inner.is_english_only()
    }

    /// Preprocess audio to the format expected by this model
    fn preprocess(&self, audio: &PyAudioData) -> PyResult<PyAudioData> {
        use ml::SpeechModel;
        let processed = self.inner.preprocess_audio(&audio.inner)?;
        Ok(PyAudioData::from(processed))
    }

    fn __repr__(&self) -> String {
        let info = self.inner.info();
        format!(
            "DistilWhisperModel(name='{}', variant='{}', device='{}', english_only={})",
            info.name,
            info.variant,
            self.device(),
            self.is_english_only()
        )
    }
}

/// List available Distil-Whisper model sizes
#[pyfunction]
fn list_distil_whisper_models() -> Vec<(&'static str, &'static str, &'static str)> {
    ml::distil_whisper::DISTIL_WHISPER_MODELS.to_vec()
}

// ============================================================================
// Wav2Vec2 Speech-to-Text API (requires ONNX feature)
// ============================================================================

/// Wav2Vec2 model for speech-to-text using ONNX Runtime
///
/// Wav2Vec2 uses CTC (Connectionist Temporal Classification) decoding,
/// which is simpler than autoregressive decoding but typically faster.
#[cfg(feature = "onnx")]
#[pyclass]
pub struct PyWav2Vec2Model {
    inner: ml::Wav2Vec2Model,
}

#[cfg(feature = "onnx")]
#[pymethods]
impl PyWav2Vec2Model {
    /// Load a Wav2Vec2 model from HuggingFace Hub
    ///
    /// Args:
    ///     model_id: HuggingFace model ID (e.g., "facebook/wav2vec2-base-960h")
    ///     device: Device to run on. Options: "cpu", "cuda", "cuda:0".
    ///             Defaults to "cpu".
    ///
    /// Returns:
    ///     Wav2Vec2Model instance ready for transcription
    ///
    /// Note:
    ///     The model must have an ONNX export available. Most popular Wav2Vec2
    ///     models on HuggingFace include ONNX versions.
    #[staticmethod]
    #[pyo3(signature = (model_id, device=None))]
    fn from_pretrained(model_id: String, device: Option<String>) -> PyResult<Self> {
        let device_str = device.as_deref().unwrap_or("cpu");
        let model = ml::Wav2Vec2Model::from_pretrained(&model_id, device_str)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner: model })
    }

    /// Transcribe audio to text
    ///
    /// Args:
    ///     audio: AudioData to transcribe (will be preprocessed automatically)
    ///     beam_size: Beam size for CTC decoding (default: 1 for greedy)
    ///
    /// Returns:
    ///     TranscriptionResult with text and segments
    #[pyo3(signature = (audio, beam_size=None))]
    fn transcribe(
        &mut self,
        audio: &PyAudioData,
        beam_size: Option<usize>,
    ) -> PyResult<PyTranscriptionResult> {
        use ml::traits::SpeechModel;

        let options = ml::traits::TranscriptionOptions {
            beam_size: beam_size.unwrap_or(1),
            ..Default::default()
        };

        let result = self.inner.transcribe(&audio.inner, options)?;

        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Get model information
    ///
    /// Returns:
    ///     ModelInfo with name, family, and variant
    fn info(&self) -> PyModelInfo {
        use ml::traits::SpeechModel;
        let info = self.inner.info();
        PyModelInfo {
            name: info.name.clone(),
            family: info.family.clone(),
            variant: info.variant.clone(),
        }
    }

    /// Get model capabilities
    ///
    /// Returns:
    ///     ModelCapabilities describing what the model can do
    fn capabilities(&self) -> PyModelCapabilities {
        use ml::traits::SpeechModel;
        let caps = &self.inner.info().capabilities;
        PyModelCapabilities {
            supports_translation: caps.supports_translation,
            supports_language_detection: caps.supports_language_detection,
            supports_timestamps: caps.supports_timestamps,
            max_audio_duration: caps.max_audio_duration,
            supported_languages: caps.supported_languages.clone(),
        }
    }

    /// Get the device this model is running on
    ///
    /// Returns:
    ///     Device string ("cpu", "cuda")
    fn device(&self) -> String {
        use ml::traits::SpeechModel;
        match self.inner.device() {
            candle_core::Device::Cpu => "cpu".to_string(),
            candle_core::Device::Cuda(_) => "cuda".to_string(),
            candle_core::Device::Metal(_) => "metal".to_string(),
        }
    }

    /// Get the execution provider used by this model
    ///
    /// Returns:
    ///     Execution provider string ("CPU", "CUDA", "TensorRT", etc.)
    fn execution_provider(&self) -> String {
        self.inner.execution_provider().to_string()
    }

    /// Preprocess audio to the format expected by this model
    ///
    /// Automatically converts to 16kHz mono and normalizes.
    ///
    /// Args:
    ///     audio: Audio data to preprocess
    ///
    /// Returns:
    ///     Preprocessed AudioData ready for transcription
    fn preprocess(&self, audio: &PyAudioData) -> PyResult<PyAudioData> {
        use ml::traits::SpeechModel;
        let processed = self.inner.preprocess_audio(&audio.inner)?;
        Ok(PyAudioData::from(processed))
    }

    fn __repr__(&self) -> String {
        use ml::traits::SpeechModel;
        let info = self.inner.info();
        format!(
            "Wav2Vec2Model(name='{}', variant='{}', device='{}', provider='{}')",
            info.name,
            info.variant,
            self.device(),
            self.execution_provider()
        )
    }
}

/// List available Wav2Vec2 models
///
/// Returns a list of (name, model_id, description) tuples.
#[cfg(feature = "onnx")]
#[pyfunction]
fn list_wav2vec2_models() -> Vec<(&'static str, &'static str, &'static str)> {
    ml::wav2vec2::WAV2VEC2_MODELS.to_vec()
}

/// Check if ONNX Runtime backend is available
#[pyfunction]
fn is_onnx_available() -> bool {
    cfg!(feature = "onnx")
}

// ============================================================================
// Unified Model Registry API
// ============================================================================

/// Model entry for catalog listing
#[pyclass]
pub struct PyModelEntry {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub hf_id: String,
    #[pyo3(get)]
    pub description: String,
    #[pyo3(get)]
    pub family: String,
    #[pyo3(get)]
    pub default_backend: String,
    #[pyo3(get)]
    pub feature_flag: Option<String>,
}

#[pymethods]
impl PyModelEntry {
    fn __repr__(&self) -> String {
        format!(
            "ModelEntry(id='{}', family='{}', backend='{}')",
            self.id, self.family, self.default_backend
        )
    }
}

/// Unified speech model wrapper
///
/// This class wraps any supported speech model and provides a consistent interface
/// for transcription regardless of the underlying model type.
///
/// Use `antenna.load_model()` to create instances.
#[pyclass]
pub struct PySpeechModel {
    inner: ml::DynSpeechModel,
}

#[pymethods]
impl PySpeechModel {
    /// Transcribe audio to text
    ///
    /// Args:
    ///     audio: AudioData to transcribe
    ///     language: Language code (e.g., "en", "es"). None for auto-detection.
    ///     task: "transcribe" or "translate" (translate to English)
    ///     beam_size: Beam size for decoding (default: 5)
    ///     timestamps: Whether to include timestamps (default: True)
    ///
    /// Returns:
    ///     TranscriptionResult with text, segments, and detected language
    #[pyo3(signature = (audio, language=None, task=None, beam_size=None, timestamps=None))]
    fn transcribe(
        &mut self,
        audio: &PyAudioData,
        language: Option<String>,
        task: Option<String>,
        beam_size: Option<usize>,
        timestamps: Option<bool>,
    ) -> PyResult<PyTranscriptionResult> {
        use ml::traits::{TranscriptionOptions, TranscriptionTask};

        let task_enum = match task.as_deref() {
            Some("translate") => TranscriptionTask::Translate,
            Some("transcribe") | None => TranscriptionTask::Transcribe,
            Some(other) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Invalid task '{}'. Use 'transcribe' or 'translate'",
                    other
                )))
            }
        };

        let options = TranscriptionOptions {
            language,
            task: task_enum,
            beam_size: beam_size.unwrap_or(5),
            timestamps: timestamps.unwrap_or(true),
            ..Default::default()
        };

        use ml::traits::SpeechModel;
        let result = self.inner.transcribe(&audio.inner, options)?;

        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Translate audio to English
    ///
    /// Note: Not all models support translation. Use `supports_translation()`
    /// to check.
    ///
    /// Returns:
    ///     TranscriptionResult with English translation
    fn translate(&mut self, audio: &PyAudioData) -> PyResult<PyTranscriptionResult> {
        let result = self.inner.translate(&audio.inner)?;

        let segments: Vec<PyTranscriptionSegment> = result
            .segments
            .into_iter()
            .map(|s| PyTranscriptionSegment {
                start: s.start,
                end: s.end,
                text: s.text,
            })
            .collect();

        Ok(PyTranscriptionResult::new(
            result.text,
            result.language,
            result.language_probability,
            segments,
        ))
    }

    /// Detect the language of audio
    ///
    /// Note: Not all models support language detection.
    ///
    /// Returns:
    ///     Detected language code (e.g., "en", "es", "zh")
    fn detect_language(&mut self, audio: &PyAudioData) -> PyResult<String> {
        use ml::traits::SpeechModel;
        let language = self.inner.detect_language(&audio.inner)?;
        Ok(language)
    }

    /// Get model information
    fn info(&self) -> PyModelInfo {
        use ml::traits::SpeechModel;
        let info = self.inner.info();
        PyModelInfo {
            name: info.name.clone(),
            family: info.family.clone(),
            variant: info.variant.clone(),
        }
    }

    /// Get model capabilities
    fn capabilities(&self) -> PyModelCapabilities {
        use ml::traits::SpeechModel;
        let caps = &self.inner.info().capabilities;
        PyModelCapabilities {
            supports_translation: caps.supports_translation,
            supports_language_detection: caps.supports_language_detection,
            supports_timestamps: caps.supports_timestamps,
            max_audio_duration: caps.max_audio_duration,
            supported_languages: caps.supported_languages.clone(),
        }
    }

    /// Check if this model supports translation
    fn supports_translation(&self) -> bool {
        self.inner.supports_translation()
    }

    /// Check if this model supports language detection
    fn supports_language_detection(&self) -> bool {
        self.inner.supports_language_detection()
    }

    /// Get the device this model is running on
    fn device(&self) -> String {
        use ml::traits::SpeechModel;
        match self.inner.device() {
            candle_core::Device::Cpu => "cpu".to_string(),
            candle_core::Device::Cuda(_) => "cuda".to_string(),
            candle_core::Device::Metal(_) => "metal".to_string(),
        }
    }

    /// Get the model family (whisper, distil-whisper, wav2vec2, etc.)
    fn model_family(&self) -> String {
        format!("{:?}", self.inner.family()).to_lowercase()
    }

    /// Get the backend used for inference
    fn backend(&self) -> String {
        self.inner.backend().to_string()
    }

    /// Preprocess audio for this model
    fn preprocess(&self, audio: &PyAudioData) -> PyResult<PyAudioData> {
        use ml::traits::SpeechModel;
        let processed = self.inner.preprocess_audio(&audio.inner)?;
        Ok(PyAudioData::from(processed))
    }

    fn __repr__(&self) -> String {
        use ml::traits::SpeechModel;
        let info = self.inner.info();
        format!(
            "SpeechModel(name='{}', family='{}', backend='{}', device='{}')",
            info.name,
            info.family,
            self.backend(),
            self.device()
        )
    }
}

/// Load a speech model by ID
///
/// This is the unified entry point for loading any speech-to-text model
/// supported by Antenna. It automatically selects the best backend.
///
/// Args:
///     model_id: Model identifier. Supports formats:
///         - "whisper/base" - family/variant format
///         - "openai/whisper-base" - HuggingFace format
///         - "distil-whisper/distil-small.en" - Distil-Whisper
///         - "wav2vec2/base-960h" - Wav2Vec2 (requires ONNX)
///     device: Device string: "cpu", "cuda", "cuda:0", "cuda:1"
///     backend: Optional explicit backend: "candle", "onnx", "ctranslate2"
///
/// Returns:
///     SpeechModel instance ready for transcription
///
/// Example (Python):
///     ```python
///     model = antenna.load_model("whisper/base", device="cuda")
///     result = model.transcribe(audio)
///
///     model = antenna.load_model("wav2vec2/base-960h", device="cpu")
///     result = model.transcribe(audio)
///     ```
#[pyfunction]
#[pyo3(signature = (model_id, device=None, backend=None))]
fn py_load_model(
    model_id: String,
    device: Option<String>,
    backend: Option<String>,
) -> PyResult<PySpeechModel> {
    let device_str = device.as_deref().unwrap_or("cpu");
    let backend_str = backend.as_deref();

    let model = ml::load_model(&model_id, device_str, backend_str)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(PySpeechModel { inner: model })
}

/// List all available models
///
/// Returns a list of model entries with their IDs, descriptions, and requirements.
///
/// Returns:
///     List of ModelEntry objects describing available models
///
/// Example:
///     >>> for m in antenna.list_models():
///     ...     print(f"{m.id}: {m.description}")
///     whisper/tiny: OpenAI Whisper tiny - Multilingual speech recognition
///     whisper/base: OpenAI Whisper base - Multilingual speech recognition
///     ...
#[pyfunction]
fn py_list_models() -> Vec<PyModelEntry> {
    ml::list_models()
        .into_iter()
        .map(|m| PyModelEntry {
            id: m.id,
            hf_id: m.hf_id,
            description: m.description,
            family: format!("{:?}", m.family).to_lowercase(),
            default_backend: m.default_backend.to_string(),
            feature_flag: m.feature_flag,
        })
        .collect()
}

/// Check if a specific model is available
///
/// A model is available if all required features are enabled.
///
/// Args:
///     model_id: Model identifier (e.g., "whisper/base", "wav2vec2/base-960h")
///
/// Returns:
///     True if the model can be loaded, False otherwise
///
/// Example:
///     >>> antenna.is_model_available("whisper/base")
///     True
///     >>> antenna.is_model_available("wav2vec2/base-960h")  # False if ONNX not enabled
///     False
#[pyfunction]
fn py_is_model_available(model_id: String) -> bool {
    ml::is_model_available(&model_id)
}

// ============================================================================
// Streaming Transcription API
// ============================================================================

/// Configuration for local agreement policy (stabilizes partial results)
#[pyclass]
#[derive(Clone)]
pub struct PyAgreementConfig {
    inner: streaming::AgreementConfig,
}

#[pymethods]
impl PyAgreementConfig {
    /// Create a new agreement configuration
    ///
    /// Args:
    ///     agreement_count: Number of consecutive runs that must agree (default: 2)
    ///     max_buffer_tokens: Maximum tokens to buffer before forcing emission (default: 100)
    ///     min_emit_tokens: Minimum tokens to emit at once (default: 1)
    #[new]
    #[pyo3(signature = (agreement_count=2, max_buffer_tokens=100, min_emit_tokens=1))]
    fn new(agreement_count: usize, max_buffer_tokens: usize, min_emit_tokens: usize) -> Self {
        Self {
            inner: streaming::AgreementConfig {
                agreement_count,
                max_buffer_tokens,
                min_emit_tokens,
            },
        }
    }

    /// Create a strict config requiring more agreement
    #[staticmethod]
    fn strict() -> Self {
        Self {
            inner: streaming::AgreementConfig::strict(),
        }
    }

    /// Create a fast config with minimal agreement
    #[staticmethod]
    fn fast() -> Self {
        Self {
            inner: streaming::AgreementConfig::fast(),
        }
    }

    #[getter]
    fn agreement_count(&self) -> usize {
        self.inner.agreement_count
    }

    #[getter]
    fn max_buffer_tokens(&self) -> usize {
        self.inner.max_buffer_tokens
    }

    #[getter]
    fn min_emit_tokens(&self) -> usize {
        self.inner.min_emit_tokens
    }

    fn __repr__(&self) -> String {
        format!(
            "AgreementConfig(agreement_count={}, max_buffer_tokens={})",
            self.inner.agreement_count, self.inner.max_buffer_tokens
        )
    }
}

/// Ring buffer for efficient audio streaming with overlap support
#[pyclass]
pub struct PyAudioRingBuffer {
    inner: streaming::AudioRingBuffer,
}

#[pymethods]
impl PyAudioRingBuffer {
    /// Create a new ring buffer
    ///
    /// Args:
    ///     capacity_seconds: Maximum audio duration to buffer (default: 60.0)
    ///     sample_rate: Audio sample rate in Hz (default: 16000)
    ///     overlap_seconds: Overlap duration for context preservation (default: 0.5)
    #[new]
    #[pyo3(signature = (capacity_seconds=60.0, sample_rate=16000, overlap_seconds=0.5))]
    fn new(capacity_seconds: f64, sample_rate: u32, overlap_seconds: f64) -> Self {
        Self {
            inner: streaming::AudioRingBuffer::new(capacity_seconds, sample_rate, overlap_seconds),
        }
    }

    /// Push samples into the buffer
    fn push(&mut self, samples: Vec<f32>) {
        self.inner.push(&samples);
    }

    /// Read samples from the buffer (consumes them)
    fn read(&mut self, num_samples: usize) -> Vec<f32> {
        self.inner.read(num_samples)
    }

    /// Read all samples from the buffer
    fn read_all(&mut self) -> Vec<f32> {
        self.inner.read_all()
    }

    /// Read samples with overlap preservation
    fn read_with_overlap(&mut self, num_samples: usize) -> Vec<f32> {
        self.inner.read_with_overlap(num_samples)
    }

    /// Peek at samples without consuming them
    fn peek(&self, num_samples: usize) -> Vec<f32> {
        self.inner.peek(num_samples)
    }

    /// Clear the buffer
    fn clear(&mut self) {
        self.inner.clear();
    }

    /// Get the number of samples in the buffer
    #[getter]
    fn len(&self) -> usize {
        self.inner.len()
    }

    /// Check if the buffer is empty
    fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    /// Get the duration of audio in the buffer (seconds)
    #[getter]
    fn duration(&self) -> f64 {
        self.inner.duration()
    }

    /// Get the sample rate
    #[getter]
    fn sample_rate(&self) -> u32 {
        self.inner.sample_rate()
    }

    /// Get the capacity in samples
    #[getter]
    fn capacity(&self) -> usize {
        self.inner.capacity()
    }

    /// Get the overlap size in samples
    #[getter]
    fn overlap_samples(&self) -> usize {
        self.inner.overlap_samples()
    }

    fn __repr__(&self) -> String {
        format!(
            "AudioRingBuffer(duration={:.2}s, capacity={:.1}s)",
            self.inner.duration(),
            self.inner.capacity_seconds()
        )
    }

    fn __len__(&self) -> usize {
        self.inner.len()
    }
}

/// Configuration for streaming transcription
#[pyclass]
#[derive(Clone)]
pub struct PyStreamingConfig {
    inner: streaming::StreamingConfig,
}

#[pymethods]
impl PyStreamingConfig {
    /// Create a new streaming configuration
    ///
    /// Args:
    ///     sample_rate: Audio sample rate in Hz (default: 16000)
    ///     min_chunk_duration: Minimum audio duration before transcription (default: 0.5s)
    ///     max_chunk_duration: Maximum audio to buffer (default: 30s)
    ///     use_vad: Enable Voice Activity Detection (default: True)
    ///     vad_threshold_db: VAD sensitivity in dB (default: -40.0)
    ///     language: Language code for transcription (default: None for auto-detect)
    ///     beam_size: Beam size for decoding (default: 1)
    ///     use_agreement: Enable local agreement policy for stable partials (default: False)
    ///     agreement_config: Custom agreement configuration (default: None)
    #[new]
    #[pyo3(signature = (
        sample_rate=16000,
        min_chunk_duration=0.5,
        max_chunk_duration=30.0,
        use_vad=true,
        vad_threshold_db=-40.0,
        language=None,
        beam_size=1,
        use_agreement=false,
        agreement_config=None
    ))]
    fn new(
        sample_rate: u32,
        min_chunk_duration: f64,
        max_chunk_duration: f64,
        use_vad: bool,
        vad_threshold_db: f32,
        language: Option<String>,
        beam_size: usize,
        use_agreement: bool,
        agreement_config: Option<PyAgreementConfig>,
    ) -> Self {
        Self {
            inner: streaming::StreamingConfig {
                sample_rate,
                min_chunk_duration,
                max_chunk_duration,
                use_vad,
                vad_threshold_db,
                vad_min_speech_duration: 0.25,
                vad_min_silence_duration: 0.5,
                language,
                beam_size,
                use_agreement,
                agreement_config: agreement_config
                    .map(|c| c.inner)
                    .unwrap_or_default(),
            },
        }
    }

    /// Create configuration for real-time, low-latency streaming
    #[staticmethod]
    fn realtime() -> Self {
        Self {
            inner: streaming::StreamingConfig::realtime(),
        }
    }

    /// Create configuration for higher quality (more latency)
    #[staticmethod]
    fn quality() -> Self {
        Self {
            inner: streaming::StreamingConfig::quality(),
        }
    }

    /// Create configuration without VAD (time-based chunking)
    #[staticmethod]
    fn no_vad() -> Self {
        Self {
            inner: streaming::StreamingConfig::no_vad(),
        }
    }

    /// Create configuration with stable partial results (agreement policy enabled)
    ///
    /// This preset enables the local agreement policy which prevents the
    /// "flickering" effect where partial transcription results change rapidly.
    /// Only tokens that have been confirmed across multiple transcription runs
    /// are emitted.
    #[staticmethod]
    fn stable() -> Self {
        Self {
            inner: streaming::StreamingConfig::stable(),
        }
    }

    #[getter]
    fn sample_rate(&self) -> u32 {
        self.inner.sample_rate
    }

    #[getter]
    fn min_chunk_duration(&self) -> f64 {
        self.inner.min_chunk_duration
    }

    #[getter]
    fn max_chunk_duration(&self) -> f64 {
        self.inner.max_chunk_duration
    }

    #[getter]
    fn use_vad(&self) -> bool {
        self.inner.use_vad
    }

    #[getter]
    fn vad_threshold_db(&self) -> f32 {
        self.inner.vad_threshold_db
    }

    #[getter]
    fn language(&self) -> Option<String> {
        self.inner.language.clone()
    }

    #[getter]
    fn beam_size(&self) -> usize {
        self.inner.beam_size
    }

    #[getter]
    fn use_agreement(&self) -> bool {
        self.inner.use_agreement
    }

    fn __repr__(&self) -> String {
        format!(
            "StreamingConfig(sample_rate={}, use_vad={}, use_agreement={}, beam_size={})",
            self.inner.sample_rate, self.inner.use_vad, self.inner.use_agreement, self.inner.beam_size
        )
    }
}

/// Event emitted during streaming transcription
#[pyclass]
#[derive(Clone)]
pub struct PyStreamingEvent {
    #[pyo3(get)]
    pub event_type: String,
    #[pyo3(get)]
    pub text: Option<String>,
    #[pyo3(get)]
    pub start_time: Option<f64>,
    #[pyo3(get)]
    pub end_time: Option<f64>,
    #[pyo3(get)]
    pub is_partial: bool,
    #[pyo3(get)]
    pub is_final: bool,
    #[pyo3(get)]
    pub language: Option<String>,
    #[pyo3(get)]
    pub timestamp: Option<f64>,
    #[pyo3(get)]
    pub duration: Option<f64>,
    #[pyo3(get)]
    pub vad_state: Option<String>,
}

impl From<streaming::StreamingEvent> for PyStreamingEvent {
    fn from(event: streaming::StreamingEvent) -> Self {
        match event {
            streaming::StreamingEvent::Partial {
                text,
                start_time,
                end_time,
                is_final,
            } => Self {
                event_type: "partial".to_string(),
                text: Some(text),
                start_time: Some(start_time),
                end_time: Some(end_time),
                is_partial: true,
                is_final,
                language: None,
                timestamp: None,
                duration: None,
                vad_state: None,
            },
            streaming::StreamingEvent::Final {
                text,
                start_time,
                end_time,
                language,
            } => Self {
                event_type: "final".to_string(),
                text: Some(text),
                start_time: Some(start_time),
                end_time: Some(end_time),
                is_partial: false,
                is_final: true,
                language,
                timestamp: None,
                duration: None,
                vad_state: None,
            },
            streaming::StreamingEvent::SegmentStart { timestamp } => Self {
                event_type: "segment_start".to_string(),
                text: None,
                start_time: None,
                end_time: None,
                is_partial: false,
                is_final: false,
                language: None,
                timestamp: Some(timestamp),
                duration: None,
                vad_state: None,
            },
            streaming::StreamingEvent::SegmentEnd { timestamp, duration } => Self {
                event_type: "segment_end".to_string(),
                text: None,
                start_time: None,
                end_time: None,
                is_partial: false,
                is_final: false,
                language: None,
                timestamp: Some(timestamp),
                duration: Some(duration),
                vad_state: None,
            },
            streaming::StreamingEvent::VadStateChange { state, timestamp } => Self {
                event_type: "vad_change".to_string(),
                text: None,
                start_time: None,
                end_time: None,
                is_partial: false,
                is_final: false,
                language: None,
                timestamp: Some(timestamp),
                duration: None,
                vad_state: Some(match state {
                    streaming::VoiceState::Silence => "silence".to_string(),
                    streaming::VoiceState::Speech => "speech".to_string(),
                }),
            },
        }
    }
}

#[pymethods]
impl PyStreamingEvent {
    fn __repr__(&self) -> String {
        match self.event_type.as_str() {
            "partial" | "final" => format!(
                "StreamingEvent(type='{}', text='{}', start={:.2}s, end={:.2}s)",
                self.event_type,
                self.text.as_deref().unwrap_or(""),
                self.start_time.unwrap_or(0.0),
                self.end_time.unwrap_or(0.0)
            ),
            "segment_start" => format!(
                "StreamingEvent(type='segment_start', timestamp={:.2}s)",
                self.timestamp.unwrap_or(0.0)
            ),
            "segment_end" => format!(
                "StreamingEvent(type='segment_end', timestamp={:.2}s, duration={:.2}s)",
                self.timestamp.unwrap_or(0.0),
                self.duration.unwrap_or(0.0)
            ),
            "vad_change" => format!(
                "StreamingEvent(type='vad_change', state='{}', timestamp={:.2}s)",
                self.vad_state.as_deref().unwrap_or("unknown"),
                self.timestamp.unwrap_or(0.0)
            ),
            _ => format!("StreamingEvent(type='{}')", self.event_type),
        }
    }
}

/// Streaming transcriber for chunk-by-chunk transcription
///
/// Wraps a speech model and provides real-time transcription with VAD support.
///
/// Example:
///     ```python
///     import antenna
///
///     model = antenna.load_model("whisper/base", device="cpu")
///     transcriber = antenna.StreamingTranscriber(model)
///
///     # Process audio chunks
///     for chunk in audio_chunks:
///         events = transcriber.process_chunk(chunk)
///         for event in events:
///             if event.is_final:
///                 print(f"[FINAL] {event.text}")
///             elif event.is_partial:
///                 print(f"[partial] {event.text}")
///
///     # Flush remaining audio
///     final_events = transcriber.flush()
///     ```
#[pyclass]
pub struct PyStreamingTranscriber {
    inner: streaming::StreamingTranscriber,
}

#[pymethods]
impl PyStreamingTranscriber {
    /// Create a new streaming transcriber
    ///
    /// Args:
    ///     model: SpeechModel to use for transcription (from load_model())
    ///     config: Optional StreamingConfig (default: StreamingConfig())
    #[new]
    #[pyo3(signature = (_model, _config=None))]
    fn new(_model: &mut PySpeechModel, _config: Option<PyStreamingConfig>) -> PyResult<Self> {
        // We need to take ownership of the model for the transcriber
        // Since PySpeechModel owns DynSpeechModel, we need to handle this carefully
        // For now, we'll create a new model - this is a limitation
        // TODO: Consider using Arc<Mutex<DynSpeechModel>> in the future

        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "StreamingTranscriber currently requires creating a new model. \
            Use StreamingTranscriber.from_model_id() instead."
        ))
    }

    /// Create a streaming transcriber from a model ID
    ///
    /// Args:
    ///     model_id: Model identifier (e.g., "whisper/base")
    ///     device: Device string ("cpu", "cuda", "cuda:0")
    ///     config: Optional StreamingConfig
    ///
    /// Returns:
    ///     StreamingTranscriber ready for use
    #[staticmethod]
    #[pyo3(signature = (model_id, device=None, config=None))]
    fn from_model_id(
        model_id: String,
        device: Option<String>,
        config: Option<PyStreamingConfig>,
    ) -> PyResult<Self> {
        let device_str = device.as_deref().unwrap_or("cpu");
        let model = ml::load_model(&model_id, device_str, None)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let streaming_config = config
            .map(|c| c.inner)
            .unwrap_or_else(streaming::StreamingConfig::default);

        let inner = streaming::StreamingTranscriber::new(model, streaming_config)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(Self { inner })
    }

    /// Process a chunk of audio samples
    ///
    /// Args:
    ///     samples: Audio samples as numpy array or list (mono, float32, at config sample rate)
    ///
    /// Returns:
    ///     List of StreamingEvent objects
    fn process_chunk(&mut self, samples: Vec<f32>) -> PyResult<Vec<PyStreamingEvent>> {
        let events = self
            .inner
            .process_chunk(&samples)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(events.into_iter().map(PyStreamingEvent::from).collect())
    }

    /// Process audio data from an AudioData object
    ///
    /// Handles resampling if needed.
    ///
    /// Args:
    ///     audio: AudioData object
    ///
    /// Returns:
    ///     List of StreamingEvent objects
    fn process_audio(&mut self, audio: &PyAudioData) -> PyResult<Vec<PyStreamingEvent>> {
        // Resample if needed
        let samples = if audio.inner.sample_rate != self.inner.config().sample_rate {
            let target_rate = self.inner.config().sample_rate;
            let resampled = crate::audio::process::resample(&audio.inner, target_rate)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            resampled.samples
        } else {
            audio.inner.samples.clone()
        };

        self.process_chunk(samples)
    }

    /// Flush remaining audio and get final results
    ///
    /// Call this when the audio stream ends.
    ///
    /// Returns:
    ///     List of StreamingEvent objects (typically Final events)
    fn flush(&mut self) -> PyResult<Vec<PyStreamingEvent>> {
        let events = self
            .inner
            .flush()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(events.into_iter().map(PyStreamingEvent::from).collect())
    }

    /// Reset the transcriber for a new session
    fn reset(&mut self) {
        self.inner.reset();
    }

    /// Get current buffer duration in seconds
    #[getter]
    fn buffer_duration(&self) -> f64 {
        self.inner.buffer_duration()
    }

    /// Get current stream time in seconds
    #[getter]
    fn current_time(&self) -> f64 {
        self.inner.current_time()
    }

    /// Check if VAD is currently detecting speech
    #[getter]
    fn is_speaking(&self) -> bool {
        self.inner.is_speaking()
    }

    /// Get the current VAD state ("silence" or "speech")
    #[getter]
    fn vad_state(&self) -> String {
        match self.inner.vad_state() {
            streaming::VoiceState::Silence => "silence".to_string(),
            streaming::VoiceState::Speech => "speech".to_string(),
        }
    }

    /// Check if agreement policy is enabled
    #[getter]
    fn has_agreement(&self) -> bool {
        self.inner.has_agreement()
    }

    /// Get the number of confirmed tokens (agreement policy)
    ///
    /// Returns 0 if agreement policy is not enabled.
    #[getter]
    fn agreement_confirmed_count(&self) -> usize {
        self.inner.agreement_confirmed_count()
    }

    fn __repr__(&self) -> String {
        format!(
            "StreamingTranscriber(buffer={:.2}s, time={:.2}s, speaking={})",
            self.inner.buffer_duration(),
            self.inner.current_time(),
            self.inner.is_speaking()
        )
    }
}

// ============================================================================
// Async Streaming Transcription API
// ============================================================================

/// Async streaming transcriber for Python asyncio integration
///
/// This class provides true async methods that work with Python's asyncio,
/// allowing non-blocking transcription in async applications.
///
/// # Example
///
/// ```python
/// import asyncio
/// import antenna
///
/// async def transcribe_stream(audio_chunks):
///     transcriber = antenna.AsyncStreamingTranscriber.from_model_id(
///         "whisper/tiny",
///         device="cuda"
///     )
///
///     for chunk in audio_chunks:
///         events = await transcriber.process_chunk_async(chunk)
///         for event in events:
///             if event.is_final():
///                 print(event.text())
///
///     final_events = await transcriber.flush_async()
/// ```
#[pyclass]
pub struct PyAsyncStreamingTranscriber {
    inner: Arc<ParkingMutex<streaming::StreamingTranscriber>>,
}

#[pymethods]
impl PyAsyncStreamingTranscriber {
    /// Create an async streaming transcriber from a model ID
    ///
    /// Args:
    ///     model_id: Model identifier (e.g., "whisper/base", "distil-whisper/distil-small.en")
    ///     device: Device string ("cpu", "cuda", "cuda:0", "metal")
    ///     config: Optional StreamingConfig
    ///
    /// Returns:
    ///     AsyncStreamingTranscriber ready for use
    #[staticmethod]
    #[pyo3(signature = (model_id, device=None, config=None))]
    fn from_model_id(
        model_id: String,
        device: Option<String>,
        config: Option<PyStreamingConfig>,
    ) -> PyResult<Self> {
        let device_str = device.as_deref().unwrap_or("cpu");
        let model = ml::load_model(&model_id, device_str, None)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let streaming_config = config
            .map(|c| c.inner)
            .unwrap_or_else(streaming::StreamingConfig::default);

        let transcriber = streaming::StreamingTranscriber::new(model, streaming_config)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(Self {
            inner: Arc::new(ParkingMutex::new(transcriber)),
        })
    }

    /// Process a chunk of audio samples asynchronously
    ///
    /// Args:
    ///     samples: Audio samples as list of floats (mono, float32, at config sample rate)
    ///
    /// Returns:
    ///     Awaitable that resolves to list of StreamingEvent objects
    fn process_chunk_async<'py>(
        &self,
        py: Python<'py>,
        samples: Vec<f32>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let inner = Arc::clone(&self.inner);

        future_into_py(py, async move {
            // Run the blocking transcription in a blocking task
            let events = tokio::task::spawn_blocking(move || {
                let mut guard = inner.lock();
                guard.process_chunk(&samples)
            })
            .await
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Task join error: {}", e)))?
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            let py_events: Vec<PyStreamingEvent> = events.into_iter().map(PyStreamingEvent::from).collect();
            Ok(py_events)
        })
    }

    /// Process audio data from an AudioData object asynchronously
    ///
    /// Handles resampling if needed.
    ///
    /// Args:
    ///     audio: AudioData object
    ///
    /// Returns:
    ///     Awaitable that resolves to list of StreamingEvent objects
    fn process_audio_async<'py>(
        &self,
        py: Python<'py>,
        audio: &PyAudioData,
    ) -> PyResult<Bound<'py, PyAny>> {
        let inner = Arc::clone(&self.inner);
        let audio_samples = audio.inner.samples.clone();
        let audio_sample_rate = audio.inner.sample_rate;

        future_into_py(py, async move {
            let events = tokio::task::spawn_blocking(move || {
                let mut guard = inner.lock();
                let config_rate = guard.config().sample_rate;

                let samples = if audio_sample_rate != config_rate {
                    // Create a temporary AudioData for resampling
                    let temp_audio = AudioData {
                        samples: audio_samples,
                        sample_rate: audio_sample_rate,
                        channels: 1,
                    };
                    let resampled = crate::audio::process::resample(&temp_audio, config_rate)?;
                    resampled.samples
                } else {
                    audio_samples
                };

                guard.process_chunk(&samples)
            })
            .await
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Task join error: {}", e)))?
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            let py_events: Vec<PyStreamingEvent> = events.into_iter().map(PyStreamingEvent::from).collect();
            Ok(py_events)
        })
    }

    /// Flush remaining audio and get final results asynchronously
    ///
    /// Call this when the audio stream ends.
    ///
    /// Returns:
    ///     Awaitable that resolves to list of StreamingEvent objects (typically Final events)
    fn flush_async<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let inner = Arc::clone(&self.inner);

        future_into_py(py, async move {
            let events = tokio::task::spawn_blocking(move || {
                let mut guard = inner.lock();
                guard.flush()
            })
            .await
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Task join error: {}", e)))?
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            let py_events: Vec<PyStreamingEvent> = events.into_iter().map(PyStreamingEvent::from).collect();
            Ok(py_events)
        })
    }

    /// Reset the transcriber for a new session
    fn reset(&self) {
        let mut guard = self.inner.lock();
        guard.reset();
    }

    /// Get current buffer duration in seconds
    #[getter]
    fn buffer_duration(&self) -> f64 {
        self.inner.lock().buffer_duration()
    }

    /// Get current stream time in seconds
    #[getter]
    fn current_time(&self) -> f64 {
        self.inner.lock().current_time()
    }

    /// Check if VAD is currently detecting speech
    #[getter]
    fn is_speaking(&self) -> bool {
        self.inner.lock().is_speaking()
    }

    /// Get the current VAD state ("silence" or "speech")
    #[getter]
    fn vad_state(&self) -> String {
        match self.inner.lock().vad_state() {
            streaming::VoiceState::Silence => "silence".to_string(),
            streaming::VoiceState::Speech => "speech".to_string(),
        }
    }

    fn __repr__(&self) -> String {
        let guard = self.inner.lock();
        format!(
            "AsyncStreamingTranscriber(buffer={:.2}s, time={:.2}s, speaking={})",
            guard.buffer_duration(),
            guard.current_time(),
            guard.is_speaking()
        )
    }
}

#[pymodule]
fn _antenna(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Audio processing functions
    m.add_function(wrap_pyfunction!(load_audio, m)?)?;
    m.add_function(wrap_pyfunction!(preprocess_audio, m)?)?;
    m.add_function(wrap_pyfunction!(analyze_audio, m)?)?;
    m.add_function(wrap_pyfunction!(trim_silence, m)?)?;
    m.add_function(wrap_pyfunction!(detect_silence, m)?)?;
    m.add_function(wrap_pyfunction!(split_on_silence, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_audio, m)?)?;
    m.add_function(wrap_pyfunction!(save_audio, m)?)?;

    // Whisper functions
    m.add_function(wrap_pyfunction!(preprocess_for_whisper, m)?)?;
    m.add_function(wrap_pyfunction!(is_model_cached, m)?)?;
    m.add_function(wrap_pyfunction!(list_whisper_models, m)?)?;

    // Distil-Whisper functions
    m.add_function(wrap_pyfunction!(list_distil_whisper_models, m)?)?;

    // Device utility functions
    m.add_function(wrap_pyfunction!(is_cuda_available, m)?)?;
    m.add_function(wrap_pyfunction!(cuda_device_count, m)?)?;
    m.add_function(wrap_pyfunction!(is_metal_available, m)?)?;
    m.add_function(wrap_pyfunction!(metal_device_count, m)?)?;
    m.add_function(wrap_pyfunction!(is_gpu_available, m)?)?;
    m.add_function(wrap_pyfunction!(is_onnx_cuda_available, m)?)?;
    m.add_function(wrap_pyfunction!(is_onnx_tensorrt_available, m)?)?;

    // Audio classes
    m.add_class::<PyAudioData>()?;
    m.add_class::<PyAudioStats>()?;

    // Model info classes (shared across all model types)
    m.add_class::<PyModelInfo>()?;
    m.add_class::<PyModelCapabilities>()?;

    // Whisper classes
    m.add_class::<PyWhisperModel>()?;
    m.add_class::<PyTranscriptionResult>()?;
    m.add_class::<PyTranscriptionSegment>()?;

    // Distil-Whisper classes
    m.add_class::<PyDistilWhisperModel>()?;

    // Wav2Vec2 classes and functions (ONNX feature)
    m.add_function(wrap_pyfunction!(is_onnx_available, m)?)?;
    #[cfg(feature = "onnx")]
    {
        m.add_class::<PyWav2Vec2Model>()?;
        m.add_function(wrap_pyfunction!(list_wav2vec2_models, m)?)?;
    }

    // Unified model registry API
    m.add_class::<PySpeechModel>()?;
    m.add_class::<PyModelEntry>()?;
    m.add_function(wrap_pyfunction!(py_load_model, m)?)?;
    m.add_function(wrap_pyfunction!(py_list_models, m)?)?;
    m.add_function(wrap_pyfunction!(py_is_model_available, m)?)?;

    // Streaming transcription API
    m.add_class::<PyAgreementConfig>()?;
    m.add_class::<PyAudioRingBuffer>()?;
    m.add_class::<PyStreamingConfig>()?;
    m.add_class::<PyStreamingEvent>()?;
    m.add_class::<PyStreamingTranscriber>()?;

    // Async streaming transcription API
    m.add_class::<PyAsyncStreamingTranscriber>()?;

    Ok(())
}

