# fetch-media

Fetch one photo or clip for a video, with its credit, ready for the renderer. Standard-library Python, plus `ffmpeg` for `--prep`.

```bash
python3 tools/fetch-media/fetch.py <url> <videos_dir>/source --info    # what it is: size, author, licence
python3 tools/fetch-media/fetch.py <url> <videos_dir>/source --prep    # download, write credits, and a renderer-ready .prep.mp4
```

It handles:
- X/Twitter posts (via the public fxtwitter API)
- Wikimedia Commons file pages (author and licence from the Commons API, `--width` for a scaled copy)
- direct file URLs
- anything `yt-dlp` supports, if yt-dlp is installed

Each download leaves `NAME.<ext>.source.json` and a line in `CREDITS.md` in the destination folder.

When you may use what you fetch, and how to credit it: see [`MEDIA_SOURCING.md`](../../MEDIA_SOURCING.md).
