package com.zionhuang.music.lyrics

data class ZukeWordEntry(
    val startTime: Long,
    val endTime: Long,
    val word: String
)

data class ZukeLyricLine(
    val time: Long,
    val endTime: Long,
    val text: String,
    val translation: String? = null,
    val romanization: String? = null,
    val isDuet: Boolean = false,
    val isBackground: Boolean = false,
    val agent: String? = null,
    val words: List<ZukeWordEntry> = emptyList()
)

data class ZukeLyricsPayload(
    val videoId: String,
    val title: String,
    val artist: String,
    val album: String? = null,
    val duration: Int = 0,
    val isrc: String? = null,
    val spotifyId: String? = null,
    val mbid: String? = null,
    val language: String? = null,
    val source: String = "Zuke",
    val syncedType: String = "word",
    val rawTtml: String? = null,
    val rawLrc: String? = null,
    val lines: List<ZukeLyricLine> = emptyList()
)
