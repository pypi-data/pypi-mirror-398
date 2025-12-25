use crate::{AntennaError, AudioData};
use rubato::{
    Resampler, SincFixedIn, SincInterpolationParameters, SincInterpolationType, WindowFunction,
};

pub fn convert_to_mono(audio: &AudioData) -> AudioData {
    if audio.channels == 1 {
        return audio.clone();
    }
    
    let channels = audio.channels as usize;
    let frame_count = audio.frame_count();
    let mut mono_samples = Vec::with_capacity(frame_count);
    
    for frame_idx in 0..frame_count {
        let mut sum = 0.0;
        for ch in 0..channels {
            sum += audio.samples[frame_idx * channels + ch];
        }
        mono_samples.push(sum / channels as f32);
    }
    
    AudioData::new(mono_samples, audio.sample_rate, 1)
}

pub fn resample(audio: &AudioData, target_rate: u32) -> Result<AudioData, AntennaError> {
    if audio.sample_rate == target_rate {
        return Ok(audio.clone());
    }
    
    let resample_ratio = target_rate as f64 / audio.sample_rate as f64;
    let channels = audio.channels as usize;
    
    let params = SincInterpolationParameters {
        sinc_len: 256,
        f_cutoff: 0.95,
        interpolation: SincInterpolationType::Linear,
        oversampling_factor: 256,
        window: WindowFunction::BlackmanHarris2,
    };
    
    let chunk_size = 1024;
    let mut resampler = SincFixedIn::<f32>::new(
        resample_ratio,
        2.0,
        params,
        chunk_size,
        channels,
    )
    .map_err(|e| AntennaError::PreprocessingError(format!("Resampler creation failed: {}", e)))?;
    
    let frame_count = audio.frame_count();
    let mut input_frames = vec![vec![0.0f32; frame_count]; channels];
    
    for ch in 0..channels {
        for frame_idx in 0..frame_count {
            input_frames[ch][frame_idx] = audio.samples[frame_idx * channels + ch];
        }
    }
    
    let mut output_frames = Vec::new();
    let mut input_pos = 0;
    
    while input_pos < frame_count {
        let end_pos = (input_pos + chunk_size).min(frame_count);
        let chunk_len = end_pos - input_pos;
        let is_last_chunk = end_pos >= frame_count;
        
        let mut chunk_data = vec![vec![0.0f32; chunk_size]; channels];
        for ch in 0..channels {
            chunk_data[ch][..chunk_len].copy_from_slice(&input_frames[ch][input_pos..end_pos]);
        }
        
        let end_of_input_vec = vec![true; channels];
        let end_of_input = if is_last_chunk {
            Some(end_of_input_vec.as_slice())
        } else {
            None
        };
        
        let output_chunk = resampler
            .process(&chunk_data, end_of_input)
            .map_err(|e| {
                AntennaError::PreprocessingError(format!("Resampling failed: {}", e))
            })?;
        
        output_frames.push(output_chunk);
        input_pos += chunk_len;
    }
    
    let total_output_frames: usize = output_frames.iter().map(|chunk| chunk[0].len()).sum();
    let mut output_samples = vec![0.0f32; total_output_frames * channels];
    
    let mut output_pos = 0;
    for chunk in output_frames {
        let chunk_frames = chunk[0].len();
        for frame_idx in 0..chunk_frames {
            for ch in 0..channels {
                output_samples[output_pos * channels + ch] = chunk[ch][frame_idx];
            }
            output_pos += 1;
        }
    }
    
    Ok(AudioData::new(output_samples, target_rate, audio.channels))
}

/// Normalization method
#[derive(Debug, Clone, Copy)]
pub enum NormalizationMethod {
    Peak,
    Rms,
    Lufs,
}

