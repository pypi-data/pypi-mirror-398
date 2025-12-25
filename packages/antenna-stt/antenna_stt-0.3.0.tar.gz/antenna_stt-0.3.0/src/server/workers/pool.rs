//! Backend Pool Implementation
//!
//! Manages a pool of STT backends for concurrent session handling.

use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Semaphore, SemaphorePermit};

use crate::server::stt::SttBackend;

/// Error types for pool operations
#[derive(Debug, thiserror::Error)]
pub enum PoolError {
    #[error("Pool exhausted: no backends available")]
    Exhausted,

    #[error("Acquire timeout after {0:?}")]
    Timeout(Duration),

    #[error("Pool is shutting down")]
    ShuttingDown,

    #[error("Backend error: {0}")]
    Backend(String),
}

/// Configuration for the backend pool
#[derive(Debug, Clone)]
pub struct BackendPoolConfig {
    /// Maximum concurrent sessions
    pub max_concurrent: usize,
    /// Timeout for acquiring a backend slot
    pub acquire_timeout: Duration,
    /// Whether to queue requests when pool is full
    pub queue_when_full: bool,
    /// Maximum queue depth (0 = unlimited)
    pub max_queue_depth: usize,
}

impl Default for BackendPoolConfig {
    fn default() -> Self {
        Self {
            max_concurrent: 10,
            acquire_timeout: Duration::from_secs(30),
            queue_when_full: true,
            max_queue_depth: 100,
        }
    }
}

impl BackendPoolConfig {
    /// Create config for high-throughput scenarios
    pub fn high_throughput() -> Self {
        Self {
            max_concurrent: 50,
            acquire_timeout: Duration::from_secs(60),
            queue_when_full: true,
            max_queue_depth: 500,
        }
    }

    /// Create config for low-latency scenarios
    pub fn low_latency() -> Self {
        Self {
            max_concurrent: 5,
            acquire_timeout: Duration::from_secs(5),
            queue_when_full: false,
            max_queue_depth: 0,
        }
    }
}

/// Statistics for the backend pool
#[derive(Debug, Default)]
pub struct PoolStats {
    /// Total requests received
    pub total_requests: AtomicU64,
    /// Currently active sessions
    pub active_sessions: AtomicUsize,
    /// Requests that were queued
    pub queued_requests: AtomicU64,
    /// Requests that timed out
    pub timeout_count: AtomicU64,
    /// Requests rejected due to pool exhaustion
    pub rejected_count: AtomicU64,
    /// Total processing time (microseconds)
    pub total_processing_time_us: AtomicU64,
    /// Peak concurrent sessions
    pub peak_concurrent: AtomicUsize,
}

impl PoolStats {
    /// Get a snapshot of current statistics
    pub fn snapshot(&self) -> PoolStatsSnapshot {
        PoolStatsSnapshot {
            total_requests: self.total_requests.load(Ordering::Relaxed),
            active_sessions: self.active_sessions.load(Ordering::Relaxed),
            queued_requests: self.queued_requests.load(Ordering::Relaxed),
            timeout_count: self.timeout_count.load(Ordering::Relaxed),
            rejected_count: self.rejected_count.load(Ordering::Relaxed),
            total_processing_time_us: self.total_processing_time_us.load(Ordering::Relaxed),
            peak_concurrent: self.peak_concurrent.load(Ordering::Relaxed),
        }
    }
}

/// Snapshot of pool statistics
#[derive(Debug, Clone, serde::Serialize)]
pub struct PoolStatsSnapshot {
    pub total_requests: u64,
    pub active_sessions: usize,
    pub queued_requests: u64,
    pub timeout_count: u64,
    pub rejected_count: u64,
    pub total_processing_time_us: u64,
    pub peak_concurrent: usize,
}

impl PoolStatsSnapshot {
    /// Calculate average processing time in milliseconds
    pub fn avg_processing_time_ms(&self) -> f64 {
        if self.total_requests == 0 {
            0.0
        } else {
            (self.total_processing_time_us as f64 / self.total_requests as f64) / 1000.0
        }
    }

    /// Calculate success rate
    pub fn success_rate(&self) -> f64 {
        let failed = self.timeout_count + self.rejected_count;
        if self.total_requests == 0 {
            1.0
        } else {
            1.0 - (failed as f64 / self.total_requests as f64)
        }
    }
}

/// A pooled backend handle
///
/// Automatically releases the permit when dropped.
pub struct PooledBackend<'a, B: SttBackend> {
    backend: Arc<B>,
    _permit: SemaphorePermit<'a>,
    stats: Arc<PoolStats>,
    acquired_at: Instant,
}

impl<'a, B: SttBackend> PooledBackend<'a, B> {
    /// Get access to the underlying backend
    pub fn backend(&self) -> &B {
        &self.backend
    }

    /// Get the Arc to the backend for async operations
    pub fn backend_arc(&self) -> Arc<B> {
        self.backend.clone()
    }
}

