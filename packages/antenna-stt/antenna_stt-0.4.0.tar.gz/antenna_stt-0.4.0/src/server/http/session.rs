//! Session Management
//!
//! Manages active transcription sessions with lifecycle tracking.

use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use tokio::sync::{broadcast, mpsc};
use uuid::Uuid;

use crate::server::streaming::StreamingEvent;

/// Session state machine
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SessionState {
    /// Session created, waiting for connection
    Created,
    /// Active transcription in progress
    Active,
    /// Gracefully closing
    Closing,
    /// Session terminated
    Closed,
}

/// Session configuration from client
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionConfig {
    /// Language hint (e.g., "en", "auto")
    #[serde(default = "default_language")]
    pub language: String,
    /// Enable translation to English
    #[serde(default)]
    pub translate: bool,
    /// Sample rate of incoming audio (default: 16000)
    #[serde(default = "default_sample_rate")]
    pub sample_rate: u32,
    /// Custom model name (optional)
    pub model: Option<String>,
}

fn default_language() -> String {
    "auto".to_string()
}

fn default_sample_rate() -> u32 {
    16000
}

impl Default for SessionConfig {
    fn default() -> Self {
        Self {
            language: default_language(),
            translate: false,
            sample_rate: default_sample_rate(),
            model: None,
        }
    }
}

/// Information about an active session
#[derive(Debug, Clone, Serialize)]
pub struct SessionInfo {
    pub id: Uuid,
    pub state: SessionState,
    pub config: SessionConfig,
    pub created_at: u64,
    pub audio_duration_ms: u64,
    pub transcript_count: u32,
}

/// Internal session data
pub struct Session {
    pub id: Uuid,
    pub state: SessionState,
    pub config: SessionConfig,
    pub created_at: Instant,
    /// Channel for sending audio chunks to the processing engine
    pub audio_tx: mpsc::Sender<Vec<f32>>,
    /// Broadcast channel for streaming events to multiple WebSocket clients
    pub event_tx: broadcast::Sender<StreamingEvent>,
    /// Statistics
    pub audio_samples: u64,
    pub transcript_count: u32,
}

impl Session {
    /// Create session info for API responses
    pub fn info(&self) -> SessionInfo {
        SessionInfo {
            id: self.id,
            state: self.state,
            config: self.config.clone(),
            created_at: self.created_at.elapsed().as_secs(),
            audio_duration_ms: (self.audio_samples as f64 / self.config.sample_rate as f64 * 1000.0) as u64,
            transcript_count: self.transcript_count,
        }
    }
}

/// Error types for session operations
#[derive(Debug, thiserror::Error)]
pub enum SessionError {
    #[error("Session not found: {0}")]
    NotFound(Uuid),

    #[error("Session already exists: {0}")]
    AlreadyExists(Uuid),

    #[error("Session in invalid state: expected {expected:?}, got {actual:?}")]
    InvalidState {
        expected: SessionState,
        actual: SessionState,
    },

    #[error("Maximum sessions reached: {0}")]
    MaxSessionsReached(usize),

    #[error("Session channel closed")]
    ChannelClosed,

    #[error("Internal error: {0}")]
    Internal(String),
}

/// Configuration for SessionManager
#[derive(Debug, Clone)]
pub struct SessionManagerConfig {
    /// Maximum concurrent sessions
    pub max_sessions: usize,
    /// Session timeout (no activity)
    pub session_timeout: Duration,
    /// Audio channel buffer size
    pub audio_buffer_size: usize,
    /// Event broadcast channel capacity
    pub event_buffer_size: usize,
}

impl Default for SessionManagerConfig {
    fn default() -> Self {
        Self {
            max_sessions: 100,
            session_timeout: Duration::from_secs(300), // 5 minutes
            audio_buffer_size: 1024,
            event_buffer_size: 256,
        }
    }
}

/// Manages active transcription sessions
///
/// Thread-safe session registry with concurrent access support.
/// Uses DashMap for lock-free reads and fine-grained write locks.
pub struct SessionManager {
    sessions: DashMap<Uuid, Session>,
    config: SessionManagerConfig,
}

impl SessionManager {
    /// Create a new session manager
    pub fn new(config: SessionManagerConfig) -> Self {
        Self {
            sessions: DashMap::new(),
            config,
        }
    }

    /// Create with default configuration
    pub fn default_manager() -> Self {
        Self::new(SessionManagerConfig::default())
    }

    /// Create a new session
    ///
    /// Returns the session ID and channels for audio input and event output.
    pub fn create_session(
        &self,
        config: SessionConfig,
    ) -> Result<(Uuid, mpsc::Receiver<Vec<f32>>, broadcast::Receiver<StreamingEvent>), SessionError>
    {
        // Check session limit
        if self.sessions.len() >= self.config.max_sessions {
            return Err(SessionError::MaxSessionsReached(self.config.max_sessions));
        }

        let id = Uuid::new_v4();
        let (audio_tx, audio_rx) = mpsc::channel(self.config.audio_buffer_size);
        let (event_tx, event_rx) = broadcast::channel(self.config.event_buffer_size);

        let session = Session {
            id,
            state: SessionState::Created,
            config,
            created_at: Instant::now(),
            audio_tx,
            event_tx,
            audio_samples: 0,
            transcript_count: 0,
        };

        self.sessions.insert(id, session);
        tracing::info!(session_id = %id, "Created new session");

        Ok((id, audio_rx, event_rx))
    }

    /// Get session info
    pub fn get_session(&self, id: Uuid) -> Result<SessionInfo, SessionError> {
        self.sessions
            .get(&id)
            .map(|s| s.info())
            .ok_or(SessionError::NotFound(id))
    }

