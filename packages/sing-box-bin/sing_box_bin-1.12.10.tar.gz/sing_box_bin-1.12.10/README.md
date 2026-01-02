# sing-box-bin

A Python wrapper for sing-box binary releases


## build and bump version

```bash
.\scripts\build.sh "vx.y.z"
bump-my-version bump --new-version "x.y.z"
git push origin main --tags
```

## install

```bash
uv add sing-box-bin
```

## usage

```python
from sing_box_bin import get_bin_path

>>> get_bin_path()
>>> ./.sing-box-bin/ sing-box-windows-amd64.exe
```
