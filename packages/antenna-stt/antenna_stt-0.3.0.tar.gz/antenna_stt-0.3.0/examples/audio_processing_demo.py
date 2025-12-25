"""
Audio Processing Demo - Antenna v0.2.0

This example demonstrates the new features in v0.2.0:
- Multi-format audio loading (WAV, MP3, FLAC, OGG, M4A)
- Audio analysis (RMS, peak, zero-crossing rate)
- Silence detection and trimming
- Audio normalization (peak, RMS, LUFS)
- Saving processed audio
"""

import antenna
import sys


def print_stats(stats, label="Audio Stats"):
    """Pretty print audio statistics"""
    print(f"\n{label}:")
    print(f"  RMS:                {stats.rms:.4f}")
    print(f"  Peak:               {stats.peak:.4f}")
    print(f"  RMS (dB):           {stats.rms_db:.2f} dB")
    print(f"  Peak (dB):          {stats.peak_db:.2f} dB")
    print(f"  Zero Crossing Rate: {stats.zero_crossing_rate:.4f}")
    print(f"  Energy:             {stats.energy:.2f}")


def main():
    input_file = "test_data/test_audio.wav"
    output_file = "test_data/processed_output.wav"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print("=" * 60)
    print("Antenna v0.2.0 - Audio Processing Demo")
    print("=" * 60)

    # Step 1: Load audio (supports WAV, MP3, FLAC, OGG, M4A)
    print(f"\n[1] Loading audio from: {input_file}")
    audio = antenna.load_audio(input_file)
    print(f"    Sample rate: {audio.sample_rate} Hz")
    print(f"    Channels:    {audio.channels}")
    print(f"    Duration:    {audio.duration:.2f} seconds")

    # Step 2: Analyze original audio
    print("\n[2] Analyzing original audio...")
    original_stats = antenna.analyze_audio(audio)
    print_stats(original_stats, "Original Audio")

    # Step 3: Detect silence regions
    print("\n[3] Detecting silence regions...")
    silence_segments = antenna.detect_silence(
        audio, threshold_db=-40.0, min_duration=0.1
    )
    print(f"    Found {len(silence_segments)} silence segments:")
    for i, (start, end) in enumerate(silence_segments[:5]):  # Show first 5
        print(f"      Segment {i+1}: {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")
    if len(silence_segments) > 5:
        print(f"      ... and {len(silence_segments) - 5} more")

    # Step 4: Trim silence from beginning and end
    print("\n[4] Trimming silence...")
    print(f"    Original duration: {audio.duration:.2f}s")
    audio = antenna.trim_silence(audio, threshold_db=-40.0)
    print(f"    Trimmed duration:  {audio.duration:.2f}s")

    # Step 5: Normalize audio
    print("\n[5] Normalizing audio (RMS to -20 dB)...")
    audio = antenna.normalize_audio(audio, method="rms", target_db=-20.0)
    normalized_stats = antenna.analyze_audio(audio)
    print(f"    Before: RMS = {original_stats.rms_db:.2f} dB")
    print(f"    After:  RMS = {normalized_stats.rms_db:.2f} dB")

    # Step 6: Preprocess for speech recognition (16kHz mono)
    print("\n[6] Preprocessing for Whisper (16kHz, mono)...")
    audio = antenna.preprocess_audio(audio, target_sample_rate=16000, mono=True)
    print(f"    Sample rate: {audio.sample_rate} Hz")
    print(f"    Channels:    {audio.channels}")
    print(f"    Duration:    {audio.duration:.2f} seconds")

    # Step 7: Final analysis
    print("\n[7] Final audio analysis...")
    final_stats = antenna.analyze_audio(audio)
    print_stats(final_stats, "Processed Audio")

    # Step 8: Save processed audio
    print(f"\n[8] Saving processed audio to: {output_file}")
    antenna.save_audio(audio, output_file)
    print("    ✓ Saved successfully!")

    # Step 9: Verify by reloading
    print("\n[9] Verifying saved file...")
    reloaded = antenna.load_audio(output_file)
    print(f"    Sample rate: {reloaded.sample_rate} Hz")
    print(f"    Channels:    {reloaded.channels}")
    print(f"    Duration:    {reloaded.duration:.2f} seconds")
    print("    ✓ Verification successful!")

    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)

    # Bonus: Split on silence example
    print("\n[BONUS] Splitting audio on silence...")
    original_audio = antenna.load_audio(input_file)
    chunks = antenna.split_on_silence(
        original_audio, threshold_db=-40.0, min_silence_duration=0.2
    )
    print(f"    Split into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks[:5]):
        print(f"      Chunk {i+1}: {chunk.duration:.2f}s")
    if len(chunks) > 5:
        print(f"      ... and {len(chunks) - 5} more")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nUsage: python audio_processing_demo.py [input_file] [output_file]")
        print("Example: python audio_processing_demo.py podcast.mp3 processed.wav")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
