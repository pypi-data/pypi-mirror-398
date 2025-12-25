//! Metrics Collection for STT Server
//!
//! Provides metrics tracking for monitoring and observability.

use parking_lot::Mutex;
use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

/// Histogram for tracking latency distributions
#[derive(Debug)]
pub struct LatencyHistogram {
    /// Buckets for latency ranges (in milliseconds)
    buckets: Vec<AtomicU64>,
    /// Bucket boundaries
    boundaries: Vec<u64>,
    /// Sum of all latencies
    sum_ms: AtomicU64,
    /// Count of samples
    count: AtomicU64,
}

impl LatencyHistogram {
    /// Create a new histogram with default buckets
    ///
    /// Default buckets: 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s
    pub fn new() -> Self {
        let boundaries = vec![10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
        let buckets = (0..=boundaries.len())
            .map(|_| AtomicU64::new(0))
            .collect();

        Self {
            buckets,
            boundaries,
            sum_ms: AtomicU64::new(0),
            count: AtomicU64::new(0),
        }
    }

    /// Create with custom bucket boundaries
    pub fn with_boundaries(boundaries: Vec<u64>) -> Self {
        let buckets = (0..=boundaries.len())
            .map(|_| AtomicU64::new(0))
            .collect();

        Self {
            buckets,
            boundaries,
            sum_ms: AtomicU64::new(0),
            count: AtomicU64::new(0),
        }
    }

    /// Record a latency observation
    pub fn observe(&self, duration: Duration) {
        let ms = duration.as_millis() as u64;

        // Find the appropriate bucket
        let bucket_idx = self
            .boundaries
            .iter()
            .position(|&b| ms <= b)
            .unwrap_or(self.boundaries.len());

        self.buckets[bucket_idx].fetch_add(1, Ordering::Relaxed);
        self.sum_ms.fetch_add(ms, Ordering::Relaxed);
        self.count.fetch_add(1, Ordering::Relaxed);
    }

    /// Get the count of observations
    pub fn count(&self) -> u64 {
        self.count.load(Ordering::Relaxed)
    }

    /// Get the mean latency in milliseconds
    pub fn mean_ms(&self) -> f64 {
        let count = self.count.load(Ordering::Relaxed);
        if count == 0 {
            0.0
        } else {
            self.sum_ms.load(Ordering::Relaxed) as f64 / count as f64
        }
    }

    /// Get bucket counts for export
    pub fn bucket_counts(&self) -> Vec<(String, u64)> {
        let mut result = Vec::new();
        let mut prev = 0u64;

        for (i, &boundary) in self.boundaries.iter().enumerate() {
            let label = format!("{}ms-{}ms", prev, boundary);
            result.push((label, self.buckets[i].load(Ordering::Relaxed)));
            prev = boundary;
        }

        // Overflow bucket
        result.push((
            format!(">{}ms", prev),
            self.buckets[self.boundaries.len()].load(Ordering::Relaxed),
        ));

        result
    }

    /// Estimate a percentile (approximate)
    pub fn percentile(&self, p: f64) -> u64 {
        let count = self.count.load(Ordering::Relaxed);
        if count == 0 {
            return 0;
        }

        let target = (count as f64 * p / 100.0) as u64;
        let mut cumulative = 0u64;

        for (i, bucket) in self.buckets.iter().enumerate() {
            cumulative += bucket.load(Ordering::Relaxed);
            if cumulative >= target {
                if i < self.boundaries.len() {
                    return self.boundaries[i];
                } else {
                    // In overflow bucket, return last boundary * 2
                    return self.boundaries.last().copied().unwrap_or(10000) * 2;
                }
            }
        }

        self.boundaries.last().copied().unwrap_or(10000)
    }
}

impl Default for LatencyHistogram {
    fn default() -> Self {
        Self::new()
    }
}

/// Rolling window for rate calculations
#[derive(Debug)]
struct RollingWindow {
    samples: Mutex<VecDeque<(Instant, u64)>>,
    window_size: Duration,
}

impl RollingWindow {
    fn new(window_size: Duration) -> Self {
        Self {
            samples: Mutex::new(VecDeque::new()),
            window_size,
        }
    }