impl<'a, B: SttBackend> Drop for PooledBackend<'a, B> {
    fn drop(&mut self) {
        // Update statistics
        let processing_time = self.acquired_at.elapsed();
        self.stats
            .total_processing_time_us
            .fetch_add(processing_time.as_micros() as u64, Ordering::Relaxed);
        self.stats.active_sessions.fetch_sub(1, Ordering::Relaxed);
    }
}

/// Pool of STT backends for concurrent session handling
///
/// Uses a semaphore to limit concurrent access and provides
/// statistics for monitoring and autoscaling.
pub struct BackendPool<B: SttBackend> {
    backend: Arc<B>,
    semaphore: Arc<Semaphore>,
    config: BackendPoolConfig,
    stats: Arc<PoolStats>,
    shutting_down: std::sync::atomic::AtomicBool,
}

impl<B: SttBackend> BackendPool<B> {
    /// Create a new backend pool
    pub fn new(backend: Arc<B>, config: BackendPoolConfig) -> Self {
        let semaphore = Arc::new(Semaphore::new(config.max_concurrent));

        Self {
            backend,
            semaphore,
            config,
            stats: Arc::new(PoolStats::default()),
            shutting_down: std::sync::atomic::AtomicBool::new(false),
        }
    }

    /// Create with default configuration
    pub fn with_backend(backend: Arc<B>) -> Self {
        Self::new(backend, BackendPoolConfig::default())
    }

    /// Acquire a backend from the pool
    ///
    /// Returns a handle that automatically releases when dropped.
    pub async fn acquire(&self) -> Result<PooledBackend<'_, B>, PoolError> {
        if self.shutting_down.load(Ordering::Relaxed) {
            return Err(PoolError::ShuttingDown);
        }

        self.stats.total_requests.fetch_add(1, Ordering::Relaxed);

        // Check if we need to queue
        let available = self.semaphore.available_permits();
        if available == 0 {
            if !self.config.queue_when_full {
                self.stats.rejected_count.fetch_add(1, Ordering::Relaxed);
                return Err(PoolError::Exhausted);
            }

            // Check queue depth
            if self.config.max_queue_depth > 0 {
                let waiting = self.config.max_concurrent - available;
                if waiting >= self.config.max_queue_depth {
                    self.stats.rejected_count.fetch_add(1, Ordering::Relaxed);
                    return Err(PoolError::Exhausted);
                }
            }

            self.stats.queued_requests.fetch_add(1, Ordering::Relaxed);
        }

        // Try to acquire with timeout
        let permit = tokio::time::timeout(
            self.config.acquire_timeout,
            self.semaphore.acquire(),
        )
        .await
        .map_err(|_| {
            self.stats.timeout_count.fetch_add(1, Ordering::Relaxed);
            PoolError::Timeout(self.config.acquire_timeout)
        })?
        .map_err(|_| PoolError::ShuttingDown)?;

        // Update active count and peak
        let active = self.stats.active_sessions.fetch_add(1, Ordering::Relaxed) + 1;
        let mut peak = self.stats.peak_concurrent.load(Ordering::Relaxed);
        while active > peak {
            match self.stats.peak_concurrent.compare_exchange_weak(
                peak,
                active,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(p) => peak = p,
            }
        }

