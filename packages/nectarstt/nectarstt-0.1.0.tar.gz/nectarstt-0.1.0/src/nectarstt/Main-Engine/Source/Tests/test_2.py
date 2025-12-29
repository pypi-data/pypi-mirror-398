import wave
from piper import PiperVoice

# Load the model (local file path)
voice = PiperVoice.load(r"D:\Projects\Dev\VoicePiled\Main-Engine\Model\en_onnx-ryan-high_Model\en_US-ryan-high.onnx", use_cuda=True)

def outetts(text: str, output_path: str = "output.wav"):
    # Create a wave file and pass to synthesize_wav
    with wave.open(output_path, "wb") as wav_file:
        # The docs say: voice.synthesize_wav(text, wav_file)
        voice.synthesize_wav(text, wav_file)
    return output_path

# Test
if __name__ == "__main__":
    outetts("Hello! This is Piper TTS running on your system.")
    print("✅ Audio saved to output.wav")