    /// Update session state
    pub fn set_state(&self, id: Uuid, state: SessionState) -> Result<(), SessionError> {
        let mut session = self
            .sessions
            .get_mut(&id)
            .ok_or(SessionError::NotFound(id))?;

        tracing::debug!(session_id = %id, old_state = ?session.state, new_state = ?state, "Session state change");
        session.state = state;
        Ok(())
    }

    /// Send audio to a session
    pub async fn send_audio(&self, id: Uuid, samples: Vec<f32>) -> Result<(), SessionError> {
        let session = self
            .sessions
            .get(&id)
            .ok_or(SessionError::NotFound(id))?;

        // Check state
        if session.state != SessionState::Active && session.state != SessionState::Created {
            return Err(SessionError::InvalidState {
                expected: SessionState::Active,
                actual: session.state,
            });
        }

        session
            .audio_tx
            .send(samples)
            .await
            .map_err(|_| SessionError::ChannelClosed)?;

        Ok(())
    }

    /// Subscribe to session events
    pub fn subscribe(&self, id: Uuid) -> Result<broadcast::Receiver<StreamingEvent>, SessionError> {
        let session = self
            .sessions
            .get(&id)
            .ok_or(SessionError::NotFound(id))?;

        Ok(session.event_tx.subscribe())
    }

    /// Broadcast an event to all subscribers
    pub fn broadcast_event(&self, id: Uuid, event: StreamingEvent) -> Result<(), SessionError> {
        let mut session = self
            .sessions
            .get_mut(&id)
            .ok_or(SessionError::NotFound(id))?;

        // Update statistics
        if matches!(event, StreamingEvent::Final(_)) {
            session.transcript_count += 1;
        }

        // Ignore send errors (no subscribers)
        let _ = session.event_tx.send(event);
        Ok(())
    }

    /// Close a session
    pub fn close_session(&self, id: Uuid) -> Result<SessionInfo, SessionError> {
        let (_, session) = self
            .sessions
            .remove(&id)
            .ok_or(SessionError::NotFound(id))?;

        tracing::info!(
            session_id = %id,
            duration_ms = session.created_at.elapsed().as_millis(),
            transcripts = session.transcript_count,
            "Session closed"
        );

        Ok(session.info())
    }

    /// List all active sessions
    pub fn list_sessions(&self) -> Vec<SessionInfo> {
        self.sessions
            .iter()
            .map(|entry| entry.value().info())
            .collect()
    }

    /// Get session count
    pub fn session_count(&self) -> usize {
        self.sessions.len()
    }

    /// Clean up expired sessions
    pub fn cleanup_expired(&self) -> Vec<Uuid> {
        let expired: Vec<Uuid> = self
            .sessions
            .iter()
            .filter(|entry| {
                entry.created_at.elapsed() > self.config.session_timeout
                    && entry.state != SessionState::Active
            })
            .map(|entry| *entry.key())
            .collect();

        for id in &expired {
            self.sessions.remove(id);
            tracing::info!(session_id = %id, "Cleaned up expired session");
        }

        expired
    }

    /// Update audio sample count for a session
    pub fn add_audio_samples(&self, id: Uuid, count: u64) -> Result<(), SessionError> {
        let mut session = self
            .sessions
            .get_mut(&id)
            .ok_or(SessionError::NotFound(id))?;
        session.audio_samples += count;
        Ok(())
    }
}

impl Default for SessionManager {
    fn default() -> Self {
        Self::default_manager()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_session_config_defaults() {
        let config = SessionConfig::default();
        assert_eq!(config.language, "auto");
        assert_eq!(config.sample_rate, 16000);
        assert!(!config.translate);
    }

    #[test]
    fn test_session_manager_create() {
        let manager = SessionManager::default();
        let result = manager.create_session(SessionConfig::default());
        assert!(result.is_ok());

        let (id, _, _) = result.unwrap();
        let info = manager.get_session(id).unwrap();
        assert_eq!(info.state, SessionState::Created);
    }

    #[test]
    fn test_session_state_transition() {
        let manager = SessionManager::default();
        let (id, _, _) = manager.create_session(SessionConfig::default()).unwrap();

        manager.set_state(id, SessionState::Active).unwrap();
        let info = manager.get_session(id).unwrap();
        assert_eq!(info.state, SessionState::Active);

        manager.set_state(id, SessionState::Closing).unwrap();
        let info = manager.get_session(id).unwrap();
        assert_eq!(info.state, SessionState::Closing);
    }

    #[test]
    fn test_session_not_found() {
        let manager = SessionManager::default();
        let fake_id = Uuid::new_v4();

        let result = manager.get_session(fake_id);
        assert!(matches!(result, Err(SessionError::NotFound(_))));
    }

    #[test]
    fn test_session_close() {
        let manager = SessionManager::default();
        let (id, _, _) = manager.create_session(SessionConfig::default()).unwrap();

        assert_eq!(manager.session_count(), 1);
        manager.close_session(id).unwrap();
        assert_eq!(manager.session_count(), 0);
    }

    #[test]
    fn test_max_sessions() {
        let config = SessionManagerConfig {
            max_sessions: 2,
            ..Default::default()
        };
        let manager = SessionManager::new(config);

        manager.create_session(SessionConfig::default()).unwrap();
        manager.create_session(SessionConfig::default()).unwrap();

        let result = manager.create_session(SessionConfig::default());
        assert!(matches!(result, Err(SessionError::MaxSessionsReached(2))));
    }

    #[test]
    fn test_list_sessions() {
        let manager = SessionManager::default();

        manager.create_session(SessionConfig::default()).unwrap();
        manager.create_session(SessionConfig::default()).unwrap();

        let list = manager.list_sessions();
        assert_eq!(list.len(), 2);
    }
}
