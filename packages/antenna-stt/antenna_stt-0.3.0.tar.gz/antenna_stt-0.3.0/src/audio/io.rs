use crate::{AntennaError, AudioData};
use hound::{WavReader, WavWriter, WavSpec, SampleFormat};
use std::path::Path;
use symphonia::core::audio::SampleBuffer;
use symphonia::core::codecs::DecoderOptions;
use symphonia::core::errors::Error as SymphoniaError;
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::MediaSourceStream;
use symphonia::core::meta::MetadataOptions;
use symphonia::core::probe::Hint;

pub fn load_wav<P: AsRef<Path>>(path: P) -> Result<AudioData, AntennaError> {
    let reader = WavReader::open(path)?;
    
    let spec = reader.spec();
    let sample_rate = spec.sample_rate;
    let channels = spec.channels as u8;
    let bits_per_sample = spec.bits_per_sample;
    
    let samples: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Int => {
            match bits_per_sample {
                8 => {
                    let max_val = (1i32 << 7) as f32;
                    reader
                        .into_samples::<i8>()
                        .map(|s| s.unwrap() as f32 / max_val)
                        .collect()
                }
                16 => {
                    let max_val = (1i32 << 15) as f32;
                    reader
                        .into_samples::<i16>()
                        .map(|s| s.unwrap() as f32 / max_val)
                        .collect()
                }
                24 | 32 => {
                    let max_val = (1i64 << (bits_per_sample - 1)) as f32;
                    reader
                        .into_samples::<i32>()
                        .map(|s| s.unwrap() as f32 / max_val)
                        .collect()
                }
                _ => {
                    return Err(AntennaError::UnsupportedFormat(format!(
                        "Unsupported bit depth: {}",
                        bits_per_sample
                    )))
                }
            }
        }
        hound::SampleFormat::Float => {
            reader
                .into_samples::<f32>()
                .map(|s| s.unwrap())
                .collect()
        }
    };
    
    if samples.is_empty() {
        return Err(AntennaError::InvalidAudio(
            "Audio file contains no samples".to_string(),
        ));
    }
    
    Ok(AudioData::new(samples, sample_rate, channels))
}

/// Detect audio format from file extension
fn detect_format<P: AsRef<Path>>(path: P) -> Option<String> {
    path.as_ref()
        .extension()
        .and_then(|e| e.to_str())
        .map(|s| s.to_lowercase())
}

/// Load audio using Symphonia for multi-format support (MP3, FLAC, OGG, M4A)
pub fn load_audio_symphonia<P: AsRef<Path>>(path: P) -> Result<AudioData, AntennaError> {
    let file = std::fs::File::open(path.as_ref())
        .map_err(|e| AntennaError::IoError(e.to_string()))?;

    let mss = MediaSourceStream::new(Box::new(file), Default::default());

    let mut hint = Hint::new();
    if let Some(ext) = detect_format(&path) {
        hint.with_extension(&ext);
    }

    let format_opts = FormatOptions::default();
    let metadata_opts = MetadataOptions::default();

    let probed = symphonia::default::get_probe()
        .format(&hint, mss, &format_opts, &metadata_opts)
        .map_err(|e| AntennaError::UnsupportedFormat(format!("Failed to probe format: {}", e)))?;

    let mut format = probed.format;
    let track = format
        .default_track()
        .ok_or_else(|| AntennaError::InvalidAudio("No audio track found".to_string()))?;

    let track_id = track.id;
    let codec_params = &track.codec_params;

    let sample_rate = codec_params
        .sample_rate
        .ok_or_else(|| AntennaError::InvalidAudio("No sample rate found".to_string()))?;

    let channels = codec_params
        .channels
        .ok_or_else(|| AntennaError::InvalidAudio("No channel info found".to_string()))?
        .count() as u8;

    let mut decoder = symphonia::default::get_codecs()
        .make(&track.codec_params, &DecoderOptions::default())
        .map_err(|e| AntennaError::UnsupportedFormat(format!("Failed to create decoder: {}", e)))?;

    let mut all_samples = Vec::new();

    loop {
        let packet = match format.next_packet() {
            Ok(packet) => packet,
            Err(SymphoniaError::IoError(_)) => break,
            Err(SymphoniaError::ResetRequired) => {
                return Err(AntennaError::InvalidAudio("Decoder reset required".to_string()));
            }
            Err(_) => break,
        };

        if packet.track_id() != track_id {
            continue;
        }

        match decoder.decode(&packet) {
            Ok(decoded) => {
                let spec = *decoded.spec();
                let duration = decoded.capacity() as u64;

                let mut sample_buffer = SampleBuffer::<f32>::new(duration, spec);
                sample_buffer.copy_interleaved_ref(decoded);

                all_samples.extend_from_slice(sample_buffer.samples());
            }
            Err(SymphoniaError::DecodeError(_)) => continue,
            Err(_) => break,
        }
    }

    if all_samples.is_empty() {
        return Err(AntennaError::InvalidAudio(
            "Audio file contains no samples".to_string(),
        ));
    }

    Ok(AudioData::new(all_samples, sample_rate, channels))
}

