# 📐 ZukeLyrics Format (ZLF v1.0) Specification

## Status: Official Standard (v1.0)

This document defines the formal data standard for **ZukeLyrics Format (ZLF) Version 1.0**. ZLF is a lightweight, human-readable, millisecond-accurate JSON standard created to represent line-synchronized, word-synchronized, multilingual, and vocal-agent-attributed lyrics for music players.

---

## 📑 Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Data Types & Constraints](#data-types--constraints)
3. [Mathematical Timing Rules](#mathematical-timing-rules)
4. [Tokenization & Whitespace Rules](#tokenization--whitespace-rules)
5. [Vocalist & Duet Modeling](#vocalist--duet-modeling)
6. [Multilingual Support (Translations & Romanization)](#multilingual-support-translations--romanization)
7. [JSON Schema Definition](#json-schema-definition)
8. [Validation Protocol](#validation-protocol)

---

## 💡 Design Philosophy

1. **Precision**: All timestamps are integer milliseconds (`ms`) from track offset `0`.
2. **Deterministic Hierarchy**: Tracks contain Lines; Lines contain Words. A word cannot exist outside a line.
3. **Lossless Conversion**: Any standard LRC, Enhanced LRC (`<mm:ss.xx>word`), SubRip (SRT), or TTML (Apple Music / Timed Text Markup Language) file can be converted into ZLF without losing sync information.
4. **Resilience**: A client that only supports line-level sync can ignore the `words` array and operate identically to standard LRC without performance penalty.

---

## 🧩 Data Types & Schema Structure

### Root Object (`ZukeLyricsTrack`)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `$schema` | `string` | No | URI reference to `zlf-v1.schema.json` |
| `version` | `string` | **Yes** | Constant `"1.0"` |
| `id` | `string` | **Yes** | 11-character YouTube video ID (`^[A-Za-z0-9_-]{11}$`) |
| `title` | `string` | **Yes** | Primary song title (non-empty) |
| `artist` | `string` | **Yes** | Primary artist/band name (non-empty) |
| `album` | `string` | No | Album title |
| `duration` | `integer`| **Yes** | Total track duration in milliseconds (positive integer) |
| `language` | `string` | **Yes** | BCP 47 / ISO 639-1 language code (e.g. `"en"`, `"ja"`, `"ko"`, `"es"`, `"hi"`) |
| `hasWordSync` | `boolean` | **Yes** | Must be `true` if at least one line has word timings; `false` otherwise |
| `lines` | `Line[]` | **Yes** | Non-empty array of synchronized lines |

---

### Line Object (`Line`)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `time` | `integer` | **Yes** | Line beginning in milliseconds (`>= 0`) |
| `endTime` | `integer` | **Yes** | Line ending in milliseconds (`> time`) |
| `text` | `string` | **Yes** | Complete textual content of the line |
| `words` | `Word[]` | No | List of word-level sync tokens |
| `romanized` | `string` | No | Romanized pronunciation (e.g. Romaji, Pinyin, Revised Romanization) |
| `translations`| `Map<string, string>` | No | Key-value pairs mapping ISO language codes to translated line text |
| `agent` | `string` | No | Vocalist identifier (e.g. `"Freddie Mercury"`, `"Lead"`, `"Chorus"`, `"Vocalist 1"`) |

---

### Word Object (`Word`)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `word` | `string` | **Yes** | Textual syllable or word token (non-empty) |
| `startTime` | `integer` | **Yes** | Syllable beginning in milliseconds (`>= 0`) |
| `endTime` | `integer` | **Yes** | Syllable ending in milliseconds (`> startTime`) |

---

## ⏱️ Mathematical Timing Rules

To ensure predictable animation curves in karaoke shaders and UI renderers, the following invariants are strictly enforced by `tools/validator.py`:

### 1. Line Monotonicity
Line start times must be non-decreasing:
$$\text{line}[i].\text{time} \ge \text{line}[i-1].\text{time} \quad \forall i > 0$$

### 2. Line Interval Validity
Every line must have a strictly positive duration:
$$\text{line}[i].\text{endTime} > \text{line}[i].\text{time}$$

### 3. Word Temporal Containment
Every word token must start at or after the line start time, and must end at or before the line end time:
$$\text{line}[i].\text{time} \le \text{word}[j].\text{startTime} < \text{word}[j].\text{endTime} \le \text{line}[i].\text{endTime}$$

### 4. Word Order Non-Decreasing
Words within the same line must be sequenced chronologically:
$$\text{word}[j].\text{startTime} \ge \text{word}[j-1].\text{startTime} \quad \forall j > 0$$

---

## 🔤 Tokenization & Whitespace Rules

### 1. Word Boundary Whitespace
When serializing words, whitespace should be handled as follows:
- The `words` array tokens themselves should contain the clean word token (or syllable).
- If trailing whitespace is necessary for rendering separation, it is derived from `line.text` or by inserting a space between consecutive words.
- In languages that do not use whitespace to delimit words (such as Japanese, Chinese, and Thai), each token represents an individual character or semantic morpheme.

### 2. Punctuation
- Commas, periods, question marks, and exclamation points should remain attached to the word they follow (e.g., `{"word": "love,", "startTime": 1000, "endTime": 1500}`).
- Opening quotes or parentheses attach to the subsequent word; closing ones attach to the preceding word.

---

## 🎤 Vocalist & Duet Modeling

In songs featuring multiple singers or back-and-forth duets, the `agent` attribute disambiguates who is singing:

```json
{
  "time": 45000,
  "endTime": 49000,
  "agent": "Singer A",
  "text": "Is this the real life?",
  "words": [ ... ]
},
{
  "time": 49100,
  "endTime": 53000,
  "agent": "Singer B",
  "text": "Is this just fantasy?",
  "words": [ ... ]
}
```

Music players can use the `agent` string to:
- Render text in distinct accent colors.
- Position lyrics on the left vs. right side of the screen (as in Apple Music Duet mode).

---

## 🌐 Multilingual Support (Translations & Romanization)

ZLF v1 natively embeds romanization and translations directly into the line object:

```json
{
  "time": 12000,
  "endTime": 15500,
  "text": "夜に駆ける",
  "romanized": "Yoru ni kakeru",
  "translations": {
    "en": "Racing into the night",
    "es": "Corriendo hacia la noche",
    "zh": "向夜晚奔去"
  },
  "words": [
    { "word": "夜", "startTime": 12000, "endTime": 12800 },
    { "word": "に", "startTime": 12810, "endTime": 13400 },
    { "word": "駆", "startTime": 13410, "endTime": 14200 },
    { "word": "け", "startTime": 14210, "endTime": 14800 },
    { "word": "る", "startTime": 14810, "endTime": 15500 }
  ]
}
```

---

## 📜 JSON Schema Definition

The canonical draft-07 JSON schema is maintained in [`schemas/zlf-v1.schema.json`](file:///home/dwip/Downloads/project/ZukeLyrics/schemas/zlf-v1.schema.json).

You can validate any document locally using standard schema validators:
```bash
# Python
pip install jsonschema
python3 -c "import jsonschema, json; jsonschema.validate(json.load(open('track.json')), json.load(open('schemas/zlf-v1.schema.json')))"
```
