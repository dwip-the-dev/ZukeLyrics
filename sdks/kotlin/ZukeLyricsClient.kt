package com.zionhuang.music.lyrics

import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.util.Base64

/**
 * Standalone Kotlin/Java Client for ZukeLyrics.
 * Zero heavy dependencies: works with vanilla JVM HttpURLConnection and org.json.
 */
class ZukeLyricsClient(
    val owner: String = "dwip-the-dev",
    val repo: String = "ZukeLyrics",
    val branch: String = "main",
    var token: String? = null
) {
    private val cdnPrimary = "https://raw.githubusercontent.com/$owner/$repo/$branch/lyrics-database"
    private val cdnFallback = "https://cdn.jsdelivr.net/gh/$owner/$repo@$branch/lyrics-database"
    private val apiBase = "https://api.github.com/repos/$owner/$repo/contents/lyrics-database"

    fun getRelativePath(videoId: String): String {
        val clean = videoId.trim()
        val c1 = if (clean.isNotEmpty() && clean[0].isLetterOrDigit()) clean[0].toString() else "_"
        val c2 = if (clean.length > 1 && clean[1].isLetterOrDigit()) clean[1].toString() else "_"
        return "$c1/$c2/$clean.json"
    }

    /**
     * Checks if lyrics exist in the repository via fast HTTP HEAD.
     */
    fun hasLyrics(videoId: String): Boolean {
        val relPath = getRelativePath(videoId)
        for (base in listOf(cdnPrimary, cdnFallback)) {
            try {
                val url = URL("$base/$relPath")
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "HEAD"
                    connectTimeout = 4000
                    readTimeout = 4000
                    setRequestProperty("User-Agent", "ZukeLyrics-Kotlin-SDK")
                }
                if (conn.responseCode == 200) {
                    return true
                }
            } catch (_: Exception) {
            }
        }
        return false
    }

    /**
     * Fetches and parses lyrics for a given YouTube video ID.
     */
    fun getLyrics(videoId: String): ZukeLyricsPayload? {
        val relPath = getRelativePath(videoId)
        for (base in listOf(cdnPrimary, cdnFallback)) {
            try {
                val url = URL("$base/$relPath")
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 6000
                    readTimeout = 6000
                    setRequestProperty("User-Agent", "ZukeLyrics-Kotlin-SDK")
                }
                if (conn.responseCode == 200) {
                    val text = BufferedReader(InputStreamReader(conn.inputStream)).readText()
                    return parsePayload(text)
                }
            } catch (_: Exception) {
            }
        }
        return null
    }

    /**
     * Pushes/commits a lyrics payload directly to the repository.
     */
    fun uploadLyrics(payload: ZukeLyricsPayload, patToken: String? = token): Boolean {
        val activeToken = patToken ?: token ?: error("No GitHub token provided.")
        val relPath = getRelativePath(payload.videoId)
        val apiUrl = URL("$apiBase/$relPath")

        val jsonStr = serializePayload(payload)
        val b64Content = Base64.getEncoder().encodeToString(jsonStr.toByteArray(Charsets.UTF_8))

        var existingSha: String? = null
        try {
            val checkConn = (apiUrl.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                setRequestProperty("Authorization", "Bearer $activeToken")
                setRequestProperty("Accept", "application/vnd.github+json")
                setRequestProperty("User-Agent", "ZukeLyrics-Kotlin-SDK")
            }
            if (checkConn.responseCode == 200) {
                val resp = BufferedReader(InputStreamReader(checkConn.inputStream)).readText()
                existingSha = JSONObject(resp).optString("sha")
            }
        } catch (_: Exception) {
        }

        val requestObj = JSONObject().apply {
            put("message", "Add synced lyrics for ${payload.title} - ${payload.artist} [${payload.videoId}]")
            put("content", b64Content)
            put("branch", branch)
            if (existingSha != null) {
                put("sha", existingSha)
            }
        }

        val putConn = (apiUrl.openConnection() as HttpURLConnection).apply {
            requestMethod = "PUT"
            doOutput = true
            setRequestProperty("Authorization", "Bearer $activeToken")
            setRequestProperty("Accept", "application/vnd.github+json")
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("User-Agent", "ZukeLyrics-Kotlin-SDK")
        }

        putConn.outputStream.use { os ->
            os.write(requestObj.toString().toByteArray(Charsets.UTF_8))
        }

        return putConn.responseCode in 200..201
    }

    private fun parsePayload(jsonStr: String): ZukeLyricsPayload {
        val root = JSONObject(jsonStr)
        val linesList = mutableListOf<ZukeLyricLine>()
        val linesArr = root.optJSONArray("lines")
        if (linesArr != null) {
            for (i in 0 until linesArr.length()) {
                val lObj = linesArr.getJSONObject(i)
                val wordsList = mutableListOf<ZukeWordEntry>()
                val wordsArr = lObj.optJSONArray("words")
                if (wordsArr != null) {
                    for (j in 0 until wordsArr.length()) {
                        val wObj = wordsArr.getJSONObject(j)
                        wordsList.add(
                            ZukeWordEntry(
                                startTime = wObj.getLong("startTime"),
                                endTime = wObj.getLong("endTime"),
                                word = wObj.getString("word")
                            )
                        )
                    }
                }
                linesList.add(
                    ZukeLyricLine(
                        time = lObj.getLong("time"),
                        endTime = lObj.getLong("endTime"),
                        text = lObj.getString("text"),
                        translation = lObj.optString("translation").takeIf { it.isNotBlank() },
                        romanization = lObj.optString("romanization").takeIf { it.isNotBlank() },
                        isDuet = lObj.optBoolean("isDuet", false),
                        isBackground = lObj.optBoolean("isBackground", false),
                        agent = lObj.optString("agent").takeIf { it.isNotBlank() },
                        words = wordsList
                    )
                )
            }
        }

        return ZukeLyricsPayload(
            videoId = root.getString("videoId"),
            title = root.getString("title"),
            artist = root.getString("artist"),
            album = root.optString("album").takeIf { it.isNotBlank() },
            duration = root.optInt("duration", 0),
            isrc = root.optString("isrc").takeIf { it.isNotBlank() },
            spotifyId = root.optString("spotifyId").takeIf { it.isNotBlank() },
            mbid = root.optString("mbid").takeIf { it.isNotBlank() },
            language = root.optString("language").takeIf { it.isNotBlank() },
            source = root.optString("source", "Zuke"),
            syncedType = root.optString("syncedType", "word"),
            rawTtml = root.optString("rawTtml").takeIf { it.isNotBlank() },
            rawLrc = root.optString("rawLrc").takeIf { it.isNotBlank() },
            lines = linesList
        )
    }

    private fun serializePayload(p: ZukeLyricsPayload): String {
        val root = JSONObject().apply {
            put("$schema", "https://raw.githubusercontent.com/$owner/$repo/$branch/schemas/zlf-v1.schema.json")
            put("version", 1)
            put("videoId", p.videoId)
            put("title", p.title)
            put("artist", p.artist)
            p.album?.let { put("album", it) }
            put("duration", p.duration)
            p.isrc?.let { put("isrc", it) }
            p.spotifyId?.let { put("spotifyId", it) }
            p.mbid?.let { put("mbid", it) }
            p.language?.let { put("language", it) }
            put("source", p.source)
            put("syncedType", p.syncedType)
            p.rawTtml?.let { put("rawTtml", it) }
            p.rawLrc?.let { put("rawLrc", it) }

            val linesArr = JSONArray()
            for (line in p.lines) {
                val lObj = JSONObject().apply {
                    put("time", line.time)
                    put("endTime", line.endTime)
                    put("text", line.text)
                    line.translation?.let { put("translation", it) }
                    line.romanization?.let { put("romanization", it) }
                    if (line.isDuet) put("isDuet", true)
                    if (line.isBackground) put("isBackground", true)
                    line.agent?.let { put("agent", it) }

                    if (line.words.isNotEmpty()) {
                        val wArr = JSONArray()
                        for (w in line.words) {
                            wArr.put(
                                JSONObject().apply {
                                    put("startTime", w.startTime)
                                    put("endTime", w.endTime)
                                    put("word", w.word)
                                }
                            )
                        }
                        put("words", wArr)
                    }
                }
                linesArr.put(lObj)
            }
            put("lines", linesArr)
        }
        return root.toString(2)
    }
}
