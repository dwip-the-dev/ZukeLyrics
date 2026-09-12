# 🤝 Contributing to ZukeLyrics

Thank you for contributing to the open-source word-by-word lyrics standard! By contributing synchronized lyrics to ZukeLyrics, you are helping thousands of music lovers around the world experience fluid karaoke, accessibility, and high-accuracy text alignment across all open-source music players.

---

## 📑 Table of Contents
1. [Contribution Methods](#contribution-methods)
   - [Method 1: GitHub Issue Gateway (Easiest - No Git Required)](#method-1-github-issue-gateway-easiest---no-git-required)
   - [Method 2: Pull Request (Advanced & Bulk Submissions)](#method-2-pull-request-advanced--bulk-submissions)
   - [Method 3: Direct Contribution from Zuke Mobile App](#method-3-direct-contribution-from-zuke-mobile-app)
2. [Directory Sharding Rules](#directory-sharding-rules)
3. [Quality & Timing Standards](#quality--timing-standards)
4. [Language & Translation Standards](#language--translation-standards)
5. [Automated CI Verification](#automated-ci-verification)

---

## 🚀 Contribution Methods

### Method 1: GitHub Issue Gateway (Easiest - No Git Required)

You do not need to install Git or Python to contribute!

1. Open [New Issue on GitHub](https://github.com/dwip-the-dev/ZukeLyrics/issues/new/choose).
2. Choose **Submit New Lyrics** or **Correct Existing Lyrics**.
3. Fill out the web form:
   - **YouTube Video ID**: The 11-character identifier (e.g. `fJ9rUzIMcZQ` from `https://www.youtube.com/watch?v=fJ9rUzIMcZQ`).
   - **Song Title & Artist**: Official track metadata.
   - **Duration**: Duration in seconds.
   - **Language**: Two-letter ISO 639-1 code (e.g. `en`, `es`, `ja`, `ko`, `de`).
   - **Lyrics Payload**: Paste either ZLF JSON or an Enhanced Rich-Sync LRC file.
4. Click **Submit New Issue**.
5. **The Automated Bot Takes Over**:
   - Our CI workflow (`.github/workflows/issue_bot.yml`) triggers within seconds.
   - It runs `tools/validator.py` to verify timestamp monotonicity and word intervals.
   - If everything passes, the bot commits the file to `main`, updates the search index, and closes the issue with a link to the published CDN endpoint!

---

### Method 2: Pull Request (Advanced & Bulk Submissions)

For developers submitting batches of converted files:

1. Fork the repository on GitHub and clone your fork:
   ```bash
   git clone https://github.com/<your-username>/ZukeLyrics.git
   cd ZukeLyrics
   ```
2. Create a new branch:
   ```bash
   git checkout -b add-lyrics-my-track
   ```
3. Place your file in the sharded directory structure:
   ```
   lyrics-database / {videoId[0]} / {videoId[1]} / {videoId}.json
   ```
   *Example*: For video `dQw4w9WgXcQ`:
   ```bash
   mkdir -p lyrics-database/d/Q
   cp path/to/dQw4w9WgXcQ.json lyrics-database/d/Q/
   ```
4. Validate your submission:
   ```bash
   python3 tools/validator.py lyrics-database/
   ```
5. Rebuild the catalog and search index:
   ```bash
   python3 tools/index_builder.py
   ```
6. Commit and push:
   ```bash
   git add .
   git commit -m "feat(lyrics): add Queen - Bohemian Rhapsody (fJ9rUzIMcZQ)"
   git push origin add-lyrics-my-track
   ```
7. Open a Pull Request against `main`. Our CI will automatically validate your files.

---

### Method 3: Direct Contribution from Zuke Mobile App

Users running the **Zuke Music App** on Android can contribute directly from the player interface:

1. Open any playlist or song in Zuke.
2. Open the song/playlist context menu (3 vertical dots).
3. Tap **Contribute Word Sync Data**.
4. The local alignment engine will synchronize the lyrics, generate the verified ZLF JSON, and submit it directly to the repository via the GitHub Issue Gateway or authenticated API!

---

## 📂 Directory Sharding Rules

To ensure high performance and avoid git tree slowdowns when scaling to hundreds of thousands of songs:

- **Path Template**: `lyrics-database/{dir1}/{dir2}/{videoId}.json`
- `dir1`: Exactly the 1st character of the video ID (case-sensitive).
- `dir2`: Exactly the 2nd character of the video ID (case-sensitive).
- `videoId.json`: Exactly the full 11-character video ID followed by `.json`.

| YouTube ID | Sharded Path |
| :--- | :--- |
| `dQw4w9WgXcQ` | `lyrics-database/d/Q/dQw4w9WgXcQ.json` |
| `fJ9rUzIMcZQ` | `lyrics-database/f/J/fJ9rUzIMcZQ.json` |
| `-_123456789` | `lyrics-database/-/_/-_123456789.json` |

---

## 🎯 Quality & Timing Standards

To provide a flawless karaoke experience, all submissions must meet these criteria:

1. **Word-Level Accuracy**:
   - Each word or syllable timestamp should align within ±150 milliseconds of the sung vocal audio transient.
2. **Strict Time Monotonicity**:
   - Line times must never decrease (`line[i].time >= line[i-1].time`).
   - Word start times must never decrease within a line.
3. **Punctuation & Whitespace**:
   - Punctuation (commas, periods, exclamation points) should be attached to the preceding word without breaking timing.
   - Do not artificially censor lyrics (e.g. replacing words with asterisks). Preserve the artist's original sung expression.
4. **Duration**:
   - Track `duration` should match the exact length of the official YouTube video in milliseconds.

---

## 🌐 Language & Translation Standards

- **Language Codes**: Use standard two-letter ISO 639-1 lowercase codes (e.g., `en`, `es`, `ja`, `ko`, `zh`, `fr`, `de`, `hi`).
- **Non-Latin Scripts**: For Japanese, Korean, Chinese, Hindi, Arabic, etc., always provide the `romanized` field if possible (e.g., Romaji, Revised Romanization, or Pinyin) to assist international listeners.
- **Translations**: Line translations should be placed inside `lines[].translations[langCode]` using native sentence structure.

---

## 🤖 Automated CI Verification

Every pull request and issue submission is tested against our continuous integration pipeline:
- Schema validation via `schemas/zlf-v1.schema.json`.
- Timing bounds verification via `tools/validator.py`.
- Regression testing via `tools/tests/test_zukelyrics.py`.
