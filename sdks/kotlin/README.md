# 📱 ZukeLyrics Kotlin & Android SDK

Official Kotlin / Android client for accessing the **ZukeLyrics** crowdsourced word-by-word synchronized lyrics ecosystem. Built with Kotlin Coroutines and OkHttp.

---

## ⚡ Integration

Drop `ZukeLyricsClient.kt` and `ZukeLyricsModels.kt` into your Android project, or add the dependency if using a multi-module setup.

Required dependencies:
```groovy
implementation("com.squareup.okhttp3:okhttp:4.12.0")
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.0")
```

---

## 🚀 Usage

### 1. Fetching Synchronized Lyrics

```kotlin
import com.zukelyrics.sdk.ZukeLyricsClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

val client = ZukeLyricsClient()

CoroutineScope(Dispatchers.Main).launch {
    val lyrics = client.getLyrics("fJ9rUzIMcZQ")
    if (lyrics != null) {
        println("Loaded: ${lyrics.title} by ${lyrics.artist}")
        println("Word synced: ${lyrics.hasWordSync}")
        
        lyrics.lines.forEach { line ->
            println("[${line.time}ms] ${line.text}")
            line.words?.forEach { word ->
                println("  └── '${word.word}' (${word.startTime}ms - ${word.endTime}ms)")
            }
        }
    }
}
```

### 2. Contributing New Lyrics (Android)

```kotlin
val result = client.submitLyrics(
    githubToken = "YOUR_GITHUB_PAT", // Or via Issue Gateway
    videoId = "dQw4w9WgXcQ",
    title = "Never Gonna Give You Up",
    artist = "Rick Astley",
    durationMs = 213000,
    language = "en",
    lines = myAlignedLines
)

if (result.isSuccess) {
    println("Lyrics successfully committed to ZukeLyrics!")
}
```

---

## 📜 License
MIT
