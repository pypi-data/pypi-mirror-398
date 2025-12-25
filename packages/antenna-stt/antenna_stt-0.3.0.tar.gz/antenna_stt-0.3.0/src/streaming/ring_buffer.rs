//! Ring buffer for streaming audio
//!
//! Provides an efficient circular buffer for accumulating audio samples
//! during real-time streaming. Supports overlapping windows for context
//! preservation during chunk-based processing.

use std::collections::VecDeque;

/// A ring buffer for audio samples with support for overlapping reads
#[derive(Debug)]
pub struct AudioRingBuffer {
    /// Internal buffer using VecDeque for efficient push/pop
    buffer: VecDeque<f32>,
    /// Maximum capacity in samples
    capacity: usize,
    /// Sample rate of the audio
    sample_rate: u32,
    /// Number of samples to keep as overlap when reading
    overlap_samples: usize,
}

impl AudioRingBuffer {
    /// Create a new ring buffer
    ///
    /// # Arguments
    /// * `capacity_seconds` - Maximum duration of audio to buffer (seconds)
    /// * `sample_rate` - Sample rate in Hz
    /// * `overlap_seconds` - Overlap duration for context preservation (seconds)
    pub fn new(capacity_seconds: f64, sample_rate: u32, overlap_seconds: f64) -> Self {
        let capacity = (capacity_seconds * sample_rate as f64) as usize;
        let overlap_samples = (overlap_seconds * sample_rate as f64) as usize;

        Self {
            buffer: VecDeque::with_capacity(capacity),
            capacity,
            sample_rate,
            overlap_samples,
        }
    }

    /// Create a buffer with default settings (60s capacity, 0.5s overlap)
    pub fn with_defaults(sample_rate: u32) -> Self {
        Self::new(60.0, sample_rate, 0.5)
    }

    /// Push samples into the buffer
    ///
    /// If the buffer exceeds capacity, oldest samples are discarded.
    pub fn push(&mut self, samples: &[f32]) {
        // Add new samples
        self.buffer.extend(samples.iter().copied());

        // Trim to capacity if needed
        while self.buffer.len() > self.capacity {
            self.buffer.pop_front();
        }
    }

    /// Get the current number of samples in the buffer
    pub fn len(&self) -> usize {
        self.buffer.len()
    }

    /// Check if the buffer is empty
    pub fn is_empty(&self) -> bool {
        self.buffer.is_empty()
    }

    /// Get the duration of audio in the buffer (seconds)
    pub fn duration(&self) -> f64 {
        self.len() as f64 / self.sample_rate as f64
    }

    /// Read samples from the buffer without consuming them
    ///
    /// Returns a copy of the samples. Useful for peeking at audio.
    pub fn peek(&self, num_samples: usize) -> Vec<f32> {
        self.buffer.iter().take(num_samples).copied().collect()
    }

    /// Read and consume samples from the buffer
    ///
    /// Keeps `overlap_samples` at the end for context preservation.
    pub fn read(&mut self, num_samples: usize) -> Vec<f32> {
        let available = self.buffer.len();
        let to_read = num_samples.min(available);

        // Drain the requested samples
        self.buffer.drain(..to_read).collect()
    }

    /// Read all samples from the buffer (for final flush)
    pub fn read_all(&mut self) -> Vec<f32> {
        self.buffer.drain(..).collect()
    }

    /// Read samples with overlap preservation
    ///
    /// Returns requested samples but keeps overlap_samples in the buffer
    /// for context in the next read.
    pub fn read_with_overlap(&mut self, num_samples: usize) -> Vec<f32> {
        let available = self.buffer.len();
        let keep = self.overlap_samples.min(available);
        let max_read = available.saturating_sub(keep);
        let to_read = num_samples.min(max_read);

        if to_read == 0 {
            return vec![];
        }

        // Drain samples, keeping overlap
        self.buffer.drain(..to_read).collect()
    }

    /// Clear the buffer
    pub fn clear(&mut self) {
        self.buffer.clear();
    }

    /// Get the sample rate
    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    /// Get the capacity in samples
    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// Get the overlap size in samples
    pub fn overlap_samples(&self) -> usize {
        self.overlap_samples
    }

    /// Get capacity in seconds
    pub fn capacity_seconds(&self) -> f64 {
        self.capacity as f64 / self.sample_rate as f64
    }

    /// Get overlap in seconds
    pub fn overlap_seconds(&self) -> f64 {
        self.overlap_samples as f64 / self.sample_rate as f64
    }
}

