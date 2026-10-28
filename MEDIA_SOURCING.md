# Media sourcing: photos and clips from outside the project

How to bring someone else's photo or video into an edit: may we use it, how to fetch it, how to prepare it for the renderer, and how to credit it. **Read this before downloading anything for a video.**

## 1 · Decide first: may we use it?

Work down this list and stop at the first option that fits.

1. **Make it ourselves.** Draw it as SVG, CSS or canvas, or recreate the scene in the video's own style. This carries no rights question. Draw from facts, not by tracing a photo: tracing copies the photo.
2. **Openly licensed.** Public domain, CC0, CC BY or CC BY-SA, usually from Wikimedia Commons. Credit as the licence says. CC BY-SA is fine for a photo shown in a video; credit it.
3. **The creator's own media, with the user's OK.** A clip or photo the subject posted themselves (a company demo, a creator's video). Use only after the user says yes in chat. Show a short excerpt, report on it rather than replace it, and credit it on screen and in the description.
4. **Everything else** (news photos, stock, agency images, TV footage) is out. Recreate it, or ask the user to supply licensed media through `assets/ASSET_REQUESTS.md`.

Cropping, filtering or pixelating doesn't change who owns a picture.

**Always ask before a download.** Tell the user the file name, where it comes from and its size (`--info` prints all three), and wait for a yes.

## 2 · Fetch it

```bash
python3 tools/fetch-media/fetch.py <url> <videos_dir>/source --info     # what it is, size, author, licence. No download
python3 tools/fetch-media/fetch.py <url> <videos_dir>/source            # download + credit files
python3 tools/fetch-media/fetch.py <url> <videos_dir>/source --prep     # videos: also write NAME.prep.mp4 (see §3)
```

| Source | How the script gets it | What you get |
|---|---|---|
| X / Twitter post | X pages hide the file. The public fxtwitter API (`api.fxtwitter.com/<user>/status/<id>`) returns the post as JSON with every video bitrate. The script takes the highest-bitrate MP4 from X's own video server. | Video or first photo. Credit uses the display name and the post's **UTC** date (the date the poster and the press use). |
| Wikimedia Commons file page | The Commons API (`imageinfo` + `extmetadata`). | Original file, or a scaled copy with `--width 1600`. Author, licence and licence URL are filled in. |
| Direct file URL (`.jpg .png .mp4 …`) | Plain download. | The file. Credit and licence are left as "fill in", so check them by hand. |
| YouTube, Instagram, TikTok, others | `yt-dlp`, if installed. | Video. **yt-dlp isn't installed by default: ask the user before `brew install yt-dlp`.** |

Every fetch writes two things:
- `NAME.<ext>.source.json` next to the file: source, author, licence, date, the credit line, and the fetch date.
- One line in `<dest>/CREDITS.md`.

Keep downloads in their own folder (`<videos_dir>/source/`): they are data, not code. `video_projects/` is git-ignored, so fetched media never reaches the repo.

## 3 · Prepare it for the renderer

`--prep` writes `NAME.prep.mp4`. Use that file in compositions, never the raw download.

- **Constant 30 fps.** Social clips are often 16, 24 or 25 fps, or variable. The renderer and later cuts want a steady 30.
- **SDR, bt709, tagged.** HDR phone footage (HLG or PQ) can stall the renderer at 0 fps. `--prep` tone-maps it to SDR.
- **A keyframe every 30 frames.** Uploads often have 8-second gaps between keyframes, which makes previews seek slowly.

Done by hand, the same thing is:
```bash
ffmpeg -i in.mp4 -vf "fps=30,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
  -c:v libx264 -crf 16 -preset slow -g 30 -keyint_min 30 -movflags +faststart out.mp4
```

Also check, by looking at a contact sheet (`ffmpeg -i x.mp4 -vf "fps=1/2.5,scale=384:-1,tile=4x3" sheet.png`):
- **Insets and watermarks.** A demo clip often has a picture-in-picture or logo in a corner. Crop it off if you re-use frames as stills, but leave the original as it is when you show it as the source's clip.
- **Orientation.** A 16:9 clip in a 9:16 video goes in a framed window, not stretched or cropped to fill the screen.

## 4 · Credit it

| Where | What |
|---|---|
| On screen, while it shows | `วิดีโอ: <name> (<date>)` or `ภาพ: <author> (<licence>)`, in small text under the media. Name the maker, not the platform. A platform name on screen ("X", "YouTube") can get a video demoted when it's cross-posted elsewhere. |
| Description | Credit plus link: the post URL, or the Commons file page with its licence. |
| `RESEARCH.md` | A "Footage" note: what was fetched, when, from where, on whose OK, and how it was changed (re-encoded, cropped, pixelated). |

The `credit` field in `.source.json` holds the on-screen line, ready to paste. Check it: Commons authors can be messy, and direct URLs have no credit at all.

## 5 · Gotchas

- **Dates.** A post made late in the US evening is already the next day in Asia. Use the post's own UTC date, which is what coverage and the poster use.
- **Commons `--width`.** If the original is narrower than `--width`, you get the original.
- **fxtwitter is a third-party mirror.** If it's down, open the post in a browser and read the `video.twimg.com/…mp4` address from the network requests. Don't sign in to anything to get a file.
- **Sign-in walls.** If a site wants a login to show the media, stop and ask the user. Don't sign in for them.
- **One clip, many uses.** When stills from the same clip become textures or pixel art, that's still the source's footage: the same credit applies.
