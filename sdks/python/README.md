# 🐍 ZukeLyrics Python SDK

Official Python client for accessing the **ZukeLyrics** crowdsourced word-by-word synchronized lyrics ecosystem. Works with Python 3.8+.

---

## 🚀 Installation

```bash
pip install zukelyrics
```

*(Or copy `zukelyrics/` directly into your project)*

---

## ⚡ Quickstart

```python
from zukelyrics import ZukeLyricsClient

client = ZukeLyricsClient()

# Fetch lyrics for Rick Astley - Never Gonna Give You Up
track = client.get_lyrics("dQw4w9WgXcQ")

if track:
    print(f"Track: {track.title} by {track.artist}")
    print(f"Duration: {track.duration}ms | Word Synced: {track.has_word_sync}")
    
    for line in track.lines:
        print(f"[{line.time}ms] {line.text}")
        if line.words:
            for w in line.words:
                print(f"   Word: '{w.word}' ({w.start_time}ms - {w.end_time}ms)")
else:
    print("Track not found.")
```

---

## 🔍 Catalog & Search

```python
# Get global catalog
catalog = client.get_catalog()
print(f"Total catalog tracks: {len(catalog)}")

# Fast search
results = client.search("bohemian")
for r in results:
    print(f"Found: {r['title']} - {r['artist']} (ID: {r['id']})")
```

---

## 📜 License
MIT
