import os
import sys
from pathlib import Path

__all__ = ["get_bin_path"]

__version__ = "1.12.10"


def get_bin_path() -> Path:
    base_path = Path(__file__).parent / "bin"

    if sys.platform == "win32":
        bin_path = base_path / "sing-box-windows-amd64.exe"
    else:
        bin_path = base_path / "sing-box-linux-amd64"

    if not bin_path.exists():
        raise FileNotFoundError(f"Binary not found at {bin_path}")

    if sys.platform != "win32":
        st = os.stat(bin_path)
        os.chmod(bin_path, st.st_mode | 0o111)

    return bin_path
