import subprocess
from pathlib import Path

# Default paths (can be overridden by arguments)
DEFAULT_MODEL_PATH = Path("./Main-Engine/Model/en_onnx-ryan-high_Model/en_US-ryan-high.onnx")
DEFAULT_PIPER_EXE = Path("./Main-Engine/TTS-Engine/piper-cpu/piper.exe")


def piper_tts(
    text: str,
    output_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    piper_exe: str | Path = DEFAULT_PIPER_EXE,
    use_cuda: bool = True,
) -> str:
    """
    Run Piper TTS and synthesize `text` into a WAV file.

    Args:
        text: Text to synthesize.
        output_path: Path to the output WAV file.
        model_path: Path to the Piper .onnx model.
        piper_exe: Path to the piper executable.
        use_cuda: Whether to pass CUDA flags (if supported by your build).

    Returns:
        The output file path as a string.

    Raises:
        FileNotFoundError: If the executable or model does not exist.
        RuntimeError: If Piper exits with a non-zero status.
    """
    output_path = Path(output_path)
    model_path = Path(model_path)
    piper_exe = Path(piper_exe)

    if not piper_exe.exists():
        raise FileNotFoundError(f"Piper executable not found at: {piper_exe}")

    if not model_path.exists():
        raise FileNotFoundError(f"Piper model not found at: {model_path}")

    cmd = [
        str(piper_exe),
        "--model", str(model_path),
        "--output_file", str(output_path),
    ]

    # CUDA flags (some builds may ignore them if unsupported) [web:80][web:83]
    if use_cuda:
        cmd.extend(["--use-cuda", "1", "--cuda"])

    # Start Piper and send text on stdin
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(input=text.encode("utf-8"))

    if process.returncode != 0:
        raise RuntimeError(
            f"Piper TTS failed with code {process.returncode}.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    return str(output_path)


# Optional: keep a simple CLI for direct use
if __name__ == "__main__":
    piper_tts(
        "Hello, how are you today? Hope you are fine.",
        "output.wav",
    )
