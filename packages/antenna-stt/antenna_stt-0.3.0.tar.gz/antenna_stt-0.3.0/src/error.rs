use pyo3::exceptions::PyException;
use pyo3::PyErr;

#[derive(Debug, thiserror::Error)]
pub enum AntennaError {
    #[error("Failed to read audio file: {0}")]
    IoError(String),

    #[error("Unsupported audio format: {0}")]
    UnsupportedFormat(String),

    #[error("Invalid audio data: {0}")]
    InvalidAudio(String),

    #[error("Preprocessing error: {0}")]
    PreprocessingError(String),

    #[error("Model error: {0}")]
    ModelError(String),

    #[error("Transcription error: {0}")]
    TranscriptionError(String),
}

impl From<AntennaError> for PyErr {
    fn from(err: AntennaError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

impl From<std::io::Error> for AntennaError {
    fn from(err: std::io::Error) -> Self {
        AntennaError::IoError(err.to_string())
    }
}

impl From<hound::Error> for AntennaError {
    fn from(err: hound::Error) -> Self {
        AntennaError::IoError(err.to_string())
    }
}

impl From<candle_core::Error> for AntennaError {
    fn from(err: candle_core::Error) -> Self {
        AntennaError::ModelError(err.to_string())
    }
}

