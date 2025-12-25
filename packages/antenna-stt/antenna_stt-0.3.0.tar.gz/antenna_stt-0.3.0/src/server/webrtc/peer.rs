//! WebRTC Peer Connection Management
//!
//! Manages WebRTC peer connections for real-time audio streaming from browsers.

use std::sync::Arc;
use tokio::sync::mpsc;
use uuid::Uuid;

use webrtc::api::interceptor_registry::register_default_interceptors;
use webrtc::api::media_engine::MediaEngine;
use webrtc::api::APIBuilder;
use webrtc::ice_transport::ice_server::RTCIceServer;
use webrtc::interceptor::registry::Registry;
use webrtc::peer_connection::configuration::RTCConfiguration;
use webrtc::peer_connection::peer_connection_state::RTCPeerConnectionState;
use webrtc::peer_connection::sdp::session_description::RTCSessionDescription;
use webrtc::peer_connection::RTCPeerConnection;
use webrtc::rtp_transceiver::rtp_codec::RTPCodecType;
use webrtc::track::track_remote::TrackRemote;

use super::audio::AudioHandler;
use super::signaling::{IceCandidate, SessionDescription};

/// Peer connection state
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PeerState {
    /// Connection not yet established
    New,
    /// Connecting (ICE gathering/checking)
    Connecting,
    /// Connected and streaming
    Connected,
    /// Connection failed
    Failed,
    /// Connection closed
    Closed,
}

impl From<RTCPeerConnectionState> for PeerState {
    fn from(state: RTCPeerConnectionState) -> Self {
        match state {
            RTCPeerConnectionState::New => PeerState::New,
            RTCPeerConnectionState::Connecting => PeerState::Connecting,
            RTCPeerConnectionState::Connected => PeerState::Connected,
            RTCPeerConnectionState::Failed => PeerState::Failed,
            RTCPeerConnectionState::Closed => PeerState::Closed,
            RTCPeerConnectionState::Disconnected => PeerState::Failed,
            _ => PeerState::New,
        }
    }
}

/// Error types for peer operations
#[derive(Debug, thiserror::Error)]
pub enum PeerError {
    #[error("WebRTC error: {0}")]
    WebRtc(String),

    #[error("Invalid SDP: {0}")]
    InvalidSdp(String),

    #[error("Invalid ICE candidate: {0}")]
    InvalidIceCandidate(String),

    #[error("Connection failed: {0}")]
    ConnectionFailed(String),

    #[error("Peer not found: {0}")]
    NotFound(Uuid),

    #[error("Internal error: {0}")]
    Internal(String),
}

impl From<webrtc::Error> for PeerError {
    fn from(e: webrtc::Error) -> Self {
        PeerError::WebRtc(e.to_string())
    }
}

/// Configuration for peer connections
#[derive(Debug, Clone)]
pub struct PeerConnectionConfig {
    /// ICE servers for NAT traversal
    pub ice_servers: Vec<String>,
    /// Whether to use only STUN (no TURN)
    pub stun_only: bool,
}

impl Default for PeerConnectionConfig {
    fn default() -> Self {
        Self {
            ice_servers: vec![
                "stun:stun.l.google.com:19302".to_string(),
                "stun:stun1.l.google.com:19302".to_string(),
            ],
            stun_only: true,
        }
    }
}

/// Wraps an RTCPeerConnection with session tracking
pub struct PeerConnection {
    /// Unique session ID
    pub id: Uuid,
    /// Underlying WebRTC peer connection
    inner: Arc<RTCPeerConnection>,
    /// Current state
    state: PeerState,
    /// Audio handler for processing incoming tracks
    audio_handler: Option<AudioHandler>,
}

impl PeerConnection {
    /// Get the current state
    pub fn state(&self) -> PeerState {
        self.state
    }

    /// Set the remote description (SDP offer from browser)
    pub async fn set_remote_description(&self, sdp: SessionDescription) -> Result<(), PeerError> {
        let rtc_sdp = RTCSessionDescription::offer(sdp.sdp)
            .map_err(|e| PeerError::InvalidSdp(e.to_string()))?;

        self.inner
            .set_remote_description(rtc_sdp)
            .await
            .map_err(|e| PeerError::InvalidSdp(e.to_string()))?;

        Ok(())
    }

