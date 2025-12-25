//! CTranslate2 backend for optimized Whisper inference
//!
//! This module provides integration with CTranslate2 via the ct2rs crate,
//! offering up to 4x faster Whisper inference with INT8 quantization support.
//!
//! **Status**: Planned - not yet implemented
//!
//! # Features
//!
//! - 4x faster than native Candle implementation
//! - INT8 and FP16 quantization support
//! - Batch processing
//! - Compatible with faster-whisper models
//!
//! # Example (planned API)
//!
//! ```ignore
//! use antenna::ml::backends::ctranslate2::CTranslate2Backend;
//!
//! let backend = CTranslate2Backend::new("path/to/model", device)?;
//! let result = backend.transcribe(audio)?;
//! ```

// Stub implementation - to be completed when ct2rs integration is added