/// Builder for AudioRingBuffer with fluent API
#[derive(Debug, Clone)]
pub struct AudioRingBufferBuilder {
    capacity_seconds: f64,
    sample_rate: u32,
    overlap_seconds: f64,
}

impl AudioRingBufferBuilder {
    pub fn new(sample_rate: u32) -> Self {
        Self {
            capacity_seconds: 60.0,
            sample_rate,
            overlap_seconds: 0.5,
        }
    }

    pub fn capacity_seconds(mut self, seconds: f64) -> Self {
        self.capacity_seconds = seconds;
        self
    }

    pub fn overlap_seconds(mut self, seconds: f64) -> Self {
        self.overlap_seconds = seconds;
        self
    }

    pub fn build(self) -> AudioRingBuffer {
        AudioRingBuffer::new(self.capacity_seconds, self.sample_rate, self.overlap_seconds)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_buffer_creation() {
        let buffer = AudioRingBuffer::new(10.0, 16000, 0.5);
        assert_eq!(buffer.sample_rate(), 16000);
        assert_eq!(buffer.capacity(), 160000);
        assert_eq!(buffer.overlap_samples(), 8000);
    }

    #[test]
    fn test_push_and_len() {
        let mut buffer = AudioRingBuffer::new(1.0, 16000, 0.0);

        buffer.push(&[1.0, 2.0, 3.0]);
        assert_eq!(buffer.len(), 3);

        buffer.push(&[4.0, 5.0]);
        assert_eq!(buffer.len(), 5);
    }

    #[test]
    fn test_capacity_limit() {
        let mut buffer = AudioRingBuffer::new(0.001, 1000, 0.0); // 1 sample capacity
        assert_eq!(buffer.capacity(), 1);

        buffer.push(&[1.0, 2.0, 3.0]);
        assert_eq!(buffer.len(), 1);

        let samples = buffer.read_all();
        assert_eq!(samples, vec![3.0]); // Only last sample kept
    }

    #[test]
    fn test_read() {
        let mut buffer = AudioRingBuffer::new(1.0, 16000, 0.0);
        buffer.push(&[1.0, 2.0, 3.0, 4.0, 5.0]);

        let samples = buffer.read(3);
        assert_eq!(samples, vec![1.0, 2.0, 3.0]);
        assert_eq!(buffer.len(), 2);

        let remaining = buffer.read_all();
        assert_eq!(remaining, vec![4.0, 5.0]);
    }

    #[test]
    fn test_read_with_overlap() {
        let mut buffer = AudioRingBuffer::new(1.0, 1000, 0.002); // 2 sample overlap
        buffer.push(&[1.0, 2.0, 3.0, 4.0, 5.0]);

        let samples = buffer.read_with_overlap(10); // Try to read more than available
        assert_eq!(samples, vec![1.0, 2.0, 3.0]); // 5 - 2 overlap = 3
        assert_eq!(buffer.len(), 2); // Overlap preserved
    }

    #[test]
    fn test_peek() {
        let mut buffer = AudioRingBuffer::new(1.0, 16000, 0.0);
        buffer.push(&[1.0, 2.0, 3.0]);

        let peeked = buffer.peek(2);
        assert_eq!(peeked, vec![1.0, 2.0]);
        assert_eq!(buffer.len(), 3); // Not consumed
    }

    #[test]
    fn test_duration() {
        let mut buffer = AudioRingBuffer::new(10.0, 16000, 0.0);
        buffer.push(&vec![0.0; 16000]); // 1 second of audio
        assert!((buffer.duration() - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_builder() {
        let buffer = AudioRingBufferBuilder::new(16000)
            .capacity_seconds(30.0)
            .overlap_seconds(1.0)
            .build();

        assert_eq!(buffer.capacity(), 480000);
        assert_eq!(buffer.overlap_samples(), 16000);
    }

    #[test]
    fn test_clear() {
        let mut buffer = AudioRingBuffer::new(1.0, 16000, 0.0);
        buffer.push(&[1.0, 2.0, 3.0]);
        buffer.clear();
        assert!(buffer.is_empty());
    }

    #[test]
    fn test_capacity_and_overlap_seconds() {
        let buffer = AudioRingBuffer::new(10.0, 16000, 0.5);
        assert!((buffer.capacity_seconds() - 10.0).abs() < 0.001);
        assert!((buffer.overlap_seconds() - 0.5).abs() < 0.001);
    }
}
