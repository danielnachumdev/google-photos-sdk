# gp_wrapper

**Typed Python wrapper for the Google Photos Library API** — albums, media, uploads, and search with a clean object model instead of raw HTTP.

[![CI](https://github.com/danielnachumdev/gp_wrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/danielnachumdev/gp_wrapper/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gp_wrapper.svg)](https://pypi.org/project/gp_wrapper/)
[![Python](https://img.shields.io/pypi/pyversions/gp_wrapper.svg)](https://pypi.org/project/gp_wrapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LISENCE)

Requires **Python 3.11+**.

## Why gp_wrapper?

Google Photos is powerful; its API is verbose. **gp_wrapper** turns authenticated sessions into first-class objects so you can script backups, migrations, and album workflows without hand-rolling OAuth, paging, or payload shapes.

- **Full Library API coverage** plus convenience helpers for real upload/migration flows
- **`GooglePhotos`**, **`Album`**, and **`MediaItem`** as the main entry points
- **Enums and dataclasses** that mirror the API (`MimeType`, `MediaItemMaskTypes`, `NewMediaItem`, …)
- **Video-aware uploads** — non-mp4 sources can be transcoded with preserved timing metadata
- **MIT licensed**, CI-tested on Python **3.11–3.13**

## Install

```bash
pip install gp_wrapper
# or
uv add gp_wrapper
```

## Quick start

```python
from gp_wrapper import GooglePhotos, Album, MediaItem, NewMediaItem, SimpleMediaItem

gp = GooglePhotos("path/to/client_secrets.json")
album = Album.exists(gp, name="Vacation") or Album.create(gp, "Vacation")
token = MediaItem.upload_media(gp, "photo.jpg")
MediaItem.batchCreate(
    gp,
    [NewMediaItem("from gp_wrapper", SimpleMediaItem(token, "photo.jpg"))],
    albumId=album.id,
)
```

Google Cloud OAuth setup and a longer walkthrough: [`READMES/example.md`](./READMES/example.md) · credentials shape: [`READMES/client_secrets_example.json`](./READMES/client_secrets_example.json)

## What you get

| Surface | Role |
| -------- | ---- |
| `GooglePhotos` | Authenticated session over the Photos Library API |
| `Album` | Create, list, share, enrich, and manage album membership |
| `MediaItem` | Upload, batch-create, search, and update media |
| Filters & enums | Content, date, feature, and media-type search filters |
| Structures | `SimpleMediaItem`, `NewMediaItem`, `AlbumPosition`, `MediaMetadata`, … |

## Contributing & development

Agent/developer workflow (uv, tests, CI/CD labels, secrets): see [`AGENTS.md`](./AGENTS.md).

Report security issues privately via [GitHub advisories](https://github.com/danielnachumdev/gp_wrapper/security/advisories/new) — please do not open a public issue for vulnerabilities.

## License

MIT — see [`LISENCE`](./LISENCE).
