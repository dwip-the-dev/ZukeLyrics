# 🛠️ ZukeLyrics CLI & Conversion Manual

The ZukeLyrics ecosystem includes a full-featured CLI converter (`tools/converter.py`) and validator (`tools/validator.py`) capable of converting between **ZLF JSON**, **TTML (Apple Music / YouTube)**, **Standard LRC**, **Enhanced Rich-Sync LRC**, and **SubRip (SRT)** subtitles.

---

## 📑 Table of Contents
1. [Installation & Requirements](#installation--requirements)
2. [Commands Overview](#commands-overview)
3. [Format Conversion Details](#format-conversion-details)
   - [TTML to ZLF (`ttml2zlf`)](#1-ttml-to-zlf-ttml2zlf)
   - [LRC & Rich-Sync LRC to ZLF (`lrc2zlf`)](#2-lrc--rich-sync-lrc-to-zlf-lrc2zlf)
   - [ZLF to Apple TTML (`zlf2ttml`)](#3-zlf-to-apple-ttml-zlf2ttml)
   - [ZLF to Enhanced LRC (`zlf2richlrc`)](#4-zlf-to-enhanced-lrc-zlf2richlrc)
   - [ZLF to Standard LRC (`zlf2lrc`)](#5-zlf-to-standard-lrc-zlf2lrc)
   - [ZLF to SubRip SRT (`zlf2srt`)](#6-zlf-to-subrip-srt-zlf2srt)
4. [Automated Batch Processing](#automated-batch-processing)
5. [Database Validation (`validator.py`)](#database-validation-validatorpy)

---

## 💻 Installation & Requirements

The tools require Python 3.8+ with no heavy external dependencies (`jsonschema` is optional for schema validation):

```bash
cd ZukeLyrics
python3 -m pip install jsonschema  # Optional, validator has built-in AST checks
```

---

## 📋 Commands Overview

```bash
python3 tools/converter.py <command> <input_file> [output_file] [options]
```

| Command | Input Format | Output Format | Word-Level Timing Preserved? |
| :--- | :--- | :--- | :---: |
| `ttml2zlf` | Timed Text XML (`.ttml`) | ZLF JSON | ✅ Yes |
| `lrc2zlf` | Standard / Enhanced LRC (`.lrc`) | ZLF JSON | ✅ Yes (if `<mm:ss.xx>`) |
| `zlf2ttml` | ZLF JSON | Timed Text XML (`.ttml`) | ✅ Yes |
| `zlf2richlrc` | ZLF JSON | Enhanced LRC (`.lrc`) | ✅ Yes |
| `zlf2lrc` | ZLF JSON | Standard LRC (`.lrc`) | ❌ Line-only |
| `zlf2srt` | ZLF JSON | SubRip Subtitle (`.srt`) | ❌ Line-only |

---

## 🔄 Format Conversion Details

### 1. TTML to ZLF (`ttml2zlf`)
Converts Apple Music or YouTube Music `.ttml` timed text XML files into ZLF format.

```bash
python3 tools/converter.py ttml2zlf \
  input_song.ttml \
  lyrics-database/a/b/ab123456789.json \
  --id "ab123456789" \
  --title "Song Title" \
  --artist "Artist Name" \
  --duration 240000 \
  --lang "en"
```

#### How it works:
- Automatically strips XML namespaces (`xmlns:ttml`, `itunes:metadata`).
- Extracts paragraph lines (`<p begin="..." end="...">`).
- Extracts word-level spans (`<span begin="..." end="...">word</span>`).
- Converts clock timestamps (`00:01:23.456` or `01:23.45`) to integer milliseconds.

---

### 2. LRC & Rich-Sync LRC to ZLF (`lrc2zlf`)
Supports both standard line-timed LRC (`[00:15.30]Line text`) and syllable-timed Enhanced LRC (`[00:15.30]<00:15.30>Word1 <00:15.80>Word2`).

```bash
python3 tools/converter.py lrc2zlf \
  lyrics.lrc \
  lyrics-database/x/y/xy123456789.json \
  --id "xy123456789" \
  --title "Song Title" \
  --artist "Artist Name"
```

#### Metadata Tags Parsed:
If the LRC file contains standard ID3/LRC tags, they are automatically parsed if CLI flags are omitted:
- `[ti:Song Title]` -> `title`
- `[ar:Artist Name]` -> `artist`
- `[al:Album Name]` -> `album`
- `[length:03:45]` -> `duration`

---

### 3. ZLF to Apple TTML (`zlf2ttml`)
Exports ZLF files back to standard W3C TTML XML suitable for media players that require subtitle tracks.

```bash
python3 tools/converter.py zlf2ttml \
  lyrics-database/f/J/fJ9rUzIMcZQ.json \
  output.ttml
```

---

### 4. ZLF to Enhanced LRC (`zlf2richlrc`)
Exports word-synced lyrics into the widely recognized Enhanced Rich-Sync LRC syntax:

```bash
python3 tools/converter.py zlf2richlrc \
  lyrics-database/f/J/fJ9rUzIMcZQ.json \
  output.lrc
```

Output format:
```
[00:45.000]<00:45.000>Is <00:45.300>this <00:45.600>the <00:45.900>real <00:46.500>life?
```

---

### 5. ZLF to Standard LRC (`zlf2lrc`)
Converts ZLF into universally compatible standard line-level LRC:

```bash
python3 tools/converter.py zlf2lrc \
  lyrics-database/f/J/fJ9rUzIMcZQ.json \
  standard.lrc
```

Output format:
```
[00:45.00]Is this the real life?
[00:49.10]Is this just fantasy?
```

---

### 6. ZLF to SubRip SRT (`zlf2srt`)
Converts ZLF into video subtitle `.srt` files:

```bash
python3 tools/converter.py zlf2srt \
  lyrics-database/f/J/fJ9rUzIMcZQ.json \
  subtitles.srt
```

---

## ⚡ Automated Batch Processing

Convert an entire folder of `.ttml` or `.lrc` files into the sharded database directory structure with this bash loop:

```bash
#!/usr/bin/env bash
set -e

INPUT_DIR="./incoming_ttml"
DB_DIR="./lyrics-database"

for file in "$INPUT_DIR"/*.ttml; do
  [ -f "$file" ] || continue
  # Extract video ID from filename: e.g. "dQw4w9WgXcQ.ttml"
  VIDEO_ID=$(basename "$file" .ttml)
  DIR1="${VIDEO_ID:0:1}"
  DIR2="${VIDEO_ID:1:1}"
  
  OUT_DIR="$DB_DIR/$DIR1/$DIR2"
  mkdir -p "$OUT_DIR"
  
  echo "Converting $file -> $OUT_DIR/$VIDEO_ID.json"
  python3 tools/converter.py ttml2zlf "$file" "$OUT_DIR/$VIDEO_ID.json" --id "$VIDEO_ID"
done

# Rebuild catalog and indexes
python3 tools/index_builder.py
```

---

## ✅ Database Validation (`validator.py`)

Always run the validator before submitting pull requests:

```bash
# Validate entire database
python3 tools/validator.py lyrics-database/

# Validate a single file
python3 tools/validator.py lyrics-database/d/Q/dQw4w9WgXcQ.json
```

The validator checks:
1. Valid JSON and UTF-8 encoding.
2. Compliance with `schemas/zlf-v1.schema.json`.
3. Non-empty string fields for `id`, `title`, `artist`, `language`.
4. Monotonically increasing line timestamps (`line[i].time >= line[i-1].time`).
5. Line interval validity (`line.endTime > line.time`).
6. Word timing boundaries (`line.time <= word.startTime < word.endTime <= line.endTime`).
7. Word sequencing within lines (`word[j].startTime >= word[j-1].startTime`).