    fn add(&self, value: u64) {
        let now = Instant::now();
        let mut samples = self.samples.lock();

        // Remove old samples
        let cutoff = now - self.window_size;
        while let Some(&(time, _)) = samples.front() {
            if time < cutoff {
                samples.pop_front();
            } else {
                break;
            }
        }

        samples.push_back((now, value));
    }

    fn rate(&self) -> f64 {
        let now = Instant::now();
        let cutoff = now - self.window_size;
        let samples = self.samples.lock();

        let total: u64 = samples
            .iter()
            .filter(|(time, _)| *time >= cutoff)
            .map(|(_, value)| *value)
            .sum();

        total as f64 / self.window_size.as_secs_f64()
    }
}

/// Comprehensive metrics for the STT server
pub struct Metrics {
    /// Transcription latency histogram
    pub transcription_latency: LatencyHistogram,
    /// First-byte latency (time to first partial result)
    pub first_byte_latency: LatencyHistogram,
    /// Request processing latency
    pub request_latency: LatencyHistogram,

    /// Total transcriptions completed
    pub transcriptions_total: AtomicU64,
    /// Total audio seconds processed
    pub audio_seconds_total: AtomicU64,
    /// Total errors
    pub errors_total: AtomicU64,

    /// Rolling request rate
    request_rate: RollingWindow,
    /// Rolling error rate
    error_rate: RollingWindow,

    /// Server start time
    start_time: Instant,
}

impl Metrics {
    /// Create a new metrics instance
    pub fn new() -> Self {
        Self {
            transcription_latency: LatencyHistogram::new(),
            first_byte_latency: LatencyHistogram::new(),
            request_latency: LatencyHistogram::new(),
            transcriptions_total: AtomicU64::new(0),
            audio_seconds_total: AtomicU64::new(0),
            errors_total: AtomicU64::new(0),
            request_rate: RollingWindow::new(Duration::from_secs(60)),
            error_rate: RollingWindow::new(Duration::from_secs(60)),
            start_time: Instant::now(),
        }
    }

    /// Record a completed transcription
    pub fn record_transcription(&self, latency: Duration, audio_duration: Duration) {
        self.transcription_latency.observe(latency);
        self.transcriptions_total.fetch_add(1, Ordering::Relaxed);
        self.audio_seconds_total
            .fetch_add(audio_duration.as_secs(), Ordering::Relaxed);
        self.request_rate.add(1);
    }

    /// Record first partial result latency
    pub fn record_first_byte(&self, latency: Duration) {
        self.first_byte_latency.observe(latency);
    }

    /// Record request processing latency
    pub fn record_request(&self, latency: Duration) {
        self.request_latency.observe(latency);
        self.request_rate.add(1);
    }

    /// Record an error
    pub fn record_error(&self) {
        self.errors_total.fetch_add(1, Ordering::Relaxed);
        self.error_rate.add(1);
    }

    /// Get current request rate (per second)
    pub fn request_rate(&self) -> f64 {
        self.request_rate.rate()
    }

    /// Get current error rate (per second)
    pub fn error_rate(&self) -> f64 {
        self.error_rate.rate()
    }

    /// Get server uptime
    pub fn uptime(&self) -> Duration {
        self.start_time.elapsed()
    }