    /// Create an SDP answer
    pub async fn create_answer(&self) -> Result<SessionDescription, PeerError> {
        let answer = self.inner.create_answer(None).await?;

        // Set local description
        self.inner.set_local_description(answer.clone()).await?;

        Ok(SessionDescription {
            sdp_type: "answer".to_string(),
            sdp: answer.sdp,
        })
    }

    /// Add an ICE candidate from the remote peer
    pub async fn add_ice_candidate(&self, candidate: IceCandidate) -> Result<(), PeerError> {
        use webrtc::ice_transport::ice_candidate::RTCIceCandidateInit;

        let init = RTCIceCandidateInit {
            candidate: candidate.candidate,
            sdp_mid: candidate.sdp_mid,
            sdp_mline_index: candidate.sdp_mline_index,
            ..Default::default()
        };

        self.inner
            .add_ice_candidate(init)
            .await
            .map_err(|e| PeerError::InvalidIceCandidate(e.to_string()))?;

        Ok(())
    }

    /// Close the peer connection
    pub async fn close(&self) -> Result<(), PeerError> {
        self.inner.close().await?;
        Ok(())
    }

    /// Get the underlying RTCPeerConnection for advanced operations
    pub fn inner(&self) -> &Arc<RTCPeerConnection> {
        &self.inner
    }
}

/// Manages WebRTC peer connections
pub struct PeerManager {
    config: PeerConnectionConfig,
}

impl PeerManager {
    /// Create a new peer manager with default configuration
    pub fn new() -> Self {
        Self {
            config: PeerConnectionConfig::default(),
        }
    }

    /// Create with custom configuration
    pub fn with_config(config: PeerConnectionConfig) -> Self {
        Self { config }
    }

    /// Create a new peer connection
    ///
    /// Returns the peer connection and channels for:
    /// - Audio samples (f32 PCM at 16kHz mono)
    /// - ICE candidates (to send to browser)
    /// - State changes
    pub async fn create_peer(
        &self,
        session_id: Uuid,
    ) -> Result<
        (
            PeerConnection,
            mpsc::Receiver<Vec<f32>>,
            mpsc::Receiver<IceCandidate>,
            mpsc::Receiver<PeerState>,
        ),
        PeerError,
    > {
        // Create media engine with Opus codec
        let mut media_engine = MediaEngine::default();
        media_engine.register_default_codecs()?;

        // Create interceptor registry
        let mut registry = Registry::new();
        registry = register_default_interceptors(registry, &mut media_engine)?;

        // Build API
        let api = APIBuilder::new()
            .with_media_engine(media_engine)
            .with_interceptor_registry(registry)
            .build();

        // Configure ICE servers
        let ice_servers: Vec<RTCIceServer> = self
            .config
            .ice_servers
            .iter()
            .map(|url| RTCIceServer {
                urls: vec![url.clone()],
                ..Default::default()
            })
            .collect();

        let rtc_config = RTCConfiguration {
            ice_servers,
            ..Default::default()
        };

        // Create peer connection
        let pc = Arc::new(api.new_peer_connection(rtc_config).await?);

        // Channels for communication
        let (audio_tx, audio_rx) = mpsc::channel::<Vec<f32>>(256);
        let (ice_tx, ice_rx) = mpsc::channel::<IceCandidate>(64);
        let (state_tx, state_rx) = mpsc::channel::<PeerState>(16);

        // Set up ICE candidate callback
        let ice_tx_clone = ice_tx.clone();
        pc.on_ice_candidate(Box::new(move |candidate| {
            let ice_tx = ice_tx_clone.clone();
            Box::pin(async move {
                if let Some(c) = candidate {
                    let ice_candidate = IceCandidate {
                        candidate: c.to_json().map(|j| j.candidate).unwrap_or_default(),
                        sdp_mid: c.to_json().ok().and_then(|j| j.sdp_mid),
                        sdp_mline_index: c.to_json().ok().and_then(|j| j.sdp_mline_index),
                    };
                    let _ = ice_tx.send(ice_candidate).await;
                }
            })
        }));

        // Set up connection state callback
        let state_tx_clone = state_tx.clone();
        let session_id_clone = session_id;
        pc.on_peer_connection_state_change(Box::new(move |state| {
            let state_tx = state_tx_clone.clone();
            let peer_state = PeerState::from(state);
            tracing::info!(session_id = %session_id_clone, state = ?peer_state, "Peer connection state changed");
            Box::pin(async move {
                let _ = state_tx.send(peer_state).await;
            })
        }));

        // Set up ICE connection state callback
        let session_id_clone = session_id;
        pc.on_ice_connection_state_change(Box::new(move |state| {
            tracing::debug!(session_id = %session_id_clone, ice_state = ?state, "ICE connection state changed");
            Box::pin(async {})
        }));

        // Set up track callback for incoming audio
        let audio_tx_clone = audio_tx.clone();
        let session_id_clone = session_id;
        pc.on_track(Box::new(move |track, _receiver, _transceiver| {
            let audio_tx = audio_tx_clone.clone();
            let session_id = session_id_clone;

            Box::pin(async move {
                if track.kind() == RTPCodecType::Audio {
                    tracing::info!(
                        session_id = %session_id,
                        codec = track.codec().capability.mime_type,
                        "Audio track received"
                    );

                    // Spawn task to read audio from track
                    let track_clone = track.clone();
                    tokio::spawn(async move {
                        Self::handle_audio_track(track_clone, audio_tx, session_id).await;
                    });
                }
            })
        }));

        let peer = PeerConnection {
            id: session_id,
            inner: pc,
            state: PeerState::New,
            audio_handler: None,
        };

        Ok((peer, audio_rx, ice_rx, state_rx))
    }

