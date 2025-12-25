"""Generate a synthetic test audio file"""
import wave
import math
import struct
from pathlib import Path

def generate_sine_wave(frequency, duration, sample_rate, num_channels):
    """Generate a sine wave at the given frequency"""
    num_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(num_samples):
        value = math.sin(2.0 * math.pi * frequency * i / sample_rate)
        # Convert to 16-bit integer
        sample = int(value * 32767)
        # Add for each channel
        for _ in range(num_channels):
            samples.append(sample)
    
    return samples

def create_test_wav():
    """Create a test WAV file"""
    output_path = Path("test_data/test_audio.wav")
    output_path.parent.mkdir(exist_ok=True)
    
    sample_rate = 44100
    duration = 2.0  # 2 seconds
    frequency = 440.0  # A4 note
    num_channels = 2  # Stereo
    
    samples = generate_sine_wave(frequency, duration, sample_rate, num_channels)
    
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"Created test audio: {output_path}")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Channels: {num_channels}")
    print(f"  Duration: {duration} seconds")
    print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    create_test_wav()

