//! WebRTC Module for Real-Time Audio Streaming
//!
//! Provides WebRTC peer connection management for browser-based audio streaming.
//!
//! # Architecture
//!
//! ```text
//! Browser ──WebRTC PeerConnection──> RTCPeerConnection
//!    │                                      │
//!    │◄────────ICE Candidates◄──────────────┤
//!    │                                      │
//!    └──────Opus Audio Track────────────────┴──> AudioHandler ──> STT Engine
//! ```
//!
//! # Components
//!
//! - **PeerManager**: Creates and manages WebRTC peer connections
//! - **Signaling**: Handles SDP offer/answer exchange and ICE candidates
//! - **AudioHandler**: Receives Opus-encoded audio, decodes, and resamples for STT

mod audio;
mod peer;
mod signaling;

pub use audio::{AudioHandler, AudioHandlerConfig, AudioSample};
pub use peer::{PeerConnection, PeerConnectionConfig, PeerError, PeerManager, PeerState};
pub use signaling::{IceCandidate, SessionDescription, SignalingMessage};
