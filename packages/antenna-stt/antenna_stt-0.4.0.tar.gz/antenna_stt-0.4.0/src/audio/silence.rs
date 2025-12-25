use crate::AudioData;

/// Represents a segment of silence in audio
#[derive(Debug, Clone)]
pub struct SilenceSegment {
    pub start: f32, // seconds
    pub end: f32,   // seconds
}

/// Detect silence segments in audio
pub fn detect_silence(
    audio: &AudioData,
    threshold_db: f32,
    min_duration: f32,
) -> Vec<SilenceSegment> {
    let threshold = 10f32.powf(threshold_db / 20.0);
    let min_samples = (min_duration * audio.sample_rate as f32) as usize;
    let frame_count = audio.frame_count();
    let channels = audio.channels as usize;

    let mut segments = Vec::new();
    let mut in_silence = false;
    let mut silence_start = 0;
    let mut silence_length = 0;

    for frame_idx in 0..frame_count {
        // Calculate frame amplitude (max across channels)
        let mut max_amp = 0.0f32;
        for ch in 0..channels {
            let sample = audio.samples[frame_idx * channels + ch].abs();
            if sample > max_amp {
                max_amp = sample;
            }
        }

        let is_silent = max_amp < threshold;

        if is_silent {
            if !in_silence {
                silence_start = frame_idx;
                in_silence = true;
                silence_length = 1;
            } else {
                silence_length += 1;
            }
        } else {
            if in_silence && silence_length >= min_samples {
                let start_sec = silence_start as f32 / audio.sample_rate as f32;
                let end_sec = (silence_start + silence_length) as f32 / audio.sample_rate as f32;
                segments.push(SilenceSegment {
                    start: start_sec,
                    end: end_sec,
                });
            }
            in_silence = false;
            silence_length = 0;
        }
    }

    // Handle trailing silence
    if in_silence && silence_length >= min_samples {
        let start_sec = silence_start as f32 / audio.sample_rate as f32;
        let end_sec = (silence_start + silence_length) as f32 / audio.sample_rate as f32;
        segments.push(SilenceSegment {
            start: start_sec,
            end: end_sec,
        });
    }

    segments
}

/// Trim silence from the beginning and end of audio
pub fn trim_silence(audio: &AudioData, threshold_db: f32) -> AudioData {
    let threshold = 10f32.powf(threshold_db / 20.0);
    let channels = audio.channels as usize;
    let frame_count = audio.frame_count();

    if frame_count == 0 {
        return audio.clone();
    }

    // Find first non-silent frame
    let mut start_frame = None;
    for frame_idx in 0..frame_count {
        let mut max_amp = 0.0f32;
        for ch in 0..channels {
            let sample = audio.samples[frame_idx * channels + ch].abs();
            max_amp = max_amp.max(sample);
        }
        if max_amp >= threshold {
            start_frame = Some(frame_idx);
            break;
        }
    }

    // Find last non-silent frame
    let mut end_frame = None;
    for frame_idx in (0..frame_count).rev() {
        let mut max_amp = 0.0f32;
        for ch in 0..channels {
            let sample = audio.samples[frame_idx * channels + ch].abs();
            max_amp = max_amp.max(sample);
        }
        if max_amp >= threshold {
            end_frame = Some(frame_idx + 1);
            break;
        }
    }

    // If entire audio is silent (no non-silent frames found)
    let (start_frame, end_frame) = match (start_frame, end_frame) {
        (Some(s), Some(e)) => (s, e),
        _ => return AudioData::new(Vec::new(), audio.sample_rate, audio.channels),
    };

    let start_sample = start_frame * channels;
    let end_sample = end_frame * channels;
    let trimmed = audio.samples[start_sample..end_sample].to_vec();

    AudioData::new(trimmed, audio.sample_rate, audio.channels)
}

/// Split audio on silence regions
pub fn split_on_silence(
    audio: &AudioData,
    threshold_db: f32,
    min_silence_duration: f32,
) -> Vec<AudioData> {
    let segments = detect_silence(audio, threshold_db, min_silence_duration);
    let mut chunks = Vec::new();
    let channels = audio.channels as usize;

    let mut last_end = 0;

    for segment in segments {
        let segment_start = (segment.start * audio.sample_rate as f32) as usize;
        if segment_start > last_end {
            let start_sample = last_end * channels;
            let end_sample = segment_start * channels;
            let chunk = audio.samples[start_sample..end_sample].to_vec();
            if !chunk.is_empty() {
                chunks.push(AudioData::new(
                    chunk,
                    audio.sample_rate,
                    audio.channels,
                ));
            }
        }
        last_end = (segment.end * audio.sample_rate as f32) as usize;
    }

    // Add final chunk
    if last_end < audio.frame_count() {
        let start_sample = last_end * channels;
        let chunk = audio.samples[start_sample..].to_vec();
        if !chunk.is_empty() {
            chunks.push(AudioData::new(
                chunk,
                audio.sample_rate,
                audio.channels,
            ));
        }
    }

    // If no chunks were created, return the original audio
    if chunks.is_empty() {
        chunks.push(audio.clone());
    }

    chunks
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_audio_with_silence() -> AudioData {
        let sample_rate = 44100;
        let mut samples = Vec::new();

        // 0.1s silence
        samples.extend(vec![0.0; 4410]);

        // 0.2s audio at 0.5 amplitude
        samples.extend(vec![0.5; 8820]);

        // 0.1s silence
        samples.extend(vec![0.0; 4410]);

        // 0.2s audio at 0.5 amplitude
        samples.extend(vec![0.5; 8820]);

        // 0.1s silence
        samples.extend(vec![0.0; 4410]);

        AudioData::new(samples, sample_rate, 1)
    }

    #[test]
    fn test_detect_silence() {
        let audio = create_test_audio_with_silence();
        let segments = detect_silence(&audio, -40.0, 0.05);

        // Should detect 3 silence segments
        assert!(segments.len() >= 2);
    }

    #[test]
    fn test_trim_silence() {
        let audio = create_test_audio_with_silence();
        let original_duration = audio.duration();

        let trimmed = trim_silence(&audio, -40.0);
        let trimmed_duration = trimmed.duration();

        // Trimmed audio should be shorter
        assert!(trimmed_duration < original_duration);
    }

    #[test]
    fn test_split_on_silence() {
        let audio = create_test_audio_with_silence();
        let chunks = split_on_silence(&audio, -40.0, 0.05);

        // Should split into at least 2 chunks
        assert!(chunks.len() >= 2);
    }

    #[test]
    fn test_trim_all_silence() {
        let audio = AudioData::new(vec![0.0; 1000], 44100, 1);
        let trimmed = trim_silence(&audio, -40.0);

        // Should return empty audio
        assert_eq!(trimmed.samples.len(), 0);
    }
}
