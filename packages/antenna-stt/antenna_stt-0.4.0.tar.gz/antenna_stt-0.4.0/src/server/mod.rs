//! Real-time Speech-to-Text Server
//!
//! This module provides a real-time transcription server with HTTP/WebSocket API.
//!
//! # Architecture
//!
//! ```text
//! Client ──HTTP POST──> /sessions/:id/audio ──> SessionManager ──> StreamingEngine
//!    │                                                                    │
//!    │◄────WebSocket◄──── /sessions/:id/ws ◄── Event Broadcast ◄──────────┘
//!                                                    │                    │
//!                                              Partial/Final          SttBackend
//!                                              Transcripts            (Whisper/Triton)
//! ```
//!
//! # Components
//!
//! - **HTTP** (`http`): Axum-based REST API and WebSocket endpoints
//! - **STT Backends** (`stt`): Pluggable speech-to-text engines
//! - **Streaming** (`streaming`): Audio buffering and chunk processing
//!
//! # Example
//!
//! ```ignore
//! use antenna::server::{
//!     http::{create_router, AppState, ServerConfig},
//!     stt::WhisperBackend,
//! };
//! use std::sync::Arc;
//!
//! #[tokio::main]
//! async fn main() -> anyhow::Result<()> {
//!     // Create STT backend
//!     let backend = WhisperBackend::with_model("base", "cpu")?;
//!     let state = Arc::new(AppState::new(Arc::new(backend)));
//!
//!     // Create HTTP router
//!     let app = create_router(state);
//!
//!     // Start server
//!     let config = ServerConfig::default();
//!     let listener = tokio::net::TcpListener::bind(&config.bind_addr()).await?;
//!     println!("Server running on http://{}", config.bind_addr());
//!     axum::serve(listener, app).await?;
//!     Ok(())
//! }
//! ```

pub mod http;
pub mod stt;
pub mod streaming;
pub mod workers;

#[cfg(feature = "webrtc")]
pub mod webrtc;

// Re-export commonly used types
pub use stt::{
    SttBackend, SttError, SttResult,
    WhisperBackend, WhisperBackendConfig,
    BackendSelector, BackendType,
};
#[cfg(feature = "triton")]
pub use stt::{TritonBackend, TritonBackendConfig, TritonClient, TritonConfig};

pub use streaming::{
    AudioChunk, AudioRingBuffer, PartialTranscript, StreamingConfig,
    StreamingEngine, StreamingEvent, EngineConfig,
    StreamingVad, VadConfig, VoiceState,
    LocalAgreementPolicy, AgreementConfig,
};

pub use http::{
    create_router, AppState, ServerConfig,
    SessionManager, SessionManagerConfig, SessionConfig, SessionInfo, SessionState, SessionError,
    ApiResponse, HealthResponse, ServerInfoResponse,
};

pub use workers::{
    BackendPool, BackendPoolConfig, PooledBackend, PoolError,
    Metrics, MetricsSnapshot, LatencyHistogram,
};

#[cfg(feature = "webrtc")]
pub use webrtc::{
    PeerConnection, PeerConnectionConfig, PeerError, PeerManager, PeerState,
    AudioHandler, AudioHandlerConfig, AudioSample,
    IceCandidate, SessionDescription, SignalingMessage,
};

#[cfg(feature = "webrtc")]
pub use http::{
    create_webrtc_router, WebRtcAppState, WebRtcState,
};
