//! HTTP Request Handlers
//!
//! Axum handlers for session management, audio upload, and WebSocket connections.

use axum::{
    body::Bytes,
    extract::{Path, State, WebSocketUpgrade},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use axum::extract::ws::{Message, WebSocket};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use super::routes::AppState;
use super::session::{SessionConfig, SessionError, SessionInfo, SessionState};
use crate::server::stt::SttBackend;
use crate::server::streaming::StreamingEvent;

/// API response wrapper
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

impl<T: Serialize> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(message: impl Into<String>) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(message.into()),
        }
    }
}

/// Convert SessionError to HTTP response
impl IntoResponse for SessionError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            SessionError::NotFound(_) => (StatusCode::NOT_FOUND, self.to_string()),
            SessionError::AlreadyExists(_) => (StatusCode::CONFLICT, self.to_string()),
            SessionError::InvalidState { .. } => (StatusCode::BAD_REQUEST, self.to_string()),
            SessionError::MaxSessionsReached(_) => (StatusCode::SERVICE_UNAVAILABLE, self.to_string()),
            SessionError::ChannelClosed => (StatusCode::GONE, self.to_string()),
            SessionError::Internal(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };

        (status, Json(ApiResponse::<()>::error(message))).into_response()
    }
}

/// Health check response
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
}

/// GET /health - Health check (basic)
pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

/// Liveness probe response
#[derive(Debug, Serialize)]
pub struct LivenessResponse {
    pub alive: bool,
    pub uptime_seconds: u64,
}

/// GET /health/live - Kubernetes liveness probe
///
/// Returns 200 if the process is running and can respond to requests.
/// This should always return true unless the process is completely stuck.
pub async fn liveness_probe() -> Json<LivenessResponse> {
    static START_TIME: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    let start = START_TIME.get_or_init(std::time::Instant::now);

    Json(LivenessResponse {
        alive: true,
        uptime_seconds: start.elapsed().as_secs(),
    })
}

/// Readiness probe response
#[derive(Debug, Serialize)]
pub struct ReadinessResponse {
    pub ready: bool,
    pub backend_ready: bool,
    pub accepting_connections: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

/// GET /health/ready - Kubernetes readiness probe
///
/// Returns 200 if the server is ready to accept traffic.
/// This checks if the backend is loaded and ready for inference.
pub async fn readiness_probe<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
) -> (StatusCode, Json<ReadinessResponse>) {
    let backend_ready = state.backend.is_ready();
    let accepting = true; // Could check session limits here

    let ready = backend_ready && accepting;

    let status = if ready {
        StatusCode::OK
    } else {
        StatusCode::SERVICE_UNAVAILABLE
    };

    let message = if !backend_ready {
        Some("Backend not ready".to_string())
    } else {
        None
    };

    (
        status,
        Json(ReadinessResponse {
            ready,
            backend_ready,
            accepting_connections: accepting,
            message,
        }),
    )
}

/// Detailed health check response
#[derive(Debug, Serialize)]
pub struct DetailedHealthResponse {
    pub status: String,
    pub version: String,
    pub uptime_seconds: u64,
    pub backend: BackendHealthInfo,
    pub sessions: SessionHealthInfo,
}

#[derive(Debug, Serialize)]
pub struct BackendHealthInfo {
    pub name: String,
    pub model: String,
    pub device: String,
    pub ready: bool,
    pub capabilities: BackendCapabilitiesInfo,
}

#[derive(Debug, Serialize)]
pub struct BackendCapabilitiesInfo {
    pub streaming: bool,
    pub language_detection: bool,
    pub translation: bool,
}

#[derive(Debug, Serialize)]
pub struct SessionHealthInfo {
    pub active: usize,
    pub max: usize,
    pub utilization_percent: f64,
}

/// GET /health/detailed - Detailed health information
pub async fn detailed_health<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
) -> Json<DetailedHealthResponse> {
    static START_TIME: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    let start = START_TIME.get_or_init(std::time::Instant::now);

    let backend_info = state.backend.info();
    let active_sessions = state.session_manager.session_count();
    let max_sessions = 100; // TODO: Get from config

    let status = if state.backend.is_ready() {
        "healthy"
    } else {
        "degraded"
    };

    Json(DetailedHealthResponse {
        status: status.to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        uptime_seconds: start.elapsed().as_secs(),
        backend: BackendHealthInfo {
            name: backend_info.name.clone(),
            model: backend_info.model.clone(),
            device: backend_info.device.clone(),
            ready: state.backend.is_ready(),
            capabilities: BackendCapabilitiesInfo {
                streaming: backend_info.capabilities.streaming,
                language_detection: backend_info.capabilities.language_detection,
                translation: backend_info.capabilities.translation,
            },
        },
        sessions: SessionHealthInfo {
            active: active_sessions,
            max: max_sessions,
            utilization_percent: (active_sessions as f64 / max_sessions as f64) * 100.0,
        },
    })
}