    /// Handle incoming audio track
    async fn handle_audio_track(
        track: Arc<TrackRemote>,
        audio_tx: mpsc::Sender<Vec<f32>>,
        session_id: Uuid,
    ) {
        tracing::info!(session_id = %session_id, "Starting audio track handler");

        // Get codec info
        let codec = track.codec();
        let mime_type = &codec.capability.mime_type;
        let clock_rate = codec.capability.clock_rate;

        tracing::info!(
            session_id = %session_id,
            mime_type = mime_type,
            clock_rate = clock_rate,
            "Audio codec info"
        );

        // Create audio handler for decoding
        let mut audio_handler = AudioHandler::new(clock_rate, 16000);

        loop {
            // Read returns (rtp::packet::Packet, Attributes)
            match track.read_rtp().await {
                Ok((packet, _attributes)) => {
                    // The payload is the decoded audio data
                    let payload = &packet.payload;

                    if payload.is_empty() {
                        continue;
                    }

                    // Process audio (decode, resample to 16kHz)
                    match audio_handler.process_packet(payload) {
                        Ok(samples) => {
                            if !samples.is_empty() {
                                if audio_tx.send(samples).await.is_err() {
                                    tracing::debug!(session_id = %session_id, "Audio channel closed");
                                    break;
                                }
                            }
                        }
                        Err(e) => {
                            tracing::warn!(session_id = %session_id, error = %e, "Audio decode error");
                        }
                    }
                }
                Err(e) => {
                    tracing::debug!(session_id = %session_id, error = %e, "Track read ended");
                    break;
                }
            }
        }

        tracing::info!(session_id = %session_id, "Audio track handler stopped");
    }
}

impl Default for PeerManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_peer_state_from_rtc() {
        assert_eq!(
            PeerState::from(RTCPeerConnectionState::New),
            PeerState::New
        );
        assert_eq!(
            PeerState::from(RTCPeerConnectionState::Connected),
            PeerState::Connected
        );
        assert_eq!(
            PeerState::from(RTCPeerConnectionState::Failed),
            PeerState::Failed
        );
    }

    #[test]
    fn test_config_defaults() {
        let config = PeerConnectionConfig::default();
        assert!(!config.ice_servers.is_empty());
        assert!(config.stun_only);
    }

    #[test]
    fn test_peer_error_display() {
        let err = PeerError::NotFound(Uuid::new_v4());
        assert!(err.to_string().contains("not found"));
    }
}
