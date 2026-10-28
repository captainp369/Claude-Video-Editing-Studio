#!/usr/bin/env python3
"""Fetch one piece of outside media for a video, with its credit, ready for the renderer.

    python3 tools/fetch-media/fetch.py <url> <dest_dir> [--name NAME] [--width PX] [--info] [--prep]

  <url>       an X/Twitter post, a Wikimedia Commons file page, any direct file URL,
              or (if yt-dlp is installed) a YouTube/Instagram/TikTok/etc. page
  <dest_dir>  where the file goes, normally <videos_dir>/source/ (a folder of its own: downloads are data)
  --name      base filename without extension (default: derived from the source)
  --width     Commons only: fetch a scaled copy this wide instead of the original
  --info      print what would be fetched (file URL, size, author, licence) and stop
  --prep      videos only: also write NAME.prep.mp4 (constant 30 fps, SDR bt709, keyframe every 30 frames)

Every fetch writes NAME.<ext>.source.json next to the file and appends one line to <dest_dir>/CREDITS.md.
Standard library only. See MEDIA_SOURCING.md for when you may use what you fetch.
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timezone

UA = {"User-Agent": "claude-video-studio-fetch/1.0 (+https://github.com/captainp369/Claude-Video-Editing-Studio)"}


def get_json(url, tries=5):
    """GET JSON, waiting and retrying when the server says 429 (Commons limits quick runs of lookups)."""
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == tries - 1:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 5 * 2 ** k
            print(f"rate-limited, waiting {wait}s…", file=sys.stderr)
            time.sleep(min(wait, 120))


def head_size(url):
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            n = r.headers.get("Content-Length")
            return int(n) if n else None
    except Exception:
        return None


def mb(n):
    return f"{n / 1e6:.1f} MB" if n else "size unknown"


def strip_html(s):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()
    h = len(t) // 2                                   # Commons often nests the name twice ("Unknown author Unknown author")
    return t[:h].strip() if len(t) % 2 == 1 and t[:h] == t[h + 1:] else t


# ── resolvers: url -> {file_url, ext, name, author, licence, licence_url, credit, source, date, kind} ──

def from_x(url):
    m = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", url)
    if not m:
        sys.exit("not an X post URL")
    user, sid = m.groups()
    # X pages hide the file; fxtwitter's public API returns the post and its media variants as JSON
    t = get_json(f"https://api.fxtwitter.com/{user}/status/{sid}").get("tweet") or {}
    media = t.get("media") or {}
    vids, pics = media.get("videos") or [], media.get("photos") or []
    when = ""
    if t.get("created_timestamp"):
        when = datetime.fromtimestamp(t["created_timestamp"], timezone.utc).date().isoformat()   # the poster's date, not ours
    handle = (t.get("author") or {}).get("screen_name") or user
    shown = (t.get("author") or {}).get("name") or handle                 # display name reads better in a credit
    base = {"author": "@" + handle, "licence": "© the author (not openly licensed)", "licence_url": "",
            "source": f"https://x.com/{handle}/status/{sid}", "date": when, "text": (t.get("text") or "")[:200]}
    if vids:
        v = vids[0]
        mp4s = [f for f in v.get("formats", []) if (f.get("url") or "").split("?")[0].endswith(".mp4")]
        best = max(mp4s, key=lambda f: f.get("bitrate") or 0)["url"] if mp4s else v["url"]
        return {**base, "file_url": best, "ext": "mp4", "kind": "video", "name": f"{handle}_{when or sid}",
                "credit": f"วิดีโอ: {shown} ({when})" if when else f"วิดีโอ: {shown}"}
    if pics:
        return {**base, "file_url": pics[0]["url"], "ext": pics[0]["url"].split("?")[0].rsplit(".", 1)[-1], "kind": "image",
                "name": f"{handle}_{when or sid}", "credit": f"ภาพ: {shown} ({when})" if when else f"ภาพ: {shown}"}
    sys.exit("that post has no photo or video")


def from_commons(url, width):
    title = urllib.parse.unquote(url.split("/wiki/")[-1]).replace("_", " ") if "/wiki/" in url else None
    if not title:  # an upload.wikimedia.org link: the file name is the last path part
        title = "File:" + urllib.parse.unquote(url.rstrip("/").split("/")[-1]).replace("_", " ")
    q = {"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "format": "json"}
    if width:
        q["iiurlwidth"] = str(width)
    pages = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q))["query"]["pages"]
    page = next(iter(pages.values()))
    if "imageinfo" not in page:
        sys.exit(f"no such Commons file: {title}")
    ii = page["imageinfo"][0]
    md = ii.get("extmetadata", {})
    val = lambda k: strip_html((md.get(k) or {}).get("value", ""))
    author, lic = val("Artist") or "unknown author", val("LicenseShortName") or "licence unknown"
    file_url = ii.get("thumburl") if width else ii["url"]
    name = re.sub(r"[^\w.-]+", "_", title.split(":", 1)[-1].rsplit(".", 1)[0])[:60]
    return {"file_url": file_url, "ext": file_url.split("?")[0].rsplit(".", 1)[-1].lower(), "kind": "image", "name": name,
            "author": author, "licence": lic, "licence_url": val("LicenseUrl"),
            "source": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
            "date": val("DateTimeOriginal")[:10], "credit": f"{author} ({lic}, Wikimedia Commons)"}


def from_direct(url):
    path = urllib.parse.urlparse(url).path
    ext = path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else "bin"
    kind = "video" if ext in ("mp4", "mov", "webm", "m4v") else "image" if ext in ("jpg", "jpeg", "png", "webp", "gif", "svg") else "file"
    return {"file_url": url, "ext": ext, "kind": kind, "name": re.sub(r"[^\w.-]+", "_", path.rsplit("/", 1)[-1].rsplit(".", 1)[0])[:60] or "file",
            "author": "", "licence": "unknown: check before use", "licence_url": "", "source": url, "date": "", "credit": "(fill in: who made it, licence)"}


def via_ytdlp(url, dest, name, info_only):
    exe = shutil.which("yt-dlp")
    if not exe:
        sys.exit("this site needs yt-dlp, which isn't installed. Ask the user before installing it (brew install yt-dlp).")
    meta = json.loads(subprocess.run([exe, "-J", "--no-playlist", url], capture_output=True, text=True, check=True).stdout)
    info = {"file_url": url, "ext": "mp4", "kind": "video", "name": name or re.sub(r"[^\w.-]+", "_", meta.get("id", "video")),
            "author": meta.get("uploader") or meta.get("channel") or "", "licence": meta.get("license") or "© the author",
            "licence_url": "", "source": meta.get("webpage_url") or url, "date": (meta.get("upload_date") or "")[:8],
            "credit": f"วิดีโอ: {meta.get('uploader') or meta.get('channel') or ''}".strip(), "size": meta.get("filesize_approx")}
    if info_only:
        return info, None
    out = os.path.join(dest, info["name"] + ".mp4")
    subprocess.run([exe, "--no-playlist", "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b", "--merge-output-format", "mp4", "-o", out, url], check=True)
    return info, out


def download(url, out):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(out, "wb") as f:
        shutil.copyfileobj(r, f)


def prep(path):
    """Constant 30 fps, SDR bt709 (HDR phone clips stall the renderer), a keyframe every 30 frames (fast seeking)."""
    out = path.rsplit(".", 1)[0] + ".prep.mp4"
    tags = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"   # newer ffmpeg keeps tags only if the frames carry them
    vf = "fps=30,format=yuv420p," + tags
    trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    if trc in ("arib-std-b67", "smpte2084"):   # HLG / PQ → tone-map to SDR
        vf = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable,zscale=t=bt709:m=bt709:r=tv,fps=30,format=yuv420p," + tags
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                    "-g", "30", "-keyint_min", "30", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", out], check=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url"); ap.add_argument("dest")
    ap.add_argument("--name"); ap.add_argument("--width", type=int)
    ap.add_argument("--info", action="store_true"); ap.add_argument("--prep", action="store_true")
    a = ap.parse_args()
    host = urllib.parse.urlparse(a.url).netloc.lower()

    if re.search(r"(^|\.)(x|twitter)\.com$", host):
        info, out = from_x(a.url), None
    elif "wikimedia.org" in host or "wikipedia.org" in host and "/wiki/File:" in a.url:
        info, out = from_commons(a.url, a.width), None
    elif re.search(r"\.(jpe?g|png|webp|gif|svg|mp4|mov|webm|m4v|pdf)(\?|$)", a.url, re.I):
        info, out = from_direct(a.url), None
    else:
        os.makedirs(a.dest, exist_ok=True)
        info, out = via_ytdlp(a.url, a.dest, a.name, a.info)
    if a.name:
        info["name"] = a.name
    info.setdefault("size", head_size(info["file_url"]) if info["file_url"].startswith("http") else None)

    print(f"source : {info['source']}\nfile   : {info['file_url']}\nsize   : {mb(info.get('size'))}\n"
          f"author : {info['author']}\nlicence: {info['licence']} {info['licence_url']}\ncredit : {info['credit']}")
    if a.info:
        return

    os.makedirs(a.dest, exist_ok=True)
    if out is None:
        out = os.path.join(a.dest, f"{info['name']}.{info['ext']}")
        if os.path.exists(out):
            sys.exit(f"exists, not overwriting: {out}")
        download(info["file_url"], out)
    info.update({"file": os.path.basename(out), "fetched": date.today().isoformat(), "bytes": os.path.getsize(out)})
    json.dump(info, open(out + ".source.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(a.dest, "CREDITS.md"), "a", encoding="utf-8") as f:
        f.write(f"- `{info['file']}` · {info['author'] or '?'} · {info['licence']} · {info['source']} · fetched {info['fetched']} · credit: {info['credit']}\n")
    print(f"wrote  : {out} ({mb(info['bytes'])})")
    if a.prep and info["kind"] == "video":
        print(f"prep   : {prep(out)}")


if __name__ == "__main__":
    main()
