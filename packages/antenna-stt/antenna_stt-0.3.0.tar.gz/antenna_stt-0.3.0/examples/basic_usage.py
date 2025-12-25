"""Basic usage example for antenna POC"""
import antenna
import numpy as np

def main():
    print("=== Antenna POC Demo ===\n")
    
    # Load audio file
    print("Loading audio file...")
    audio = antenna.load_audio("test_data/test_audio.wav")
    print(f"  Sample rate: {audio.sample_rate} Hz")
    print(f"  Channels: {audio.channels}")
    print(f"  Duration: {audio.duration:.2f} seconds")
    
    # Preprocess
    print("\nPreprocessing audio...")
    processed = antenna.preprocess_audio(
        audio,
        target_sample_rate=16000,
        mono=True
    )
    print(f"  New sample rate: {processed.sample_rate} Hz")
    print(f"  New channels: {processed.channels}")
    print(f"  New duration: {processed.duration:.2f} seconds")
    
    # Get as numpy array
    samples = processed.to_numpy()
    print(f"\nNumPy array shape: {samples.shape}")
    print(f"Data type: {samples.dtype}")
    print(f"Value range: [{samples.min():.3f}, {samples.max():.3f}]")
    
    print("\n✅ POC successful!")

if __name__ == "__main__":
    main()