/// Server info response
#[derive(Debug, Serialize)]
pub struct ServerInfoResponse {
    pub name: String,
    pub version: String,
    pub backend: BackendInfoResponse,
    pub sessions: SessionsInfoResponse,
}

#[derive(Debug, Serialize)]
pub struct BackendInfoResponse {
    pub name: String,
    pub model: String,
    pub device: String,
    pub ready: bool,
}

#[derive(Debug, Serialize)]
pub struct SessionsInfoResponse {
    pub active: usize,
    pub max: usize,
}

/// GET /info - Server information
pub async fn server_info<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
) -> Json<ServerInfoResponse> {
    let backend_info = state.backend.info();

    Json(ServerInfoResponse {
        name: "antenna-server".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        backend: BackendInfoResponse {
            name: backend_info.name.clone(),
            model: backend_info.model.clone(),
            device: backend_info.device.clone(),
            ready: state.backend.is_ready(),
        },
        sessions: SessionsInfoResponse {
            active: state.session_manager.session_count(),
            max: 100, // TODO: Get from config
        },
    })
}

/// Create session request
#[derive(Debug, Deserialize)]
pub struct CreateSessionRequest {
    #[serde(flatten)]
    pub config: SessionConfig,
}

/// Create session response
#[derive(Debug, Serialize)]
pub struct CreateSessionResponse {
    pub session_id: Uuid,
    pub websocket_url: String,
    pub audio_url: String,
}

/// POST /sessions - Create a new session
pub async fn create_session<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
    Json(request): Json<CreateSessionRequest>,
) -> Result<(StatusCode, Json<ApiResponse<CreateSessionResponse>>), SessionError> {
    let session_config = request.config.clone();
    let (session_id, audio_rx, _event_rx) = state
        .session_manager
        .create_session(request.config)?;

    // Spawn audio processing worker
    let worker_state = state.clone();
    tokio::spawn(async move {
        process_session_audio(session_id, audio_rx, session_config, worker_state).await;
    });

    let response = CreateSessionResponse {
        session_id,
        websocket_url: format!("/sessions/{}/ws", session_id),
        audio_url: format!("/sessions/{}/audio", session_id),
    };

    tracing::info!(session_id = %session_id, "Session created via API");

    Ok((StatusCode::CREATED, Json(ApiResponse::success(response))))
}

