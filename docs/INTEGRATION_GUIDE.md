# 📱 ZukeLyrics Integration Guide

This guide provides end-to-end, production-ready code examples demonstrating how to integrate **ZukeLyrics** into Android, Web, iOS, Discord bots, and Python applications.

---

## 📑 Table of Contents
1. [Android (Kotlin & Jetpack Compose)](#1-android-kotlin--jetpack-compose)
2. [Web & React (HTML5 Audio & Smooth Karaoke UI)](#2-web--react-html5-audio--smooth-karaoke-ui)
3. [iOS (Swift & SwiftUI with AVPlayer)](#3-ios-swift--swiftui-with-avplayer)
4. [Node.js & Discord Music Bot](#4-nodejs--discord-music-bot)
5. [Python Terminal Karaoke Player](#5-python-terminal-karaoke-player)

---

## 1. Android (Kotlin & Jetpack Compose)

### Step 1: Model & Client Setup
Using OkHttp and Kotlinx Serialization (or Gson):

```kotlin
// ZukeLyricsClient.kt
package com.example.music.lyrics

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject

data class WordSync(val word: String, val startTime: Long, val endTime: Long)
data class LyricLine(val time: Long, val endTime: Long, val text: String, val words: List<WordSync>?)
data class SyncedLyrics(val id: String, val title: String, val artist: String, val lines: List<LyricLine>)

class ZukeLyricsClient(private val client: OkHttpClient = OkHttpClient()) {
    suspend fun fetchLyrics(videoId: String): SyncedLyrics? = withContext(Dispatchers.IO) {
        if (videoId.length < 2) return@withContext null
        val d1 = videoId[0]
        val d2 = videoId[1]
        val url = "https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/$d1/$d2/$videoId.json"
        
        val request = Request.Builder().url(url).build()
        try {
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext null
                val body = response.body?.string() ?: return@withContext null
                val json = JSONObject(body)
                val linesJson = json.getJSONArray("lines")
                val lines = ArrayList<LyricLine>()
                for (i in 0 until linesJson.length()) {
                    val lineObj = linesJson.getJSONObject(i)
                    val wordsList = if (lineObj.has("words")) {
                        val wordsArr = lineObj.getJSONArray("words")
                        (0 until wordsArr.length()).map { j ->
                            val w = wordsArr.getJSONObject(j)
                            WordSync(w.getString("word"), w.getLong("startTime"), w.getLong("endTime"))
                        }
                    } else null
                    lines.add(LyricLine(
                        time = lineObj.getLong("time"),
                        endTime = lineObj.optLong("endTime", lineObj.getLong("time") + 3000),
                        text = lineObj.getString("text"),
                        words = wordsList
                    ))
                }
                SyncedLyrics(
                    id = json.getString("id"),
                    title = json.getString("title"),
                    artist = json.getString("artist"),
                    lines = lines
                )
            }
        } catch (e: Exception) {
            null
        }
    }
}
```

### Step 2: Glowing Karaoke Line in Jetpack Compose

```kotlin
// KaraokeLine.kt
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

@Composable
fun KaraokeLine(line: LyricLine, currentPositionMs: Long) {
    if (line.words.isNullOrEmpty()) {
        // Fallback to line-level highlight
        val isActive = currentPositionMs in line.time..line.endTime
        Text(
            text = line.text,
            fontSize = 22.sp,
            fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
            color = if (isActive) Color.White else Color.White.copy(alpha = 0.4f)
        )
    } else {
        // Word-by-word synchronized karaoke
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Start) {
            line.words.forEach { word ->
                val isPast = currentPositionMs >= word.endTime
                val isCurrent = currentPositionMs in word.startTime..word.endTime
                
                val textColor = when {
                    isPast -> Color.White
                    isCurrent -> Color(0xFF64B5F6) // Active glowing cyan
                    else -> Color.White.copy(alpha = 0.35f)
                }
                
                Text(
                    text = "${word.word} ",
                    fontSize = 22.sp,
                    fontWeight = if (isPast || isCurrent) FontWeight.Bold else FontWeight.Normal,
                    color = textColor
                )
            }
        }
    }
}
```

---

## 2. Web & React (HTML5 Audio & Smooth Karaoke UI)

### React Hook & Component

```tsx
// useZukeLyrics.ts
import { useState, useEffect } from 'react';

export interface WordSync {
  word: string;
  startTime: number;
  endTime: number;
}

export interface LyricLine {
  time: number;
  endTime: number;
  text: string;
  words?: WordSync[];
}

export function useZukeLyrics(videoId: string) {
  const [lyrics, setLyrics] = useState<LyricLine[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!videoId) return;
    setLoading(true);
    const d1 = videoId[0];
    const d2 = videoId[1];
    fetch(`https://cdn.jsdelivr.net/gh/dwip-the-dev/ZukeLyrics@main/lyrics-database/${d1}/${d2}/${videoId}.json`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        setLyrics(data ? data.lines : null);
        setLoading(false);
      })
      .catch(() => {
        setLyrics(null);
        setLoading(false);
      });
  }, [videoId]);

  return { lyrics, loading };
}
```

### Component with Word Highlighting

```tsx
// LyricsPlayer.tsx
import React from 'react';
import { LyricLine } from './useZukeLyrics';

interface Props {
  lines: LyricLine[];
  currentTimeMs: number;
}

