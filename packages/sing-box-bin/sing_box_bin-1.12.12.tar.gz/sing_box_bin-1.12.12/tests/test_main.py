import subprocess
from unittest.mock import patch

import pytest

from sing_box_bin import get_bin_path


def test_real_execution():
    try:
        bin_path = get_bin_path()
        print(f"Testing binary at: {bin_path}")

        result = subprocess.run(
            [str(bin_path), "version"], capture_output=True, text=True
        )

        assert result.returncode == 0, f"Binary failed with stderr: {result.stderr}"
        assert "sing-box" in result.stdout or "version" in result.stdout
        print("✅ Real binary execution passed")

    except FileNotFoundError:
        pytest.fail("Binary not found. Did you build it first?")


def test_get_bin_path_windows():
    with patch("sys.platform", "win32"):
        with patch("pathlib.Path.exists", return_value=True):
            path = get_bin_path()
            assert path.name == "sing-box-windows-amd64.exe"
            assert str(path).endswith("sing-box-windows-amd64.exe")


def test_get_bin_path_linux_chmod():
    with patch("sys.platform", "linux"):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("os.stat") as mock_stat:
                with patch("os.chmod") as mock_chmod:
                    mock_stat.return_value.st_mode = 0o644

                    path = get_bin_path()

                    assert path.name == "sing-box-linux-amd64"
                    mock_chmod.assert_called_once()
                    args, _ = mock_chmod.call_args
                    assert args[1] & 0o111


def test_binary_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError) as excinfo:
            get_bin_path()
        assert "Binary not found" in str(excinfo.value)
