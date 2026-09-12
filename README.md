# 🎵 ZukeLyrics

[![ZukeLyrics CI](https://github.com/dwip-the-dev/ZukeLyrics/actions/workflows/validate.yml/badge.svg)](https://github.com/dwip-the-dev/ZukeLyrics/actions/workflows/validate.yml)
[![Build Indexes](https://github.com/dwip-the-dev/ZukeLyrics/actions/workflows/build_indexes.yml/badge.svg)](https://github.com/dwip-the-dev/ZukeLyrics/actions/workflows/build_indexes.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Format: ZLF v1.0](https://img.shields.io/badge/Format-ZLF%20v1.0-blue.svg)](schemas/zlf-v1.schema.json)
[![CDN: jsDelivr & GitHub](https://img.shields.io/badge/CDN-Global%20Fastly%20%2F%20Cloudflare-green.svg)](docs/API_REFERENCE.md)

> **The Universal, Free, High-Performance Crowdsourced Word-by-Word Lyrics Standard & CDN API.**  
> Built for open-source music players, streamers, and developers worldwide.

---

## 🌟 Why ZukeLyrics?

Existing lyrics providers like LRCLIB are fantastic, but standard LRC timestamps only offer **line-level** synchronization (`[01:23.45] Some lyric`). Proprietary streaming services (Apple Music, Spotify) offer syllable and word-level karaoke animations, but keep their rich sync data locked behind closed, DRM-restricted APIs.

**ZukeLyrics** solves this once and for all:
- **Zero API Keys & Zero Rate Limits**: Free public access via global edge CDNs (GitHub Raw, jsDelivr, Fastly).
- **Millisecond-Precise Word-by-Word Sync**: Syllable and word timestamps enable fluid Apple Music-style glowing karaoke animations.
- **ZLF (ZukeLyrics Format) Standard**: A lightweight, strictly-typed JSON standard supporting word timing, romanization, translations, vocal agents, and duets.
- **Bidirectional Tooling**: Convert to and from **TTML**, **Enhanced Rich-Sync LRC** (`<mm:ss.xx>word`), **Standard LRC**, and **SRT**.
- **Community-Powered Automated Gateway**: Submit or correct lyrics directly through GitHub Issues or the Zuke mobile app with zero Git knowledge required.

---

## 🚀 CDN API Endpoints

ZukeLyrics uses a deterministic **2-level sharded directory structure** based on the 11-character YouTube video ID:
`lyrics-database/{videoId[0]}/{videoId[1]}/{videoId}.json`

### 1. Direct Track Lookup

| CDN Provider | URL Template | Features |
| :--- | :--- | :--- |
| **jsDelivr (Recommended)** | `https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/{dir1}/{dir2}/{videoId}.json` | Global Anycast CDN, HTTP/3, Brotli, aggressive edge caching |
| **GitHub Raw (Instant)** | `https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/lyrics-database/{dir1}/{dir2}/{videoId}.json` | Real-time updates immediately on commit |

#### Example Track: *Queen – Bohemian Rhapsody* (`fJ9rUzIMcZQ`)
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/f/J/fJ9rUzIMcZQ.json" | jq .
```

### 2. Catalog & Search Index

| Resource | jsDelivr URL | GitHub Raw URL |
| :--- | :--- | :--- |
| **Global Catalog** | `https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/catalog.json` | `https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/index/catalog.json` |
| **Fast Search Index** | `https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/search-index.json` | `https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/index/search-index.json` |
| **Repository Stats** | `https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/api/v1/stats.json` | `https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/api/v1/stats.json` |

---

## ⚡ Quickstart in 5 Languages

### 1. Kotlin / Android

```kotlin
import com.zukelyrics.sdk.ZukeLyricsClient
import kotlinx.coroutines.runBlocking

val client = ZukeLyricsClient()

runBlocking {
    val lyrics = client.getLyrics("fJ9rUzIMcZQ")
    if (lyrics != null) {
        println("Found: ${lyrics.title} by ${lyrics.artist}")
        println("Word synced? ${lyrics.hasWordSync}")
        
        lyrics.lines.forEach { line ->
            println("[${line.time}ms] ${line.text}")
            line.words?.forEach { word ->
                println("  └── Word: '${word.word}' (${word.startTime}ms - ${word.endTime}ms)")
            }
        }
    }
}
```

### 2. TypeScript / JavaScript (Node.js & Web)

```typescript
import { ZukeLyricsClient } from 'zukelyrics';

const client = new ZukeLyricsClient();
const lyrics = await client.getLyrics('dQw4w9WgXcQ');

if (lyrics) {
  console.log(`Now playing: ${lyrics.title} by ${lyrics.artist}`);
  for (const line of lyrics.lines) {
    console.log(`Line: ${line.text}`);
    line.words?.forEach(w => console.log(`  ${w.word} [${w.startTime}-${w.endTime}]`));
  }
}
```

### 3. Python

```python
from zukelyrics import ZukeLyricsClient

client = ZukeLyricsClient()
lyrics = client.get_lyrics("fJ9rUzIMcZQ")

if lyrics:
    print(f"Title: {lyrics.title} - {lyrics.artist}")
    for line in lyrics.lines:
        print(f"[{line.time}ms] {line.text}")
```

### 4. Swift / iOS

```swift
let url = URL(string: "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/f/J/fJ9rUzIMcZQ.json")!
let (data, _) = try await URLSession.shared.data(from: url)
let lyrics = try JSONDecoder().decode(ZukeLyricsTrack.self, from: data)
print("Loaded: \(lyrics.title)")
```

### 5. cURL / Shell

```bash
curl -sL "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/d/Q/dQw4w9WgXcQ.json" \
  | jq '{title: .title, artist: .artist, first_line: .lines[0]}'
```

---

## 📊 Format Comparison

| Feature | Standard LRC | Enhanced LRC | Apple TTML | **ZLF (ZukeLyrics)** |
| :--- | :---: | :---: | :---: | :---: |
| **Line-Level Sync** | ✅ | ✅ | ✅ | ✅ |
| **Word-Level Sync** | ❌ | ✅ (`<mm:ss.xx>`) | ✅ (`<span begin=..>`) | ✅ (`startTime`/`endTime`) |
| **Millisecond Precision** | Centisecond | Centisecond | Millisecond | **Millisecond** |
| **JSON Native** | ❌ | ❌ | ❌ (XML) | ✅ |
| **Romanization** | ❌ | ❌ | ❌ | ✅ (`romanized`) |
| **Multi-Language Translations** | ❌ | ❌ | Partial | ✅ (`translations`) |
| **Duets / Multiple Singers** | ❌ | ❌ | ✅ | ✅ (`agent`) |
| **Free Open CDN Distribution** | ❌ | ❌ | ❌ | ✅ |

---

## 🛠️ CLI Tools & Converters

ZukeLyrics ships with a built-in Python toolkit in `tools/`:

```bash
# Validate database or a single file
python3 tools/validator.py lyrics-database/

# Convert Apple Music / YouTube Music TTML to ZLF
python3 tools/converter.py ttml2zlf track.ttml output.json --id "abc12345678" --title "Song Title" --artist "Artist Name"

# Convert Enhanced LRC (<00:01.23>word) to ZLF
python3 tools/converter.py lrc2zlf synced.lrc output.json --id "abc12345678" --title "Song" --artist "Artist"

# Export ZLF back to TTML XML
python3 tools/converter.py zlf2ttml lyrics-database/f/J/fJ9rUzIMcZQ.json exported.ttml

# Export ZLF to SubRip Subtitles (SRT)
python3 tools/converter.py zlf2srt lyrics-database/f/J/fJ9rUzIMcZQ.json subtitles.srt

# Rebuild search and catalog indexes
python3 tools/index_builder.py
```

---

## 📂 Project Architecture

```
ZukeLyrics/
├── .github/
│   ├── ISSUE_TEMPLATE/       # GitHub Web Form templates for zero-git contributions
│   └── workflows/
│       ├── validate.yml       # Automated PR and push CI validation
│       ├── build_indexes.yml  # Auto-rebuilds catalog & search index on updates
│       └── issue_bot.yml      # Bot that automatically verifies & merges submitted issues
├── api/
│   └── v1/
│       └── stats.json         # Real-time aggregated repository statistics
├── docs/                      # Comprehensive Documentation Suite
│   ├── API_REFERENCE.md       # Complete REST & CDN API documentation
│   ├── SPECIFICATION.md       # Formal ZLF v1.0 data standard specification
│   ├── INTEGRATION_GUIDE.md   # Step-by-step app integration (Android, Web, iOS, Bots)
│   ├── CONVERTER_CLI.md       # Comprehensive format converter manual
│   ├── CONTRIBUTING.md        # How to submit and correct lyrics
│   └── FAQ.md                 # Frequently asked questions
├── index/
│   ├── catalog.json           # Lightweight index of all verified tracks
│   └── search-index.json      # Inverted substring search index for fast lookup
├── lyrics-database/           # Sharded lyrics files ({dir1}/{dir2}/{videoId}.json)
│   ├── d/Q/dQw4w9WgXcQ.json   # Rick Astley - Never Gonna Give You Up
│   └── f/J/fJ9rUzIMcZQ.json   # Queen - Bohemian Rhapsody
├── schemas/
│   └── zlf-v1.schema.json     # Formal JSON Schema (draft-07)
├── sdks/
│   ├── kotlin/                # Official Kotlin / Android SDK
│   ├── python/                # Official Python SDK
│   └── typescript/            # Official TypeScript / JavaScript SDK
└── tools/
    ├── validator.py           # Strict schema & timing validator
    ├── converter.py           # Bidirectional converter (TTML, LRC, Rich LRC, SRT)
    ├── index_builder.py       # Catalog & search index generator
    └── tests/                 # Complete unit test suite
```

---

## 🤝 Contributing & Automated Ingestion

Anyone can submit or correct lyrics! We support two methods:

1. **GitHub Issue Gateway (Easiest)**: Go to [New Issue](https://github.com/dwip-the-dev/ZukeLyrics/issues/new/choose), select **Submit New Lyrics** or **Correct Existing Lyrics**, fill in the fields, and our automated GitHub Actions Bot will validate the timing and commit the file automatically!
2. **Pull Request**: Clone the repo, add your file under `lyrics-database/{d1}/{d2}/{videoId}.json`, run `python3 tools/validator.py`, and submit a PR.

For detailed guidelines, see [CONTRIBUTING.md](docs/CONTRIBUTING.md).

---

## 📜 License

ZukeLyrics code, schemas, tools, and SDKs are distributed under the [MIT License](LICENSE).  
Lyrics metadata and text timings are community contributions distributed for transformative personal playback and accessibility.
