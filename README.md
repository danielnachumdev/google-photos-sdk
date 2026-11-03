# google-photos-sdk

Python client for the Google Photos Library API (albums, media, upload, search).

**PyPI:** [`google-photos-sdk`](https://pypi.org/project/google-photos-sdk/)  
**Import:** `gpsdk` (formerly `gp_wrapper`).  
Older releases were also published as [`gp_wrapper`](https://pypi.org/project/gp_wrapper/).

Requires **Python 3.11+**.

## Install

```bash
pip install google-photos-sdk
# or from this repo:
pip install -e .
```

## Usage

```python
from gpsdk import GooglePhotos

gp = GooglePhotos()  # OAuth as configured for the package
albums = gp.get_albums()
```

Main types: `GooglePhotos`, `Album`, `MediaItem`. See `gpsdk/` for the API surface.

## Develop

```bash
uv sync  # or pip install -e ".[dev]" if configured
# tests under tests/
```

## License

See `LISENCE` in this repo.
