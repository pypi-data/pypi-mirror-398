use crate::AudioData;

/// Audio statistics and analysis metrics
#[derive(Debug, Clone)]
pub struct AudioStats {
    pub rms: f32,
    pub peak: f32,
    pub peak_db: f32,
    pub rms_db: f32,
    pub zero_crossing_rate: f32,
    pub energy: f32,
}

/// Analyze audio and return statistics
pub fn analyze(audio: &AudioData) -> AudioStats {
    let samples = &audio.samples;

    if samples.is_empty() {
        return AudioStats {
            rms: 0.0,
            peak: 0.0,
            peak_db: -96.0,
            rms_db: -96.0,
            zero_crossing_rate: 0.0,
            energy: 0.0,
        };
    }

    // Calculate RMS (Root Mean Square)
    let sum_squares: f32 = samples.iter().map(|&s| s * s).sum();
    let rms = (sum_squares / samples.len() as f32).sqrt();

    // Calculate peak amplitude
    let peak = samples
        .iter()
        .map(|&s| s.abs())
        .fold(0.0f32, f32::max);

    // Convert to dB
    let rms_db = if rms > 0.0 {
        20.0 * rms.log10()
    } else {
        -96.0
    };

    let peak_db = if peak > 0.0 {
        20.0 * peak.log10()
    } else {
        -96.0
    };

    // Calculate zero crossing rate
    let mut zero_crossings = 0;
    for i in 1..samples.len() {
        if (samples[i] >= 0.0 && samples[i - 1] < 0.0)
            || (samples[i] < 0.0 && samples[i - 1] >= 0.0)
        {
            zero_crossings += 1;
        }
    }
    let zcr = if samples.len() > 1 {
        zero_crossings as f32 / (samples.len() - 1) as f32
    } else {
        0.0
    };

    // Energy is sum of squares
    let energy = sum_squares;

    AudioStats {
        rms,
        peak,
        peak_db,
        rms_db,
        zero_crossing_rate: zcr,
        energy,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_analyze_silence() {
        let audio = AudioData::new(vec![0.0; 1000], 44100, 1);
        let stats = analyze(&audio);

        assert_eq!(stats.rms, 0.0);
        assert_eq!(stats.peak, 0.0);
        assert_eq!(stats.peak_db, -96.0);
        assert_eq!(stats.zero_crossing_rate, 0.0);
        assert_eq!(stats.energy, 0.0);
    }

    #[test]
    fn test_analyze_sine_wave() {
        // Generate a simple sine wave
        let sample_rate = 44100;
        let duration = 1.0; // 1 second
        let frequency = 440.0; // A4 note

        let num_samples = (sample_rate as f32 * duration) as usize;
        let mut samples = Vec::with_capacity(num_samples);

        for i in 0..num_samples {
            let t = i as f32 / sample_rate as f32;
            let sample = (2.0 * std::f32::consts::PI * frequency * t).sin() * 0.5;
            samples.push(sample);
        }

        let audio = AudioData::new(samples, sample_rate, 1);
        let stats = analyze(&audio);

        // For a sine wave at 0.5 amplitude:
        // Peak should be ~0.5
        assert!((stats.peak - 0.5).abs() < 0.01);

        // RMS should be ~0.353 (0.5 / sqrt(2))
        assert!((stats.rms - 0.353).abs() < 0.01);

        // Should have non-zero ZCR
        assert!(stats.zero_crossing_rate > 0.0);
    }
}
