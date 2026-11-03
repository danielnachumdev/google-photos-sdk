# google-photos-sdk

Python client for the Google Photos Library API (albums, media, upload, search).

Published on PyPI as [`gp_wrapper`](https://pypi.org/project/gp_wrapper/) (package name unchanged).

Requires **Python 3.11+**.

## Install

```bash
pip install gp_wrapper
# or from this repo:
pip install -e .
```

## Usage

```python
from gp_wrapper import GooglePhotos

gp = GooglePhotos()  # OAuth as configured for the package
albums = gp.get_albums()
```

Main types: `GooglePhotos`, `Album`, `MediaItem`. See `gp_wrapper/` for the API surface.

## Develop

```bash
uv sync  # or pip install -e ".[dev]" if configured
# tests under tests/
```

## License

See `LISENCE` in this repo.
