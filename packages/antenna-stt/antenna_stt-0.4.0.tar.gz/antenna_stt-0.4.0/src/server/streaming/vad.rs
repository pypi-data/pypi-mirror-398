//! Streaming Voice Activity Detection (VAD)
//!
//! Provides frame-by-frame voice activity detection for real-time audio streaming.
//! Adapted from the batch-mode silence detection in `audio/silence.rs`.

use parking_lot::Mutex;

/// Voice activity state
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum VoiceState {
    /// Currently detecting silence
    Silence,
    /// Currently detecting speech/voice
    Speech,
    /// Uncertain (transition period)
    Uncertain,
}

/// Result of processing a frame through VAD
#[derive(Debug, Clone)]
pub struct VadFrame {
    /// Whether this frame contains speech
    pub is_speech: bool,
    /// Current voice state
    pub state: VoiceState,
    /// RMS energy of the frame
    pub energy: f32,
    /// Whether a speech segment just ended (good point to process)
    pub segment_ended: bool,
    /// Duration of current segment in seconds
    pub segment_duration: f64,
}

/// Configuration for streaming VAD
#[derive(Debug, Clone)]
pub struct VadConfig {
    /// Sample rate in Hz
    pub sample_rate: u32,
    /// Frame size in samples (typically 10-30ms worth)
    pub frame_size: usize,
    /// Energy threshold in dB (below this is silence)
    pub threshold_db: f32,
    /// Minimum speech duration to trigger segment (seconds)
    pub min_speech_duration: f64,
    /// Minimum silence duration to end segment (seconds)
    pub min_silence_duration: f64,
    /// Hangover frames (continue speech state briefly after energy drops)
    pub hangover_frames: usize,
}

impl Default for VadConfig {
    fn default() -> Self {
        Self {
            sample_rate: 16000,
            frame_size: 480, // 30ms at 16kHz
            threshold_db: -40.0,
            min_speech_duration: 0.25,  // 250ms minimum speech
            min_silence_duration: 0.5,  // 500ms silence to end segment
            hangover_frames: 10,        // ~300ms hangover at 30ms frames
        }
    }
}

impl VadConfig {
    /// Frame duration in seconds
    pub fn frame_duration(&self) -> f64 {
        self.frame_size as f64 / self.sample_rate as f64
    }

    /// Minimum speech frames based on duration
    pub fn min_speech_frames(&self) -> usize {
        (self.min_speech_duration / self.frame_duration()).ceil() as usize
    }

    /// Minimum silence frames based on duration
    pub fn min_silence_frames(&self) -> usize {
        (self.min_silence_duration / self.frame_duration()).ceil() as usize
    }
}

/// Internal state for streaming VAD
#[derive(Debug)]
struct VadState {
    /// Current voice state
    state: VoiceState,
    /// Number of consecutive speech frames
    speech_frames: usize,
    /// Number of consecutive silence frames
    silence_frames: usize,
    /// Hangover counter (frames to stay in speech after energy drops)
    hangover_counter: usize,
    /// Total frames in current segment
    segment_frames: usize,
    /// Whether we're in an active speech segment
    in_segment: bool,
    /// Linear threshold (computed from dB)
    threshold: f32,
}

impl VadState {
    fn new(threshold_db: f32) -> Self {
        Self {
            state: VoiceState::Silence,
            speech_frames: 0,
            silence_frames: 0,
            hangover_counter: 0,
            segment_frames: 0,
            in_segment: false,
            threshold: 10f32.powf(threshold_db / 20.0),
        }
    }

    fn reset(&mut self) {
        self.state = VoiceState::Silence;
        self.speech_frames = 0;
        self.silence_frames = 0;
        self.hangover_counter = 0;
        self.segment_frames = 0;
        self.in_segment = false;
    }
}

/// Streaming Voice Activity Detector
///
/// Processes audio frame-by-frame and detects speech boundaries.
/// Uses energy-based detection with hangover to smooth transitions.
#[derive(Debug)]
pub struct StreamingVad {
    config: VadConfig,
    state: Mutex<VadState>,
}

impl StreamingVad {
    /// Create a new streaming VAD with default config
    pub fn new() -> Self {
        Self::with_config(VadConfig::default())
    }

    /// Create a new streaming VAD with custom config
    pub fn with_config(config: VadConfig) -> Self {
        let state = VadState::new(config.threshold_db);
        Self {
            config,
            state: Mutex::new(state),
        }
    }

