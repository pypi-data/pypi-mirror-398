"""Download a small test audio file"""
import urllib.request
from pathlib import Path

def download_test_audio():
    url = "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav"
    output_path = Path("test_data/test_audio.wav")
    output_path.parent.mkdir(exist_ok=True)
    
    print(f"Downloading test audio from {url}...")
    urllib.request.urlretrieve(url, output_path)
    print(f"Saved to {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    download_test_audio()

