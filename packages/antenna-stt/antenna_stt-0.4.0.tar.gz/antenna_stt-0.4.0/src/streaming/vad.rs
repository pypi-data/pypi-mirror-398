//! Simple Voice Activity Detection for streaming

/// Voice activity state
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VoiceState {
    /// Currently detecting silence
    Silence,
    /// Currently detecting speech
    Speech,
}

/// Configuration for VAD
#[derive(Debug, Clone)]
pub struct VadConfig {
    /// Sample rate in Hz
    pub sample_rate: u32,
    /// Energy threshold in dB (below this is silence)
    pub threshold_db: f32,
    /// Minimum speech duration to trigger segment (seconds)
    pub min_speech_duration: f64,
    /// Minimum silence duration to end segment (seconds)
    pub min_silence_duration: f64,
}

impl Default for VadConfig {
    fn default() -> Self {
        Self {
            sample_rate: 16000,
            threshold_db: -40.0,
            min_speech_duration: 0.25,
            min_silence_duration: 0.5,
        }
    }
}

/// Simple energy-based Voice Activity Detector
#[derive(Debug)]
pub struct SimpleVad {
    config: VadConfig,
    /// Linear threshold (computed from dB)
    threshold: f32,
    /// Current state
    state: VoiceState,
    /// Consecutive speech samples
    speech_samples: usize,
    /// Consecutive silence samples
    silence_samples: usize,
    /// Current segment sample count
    segment_samples: usize,
    /// Whether we're in an active segment
    in_segment: bool,
}

impl SimpleVad {
    /// Create a new VAD with default config
    pub fn new() -> Self {
        Self::with_config(VadConfig::default())
    }

    /// Create a new VAD with custom config
    pub fn with_config(config: VadConfig) -> Self {
        let threshold = 10f32.powf(config.threshold_db / 20.0);
        Self {
            config,
            threshold,
            state: VoiceState::Silence,
            speech_samples: 0,
            silence_samples: 0,
            segment_samples: 0,
            in_segment: false,
        }
    }

    /// Process audio samples and return (state_changed, segment_ended)
    ///
    /// # Returns
    /// - `state_changed`: true if voice state changed
    /// - `segment_ended`: true if a speech segment just ended (good time to transcribe)
    pub fn process(&mut self, samples: &[f32]) -> (bool, bool) {
        let energy = Self::calculate_rms(samples);
        let is_speech = energy >= self.threshold;

        let min_speech_samples =
            (self.config.min_speech_duration * self.config.sample_rate as f64) as usize;
        let min_silence_samples =
            (self.config.min_silence_duration * self.config.sample_rate as f64) as usize;

        let prev_state = self.state;
        let mut segment_ended = false;

        if is_speech {
            self.speech_samples += samples.len();
            self.silence_samples = 0;

            if self.speech_samples >= min_speech_samples && !self.in_segment {
                self.state = VoiceState::Speech;
                self.in_segment = true;
                self.segment_samples = self.speech_samples;
            } else if self.in_segment {
                self.segment_samples += samples.len();
            }
        } else {
            self.silence_samples += samples.len();

            if self.in_segment {
                self.segment_samples += samples.len();

                if self.silence_samples >= min_silence_samples {
                    self.state = VoiceState::Silence;
                    self.in_segment = false;
                    segment_ended = true;
                    self.speech_samples = 0;
                }
            } else {
                self.speech_samples = 0;
            }
        }

        let state_changed = self.state != prev_state;
        (state_changed, segment_ended)
    }

    /// Get current voice state
    pub fn state(&self) -> VoiceState {
        self.state
    }

    /// Check if currently in a speech segment
    pub fn in_segment(&self) -> bool {
        self.in_segment
    }

    /// Get current segment duration in seconds
    pub fn segment_duration(&self) -> f64 {
        self.segment_samples as f64 / self.config.sample_rate as f64
    }

    /// Reset VAD state
    pub fn reset(&mut self) {
        self.state = VoiceState::Silence;
        self.speech_samples = 0;
        self.silence_samples = 0;
        self.segment_samples = 0;
        self.in_segment = false;
    }