/// Load audio from any supported format (auto-detects: WAV, MP3, FLAC, OGG, M4A)
pub fn load_audio<P: AsRef<Path>>(path: P) -> Result<AudioData, AntennaError> {
    let format = detect_format(&path);

    match format.as_deref() {
        Some("wav") => load_wav(&path),
        Some("mp3") | Some("flac") | Some("ogg") | Some("m4a") | Some("aac") => {
            load_audio_symphonia(&path)
        }
        _ => Err(AntennaError::UnsupportedFormat(
            format.unwrap_or_else(|| "unknown".to_string()),
        )),
    }
}

/// Save audio to WAV format
pub fn save_wav<P: AsRef<Path>>(audio: &AudioData, path: P) -> Result<(), AntennaError> {
    let spec = WavSpec {
        channels: audio.channels as u16,
        sample_rate: audio.sample_rate,
        bits_per_sample: 16,
        sample_format: SampleFormat::Int,
    };

    let mut writer = WavWriter::create(path, spec)
        .map_err(|e| AntennaError::IoError(e.to_string()))?;

    for &sample in &audio.samples {
        let sample_i16 = (sample.clamp(-1.0, 1.0) * i16::MAX as f32) as i16;
        writer
            .write_sample(sample_i16)
            .map_err(|e| AntennaError::IoError(e.to_string()))?;
    }

    writer
        .finalize()
        .map_err(|e| AntennaError::IoError(e.to_string()))?;

    Ok(())
}

/// Save audio to file (currently only supports WAV)
pub fn save_audio<P: AsRef<Path>>(audio: &AudioData, path: P) -> Result<(), AntennaError> {
    let format = detect_format(&path);

    match format.as_deref() {
        Some("wav") => save_wav(audio, path),
        _ => Err(AntennaError::UnsupportedFormat(
            "Only WAV export supported in v0.2.0".to_string(),
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hound::{WavSpec, WavWriter};
    use std::fs;
    use std::path::PathBuf;
    
    fn create_test_wav(path: &Path, sample_rate: u32, channels: u16) {
        let spec = WavSpec {
            channels,
            sample_rate,
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        };
        
        let mut writer = WavWriter::create(path, spec).unwrap();
        
        for i in 0..sample_rate {
            let sample = (i as f32 * 0.01).sin() * i16::MAX as f32;
            for _ in 0..channels {
                writer.write_sample(sample as i16).unwrap();
            }
        }
        
        writer.finalize().unwrap();
    }
    
    #[test]
    fn test_load_wav_mono() {
        let test_file = PathBuf::from("/tmp/test_mono.wav");
        create_test_wav(&test_file, 44100, 1);
        
        let audio = load_wav(&test_file).unwrap();
        assert_eq!(audio.sample_rate, 44100);
        assert_eq!(audio.channels, 1);
        assert_eq!(audio.frame_count(), 44100);
        
        fs::remove_file(test_file).ok();
    }
    
    #[test]
    fn test_load_wav_stereo() {
        let test_file = PathBuf::from("/tmp/test_stereo.wav");
        create_test_wav(&test_file, 48000, 2);
        
        let audio = load_wav(&test_file).unwrap();
        assert_eq!(audio.sample_rate, 48000);
        assert_eq!(audio.channels, 2);
        assert_eq!(audio.frame_count(), 48000);
        assert_eq!(audio.samples.len(), 48000 * 2);
        
        fs::remove_file(test_file).ok();
    }
}

