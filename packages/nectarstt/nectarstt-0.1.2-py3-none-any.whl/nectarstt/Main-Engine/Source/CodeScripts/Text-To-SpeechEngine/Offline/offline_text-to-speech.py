import subprocess

def piper_tts(text, output_path):
    model_path = r"D:\Projects\Dev\VoicePiled\Main-Engine\Model\en_onnx-ryan-high_Model\en_US-ryan-high.onnx"
    piper_exe = r"D:\Projects\Dev\VoicePiled\Main-Engine\TTS-Engine\piper-cpu\piper.exe"

    cmd = [
        piper_exe,
        "--model", model_path,
        "--output_file", output_path,
        "--use-cuda", "1",    # Explicitly enable CUDA
        "--cuda"              # Secondary flag (ignored if unsupported)
    ]

    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    process.communicate(input=text.encode("utf-8"))

piper_tts("Hello, how are you today hope you are fine", "output.wav")