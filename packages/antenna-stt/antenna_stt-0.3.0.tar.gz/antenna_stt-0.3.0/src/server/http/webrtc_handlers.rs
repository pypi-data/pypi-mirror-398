//! WebRTC HTTP Handlers
//!
//! Handlers for WebRTC signaling over HTTP.

use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use super::handlers::{
    ApiResponse, BackendCapabilitiesInfo, BackendHealthInfo, DetailedHealthResponse,
    ReadinessResponse, SessionHealthInfo,
};
use super::routes::AppState;
use super::session::{SessionError, SessionState};
use crate::server::stt::SttBackend;
use crate::server::webrtc::{IceCandidate, PeerManager, SessionDescription};

/// WebRTC session state stored in AppState
pub struct WebRtcState {
    pub peer_manager: PeerManager,
}

impl Default for WebRtcState {
    fn default() -> Self {
        Self {
            peer_manager: PeerManager::new(),
        }
    }
}

/// Extended app state with WebRTC support
pub struct WebRtcAppState<B: SttBackend + 'static> {
    pub base: AppState<B>,
    pub webrtc: WebRtcState,
}

impl<B: SttBackend + 'static> WebRtcAppState<B> {
    pub fn new(backend: Arc<B>) -> Self {
        Self {
            base: AppState::new(backend),
            webrtc: WebRtcState::default(),
        }
    }
}

/// Request to create WebRTC session
#[derive(Debug, Deserialize)]
pub struct CreateWebRtcSessionRequest {
    /// SDP offer from browser
    pub offer: SessionDescription,
}

/// Response with WebRTC session details
#[derive(Debug, Serialize)]
pub struct WebRtcSessionResponse {
    /// Session ID
    pub session_id: Uuid,
    /// SDP answer
    pub answer: SessionDescription,
    /// ICE candidates endpoint
    pub ice_url: String,
}

/// POST /webrtc/sessions - Create a WebRTC session with SDP offer
pub async fn create_webrtc_session<B: SttBackend + 'static>(
    State(state): State<Arc<WebRtcAppState<B>>>,
    Json(request): Json<CreateWebRtcSessionRequest>,
) -> Result<(StatusCode, Json<ApiResponse<WebRtcSessionResponse>>), SessionError> {
    // Create a regular session first
    let session_config = super::session::SessionConfig::default();
    let (session_id, audio_rx, _event_rx) = state
        .base
        .session_manager
        .create_session(session_config)?;

    // Create WebRTC peer connection
    let (peer, webrtc_audio_rx, ice_rx, state_rx) = state
        .webrtc
        .peer_manager
        .create_peer(session_id)
        .await
        .map_err(|e| SessionError::Internal(format!("WebRTC error: {}", e)))?;

    // Set remote description (offer)
    peer.set_remote_description(request.offer)
        .await
        .map_err(|e| SessionError::Internal(format!("SDP error: {}", e)))?;

    // Create answer
    let answer = peer
        .create_answer()
        .await
        .map_err(|e| SessionError::Internal(format!("Answer error: {}", e)))?;

    // Mark session as active
    state
        .base
        .session_manager
        .set_state(session_id, SessionState::Active)?;

    // Spawn task to forward WebRTC audio to session
    let state_clone = state.clone();
    tokio::spawn(async move {
        forward_webrtc_audio(session_id, webrtc_audio_rx, state_clone).await;
    });

    // Spawn task to handle ICE candidates
    let session_id_clone = session_id;
    tokio::spawn(async move {
        handle_ice_candidates(session_id_clone, ice_rx).await;
    });

    // Spawn task to handle state changes
    let state_clone = state.clone();
    tokio::spawn(async move {
        handle_peer_state(session_id, state_rx, state_clone).await;
    });

    let response = WebRtcSessionResponse {
        session_id,
        answer,
        ice_url: format!("/webrtc/sessions/{}/ice", session_id),
    };

    tracing::info!(session_id = %session_id, "WebRTC session created");

    Ok((StatusCode::CREATED, Json(ApiResponse::success(response))))
}

/// POST /webrtc/sessions/:id/ice - Add ICE candidate
pub async fn add_ice_candidate<B: SttBackend + 'static>(
    State(_state): State<Arc<WebRtcAppState<B>>>,
    Path(id): Path<Uuid>,
    Json(candidate): Json<IceCandidate>,
) -> Result<StatusCode, SessionError> {
    tracing::debug!(session_id = %id, candidate = ?candidate.candidate, "Received ICE candidate");

    // In a full implementation, we'd store the peer connection and add the candidate
    // For now, just acknowledge receipt
    // TODO: Store peer connections in state and add ICE candidates

    Ok(StatusCode::ACCEPTED)
}

/// GET /health/ready - Kubernetes readiness probe for WebRTC router
pub async fn readiness_probe<B: SttBackend + 'static>(
    State(state): State<Arc<WebRtcAppState<B>>>,
) -> (StatusCode, Json<ReadinessResponse>) {
    let backend_ready = state.base.backend.is_ready();
    let accepting = true;

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

/// GET /health/detailed - Detailed health for WebRTC router
pub async fn detailed_health<B: SttBackend + 'static>(
    State(state): State<Arc<WebRtcAppState<B>>>,
) -> Json<DetailedHealthResponse> {
    static START_TIME: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    let start = START_TIME.get_or_init(std::time::Instant::now);

    let backend_info = state.base.backend.info();
    let active_sessions = state.base.session_manager.session_count();
    let max_sessions = 100;

    let status = if state.base.backend.is_ready() {
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
            ready: state.base.backend.is_ready(),
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

/// Forward audio from WebRTC to session
async fn forward_webrtc_audio<B: SttBackend + 'static>(
    session_id: Uuid,
    mut audio_rx: tokio::sync::mpsc::Receiver<Vec<f32>>,
    state: Arc<WebRtcAppState<B>>,
) {
    tracing::info!(session_id = %session_id, "Starting WebRTC audio forwarding");

    while let Some(samples) = audio_rx.recv().await {
        if state.base.session_manager.send_audio(session_id, samples).await.is_err() {
            tracing::debug!(session_id = %session_id, "Session audio channel closed");
            break;
        }
    }

    tracing::info!(session_id = %session_id, "WebRTC audio forwarding stopped");
}

/// Handle outgoing ICE candidates
async fn handle_ice_candidates(
    session_id: Uuid,
    mut ice_rx: tokio::sync::mpsc::Receiver<IceCandidate>,
) {
    while let Some(candidate) = ice_rx.recv().await {
        tracing::debug!(
            session_id = %session_id,
            candidate = ?candidate.candidate,
            "ICE candidate generated"
        );
        // In a full implementation, we'd send this to the client via WebSocket
        // or store it for polling
    }
}

/// Handle peer connection state changes
async fn handle_peer_state<B: SttBackend + 'static>(
    session_id: Uuid,
    mut state_rx: tokio::sync::mpsc::Receiver<crate::server::webrtc::PeerState>,
    state: Arc<WebRtcAppState<B>>,
) {
    use crate::server::webrtc::PeerState;

    while let Some(peer_state) = state_rx.recv().await {
        match peer_state {
            PeerState::Failed | PeerState::Closed => {
                tracing::info!(session_id = %session_id, state = ?peer_state, "Peer connection ended");
                let _ = state.base.session_manager.set_state(session_id, SessionState::Closing);
                break;
            }
            _ => {}
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_webrtc_state_default() {
        let state = WebRtcState::default();
        // Just verify it creates without panic
        let _ = state;
    }
}
