//! HTTP Server Layer
//!
//! Provides an Axum-based HTTP server for the real-time STT API.
//!
//! # Architecture
//!
//! ```text
//! Client ──HTTP POST──> /sessions/:id/audio ──> SessionManager ──> Audio Channel
//!    │                                                                  │
//!    │◄────WebSocket◄──── /sessions/:id/ws ◄── Event Broadcast ◄────────┘
//!                                                    │
//!                                            StreamingEngine
//! ```
//!
//! # Example
//!
//! ```ignore
//! use antenna::server::http::{create_router, AppState, ServerConfig};
//! use antenna::server::stt::WhisperBackend;
//!
//! #[tokio::main]
//! async fn main() {
//!     // Create backend
//!     let backend = WhisperBackend::with_model("base", "cpu").unwrap();
//!     let state = Arc::new(AppState::new(Arc::new(backend)));
//!
//!     // Create router
//!     let app = create_router(state);
//!
//!     // Start server
//!     let config = ServerConfig::default();
//!     let listener = tokio::net::TcpListener::bind(&config.bind_addr()).await.unwrap();
//!     axum::serve(listener, app).await.unwrap();
//! }
//! ```

pub mod handlers;
pub mod routes;
pub mod session;

#[cfg(feature = "webrtc")]
pub mod webrtc_handlers;

pub use handlers::{
    ApiResponse, BackendInfoResponse, CreateSessionRequest, CreateSessionResponse,
    HealthResponse, ServerInfoResponse, SessionsInfoResponse,
    LivenessResponse, ReadinessResponse, DetailedHealthResponse,
    BackendHealthInfo, BackendCapabilitiesInfo, SessionHealthInfo,
};
pub use routes::{create_router, AppState, ServerConfig};
pub use session::{
    Session, SessionConfig, SessionError, SessionInfo, SessionManager, SessionManagerConfig,
    SessionState,
};

#[cfg(feature = "webrtc")]
pub use routes::create_webrtc_router;

#[cfg(feature = "webrtc")]
pub use webrtc_handlers::{
    WebRtcAppState, WebRtcState, CreateWebRtcSessionRequest, WebRtcSessionResponse,
    create_webrtc_session, add_ice_candidate,
};