/// Normalize audio to a target level in dB
pub fn normalize(
    audio: &AudioData,
    method: NormalizationMethod,
    target_db: f32,
) -> AudioData {
    if audio.samples.is_empty() {
        return audio.clone();
    }

    let current_level = match method {
        NormalizationMethod::Peak => {
            let peak = audio
                .samples
                .iter()
                .map(|&s| s.abs())
                .fold(0.0f32, f32::max);
            if peak > 0.0 {
                20.0 * peak.log10()
            } else {
                -96.0
            }
        }
        NormalizationMethod::Rms => {
            let sum_squares: f32 = audio.samples.iter().map(|&s| s * s).sum();
            let rms = (sum_squares / audio.samples.len() as f32).sqrt();
            if rms > 0.0 {
                20.0 * rms.log10()
            } else {
                -96.0
            }
        }
        NormalizationMethod::Lufs => {
            // Simplified LUFS calculation
            // Full implementation would require K-weighting filter
            let sum_squares: f32 = audio.samples.iter().map(|&s| s * s).sum();
            let rms = (sum_squares / audio.samples.len() as f32).sqrt();
            if rms > 0.0 {
                -23.0 + 20.0 * rms.log10() // Approximate LUFS
            } else {
                -96.0
            }
        }
    };

    let gain_db = target_db - current_level;
    let gain_linear = 10f32.powf(gain_db / 20.0);

    let normalized: Vec<f32> = audio
        .samples
        .iter()
        .map(|&s| (s * gain_linear).clamp(-1.0, 1.0))
        .collect();

    AudioData::new(normalized, audio.sample_rate, audio.channels)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_convert_to_mono_already_mono() {
        let audio = AudioData::new(vec![0.1, 0.2, 0.3], 44100, 1);
        let mono = convert_to_mono(&audio);
        
        assert_eq!(mono.channels, 1);
        assert_eq!(mono.samples.len(), 3);
        assert_eq!(mono.samples, audio.samples);
    }
    
    #[test]
    fn test_convert_to_mono_from_stereo() {
        let audio = AudioData::new(
            vec![0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            44100,
            2,
        );
        let mono = convert_to_mono(&audio);
        
        assert_eq!(mono.channels, 1);
        assert_eq!(mono.samples.len(), 3);
        assert!((mono.samples[0] - 0.15).abs() < 1e-6);
        assert!((mono.samples[1] - 0.35).abs() < 1e-6);
        assert!((mono.samples[2] - 0.55).abs() < 1e-6);
    }
    
    #[test]
    fn test_resample_no_change() {
        let samples = vec![0.1, 0.2, 0.3, 0.4];
        let audio = AudioData::new(samples.clone(), 16000, 1);
        let resampled = resample(&audio, 16000).unwrap();
        
        assert_eq!(resampled.sample_rate, 16000);
        assert_eq!(resampled.samples, samples);
    }
    
    #[test]
    fn test_resample_downsample() {
        let mut samples = Vec::new();
        for i in 0..44100 {
            samples.push((i as f32 * 0.01).sin());
        }
        let audio = AudioData::new(samples, 44100, 1);
        let resampled = resample(&audio, 16000).unwrap();
        
        assert_eq!(resampled.sample_rate, 16000);
        assert_eq!(resampled.channels, 1);
        
        let expected_frames = (16000.0 / 44100.0 * 44100.0) as usize;
        let actual_frames = resampled.frame_count();
        let tolerance = expected_frames / 10;
        assert!(
            (actual_frames as i32 - expected_frames as i32).abs() < tolerance as i32,
            "Expected ~{} frames, got {}",
            expected_frames,
            actual_frames
        );
    }
    
    #[test]
    fn test_resample_upsample() {
        let mut samples = Vec::new();
        for i in 0..16000 {
            samples.push((i as f32 * 0.01).sin());
        }
        let audio = AudioData::new(samples, 16000, 1);
        let resampled = resample(&audio, 44100).unwrap();
        
        assert_eq!(resampled.sample_rate, 44100);
        assert_eq!(resampled.channels, 1);
        
        let expected_frames = (44100.0 / 16000.0 * 16000.0) as usize;
        let actual_frames = resampled.frame_count();
        let tolerance = expected_frames / 10;
        assert!(
            (actual_frames as i32 - expected_frames as i32).abs() < tolerance as i32,
            "Expected ~{} frames, got {}",
            expected_frames,
            actual_frames
        );
    }
}

