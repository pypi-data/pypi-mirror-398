//! HTTP Routes
//!
//! Axum router configuration for the STT server.

use axum::{
    routing::{get, post, delete},
    Router,
};
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

use super::handlers;
use super::session::SessionManager;
use crate::server::stt::SttBackend;

/// Application state shared across handlers
pub struct AppState<B: SttBackend + 'static> {
    pub session_manager: SessionManager,
    pub backend: Arc<B>,
}

impl<B: SttBackend + 'static> AppState<B> {
    pub fn new(backend: Arc<B>) -> Self {
        Self {
            session_manager: SessionManager::default(),
            backend,
        }
    }

    pub fn with_session_manager(backend: Arc<B>, session_manager: SessionManager) -> Self {
        Self {
            session_manager,
            backend,
        }
    }
}

/// Create the main application router
///
/// # Routes
///
/// ## Health & Info
/// - `GET /health` - Basic health check endpoint
/// - `GET /health/live` - Kubernetes liveness probe
/// - `GET /health/ready` - Kubernetes readiness probe
/// - `GET /health/detailed` - Detailed health with backend/session info
/// - `GET /info` - Server and backend information
///
/// ## Sessions
/// - `POST /sessions` - Create a new transcription session
/// - `GET /sessions` - List all active sessions
/// - `GET /sessions/:id` - Get session details
/// - `DELETE /sessions/:id` - Close a session
///
/// ## Audio & Transcription
/// - `POST /sessions/:id/audio` - Send audio chunk (binary)
/// - `GET /sessions/:id/ws` - WebSocket for real-time transcripts
///
pub fn create_router<B: SttBackend + 'static>(state: Arc<AppState<B>>) -> Router {
    // CORS configuration for browser clients
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        // Health & Info
        .route("/health", get(handlers::health_check))
        .route("/health/live", get(handlers::liveness_probe))
        .route("/health/ready", get(handlers::readiness_probe::<B>))
        .route("/health/detailed", get(handlers::detailed_health::<B>))
        .route("/info", get(handlers::server_info::<B>))
        // Session management
        .route("/sessions", post(handlers::create_session::<B>))
        .route("/sessions", get(handlers::list_sessions::<B>))
        .route("/sessions/{id}", get(handlers::get_session::<B>))
        .route("/sessions/{id}", delete(handlers::close_session::<B>))
        // Audio & WebSocket
        .route("/sessions/{id}/audio", post(handlers::send_audio::<B>))
        .route("/sessions/{id}/ws", get(handlers::websocket_handler::<B>))
        // Middleware
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

/// Configuration for the HTTP server
#[derive(Debug, Clone)]
pub struct ServerConfig {
    /// Host to bind to
    pub host: String,
    /// Port to bind to
    pub port: u16,
    /// Enable detailed request logging
    pub trace_requests: bool,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: "0.0.0.0".to_string(),
            port: 8080,
            trace_requests: true,
        }
    }
}

impl ServerConfig {
    /// Create configuration for local development
    pub fn local() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 8080,
            trace_requests: true,
        }
    }

    /// Get the bind address
    pub fn bind_addr(&self) -> String {
        format!("{}:{}", self.host, self.port)
    }
}

/// Create router with WebRTC support
///
/// # Additional WebRTC Routes
///
/// - `POST /webrtc/sessions` - Create WebRTC session with SDP offer
/// - `POST /webrtc/sessions/:id/ice` - Add ICE candidate
///
#[cfg(feature = "webrtc")]
pub fn create_webrtc_router<B: SttBackend + 'static>(
    state: Arc<super::webrtc_handlers::WebRtcAppState<B>>,
) -> Router {
    use super::webrtc_handlers;

    // CORS configuration for browser clients
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        // Health & Info
        .route("/health", get(handlers::health_check))
        .route("/health/live", get(handlers::liveness_probe))
        .route(
            "/health/ready",
            get(webrtc_handlers::readiness_probe::<B>),
        )
        .route(
            "/health/detailed",
            get(webrtc_handlers::detailed_health::<B>),
        )
        // WebRTC signaling
        .route(
            "/webrtc/sessions",
            post(webrtc_handlers::create_webrtc_session::<B>),
        )
        .route(
            "/webrtc/sessions/{id}/ice",
            post(webrtc_handlers::add_ice_candidate::<B>),
        )
        // Middleware
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_server_config_defaults() {
        let config = ServerConfig::default();
        assert_eq!(config.host, "0.0.0.0");
        assert_eq!(config.port, 8080);
    }

    #[test]
    fn test_bind_addr() {
        let config = ServerConfig::default();
        assert_eq!(config.bind_addr(), "0.0.0.0:8080");
    }

    #[test]
    fn test_local_config() {
        let config = ServerConfig::local();
        assert_eq!(config.host, "127.0.0.1");
    }
}
