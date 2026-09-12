# 📦 ZukeLyrics TypeScript / JavaScript SDK

Official TypeScript and JavaScript client for accessing the **ZukeLyrics** crowdsourced word-by-word synchronized lyrics ecosystem. Works in Node.js, Browsers, React, Next.js, Electron, and React Native.

---

## 🚀 Installation

```bash
npm install zukelyrics
# or
yarn add zukelyrics
# or
pnpm add zukelyrics
```

---

## ⚡ Quickstart

```typescript
import { ZukeLyricsClient } from 'zukelyrics';

const client = new ZukeLyricsClient();

async function run() {
  // Fetch word-synced lyrics for Queen - Bohemian Rhapsody
  const track = await client.getLyrics('fJ9rUzIMcZQ');
  
  if (track) {
    console.log(`Title: ${track.title} - ${track.artist}`);
    console.log(`Word-synced: ${track.hasWordSync}`);

    // Print lines and word timings
    for (const line of track.lines) {
      console.log(`[${line.time}ms] ${line.text}`);
      line.words?.forEach(w => {
        console.log(`  -> ${w.word} (${w.startTime}ms - ${w.endTime}ms)`);
      });
    }
  } else {
    console.log('Lyrics not found.');
  }
}

run();
```

---

## 🛠️ API Reference

### `new ZukeLyricsClient(options?)`
Creates a new client instance.

Options:
- `primaryCdnUrl?: string`: Defaults to jsDelivr edge CDN.
- `secondaryCdnUrl?: string`: Defaults to GitHub raw content CDN.
- `timeoutMs?: number`: HTTP request timeout in milliseconds (default: `5000`).

### `client.getLyrics(videoId: string): Promise<ZukeLyricsTrack | null>`
Fetches synchronized lyrics for a YouTube video ID. Returns `null` if not found.

### `client.getCatalog(): Promise<CatalogEntry[]>`
Fetches the full lightweight catalog of all verified tracks.

### `client.search(query: string): Promise<SearchTrack[]>`
Searches the track index by title or artist.

### `client.getStats(): Promise<RepoStats>`
Returns real-time repository statistics (total tracks, word-synced tracks, languages).

---

## 📜 License
MIT