    /// Get a snapshot of all metrics
    pub fn snapshot(&self) -> MetricsSnapshot {
        MetricsSnapshot {
            uptime_seconds: self.uptime().as_secs(),
            transcriptions_total: self.transcriptions_total.load(Ordering::Relaxed),
            audio_seconds_total: self.audio_seconds_total.load(Ordering::Relaxed),
            errors_total: self.errors_total.load(Ordering::Relaxed),
            request_rate_per_sec: self.request_rate(),
            error_rate_per_sec: self.error_rate(),
            transcription_latency_p50_ms: self.transcription_latency.percentile(50.0),
            transcription_latency_p95_ms: self.transcription_latency.percentile(95.0),
            transcription_latency_p99_ms: self.transcription_latency.percentile(99.0),
            transcription_latency_mean_ms: self.transcription_latency.mean_ms(),
            first_byte_latency_p50_ms: self.first_byte_latency.percentile(50.0),
            first_byte_latency_p95_ms: self.first_byte_latency.percentile(95.0),
            request_latency_mean_ms: self.request_latency.mean_ms(),
        }
    }
}

impl Default for Metrics {
    fn default() -> Self {
        Self::new()
    }
}

/// Snapshot of metrics for serialization
#[derive(Debug, Clone, serde::Serialize)]
pub struct MetricsSnapshot {
    pub uptime_seconds: u64,
    pub transcriptions_total: u64,
    pub audio_seconds_total: u64,
    pub errors_total: u64,
    pub request_rate_per_sec: f64,
    pub error_rate_per_sec: f64,
    pub transcription_latency_p50_ms: u64,
    pub transcription_latency_p95_ms: u64,
    pub transcription_latency_p99_ms: u64,
    pub transcription_latency_mean_ms: f64,
    pub first_byte_latency_p50_ms: u64,
    pub first_byte_latency_p95_ms: u64,
    pub request_latency_mean_ms: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_histogram_observe() {
        let histogram = LatencyHistogram::new();

        histogram.observe(Duration::from_millis(5));
        histogram.observe(Duration::from_millis(50));
        histogram.observe(Duration::from_millis(500));

        assert_eq!(histogram.count(), 3);
    }

    #[test]
    fn test_histogram_mean() {
        let histogram = LatencyHistogram::new();

        histogram.observe(Duration::from_millis(100));
        histogram.observe(Duration::from_millis(200));
        histogram.observe(Duration::from_millis(300));

        assert!((histogram.mean_ms() - 200.0).abs() < 0.01);
    }

    #[test]
    fn test_histogram_buckets() {
        let histogram = LatencyHistogram::new();

        histogram.observe(Duration::from_millis(5));   // 0-10ms bucket
        histogram.observe(Duration::from_millis(15));  // 10-25ms bucket
        histogram.observe(Duration::from_millis(1500)); // 1000-2500ms bucket

        let buckets = histogram.bucket_counts();
        assert!(buckets.len() > 0);
    }

    #[test]
    fn test_metrics_record() {
        let metrics = Metrics::new();

        metrics.record_transcription(Duration::from_millis(100), Duration::from_secs(5));
        metrics.record_error();

        assert_eq!(metrics.transcriptions_total.load(Ordering::Relaxed), 1);
        assert_eq!(metrics.audio_seconds_total.load(Ordering::Relaxed), 5);
        assert_eq!(metrics.errors_total.load(Ordering::Relaxed), 1);
    }

    #[test]
    fn test_metrics_snapshot() {
        let metrics = Metrics::new();

        metrics.record_transcription(Duration::from_millis(100), Duration::from_secs(10));

        let snapshot = metrics.snapshot();
        assert_eq!(snapshot.transcriptions_total, 1);
        assert_eq!(snapshot.audio_seconds_total, 10);
    }

    #[test]
    fn test_percentile_empty() {
        let histogram = LatencyHistogram::new();
        assert_eq!(histogram.percentile(50.0), 0);
    }

    #[test]
    fn test_percentile_multiple_values() {
        let histogram = LatencyHistogram::new();
        // Add 10 values at 100ms
        for _ in 0..10 {
            histogram.observe(Duration::from_millis(100));
        }

        // All values are at 100ms, so p50 and p95 should both return 100
        assert_eq!(histogram.percentile(50.0), 100);
        assert_eq!(histogram.percentile(95.0), 100);
    }
}
