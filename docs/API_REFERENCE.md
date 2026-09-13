# 🌐 ZukeLyrics API Reference

Welcome to the **ZukeLyrics API Reference**. ZukeLyrics is engineered from the ground up as a **serverless, globally distributed CDN API**. Unlike traditional REST services hosted on fragile single servers or cloud functions with rate limits and quota walls, ZukeLyrics serves directly from Anycast edge points across hundreds of worldwide PoPs (Points of Presence) via jsDelivr and GitHub.

---

## 📑 Table of Contents
1. [Core Architecture & Principles](#core-architecture--principles)
2. [Base URLs & CDN Routing](#base-urls--cdn-routing)
3. [Endpoints](#endpoints)
   - [1. Single Track Lookup](#1-single-track-lookup)
   - [2. Global Track Catalog](#2-global-track-catalog)
   - [3. Substring Search Index](#3-substring-search-index)
   - [4. Repository Statistics](#4-repository-statistics)
4. [Client Implementation Best Practices](#client-implementation-best-practices)
5. [Programmatic Submissions API](#programmatic-submissions-api)
6. [Error Handling & Edge Cases](#error-handling--edge-cases)

---

## 🏛️ Core Architecture & Principles

- **Zero Authentication Required**: All read queries are completely open. No API keys, no bearer tokens, no signups.
- **Zero Rate Limits**: Powered by Fastly and Cloudflare edge caches. You can query thousands of tracks without being IP-banned.
- **CORS Enabled**: All endpoints return `Access-Control-Allow-Origin: *`, allowing direct client-side fetch calls from browsers, Electron, Tauri, and mobile apps.
- **Deterministic 2-Level Sharding**: To prevent git and filesystem performance bottlenecks at scale (1,000,000+ files), files are sharded by the first two characters of their YouTube video ID:
  ```
  lyrics-database / {videoId[0]} / {videoId[1]} / {videoId}.json
  ```
  *Example*: `fJ9rUzIMcZQ` -> `f` -> `J` -> `lyrics-database/f/J/fJ9rUzIMcZQ.json`

---

## 🌐 Base URLs & CDN Routing

ZukeLyrics is accessible through two primary mirrors:

| Provider | Base URL | Caching Policy | Best For |
| :--- | :--- | :--- | :--- |
| **jsDelivr (Primary CDN)** | `https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/` | 12 hours edge cache (HTTP/3, Brotli, Cloudflare/Fastly) | Production mobile, desktop & web apps |
| **GitHub Raw (Secondary CDN)** | `https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/` | 5 minutes cache (`Cache-Control: max-age=300`) | Instant updates right after submission / commit |

### Recommended Multi-CDN Fallback Algorithm

Production music players should implement a graceful fallback:

```
                  ┌────────────────────────┐
                  │ Request YouTube Song   │
                  └───────────┬────────────┘
                              │
                              ▼
                 ┌───────────────────────────┐
                 │ 1. Try jsDelivr CDN       │
                 └────────────┬──────────────┘
                              │
                    Success? ─┴──► Yes ──► [ Return Lyrics ]
                              │
                             No (Timeout / 5xx)
                              │
                              ▼
                 ┌───────────────────────────┐
                 │ 2. Try GitHub Raw CDN     │
                 └────────────┬──────────────┘
                              │
                    Success? ─┴──► Yes ──► [ Return Lyrics ]
                              │
                             No (404 Not Found)
                              │
                              ▼
                 ┌───────────────────────────┐
                 │ 3. Fallback to Local/LRC  │
                 └───────────────────────────┘
```

---

## 📡 Endpoints

### 1. Single Track Lookup

Retrieves the millisecond-accurate synchronized lyrics in ZLF v1 format for a specific track.

#### HTTP Request
`GET /lyrics-database/{dir1}/{dir2}/{videoId}.json`

#### Parameters
| Name | Type | In | Description |
| :--- | :--- | :--- | :--- |
| `dir1` | `string` | path | First character of the YouTube video ID (`videoId[0]`) |
| `dir2` | `string` | path | Second character of the YouTube video ID (`videoId[1]`) |
| `videoId` | `string` | path | 11-character YouTube video ID (e.g. `dQw4w9WgXcQ`) |

#### Example Request
```bash
curl -i "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/d/Q/dQw4w9WgXcQ.json"
```

#### Response Headers
```http
HTTP/2 200 OK
content-type: application/json; charset=utf-8
access-control-allow-origin: *
cache-control: public, max-age=43200, s-maxage=43200
etag: W/"..."
```

#### Response Body (JSON)
```json
{
  "$schema": "https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/schemas/zlf-v1.schema.json",
  "version": "1.0",
  "id": "dQw4w9WgXcQ",
  "title": "Never Gonna Give You Up",
  "artist": "Rick Astley",
  "album": "Whenever You Need Somebody",
  "duration": 213000,
  "language": "en",
  "hasWordSync": true,
  "lines": [
    {
      "time": 18450,
      "endTime": 22100,
      "text": "We're no strangers to love",
      "words": [
        { "word": "We're", "startTime": 18450, "endTime": 18900 },
        { "word": "no", "startTime": 18910, "endTime": 19350 },
        { "word": "strangers", "startTime": 19360, "endTime": 20400 },
        { "word": "to", "startTime": 20410, "endTime": 20850 },
        { "word": "love", "startTime": 20860, "endTime": 22100 }
      ]
    }
  ]
}
```

#### Field Definitions
| Field | Type | Description |
| :--- | :--- | :--- |
| `version` | `string` | Format specification version (currently `"1.0"`) |
| `id` | `string` | Canonical YouTube 11-character video ID |
| `title` | `string` | Song title |
| `artist` | `string` | Artist / Performer name |
| `album` | `string?` | Optional album name |
| `duration` | `integer` | Track duration in milliseconds |
| `language` | `string` | Primary language ISO 639-1 code (e.g. `"en"`, `"ja"`, `"es"`) |
| `hasWordSync` | `boolean` | `true` if line contains word/syllable timing array |
| `lines` | `array` | List of line objects |
| `lines[].time` | `integer` | Line start time in milliseconds |
| `lines[].endTime` | `integer` | Line end time in milliseconds |
| `lines[].text` | `string` | Full textual line |
| `lines[].words` | `array?` | Array of word objects (`startTime`, `endTime`, `word`) |
| `lines[].romanized`| `string?` | Optional romanized text for non-Latin scripts |
| `lines[].translations`| `object?` | Optional dictionary of translated lines keyed by ISO code |

---

### 2. Global Track Catalog

Retrieves the lightweight catalog of all verified tracks currently available in the ZukeLyrics database. Ideal for initial sync, offline caching, and pre-loading.

#### HTTP Request
`GET /index/catalog.json`

#### Example Request
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/catalog.json"
```

#### Response Body (JSON)
```json
[
  {
    "id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "artist": "Rick Astley",
    "duration": 213000,
    "hasWordSync": true,
    "language": "en",
    "path": "lyrics-database/d/Q/dQw4w9WgXcQ.json"
  }
]
```

---

### 3. Ultra-Fast Global ID Index (Instant Availability Check)

Returns a lightweight, minimal array of all available YouTube `videoId` strings in the entire database.

**Why use this?**
- Eliminates 404 network roundtrips: music apps can download this once (~10 KB gzipped) and instantly check in-memory (`availableIds.contains(id)`) in **0.001 ms** whether lyrics exist before making any network calls!
- Perfect for batch playlist checking: verify 100 songs in under **1 millisecond**.

#### HTTP Request
`GET /index/ids.min.json` (or `/index/ids.json` formatted)

#### Example Request
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/ids.min.json"
```

#### Response Body (JSON)
```json
["0vPdpUiVWi8","2cnloO84LA0","by4SYYWlhVE","dQw4w9WgXcQ","fJ9rUzIMcZQ","tvTRZJ-4EyI"]
```

---

### 4. High-Speed Key-Value Lookup Map

Returns a direct hash map of `videoId` to compact track metadata.

#### HTTP Request
`GET /index/lookup.min.json` (or `/index/lookup.json` formatted)

#### Example Request
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/lookup.min.json"
```

#### Response Body (JSON)
```json
{
  "fJ9rUzIMcZQ": {
    "p": "f/J/fJ9rUzIMcZQ.json",
    "t": "word",
    "d": 354,
    "a": "Queen",
    "s": "Bohemian Rhapsody",
    "l": "en"
  }
}
```

---

### 5. Prefix Sharded Index

For low-memory devices or large-scale partitioned fetching, download lyrics metadata for tracks starting with a specific character.

#### HTTP Request
`GET /index/shards/{prefix}.json` (e.g. `0`, `a`, `b`, `f`)

#### Example Request
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/shards/f.json"
```

#### Response Body (JSON)
```json
[
  {
    "id": "fJ9rUzIMcZQ",
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "duration": 355000,
    "hasWordSync": true,
    "language": "en",
    "path": "lyrics-database/f/J/fJ9rUzIMcZQ.json"
  }
]
```

---

### 3. Substring Search Index

A compact index optimized for rapid client-side search without downloading full lyrics files. Maps normalized lowercase tokens and titles to track metadata.

#### HTTP Request
`GET /index/search-index.json`

#### Example Request
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/index/search-index.json"
```

#### Response Body (JSON)
```json
{
  "tracks": [
    {
      "id": "dQw4w9WgXcQ",
      "title": "Never Gonna Give You Up",
      "artist": "Rick Astley",
      "searchKey": "never gonna give you up rick astley"
    },
    {
      "id": "fJ9rUzIMcZQ",
      "title": "Bohemian Rhapsody",
      "artist": "Queen",
      "searchKey": "bohemian rhapsody queen"
    }
  ]
}
```

---

### 4. Repository Statistics

Provides real-time aggregate health and metadata statistics about the ZukeLyrics ecosystem.

#### HTTP Request
`GET /api/v1/stats.json`

#### Example Request
```bash
curl -s "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/api/v1/stats.json"
```

#### Response Body (JSON)
```json
{
  "totalTracks": 2,
  "wordSyncedTracks": 2,
  "lineSyncedTracks": 0,
  "languages": {
    "en": 2
  },
  "updatedUtc": "2026-09-12T17:11:59Z"
}
```

---

## ⚡ Client Implementation Best Practices

### 1. In-Memory & On-Disk Caching
Since synchronized lyrics files are immutable for a given recording, clients should store fetched tracks in a local key-value store (e.g., Room database in Android, IndexedDB in browsers, SQLite in Python/Rust/Go).

```typescript
// Pseudocode for client-side cache
async function getLyricsWithCache(videoId: string) {
  const cached = await localDb.get(videoId);
  if (cached) return cached;

  const res = await fetch(`https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/${videoId[0]}/${videoId[1]}/${videoId}.json`);
  if (res.status === 200) {
    const data = await res.json();
    await localDb.set(videoId, data);
    return data;
  }
  return null;
}
```

### 2. HTTP ETag / Conditional Requests
When re-checking whether a track has been updated or corrected:
```http
GET /lyrics-database/f/J/fJ9rUzIMcZQ.json HTTP/1.1
Host: cdn.jsdelivr.net
If-None-Match: W/"your-saved-etag"
```
If the track hasn't changed, the CDN immediately returns `304 Not Modified` with zero payload body transfer.

---

## 🤖 Programmatic Submissions API

Music apps, AI aligners, and automated tools can submit crowd-generated word-level sync data to ZukeLyrics using the **GitHub Issue Gateway**.

### Submission via GitHub REST API

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/dwip-the-dev/ZukeLyrics/issues \
  -d '{
    "title": "Lyrics Submission: Bohemian Rhapsody (fJ9rUzIMcZQ)",
    "labels": ["lyrics-submission"],
    "body": "### YouTube Video ID\nfJ9rUzIMcZQ\n\n### Song Title\nBohemian Rhapsody\n\n### Artist Name\nQueen\n\n### Track Duration (Seconds)\n355\n\n### Language Code\nen\n\n### Synchronized Lyrics Data (ZLF JSON or Enhanced LRC)\n```json\n{\n  \"version\": \"1.0\",\n  \"id\": \"fJ9rUzIMcZQ\",\n  ...\n}\n```"
  }'
```

### Automated Ingestion Bot Lifecycle
1. User or application creates an issue with the label `lyrics-submission`.
2. The `.github/workflows/issue_bot.yml` GitHub Action triggers immediately.
3. The bot extracts the payload, runs `tools/validator.py` on the JSON data.
4. If validation passes:
   - File is written to `lyrics-database/{dir1}/{dir2}/{videoId}.json`.
   - `tools/index_builder.py` regenerates catalogs.
   - Commit is made to `main`.
   - Issue is closed automatically with a celebratory confirmation comment.
5. If validation fails:
   - Bot comments with exact line and timestamp violation details.