export const LyricsPlayer: React.FC<Props> = ({ lines, currentTimeMs }) => {
  return (
    <div style={{ fontFamily: 'sans-serif', background: '#0a0a0a', padding: '2rem', color: '#fff' }}>
      {lines.map((line, idx) => {
        const isLineActive = currentTimeMs >= line.time && currentTimeMs <= line.endTime;
        return (
          <div
            key={idx}
            style={{
              margin: '1.2rem 0',
              fontSize: '1.5rem',
              transition: 'all 0.3s ease',
              opacity: isLineActive ? 1 : 0.4,
              transform: isLineActive ? 'scale(1.05)' : 'scale(1)',
              transformOrigin: 'left center'
            }}
          >
            {line.words ? (
              line.words.map((w, wIdx) => {
                const isWordDone = currentTimeMs >= w.endTime;
                const isWordActive = currentTimeMs >= w.startTime && currentTimeMs <= w.endTime;
                return (
                  <span
                    key={wIdx}
                    style={{
                      color: isWordDone ? '#ffffff' : isWordActive ? '#38bdf8' : 'rgba(255,255,255,0.4)',
                      fontWeight: isWordDone || isWordActive ? 700 : 400,
                      marginRight: '0.3em',
                      textShadow: isWordActive ? '0 0 12px rgba(56,189,248,0.8)' : 'none'
                    }}
                  >
                    {w.word}
                  </span>
                );
              })
            ) : (
              <span>{line.text}</span>
            )}
          </div>
        );
      })}
    </div>
  );
};
```

---

## 3. iOS (Swift & SwiftUI with AVPlayer)

```swift
// ZukeLyricsView.swift
import SwiftUI
import AVFoundation

struct WordSync: Codable, Identifiable {
    var id: String { "\(startTime)_\(word)" }
    let word: String
    let startTime: Int
    let endTime: Int
}

struct LyricLine: Codable, Identifiable {
    var id: Int { time }
    let time: Int
    let endTime: Int
    let text: String
    let words: [WordSync]?
}

struct TrackLyrics: Codable {
    let title: String
    let artist: String
    let lines: [LyricLine]
}

struct ZukeKaraokeView: View {
    let lines: [LyricLine]
    let currentTimeMs: Int

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    ForEach(lines) { line in
                        let isLineActive = currentTimeMs >= line.time && currentTimeMs <= line.endTime
                        HStack(spacing: 4) {
                            if let words = line.words {
                                ForEach(words) { word in
                                    let isHighlighted = currentTimeMs >= word.startTime
                                    Text(word.word)
                                        .font(.system(size: 22, weight: isHighlighted ? .bold : .regular))
                                        .foregroundColor(isHighlighted ? .white : .gray.opacity(0.5))
                                }
                            } else {
                                Text(line.text)
                                    .font(.system(size: 22, weight: isLineActive ? .bold : .regular))
                                    .foregroundColor(isLineActive ? .white : .gray.opacity(0.5))
                            }
                        }
                        .id(line.time)
                    }
                }
                .padding()
            }
        }
    }
}
```

---

## 4. Node.js & Discord Music Bot

Display live synchronized lyrics directly in a Discord voice channel or status embed:

```javascript
// bot-lyrics.js
import { ZukeLyricsClient } from 'zukelyrics';
import { EmbedBuilder } from 'discord.js';

const client = new ZukeLyricsClient();

export async function sendLiveLyrics(channel, youtubeVideoId, player) {
  const lyrics = await client.getLyrics(youtubeVideoId);
  if (!lyrics) {
    return channel.send("❌ No synchronized lyrics found in ZukeLyrics database.");
  }

  const message = await channel.send({
    embeds: [
      new EmbedBuilder()
        .setTitle(`🎵 ${lyrics.title} - ${lyrics.artist}`)
        .setDescription("Starting lyrics...")
        .setColor(0x38bdf8)
    ]
  });

  // Track player progress
  const interval = setInterval(() => {
    const currentMs = player.position; // Player timestamp in ms
    const currentLine = lyrics.lines.find(l => currentMs >= l.time && currentMs <= l.endTime);
    
    if (currentLine) {
      message.edit({
        embeds: [
          new EmbedBuilder()
            .setTitle(`🎵 ${lyrics.title} - ${lyrics.artist}`)
            .setDescription(`**${currentLine.text}**`)
            .setFooter({ text: `ZukeLyrics • ${lyrics.hasWordSync ? "Word-Synced" : "Line-Synced"}` })
            .setColor(0x38bdf8)
        ]
      });
    }
  }, 1500);

  player.on('end', () => clearInterval(interval));
}
```

---

## 5. Python Terminal Karaoke Player

Run in your terminal to see live lyrics play in sync:

```python
# cli_karaoke.py
import time
import sys
from zukelyrics import ZukeLyricsClient

def play_terminal_karaoke(video_id: str):
    client = ZukeLyricsClient()
    track = client.get_lyrics(video_id)
    if not track:
        print(f"No lyrics found for {video_id}")
        return

    print(f"\n🎶 Now Playing: {track.title} - {track.artist}\n")
    start_time = time.time()

    line_idx = 0
    while line_idx < len(track.lines):
        elapsed_ms = int((time.time() - start_time) * 1000)
        current_line = track.lines[line_idx]

        if elapsed_ms < current_line.time:
            time.sleep(0.02)
            continue

        if current_line.words:
            # Word by word printing
            sys.stdout.write(f"\r[{current_line.time/1000:05.2f}] ")
            for w in current_line.words:
                while int((time.time() - start_time) * 1000) < w.startTime:
                    time.sleep(0.01)
                sys.stdout.write(f"\033[1;36m{w.word}\033[0m ")
                sys.stdout.flush()
            print()
        else:
            print(f"[{current_line.time/1000:05.2f}] {current_line.text}")

        line_idx += 1

if __name__ == "__main__":
    play_terminal_karaoke("dQw4w9WgXcQ")
```
