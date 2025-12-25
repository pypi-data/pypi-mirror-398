use numpy::{PyArray1, ToPyArray};
use pyo3::prelude::*;

#[derive(Clone, Debug)]
pub struct AudioData {
    pub samples: Vec<f32>,
    pub sample_rate: u32,
    pub channels: u8,
}

impl AudioData {
    pub fn new(samples: Vec<f32>, sample_rate: u32, channels: u8) -> Self {
        Self {
            samples,
            sample_rate,
            channels,
        }
    }

    pub fn duration(&self) -> f32 {
        self.samples.len() as f32 / (self.sample_rate as f32 * self.channels as f32)
    }

    pub fn frame_count(&self) -> usize {
        self.samples.len() / self.channels as usize
    }
}

#[pyclass]
pub struct PyAudioData {
    pub inner: AudioData,
}

#[pymethods]
impl PyAudioData {
    #[getter]
    fn sample_rate(&self) -> u32 {
        self.inner.sample_rate
    }

    #[getter]
    fn channels(&self) -> u8 {
        self.inner.channels
    }

    #[getter]
    fn duration(&self) -> f32 {
        self.inner.duration()
    }

    fn to_numpy<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f32>> {
        self.inner.samples.to_pyarray(py)
    }

    fn __repr__(&self) -> String {
        format!(
            "AudioData(sample_rate={}, channels={}, duration={:.2}s)",
            self.inner.sample_rate,
            self.inner.channels,
            self.inner.duration()
        )
    }
}

impl From<AudioData> for PyAudioData {
    fn from(inner: AudioData) -> Self {
        PyAudioData { inner }
    }
}

// ============================================================================
// Transcription Result Types
// ============================================================================

/// A single transcription segment with timing information
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyTranscriptionSegment {
    #[pyo3(get)]
    pub start: f32,
    #[pyo3(get)]
    pub end: f32,
    #[pyo3(get)]
    pub text: String,
}

#[pymethods]
impl PyTranscriptionSegment {
    fn __repr__(&self) -> String {
        format!(
            "TranscriptionSegment(start={:.2}, end={:.2}, text={:?})",
            self.start, self.end, self.text
        )
    }
}

/// Complete transcription result with text, segments, and metadata
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyTranscriptionResult {
    #[pyo3(get)]
    pub text: String,
    #[pyo3(get)]
    pub language: Option<String>,
    #[pyo3(get)]
    pub language_probability: Option<f32>,
    segments_inner: Vec<PyTranscriptionSegment>,
}

#[pymethods]
impl PyTranscriptionResult {
    #[getter]
    fn segments(&self) -> Vec<PyTranscriptionSegment> {
        self.segments_inner.clone()
    }

    fn __repr__(&self) -> String {
        format!(
            "TranscriptionResult(language={:?}, segments={}, text={:?}...)",
            self.language,
            self.segments_inner.len(),
            if self.text.len() > 50 {
                format!("{}...", &self.text[..50])
            } else {
                self.text.clone()
            }
        )
    }

    /// Get the number of segments
    fn __len__(&self) -> usize {
        self.segments_inner.len()
    }
}

impl PyTranscriptionResult {
    /// Create a new transcription result from model output
    pub fn new(
        text: String,
        language: Option<String>,
        language_probability: Option<f32>,
        segments: Vec<PyTranscriptionSegment>,
    ) -> Self {
        Self {
            text,
            language,
            language_probability,
            segments_inner: segments,
        }
    }
}

