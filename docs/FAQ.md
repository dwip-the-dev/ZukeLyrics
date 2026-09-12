# ❓ Frequently Asked Questions (FAQ)

Everything you need to know about ZukeLyrics architecture, licensing, synchronization, and usage.

---

## 📑 Table of Contents
1. [General Questions](#1-general-questions)
2. [Technical & Architectural Questions](#2-technical--architectural-questions)
3. [Integration & Usage](#3-integration--usage)
4. [Contributing & Moderation](#4-contributing--moderation)

---

## 1. General Questions

### Why not just use LRCLIB or Musixmatch?
- **LRCLIB** is an incredible service, but standard LRC format only contains **line-level** timestamps (`[01:23.45] Lyric line`). It cannot power Apple Music or Spotify-style word-by-word, syllable-glowing karaoke animations.
- **Musixmatch** and **Genius** are proprietary commercial services with strict API rate limits, closed ecosystems, and restrictive developer terms of service.
- **ZukeLyrics** is **100% open-source**, free, provides **millisecond-precise word-level sync**, and is hosted on a high-speed Anycast CDN with zero authentication barriers.

### Are there any API keys, fees, or rate limits?
**No.** All read queries to ZukeLyrics are served through global Anycast CDN edges (jsDelivr, Fastly, Cloudflare, GitHub). There are no API keys to manage, no credit card requirements, and no arbitrary 100-request/minute rate limit caps.

### Can I self-host or mirror the entire database?
**Yes.** Because ZukeLyrics is a Git repository:
- You can mirror the entire dataset with a single `git clone https://github.com/dwip-the-dev/ZukeLyrics.git`.
- You can host it on your own S3 bucket, Cloudflare R2, Cloudflare Workers, or private CDN.
- All code and schemas are licensed under the permissive MIT license.

---

## 2. Technical & Architectural Questions

### Why use a 2-level sharded directory structure?
Operating systems and Git performance can degrade when a single directory contains tens of thousands of files. By sharding files into `lyrics-database/{dir1}/{dir2}/{videoId}.json` (where `dir1` and `dir2` are the first two characters of the YouTube video ID), we distribute files across 4,000+ buckets (64 x 64 combinations), ensuring instantaneous file lookups and smooth Git operations even at 1,000,000+ tracks.

### How are word-level timestamps generated?
Word-level timings originate from three primary sources:
1. **Local Acoustic Alignment**: In the Zuke Android app, songs are aligned using syllable and phonetic duration weighting or quantized local Wav2Vec2 CTC alignment models against audio waveforms.
2. **TTML Conversion**: Extracting syllable spans from official artist TTML (Timed Text Markup Language) captions.
3. **Enhanced LRC Transcriptions**: Transcribing audio with millisecond word tags using tools like Whisper, CTC aligners, or manual community timing tools.

### What happens if a track does not have word-level sync yet?
If a track only has line-level timestamps, `hasWordSync` is set to `false`, and lines contain only `time`, `endTime`, and `text` (the `words` array is omitted). Music player clients will seamlessly fall back to classic line-by-line karaoke highlighting.

---

## 3. Integration & Usage

### What if the YouTube Video ID has different video versions (Music Video vs Audio)?
We recommend using the **YouTube Music Official Audio** video ID as the primary key. If a song has popular alternative video IDs, multiple JSON files can point to the same synced data or community PRs can submit entries for both IDs.

### How does my app handle offline playback?
Because ZLF files are lightweight JSON documents (typically 3KB to 15KB per song), apps can cache retrieved files in local SQLite/Room/IndexedDB storage. When offline, simply check the local cache before attempting network queries.

### Is CORS supported for web browsers?
**Yes.** Both jsDelivr and GitHub Raw send `Access-Control-Allow-Origin: *` headers, allowing Web apps, Single-Page Apps (React/Vue/Svelte), and browser extensions to make direct client-side `fetch()` requests without proxy servers.

---

## 4. Contributing & Moderation

### How are submitted lyrics moderated?
All contributions submitted via the GitHub Issue Gateway or Pull Requests must pass our strict automated CI validator (`tools/validator.py`), which checks:
- Strict JSON Schema adherence.
- Time monotonicity (timestamps cannot move backward).
- Word timing containment (words must start and end within line bounds).
- Non-empty metadata.

Malicious or malformed submissions are automatically rejected before entering the main database.

### How do I correct lyrics with inaccurate timing or typos?
Open a [Correction Issue](https://github.com/dwip-the-dev/ZukeLyrics/issues/new?template=02_lyrics_correction.yml) or submit a Pull Request modifying the JSON file. Our automated bot will validate the update and re-build the search catalog.
