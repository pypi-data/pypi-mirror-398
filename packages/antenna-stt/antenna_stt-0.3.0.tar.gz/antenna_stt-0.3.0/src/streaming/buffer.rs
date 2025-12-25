//! Audio buffer for streaming transcription

use std::collections::VecDeque;

/// Simple audio buffer for accumulating samples
#[derive(Debug)]
pub struct AudioBuffer {
    /// Internal sample storage
    samples: VecDeque<f32>,
    /// Sample rate
    sample_rate: u32,
    /// Maximum capacity in samples
    capacity: usize,
}

impl AudioBuffer {
    /// Create a new audio buffer
    ///
    /// # Arguments
    /// * `max_duration` - Maximum audio duration to store (seconds)
    /// * `sample_rate` - Audio sample rate (Hz)
    pub fn new(max_duration: f64, sample_rate: u32) -> Self {
        let capacity = (max_duration * sample_rate as f64) as usize;
        Self {
            samples: VecDeque::with_capacity(capacity),
            sample_rate,
            capacity,
        }
    }

    /// Create a buffer with default settings (60s capacity at 16kHz)
    pub fn with_defaults() -> Self {
        Self::new(60.0, 16000)
    }

    /// Push samples into the buffer
    ///
    /// If capacity is exceeded, oldest samples are discarded.
    pub fn push(&mut self, samples: &[f32]) {
        self.samples.extend(samples.iter().copied());

        // Trim to capacity if needed
        while self.samples.len() > self.capacity {
            self.samples.pop_front();
        }
    }

    /// Get current number of samples
    pub fn len(&self) -> usize {
        self.samples.len()
    }

    /// Check if buffer is empty
    pub fn is_empty(&self) -> bool {
        self.samples.is_empty()
    }

    /// Get duration of buffered audio in seconds
    pub fn duration(&self) -> f64 {
        self.samples.len() as f64 / self.sample_rate as f64
    }

    /// Read and consume samples from the buffer
    pub fn read(&mut self, num_samples: usize) -> Vec<f32> {
        let to_read = num_samples.min(self.samples.len());
        self.samples.drain(..to_read).collect()
    }

    /// Read all samples from the buffer (clears it)
    pub fn read_all(&mut self) -> Vec<f32> {
        self.samples.drain(..).collect()
    }

    /// Peek at samples without consuming them
    pub fn peek(&self, num_samples: usize) -> Vec<f32> {
        self.samples.iter().take(num_samples).copied().collect()
    }

    /// Peek at all samples
    pub fn peek_all(&self) -> Vec<f32> {
        self.samples.iter().copied().collect()
    }

    /// Clear the buffer
    pub fn clear(&mut self) {
        self.samples.clear();
    }

    /// Get the sample rate
    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    /// Get capacity in samples
    pub fn capacity(&self) -> usize {
        self.capacity
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_buffer_creation() {
        let buffer = AudioBuffer::new(10.0, 16000);
        assert_eq!(buffer.sample_rate(), 16000);
        assert_eq!(buffer.capacity(), 160000);
        assert!(buffer.is_empty());
    }

    #[test]
    fn test_push_and_read() {
        let mut buffer = AudioBuffer::new(1.0, 1000);
        buffer.push(&[1.0, 2.0, 3.0, 4.0, 5.0]);

        assert_eq!(buffer.len(), 5);
        assert!((buffer.duration() - 0.005).abs() < 0.0001);

        let samples = buffer.read(3);
        assert_eq!(samples, vec![1.0, 2.0, 3.0]);
        assert_eq!(buffer.len(), 2);
    }

    #[test]
    fn test_capacity_enforcement() {
        let mut buffer = AudioBuffer::new(0.003, 1000); // 3 samples
        buffer.push(&[1.0, 2.0, 3.0, 4.0, 5.0]);

        assert_eq!(buffer.len(), 3);
        let samples = buffer.read_all();
        assert_eq!(samples, vec![3.0, 4.0, 5.0]); // Oldest dropped
    }

    #[test]
    fn test_peek() {
        let mut buffer = AudioBuffer::new(1.0, 1000);
        buffer.push(&[1.0, 2.0, 3.0]);

        let peeked = buffer.peek(2);
        assert_eq!(peeked, vec![1.0, 2.0]);
        assert_eq!(buffer.len(), 3); // Not consumed
    }

    #[test]
    fn test_clear() {
        let mut buffer = AudioBuffer::new(1.0, 1000);
        buffer.push(&[1.0, 2.0, 3.0]);
        buffer.clear();
        assert!(buffer.is_empty());
    }
}