/// Audio processing worker for a session
async fn process_session_audio<B: SttBackend + 'static>(
    session_id: Uuid,
    mut audio_rx: tokio::sync::mpsc::Receiver<Vec<f32>>,
    config: SessionConfig,
    state: Arc<AppState<B>>,
) {
    use crate::server::streaming::{EngineConfig, StreamingConfig, StreamingEngine, StreamingEvent};
    use tokio::time::{timeout, Duration};

    tracing::info!(session_id = %session_id, "Audio processing worker started");

    // Create streaming engine for this session
    let streaming_config = StreamingConfig {
        language: if config.language == "auto" {
            None
        } else {
            Some(config.language.clone())
        },
        ..Default::default()
    };

    let engine_config = EngineConfig {
        streaming: streaming_config,
        ..Default::default()
    };

    let engine = StreamingEngine::new(state.backend.clone(), engine_config);

    // Track timing for transcription
    let mut total_samples: u64 = 0;
    let sample_rate = config.sample_rate as f64;

    // Inactivity timeout for triggering flush (2 seconds without new audio)
    const INACTIVITY_TIMEOUT: Duration = Duration::from_secs(2);

    // Process audio chunks with inactivity timeout for flushing
    loop {
        match timeout(INACTIVITY_TIMEOUT, audio_rx.recv()).await {
            // Received audio chunk within timeout
            Ok(Some(samples)) => {
                let chunk_samples = samples.len() as u64;
                total_samples += chunk_samples;

                // Calculate timestamp
                let timestamp = total_samples as f64 / sample_rate;

                tracing::debug!(
                    session_id = %session_id,
                    chunk_samples = chunk_samples,
                    total_samples = total_samples,
                    timestamp_s = format!("{:.2}", timestamp),
                    buffer_duration_s = format!("{:.2}", engine.buffer_duration()),
                    "Received audio chunk"
                );

                // Process through streaming engine
                match engine.process_audio(&samples, timestamp).await {
                    Ok(events) => {
                        if !events.is_empty() {
                            tracing::info!(
                                session_id = %session_id,
                                event_count = events.len(),
                                "Processing produced events"
                            );
                        }
                        for event in events {
                            // Broadcast event to WebSocket clients
                            if let Err(e) = state.session_manager.broadcast_event(session_id, event) {
                                tracing::debug!(session_id = %session_id, "Failed to broadcast event: {}", e);
                            }
                        }
                    }
                    Err(e) => {
                        tracing::warn!(session_id = %session_id, "Processing error: {}", e);
                        let _ = state.session_manager.broadcast_event(
                            session_id,
                            StreamingEvent::Error(e.to_string()),
                        );
                    }
                }
            }

            // Timeout - no audio received, flush if there's buffered audio
            Err(_) => {
                let buffer_duration = engine.buffer_duration();
                if buffer_duration > 0.1 {
                    tracing::info!(
                        session_id = %session_id,
                        buffer_duration_s = format!("{:.2}", buffer_duration),
                        "Inactivity timeout, flushing buffered audio"
                    );

                    match engine.flush().await {
                        Ok(events) => {
                            tracing::info!(
                                session_id = %session_id,
                                event_count = events.len(),
                                "Timeout flush produced events"
                            );
                            for event in events {
                                if let Err(e) = state.session_manager.broadcast_event(session_id, event) {
                                    tracing::debug!(session_id = %session_id, "Failed to broadcast event: {}", e);
                                }
                            }
                        }
                        Err(e) => {
                            tracing::warn!(session_id = %session_id, "Timeout flush failed: {}", e);
                        }
                    }

                    // Reset engine for next segment
                    if let Err(e) = engine.reset().await {
                        tracing::warn!(session_id = %session_id, "Engine reset failed: {}", e);
                    }
                }
                // Continue waiting for more audio
            }

            // Channel closed (session ended)
            Ok(None) => {
                tracing::info!(session_id = %session_id, "Audio channel closed, performing final flush");
                break;
            }
        }
    }

    // Final flush for any remaining audio
    let total_duration = total_samples as f64 / sample_rate;
    let buffer_duration = engine.buffer_duration();

    if buffer_duration > 0.0 {
        tracing::info!(
            session_id = %session_id,
            total_samples = total_samples,
            total_duration_s = format!("{:.2}", total_duration),
            buffer_duration_s = format!("{:.2}", buffer_duration),
            "Final flush of remaining audio"
        );

        match engine.flush().await {
            Ok(events) => {
                tracing::info!(session_id = %session_id, event_count = events.len(), "Final flush produced events");
                for event in events {
                    if let Err(e) = state.session_manager.broadcast_event(session_id, event) {
                        tracing::debug!(session_id = %session_id, "Failed to broadcast final event: {}", e);
                    }
                }
            }
            Err(e) => {
                tracing::error!(session_id = %session_id, "Final flush failed: {}", e);
            }
        }
    }

    tracing::info!(session_id = %session_id, "Audio processing worker stopped");
}

/// GET /sessions - List all sessions
pub async fn list_sessions<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
) -> Json<ApiResponse<Vec<SessionInfo>>> {
    let sessions = state.session_manager.list_sessions();
    Json(ApiResponse::success(sessions))
}

/// GET /sessions/:id - Get session details
pub async fn get_session<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<SessionInfo>>, SessionError> {
    let info = state.session_manager.get_session(id)?;
    Ok(Json(ApiResponse::success(info)))
}

/// DELETE /sessions/:id - Close a session
pub async fn close_session<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<SessionInfo>>, SessionError> {
    let info = state.session_manager.close_session(id)?;
    Ok(Json(ApiResponse::success(info)))
}

