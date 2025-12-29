import subprocess
import re

def piper_tts(text, output_path):
    model_path = r"D:\Projects\Dev\VoicePiled\Main-Engine\Model\en_onnx-ryan-high_Model\en_US-ryan-high.onnx"
    piper_exe = r"D:\Projects\Dev\VoicePiled\Main-Engine\TTS-Engine\piper-cpu\piper.exe"

    cmd = [
        piper_exe,
        "--model", model_path,
        "--output_file", output_path,
        "--use-cuda", "1",
    ]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    out, err = process.communicate(input=text)

    # Detect RTF in Piper log
    match = re.search(r"Real-time factor:\s*([0-9.]+)", err)
    
    if match:
        rtf = float(match.group(1))

        if rtf < 1.0:
            print("✔ GPU detected (fast inference)")
        else:
            print("✔ CPU detected (slow inference)")
    else:
        print("⚠ Could not detect RTF — assuming CPU")

    print(out, err)

# Example usage:
piper_tts("Hello, this is GPU-powered Piper TTS!", "output2.wav")
