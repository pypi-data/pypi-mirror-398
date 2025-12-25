//! Distil-Whisper configuration
//!
//! Configuration for distilled Whisper models from HuggingFace.

/// Distil-Whisper model size variants
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DistilWhisperSize {
    /// distil-small.en - English only, ~166M params
    DistilSmallEn,
    /// distil-medium.en - English only, ~394M params
    DistilMediumEn,
    /// distil-large-v2 - Multilingual, ~756M params
    DistilLargeV2,
    /// distil-large-v3 - Multilingual, ~756M params
    DistilLargeV3,
}

impl DistilWhisperSize {
    /// Get the HuggingFace model ID for this size
    pub fn model_id(&self) -> &'static str {
        match self {
            DistilWhisperSize::DistilSmallEn => "distil-whisper/distil-small.en",
            DistilWhisperSize::DistilMediumEn => "distil-whisper/distil-medium.en",
            DistilWhisperSize::DistilLargeV2 => "distil-whisper/distil-large-v2",
            DistilWhisperSize::DistilLargeV3 => "distil-whisper/distil-large-v3",
        }
    }

    /// Parse model size from string
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "distil-small.en" | "distil-small-en" | "small.en" | "small-en" => {
                Some(DistilWhisperSize::DistilSmallEn)
            }
            "distil-medium.en" | "distil-medium-en" | "medium.en" | "medium-en" => {
                Some(DistilWhisperSize::DistilMediumEn)
            }
            "distil-large-v2" | "large-v2" => Some(DistilWhisperSize::DistilLargeV2),
            "distil-large-v3" | "large-v3" => Some(DistilWhisperSize::DistilLargeV3),
            _ => None,
        }
    }

    /// Get the display name for this size
    pub fn display_name(&self) -> &'static str {
        match self {
            DistilWhisperSize::DistilSmallEn => "distil-small.en",
            DistilWhisperSize::DistilMediumEn => "distil-medium.en",
            DistilWhisperSize::DistilLargeV2 => "distil-large-v2",
            DistilWhisperSize::DistilLargeV3 => "distil-large-v3",
        }
    }

    /// Check if this model is English-only
    pub fn is_english_only(&self) -> bool {
        matches!(
            self,
            DistilWhisperSize::DistilSmallEn | DistilWhisperSize::DistilMediumEn
        )
    }

    /// Get approximate model size in bytes
    pub fn model_size_bytes(&self) -> u64 {
        match self {
            DistilWhisperSize::DistilSmallEn => 166_000_000,
            DistilWhisperSize::DistilMediumEn => 394_000_000,
            DistilWhisperSize::DistilLargeV2 => 756_000_000,
            DistilWhisperSize::DistilLargeV3 => 756_000_000,
        }
    }
}

/// List of available Distil-Whisper models
pub const DISTIL_WHISPER_MODELS: &[(&str, &str, &str)] = &[
    (
        "distil-small.en",
        "distil-whisper/distil-small.en",
        "English-only, fastest inference",
    ),
    (
        "distil-medium.en",
        "distil-whisper/distil-medium.en",
        "English-only, balanced speed/quality",
    ),
    (
        "distil-large-v2",
        "distil-whisper/distil-large-v2",
        "Multilingual, based on Whisper large-v2",
    ),
    (
        "distil-large-v3",
        "distil-whisper/distil-large-v3",
        "Multilingual, based on Whisper large-v3",
    ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_model_size_parsing() {
        assert_eq!(
            DistilWhisperSize::from_str("distil-small.en"),
            Some(DistilWhisperSize::DistilSmallEn)
        );
        assert_eq!(
            DistilWhisperSize::from_str("small.en"),
            Some(DistilWhisperSize::DistilSmallEn)
        );
        assert_eq!(
            DistilWhisperSize::from_str("distil-large-v3"),
            Some(DistilWhisperSize::DistilLargeV3)
        );
        assert_eq!(DistilWhisperSize::from_str("invalid"), None);
    }

    #[test]
    fn test_english_only() {
        assert!(DistilWhisperSize::DistilSmallEn.is_english_only());
        assert!(DistilWhisperSize::DistilMediumEn.is_english_only());
        assert!(!DistilWhisperSize::DistilLargeV2.is_english_only());
        assert!(!DistilWhisperSize::DistilLargeV3.is_english_only());
    }
}