    /// Process a frame of audio samples
    ///
    /// # Arguments
    /// * `samples` - Audio samples (mono, f32)
    ///
    /// # Returns
    /// VAD result for this frame
    pub fn process_frame(&self, samples: &[f32]) -> VadFrame {
        let energy = Self::calculate_rms(samples);
        let mut state = self.state.lock();

        let is_speech = energy >= state.threshold;
        let mut segment_ended = false;

        match (state.state, is_speech) {
            // Currently in silence, detected speech
            (VoiceState::Silence, true) => {
                state.speech_frames += 1;
                state.silence_frames = 0;

                if state.speech_frames >= self.config.min_speech_frames() {
                    // Confirmed speech start
                    state.state = VoiceState::Speech;
                    state.in_segment = true;
                    state.segment_frames = state.speech_frames;
                    state.hangover_counter = self.config.hangover_frames;
                } else {
                    state.state = VoiceState::Uncertain;
                }
            }

            // Currently in silence, still silence
            (VoiceState::Silence, false) => {
                state.speech_frames = 0;
                state.silence_frames += 1;
            }

            // Uncertain state, more speech
            (VoiceState::Uncertain, true) => {
                state.speech_frames += 1;
                state.silence_frames = 0;

                if state.speech_frames >= self.config.min_speech_frames() {
                    state.state = VoiceState::Speech;
                    state.in_segment = true;
                    state.segment_frames = state.speech_frames;
                    state.hangover_counter = self.config.hangover_frames;
                }
            }

            // Uncertain state, back to silence
            (VoiceState::Uncertain, false) => {
                state.speech_frames = 0;
                state.silence_frames += 1;
                state.state = VoiceState::Silence;
            }

            // In speech, more speech
            (VoiceState::Speech, true) => {
                state.speech_frames += 1;
                state.silence_frames = 0;
                state.segment_frames += 1;
                state.hangover_counter = self.config.hangover_frames;
            }

            // In speech, silence detected
            (VoiceState::Speech, false) => {
                state.silence_frames += 1;
                state.segment_frames += 1;

                if state.hangover_counter > 0 {
                    // Still in hangover period
                    state.hangover_counter -= 1;
                } else if state.silence_frames >= self.config.min_silence_frames() {
                    // Confirmed end of speech
                    state.state = VoiceState::Silence;
                    state.in_segment = false;
                    segment_ended = true;
                    state.speech_frames = 0;
                }
            }
        }

        let segment_duration = state.segment_frames as f64 * self.config.frame_duration();

        VadFrame {
            is_speech,
            state: state.state,
            energy,
            segment_ended,
            segment_duration,
        }
    }

    /// Check if currently in a speech segment
    pub fn in_segment(&self) -> bool {
        self.state.lock().in_segment
    }

    /// Get current segment duration in seconds
    pub fn segment_duration(&self) -> f64 {
        let state = self.state.lock();
        state.segment_frames as f64 * self.config.frame_duration()
    }

    /// Reset VAD state
    pub fn reset(&self) {
        self.state.lock().reset();
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
}

impl Default for StreamingVad {
    fn default() -> Self {
        Self::new()
    }
}

/// Simple energy-based speech detector for quick checks
pub fn is_speech_frame(samples: &[f32], threshold_db: f32) -> bool {
    let threshold = 10f32.powf(threshold_db / 20.0);
    let rms = StreamingVad::calculate_rms(samples);
    rms >= threshold
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_silence(duration_ms: usize, sample_rate: u32) -> Vec<f32> {
        vec![0.0; (duration_ms * sample_rate as usize) / 1000]
    }

    fn create_speech(duration_ms: usize, sample_rate: u32, amplitude: f32) -> Vec<f32> {
        // Simple sine wave to simulate speech
        let samples = (duration_ms * sample_rate as usize) / 1000;
        (0..samples)
            .map(|i| amplitude * (2.0 * std::f32::consts::PI * 440.0 * i as f32 / sample_rate as f32).sin())
            .collect()
    }

    #[test]
    fn test_vad_config_defaults() {
        let config = VadConfig::default();
        assert_eq!(config.sample_rate, 16000);
        assert_eq!(config.frame_size, 480);
        assert!((config.frame_duration() - 0.03).abs() < 0.001);
    }

    #[test]
    fn test_silence_detection() {
        let vad = StreamingVad::new();
        let silence = create_silence(30, 16000);

        let result = vad.process_frame(&silence);
        assert!(!result.is_speech);
        assert_eq!(result.state, VoiceState::Silence);
    }

    #[test]
    fn test_speech_detection() {
        let config = VadConfig {
            min_speech_duration: 0.06, // 2 frames at 30ms
            ..Default::default()
        };
        let vad = StreamingVad::with_config(config);

        // Process multiple speech frames
        let speech = create_speech(30, 16000, 0.5);
        for _ in 0..5 {
            vad.process_frame(&speech);
        }

        assert!(vad.in_segment());
    }

    #[test]
    fn test_segment_end_detection() {
        let config = VadConfig {
            min_speech_duration: 0.03,  // 1 frame
            min_silence_duration: 0.06, // 2 frames
            hangover_frames: 0,
            ..Default::default()
        };
        let vad = StreamingVad::with_config(config);

        // Start with speech
        let speech = create_speech(30, 16000, 0.5);
        vad.process_frame(&speech);
        vad.process_frame(&speech);

        // Then silence
        let silence = create_silence(30, 16000);
        vad.process_frame(&silence);
        let result = vad.process_frame(&silence);

        assert!(result.segment_ended);
    }

    #[test]
    fn test_reset() {
        let vad = StreamingVad::new();
        let speech = create_speech(30, 16000, 0.5);

        // Build up some state
        for _ in 0..10 {
            vad.process_frame(&speech);
        }
        assert!(vad.in_segment());

        // Reset
        vad.reset();
        assert!(!vad.in_segment());
        assert_eq!(vad.segment_duration(), 0.0);
    }

    #[test]
    fn test_is_speech_frame() {
        let speech = create_speech(30, 16000, 0.5);
        let silence = create_silence(30, 16000);

        assert!(is_speech_frame(&speech, -40.0));
        assert!(!is_speech_frame(&silence, -40.0));
    }
}
