//! WebRTC Signaling Types
//!
//! Types for SDP offer/answer exchange and ICE candidate negotiation.

use serde::{Deserialize, Serialize};

/// Session Description Protocol (SDP) message
///
/// Used for offer/answer exchange between browser and server.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionDescription {
    /// Type of SDP: "offer" or "answer"
    #[serde(rename = "type")]
    pub sdp_type: String,
    /// The SDP content
    pub sdp: String,
}

impl SessionDescription {
    /// Create an offer
    pub fn offer(sdp: impl Into<String>) -> Self {
        Self {
            sdp_type: "offer".to_string(),
            sdp: sdp.into(),
        }
    }

    /// Create an answer
    pub fn answer(sdp: impl Into<String>) -> Self {
        Self {
            sdp_type: "answer".to_string(),
            sdp: sdp.into(),
        }
    }

    /// Check if this is an offer
    pub fn is_offer(&self) -> bool {
        self.sdp_type == "offer"
    }

    /// Check if this is an answer
    pub fn is_answer(&self) -> bool {
        self.sdp_type == "answer"
    }
}

/// ICE Candidate for connection establishment
///
/// Exchanged between peers to establish the optimal network path.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IceCandidate {
    /// The ICE candidate string
    pub candidate: String,
    /// Media stream identification tag
    #[serde(rename = "sdpMid")]
    pub sdp_mid: Option<String>,
    /// Media line index
    #[serde(rename = "sdpMLineIndex")]
    pub sdp_mline_index: Option<u16>,
}

impl IceCandidate {
    /// Create a new ICE candidate
    pub fn new(candidate: impl Into<String>) -> Self {
        Self {
            candidate: candidate.into(),
            sdp_mid: None,
            sdp_mline_index: None,
        }
    }

    /// With media stream ID
    pub fn with_sdp_mid(mut self, mid: impl Into<String>) -> Self {
        self.sdp_mid = Some(mid.into());
        self
    }

    /// With media line index
    pub fn with_sdp_mline_index(mut self, index: u16) -> Self {
        self.sdp_mline_index = Some(index);
        self
    }
}

/// Signaling message types for WebSocket communication
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum SignalingMessage {
    /// SDP offer from client
    Offer(SessionDescription),
    /// SDP answer from server
    Answer(SessionDescription),
    /// ICE candidate
    IceCandidate(IceCandidate),
    /// Connection ready
    Ready,
    /// Error occurred
    Error { message: String },
}

impl SignalingMessage {
    /// Create an error message
    pub fn error(message: impl Into<String>) -> Self {
        SignalingMessage::Error {
            message: message.into(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_session_description_offer() {
        let sdp = SessionDescription::offer("v=0\r\n...");
        assert!(sdp.is_offer());
        assert!(!sdp.is_answer());
    }

    #[test]
    fn test_session_description_answer() {
        let sdp = SessionDescription::answer("v=0\r\n...");
        assert!(sdp.is_answer());
        assert!(!sdp.is_offer());
    }

    #[test]
    fn test_ice_candidate_builder() {
        let candidate = IceCandidate::new("candidate:123...")
            .with_sdp_mid("audio")
            .with_sdp_mline_index(0);

        assert_eq!(candidate.sdp_mid, Some("audio".to_string()));
        assert_eq!(candidate.sdp_mline_index, Some(0));
    }

    #[test]
    fn test_signaling_message_serialize() {
        let msg = SignalingMessage::Ready;
        let json = serde_json::to_string(&msg).unwrap();
        assert!(json.contains("ready"));
    }

    #[test]
    fn test_session_description_deserialize() {
        let json = r#"{"type":"offer","sdp":"v=0\r\n..."}"#;
        let sdp: SessionDescription = serde_json::from_str(json).unwrap();
        assert!(sdp.is_offer());
    }

    #[test]
    fn test_ice_candidate_deserialize() {
        let json = r#"{"candidate":"candidate:123","sdpMid":"audio","sdpMLineIndex":0}"#;
        let candidate: IceCandidate = serde_json::from_str(json).unwrap();
        assert_eq!(candidate.sdp_mid, Some("audio".to_string()));
    }
}