    /// Get the configuration
    pub fn config(&self) -> &VadConfig {
        &self.config
    }

    /// Calculate RMS energy of samples
    fn calculate_rms(samples: &[f32]) -> f32 {
        if samples.is_empty() {
            return 0.0;
        }
        let sum_sq: f32 = samples.iter().map(|s| s * s).sum();
        (sum_sq / samples.len() as f32).sqrt()
    }

    /// Check if a single frame contains speech (stateless check)
    pub fn is_speech_frame(samples: &[f32], threshold_db: f32) -> bool {
        let threshold = 10f32.powf(threshold_db / 20.0);
        Self::calculate_rms(samples) >= threshold
    }
}

impl Default for SimpleVad {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_silence(duration_ms: usize, sample_rate: u32) -> Vec<f32> {
        vec![0.0; (duration_ms * sample_rate as usize) / 1000]
    }

    fn create_speech(duration_ms: usize, sample_rate: u32, amplitude: f32) -> Vec<f32> {
        let samples = (duration_ms * sample_rate as usize) / 1000;
        (0..samples)
            .map(|i| {
                amplitude
                    * (2.0 * std::f32::consts::PI * 440.0 * i as f32 / sample_rate as f32).sin()
            })
            .collect()
    }

    #[test]
    fn test_vad_creation() {
        let vad = SimpleVad::new();
        assert_eq!(vad.state(), VoiceState::Silence);
        assert!(!vad.in_segment());
    }

    #[test]
    fn test_silence_detection() {
        let mut vad = SimpleVad::new();
        let silence = create_silence(500, 16000);

        let (changed, ended) = vad.process(&silence);
        assert!(!changed);
        assert!(!ended);
        assert_eq!(vad.state(), VoiceState::Silence);
    }

    #[test]
    fn test_speech_detection() {
        let config = VadConfig {
            min_speech_duration: 0.1, // 100ms
            ..Default::default()
        };
        let mut vad = SimpleVad::with_config(config);

        // Process speech for 150ms (more than min_speech_duration)
        let speech = create_speech(150, 16000, 0.5);
        let (changed, _) = vad.process(&speech);

        assert!(changed);
        assert_eq!(vad.state(), VoiceState::Speech);
        assert!(vad.in_segment());
    }

    #[test]
    fn test_segment_end() {
        let config = VadConfig {
            min_speech_duration: 0.05,  // 50ms
            min_silence_duration: 0.1,  // 100ms
            ..Default::default()
        };
        let mut vad = SimpleVad::with_config(config);

        // Start with speech
        let speech = create_speech(100, 16000, 0.5);
        vad.process(&speech);
        assert!(vad.in_segment());

        // Then silence
        let silence = create_silence(150, 16000);
        let (_, segment_ended) = vad.process(&silence);

        assert!(segment_ended);
        assert!(!vad.in_segment());
    }

    #[test]
    fn test_reset() {
        let mut vad = SimpleVad::new();
        let speech = create_speech(500, 16000, 0.5);
        vad.process(&speech);

        vad.reset();
        assert_eq!(vad.state(), VoiceState::Silence);
        assert!(!vad.in_segment());
        assert_eq!(vad.segment_duration(), 0.0);
    }

    #[test]
    fn test_is_speech_frame() {
        let speech = create_speech(30, 16000, 0.5);
        let silence = create_silence(30, 16000);

        assert!(SimpleVad::is_speech_frame(&speech, -40.0));
        assert!(!SimpleVad::is_speech_frame(&silence, -40.0));
    }

    #[test]
    fn test_segment_duration() {
        let config = VadConfig {
            min_speech_duration: 0.05,
            sample_rate: 16000,
            ..Default::default()
        };
        let mut vad = SimpleVad::with_config(config);

        // 200ms of speech
        let speech = create_speech(200, 16000, 0.5);
        vad.process(&speech);

        // Duration should be close to 200ms
        let duration = vad.segment_duration();
        assert!((duration - 0.2).abs() < 0.01);
    }
}
