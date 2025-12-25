pub mod analysis;
pub mod io;
pub mod process;
pub mod silence;

pub use analysis::{analyze, AudioStats};
pub use io::{load_audio, load_audio_symphonia, load_wav, save_audio, save_wav};
pub use process::{convert_to_mono, normalize, resample, NormalizationMethod};
pub use silence::{detect_silence, split_on_silence, trim_silence, SilenceSegment};