        Ok(PooledBackend {
            backend: self.backend.clone(),
            _permit: permit,
            stats: self.stats.clone(),
            acquired_at: Instant::now(),
        })
    }

    /// Try to acquire without waiting
    pub fn try_acquire(&self) -> Result<PooledBackend<'_, B>, PoolError> {
        if self.shutting_down.load(Ordering::Relaxed) {
            return Err(PoolError::ShuttingDown);
        }

        self.stats.total_requests.fetch_add(1, Ordering::Relaxed);

        let permit = self.semaphore.try_acquire().map_err(|_| {
            self.stats.rejected_count.fetch_add(1, Ordering::Relaxed);
            PoolError::Exhausted
        })?;

        let active = self.stats.active_sessions.fetch_add(1, Ordering::Relaxed) + 1;
        let mut peak = self.stats.peak_concurrent.load(Ordering::Relaxed);
        while active > peak {
            match self.stats.peak_concurrent.compare_exchange_weak(
                peak,
                active,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(p) => peak = p,
            }
        }

        Ok(PooledBackend {
            backend: self.backend.clone(),
            _permit: permit,
            stats: self.stats.clone(),
            acquired_at: Instant::now(),
        })
    }

    /// Get pool statistics
    pub fn stats(&self) -> PoolStatsSnapshot {
        self.stats.snapshot()
    }

    /// Get current number of active sessions
    pub fn active_count(&self) -> usize {
        self.stats.active_sessions.load(Ordering::Relaxed)
    }

    /// Get number of available slots
    pub fn available(&self) -> usize {
        self.semaphore.available_permits()
    }

    /// Check if pool is at capacity
    pub fn is_full(&self) -> bool {
        self.semaphore.available_permits() == 0
    }

    /// Get the maximum concurrent sessions
    pub fn capacity(&self) -> usize {
        self.config.max_concurrent
    }

    /// Check if pool is healthy (not shutting down and backend ready)
    pub fn is_healthy(&self) -> bool {
        !self.shutting_down.load(Ordering::Relaxed) && self.backend.is_ready()
    }

    /// Initiate graceful shutdown
    pub fn shutdown(&self) {
        self.shutting_down.store(true, Ordering::Relaxed);
    }

    /// Check if pool is shutting down
    pub fn is_shutting_down(&self) -> bool {
        self.shutting_down.load(Ordering::Relaxed)
    }

    /// Wait for all active sessions to complete
    pub async fn drain(&self, timeout: Duration) -> bool {
        self.shutdown();

        let deadline = Instant::now() + timeout;

        while self.active_count() > 0 {
            if Instant::now() > deadline {
                return false;
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }

        true
    }

    /// Get the underlying backend for direct access
    pub fn backend(&self) -> &B {
        &self.backend
    }

    /// Get Arc to the backend
    pub fn backend_arc(&self) -> Arc<B> {
        self.backend.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::server::stt::{BackendCapabilities, BackendInfo, SttResult};
    use crate::server::streaming::{AudioChunk, PartialTranscript, StreamingConfig};
    use async_trait::async_trait;

    #[derive(Debug)]
    struct MockBackend;

    #[async_trait]
    impl SttBackend for MockBackend {
        fn info(&self) -> &BackendInfo {
            static INFO: std::sync::OnceLock<BackendInfo> = std::sync::OnceLock::new();
            INFO.get_or_init(|| BackendInfo {
                name: "mock".to_string(),
                model: "test".to_string(),
                device: "cpu".to_string(),
                capabilities: BackendCapabilities::default(),
            })
        }

        fn is_ready(&self) -> bool {
            true
        }

        async fn transcribe(
            &self,
            _chunk: &AudioChunk,
            _config: &StreamingConfig,
        ) -> SttResult<Vec<PartialTranscript>> {
            Ok(vec![])
        }

        async fn flush(&self, _config: &StreamingConfig) -> SttResult<Vec<PartialTranscript>> {
            Ok(vec![])
        }

        async fn reset(&self) -> SttResult<()> {
            Ok(())
        }
    }

    #[test]
    fn test_config_defaults() {
        let config = BackendPoolConfig::default();
        assert_eq!(config.max_concurrent, 10);
        assert!(config.queue_when_full);
    }

    #[test]
    fn test_config_presets() {
        let high = BackendPoolConfig::high_throughput();
        assert_eq!(high.max_concurrent, 50);

        let low = BackendPoolConfig::low_latency();
        assert_eq!(low.max_concurrent, 5);
        assert!(!low.queue_when_full);
    }

    #[tokio::test]
    async fn test_pool_acquire_release() {
        let backend = Arc::new(MockBackend);
        let pool = BackendPool::new(backend, BackendPoolConfig::default());

        assert_eq!(pool.available(), 10);
        assert_eq!(pool.active_count(), 0);

        {
            let _handle = pool.acquire().await.unwrap();
            assert_eq!(pool.available(), 9);
            assert_eq!(pool.active_count(), 1);
        }

        // After drop, slot is released
        assert_eq!(pool.available(), 10);
        assert_eq!(pool.active_count(), 0);
    }

    #[tokio::test]
    async fn test_pool_stats() {
        let backend = Arc::new(MockBackend);
        let pool = BackendPool::new(backend, BackendPoolConfig::default());

        let _handle = pool.acquire().await.unwrap();
        let stats = pool.stats();

        assert_eq!(stats.total_requests, 1);
        assert_eq!(stats.active_sessions, 1);
        assert_eq!(stats.peak_concurrent, 1);
    }

    #[tokio::test]
    async fn test_pool_try_acquire() {
        let backend = Arc::new(MockBackend);
        let config = BackendPoolConfig {
            max_concurrent: 1,
            ..Default::default()
        };
        let pool = BackendPool::new(backend, config);

        let _handle1 = pool.try_acquire().unwrap();
        let result = pool.try_acquire();

        assert!(matches!(result, Err(PoolError::Exhausted)));
    }

    #[tokio::test]
    async fn test_pool_shutdown() {
        let backend = Arc::new(MockBackend);
        let pool = BackendPool::new(backend, BackendPoolConfig::default());

        assert!(!pool.is_shutting_down());
        pool.shutdown();
        assert!(pool.is_shutting_down());

        let result = pool.acquire().await;
        assert!(matches!(result, Err(PoolError::ShuttingDown)));
    }

    #[test]
    fn test_stats_calculations() {
        let stats = PoolStatsSnapshot {
            total_requests: 100,
            active_sessions: 5,
            queued_requests: 10,
            timeout_count: 2,
            rejected_count: 3,
            total_processing_time_us: 5_000_000, // 5 seconds
            peak_concurrent: 8,
        };

        assert!((stats.avg_processing_time_ms() - 50.0).abs() < 0.01);
        assert!((stats.success_rate() - 0.95).abs() < 0.01);
    }
}
