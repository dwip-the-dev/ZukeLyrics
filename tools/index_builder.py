#!/usr/bin/env python3
"""
ZukeLyrics Index Builder
Generates compact catalog, search index, and statistics for static CDN consumption.
"""

import os
import json
from pathlib import Path

def build_indexes(base_dir="."):
    lyrics_dir = Path(base_dir) / "lyrics-database"
    index_dir = Path(base_dir) / "index"
    api_dir = Path(base_dir) / "api" / "v1"

    index_dir.mkdir(parents=True, exist_ok=True)
    api_dir.mkdir(parents=True, exist_ok=True)

    catalog = []
    search_index = {}
    stats = {
        "totalTracks": 0,
        "wordSynced": 0,
        "lineSynced": 0,
        "plain": 0,
        "instrumental": 0,
        "languages": {},
        "artists": set()
    }

    for json_file in lyrics_dir.rglob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Skipping {json_file}: {e}")
            continue

        video_id = data.get("videoId")
        if not video_id:
            continue

        title = data.get("title", "Unknown")
        artist = data.get("artist", "Unknown")
        synced_type = data.get("syncedType", "line")
        language = data.get("language", "und")
        duration = data.get("duration", 0)
        lines = data.get("lines", [])

        rel_path = f"lyrics-database/{json_file.relative_to(lyrics_dir)}"

        catalog_entry = {
            "videoId": video_id,
            "title": title,
            "artist": artist,
            "duration": duration,
            "language": language,
            "syncedType": synced_type,
            "linesCount": len(lines),
            "path": rel_path
        }
        catalog.append(catalog_entry)

        # Build search keywords
        keywords = [
            video_id.lower(),
            title.lower(),
            artist.lower(),
            f"{artist} {title}".lower()
        ]
        if data.get("isrc"):
            keywords.append(data["isrc"].lower())

        for kw in keywords:
            if kw not in search_index:
                search_index[kw] = []
            if video_id not in search_index[kw]:
                search_index[kw].append(video_id)

        # Accumulate stats
        stats["totalTracks"] += 1
        if synced_type == "word":
            stats["wordSynced"] += 1
        elif synced_type == "line":
            stats["lineSynced"] += 1
        elif synced_type == "plain":
            stats["plain"] += 1
        elif synced_type == "instrumental":
            stats["instrumental"] += 1

        stats["languages"][language] = stats["languages"].get(language, 0) + 1
        stats["artists"].add(artist)

    stats["uniqueArtists"] = len(stats["artists"])
    stats.pop("artists")

    # Write catalog.json and catalog.min.json
    catalog_path = index_dir / "catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    with open(index_dir / "catalog.min.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, separators=(',', ':'), ensure_ascii=False)
    print(f"Generated {catalog_path} with {len(catalog)} tracks")

    # Generate ultra-fast O(1) ID set index
    all_ids = sorted([c["videoId"] for c in catalog])
    ids_path = index_dir / "ids.json"
    with open(ids_path, "w", encoding="utf-8") as f:
        json.dump(all_ids, f, indent=2, ensure_ascii=False)
    ids_min_path = index_dir / "ids.min.json"
    with open(ids_min_path, "w", encoding="utf-8") as f:
        json.dump(all_ids, f, separators=(',', ':'), ensure_ascii=False)
    print(f"Generated {ids_path} & {ids_min_path} ({len(all_ids)} IDs)")

    # Generate high-speed lookup table: videoId -> compact metadata
    lookup = {
        c["videoId"]: {
            "p": c["path"].replace("lyrics-database/", ""),
            "t": c["syncedType"],
            "d": c["duration"],
            "a": c["artist"],
            "s": c["title"],
            "l": c["language"]
        }
        for c in catalog
    }
    lookup_path = index_dir / "lookup.json"
    with open(lookup_path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, indent=2, ensure_ascii=False)
    lookup_min_path = index_dir / "lookup.min.json"
    with open(lookup_min_path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, separators=(',', ':'), ensure_ascii=False)
    print(f"Generated {lookup_path} & {lookup_min_path}")

    # Generate sharded index for scalable partitioned downloads
    shards_dir = index_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    shards = {}
    for vid, meta in lookup.items():
        prefix = vid[0].lower() if vid and vid[0].isalnum() else "_"
        if prefix not in shards:
            shards[prefix] = {}
        shards[prefix][vid] = meta

    for prefix, shard_data in shards.items():
        shard_path = shards_dir / f"{prefix}.json"
        with open(shard_path, "w", encoding="utf-8") as f:
            json.dump(shard_data, f, separators=(',', ':'), ensure_ascii=False)
    print(f"Generated {len(shards)} prefix shards in {shards_dir}")

    # Write search-index.json and search-index.min.json
    search_path = index_dir / "search-index.json"
    with open(search_path, "w", encoding="utf-8") as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
    with open(index_dir / "search-index.min.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, separators=(',', ':'), ensure_ascii=False)
    print(f"Generated {search_path}")

    # Write api/v1/stats.json
    stats_path = api_dir / "stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Generated {stats_path}")

if __name__ == "__main__":
    build_indexes()
