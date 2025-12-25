//! Worker Pool for STT Backend Management
//!
//! Provides a pool of STT backends for handling concurrent transcription sessions.
//!
//! # Architecture
//!
//! ```text
//! Session ──acquire()──> BackendPool ──> Available Backend
//!    │                       │                │
//!    │                   Semaphore         Process
//!    │                       │                │
//!    │◄──────release()───────┴────────────────┘
//! ```

mod pool;
mod metrics;

pub use pool::{BackendPool, BackendPoolConfig, PooledBackend, PoolError};
pub use metrics::{Metrics, MetricsSnapshot, LatencyHistogram};