/// POST /sessions/:id/audio - Send audio chunk
///
/// Expects raw binary audio data (f32 samples, little-endian).
pub async fn send_audio<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
    Path(id): Path<Uuid>,
    body: Bytes,
) -> Result<StatusCode, SessionError> {
    // Convert bytes to f32 samples
    if body.len() % 4 != 0 {
        return Err(SessionError::Internal(
            "Audio data must be aligned to 4 bytes (f32)".to_string(),
        ));
    }

    let samples: Vec<f32> = body
        .chunks_exact(4)
        .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect();

    let sample_count = samples.len() as u64;

    // Mark session as active on first audio
    if let Ok(info) = state.session_manager.get_session(id) {
        if info.state == SessionState::Created {
            state.session_manager.set_state(id, SessionState::Active)?;
        }
    }

    state.session_manager.send_audio(id, samples).await?;
    state.session_manager.add_audio_samples(id, sample_count)?;

    Ok(StatusCode::ACCEPTED)
}

/// GET /sessions/:id/ws - WebSocket connection for real-time transcripts
pub async fn websocket_handler<B: SttBackend + 'static>(
    State(state): State<Arc<AppState<B>>>,
    Path(id): Path<Uuid>,
    ws: WebSocketUpgrade,
) -> Result<Response, SessionError> {
    // Validate session exists
    let _info = state.session_manager.get_session(id)?;

    // Subscribe to events before upgrading
    let event_rx = state.session_manager.subscribe(id)?;

    Ok(ws.on_upgrade(move |socket| handle_websocket(socket, id, event_rx, state)))
}

/// Handle WebSocket connection
async fn handle_websocket<B: SttBackend + 'static>(
    mut socket: WebSocket,
    session_id: Uuid,
    mut event_rx: tokio::sync::broadcast::Receiver<StreamingEvent>,
    state: Arc<AppState<B>>,
) {
    tracing::info!(session_id = %session_id, "WebSocket connected");

    // Simple loop: receive events and send to client, handle incoming messages
    loop {
        tokio::select! {
            // Forward events from backend to WebSocket client
            event = event_rx.recv() => {
                match event {
                    Ok(streaming_event) => {
                        let json = match serde_json::to_string(&streaming_event) {
                            Ok(j) => j,
                            Err(e) => {
                                tracing::warn!("Failed to serialize event: {}", e);
                                continue;
                            }
                        };
                        if socket.send(Message::Text(json.into())).await.is_err() {
                            tracing::debug!(session_id = %session_id, "WebSocket send failed, closing");
                            break;
                        }
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                        tracing::warn!(session_id = %session_id, "WebSocket lagged {} events", n);
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Closed) => {
                        tracing::info!(session_id = %session_id, "Event channel closed");
                        break;
                    }
                }
            }

            // Handle incoming messages from client
            msg = socket.recv() => {
                match msg {
                    Some(Ok(Message::Text(text))) => {
                        tracing::debug!(session_id = %session_id, "Received message: {}", text);

                        // Parse control message
                        if let Ok(control) = serde_json::from_str::<WebSocketControl>(&text) {
                            if control.action == "close" {
                                tracing::info!(session_id = %session_id, "Client requested close");
                                break;
                            }
                        }
                    }
                    Some(Ok(Message::Binary(data))) => {
                        tracing::debug!(session_id = %session_id, "Received {} bytes binary", data.len());
                    }
                    Some(Ok(Message::Close(_))) => {
                        tracing::info!(session_id = %session_id, "WebSocket close frame");
                        break;
                    }
                    Some(Ok(_)) => {} // Ignore ping/pong
                    Some(Err(e)) => {
                        tracing::warn!(session_id = %session_id, "WebSocket error: {}", e);
                        break;
                    }
                    None => {
                        tracing::info!(session_id = %session_id, "WebSocket stream ended");
                        break;
                    }
                }
            }
        }
    }

    tracing::info!(session_id = %session_id, "WebSocket disconnected");

    // Mark session as closing when WebSocket disconnects
    let _ = state.session_manager.set_state(session_id, SessionState::Closing);
}

/// WebSocket control message
#[derive(Debug, Deserialize)]
struct WebSocketControl {
    action: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_api_response_success() {
        let response = ApiResponse::success("test");
        assert!(response.success);
        assert!(response.data.is_some());
        assert!(response.error.is_none());
    }

    #[test]
    fn test_api_response_error() {
        let response = ApiResponse::<()>::error("something failed");
        assert!(!response.success);
        assert!(response.data.is_none());
        assert_eq!(response.error, Some("something failed".to_string()));
    }

    #[test]
    fn test_health_response_serialize() {
        let response = HealthResponse {
            status: "healthy".to_string(),
            version: "0.1.0".to_string(),
        };
        let json = serde_json::to_string(&response).unwrap();
        assert!(json.contains("healthy"));
    }
}
