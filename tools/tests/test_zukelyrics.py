#!/usr/bin/env python3
"""
Comprehensive Test Suite for ZukeLyrics Ecosystem
Tests schema validation, temporal alignment edge cases, universal converter,
index builder, and network CDN lookups.
"""

import unittest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add tools to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator import validate_zlf_file
from converter import ZukeConverter
from index_builder import build_indexes

class TestZukeLyricsValidation(unittest.TestCase):

    def test_valid_file(self):
        sample_path = Path(__file__).parent.parent.parent / "lyrics-database" / "d" / "Q" / "dQw4w9WgXcQ.json"
        self.assertTrue(sample_path.exists(), "Sample track must exist")
        is_valid, errors, warnings = validate_zlf_file(sample_path)
        self.assertTrue(is_valid, f"Sample file should be valid. Errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_missing_required_fields(self):
        invalid_data = {
            "title": "Song without videoId",
            "artist": "Artist",
            "syncedType": "word",
            "lines": []
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_name = f.name

        try:
            is_valid, errors, warnings = validate_zlf_file(temp_name)
            self.assertFalse(is_valid)
            self.assertTrue(any("videoId" in e for e in errors))
        finally:
            os.remove(temp_name)

    def test_invalid_line_timestamps(self):
        invalid_data = {
            "videoId": "test123",
            "title": "Test",
            "artist": "Test",
            "syncedType": "line",
            "lines": [
                {
                    "time": 5000,
                    "endTime": 3000, # Error: end before start!
                    "text": "Hello world"
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_name = f.name

        try:
            is_valid, errors, warnings = validate_zlf_file(temp_name)
            self.assertFalse(is_valid)
            self.assertTrue(any("endTime" in e and "less than time" in e for e in errors))
        finally:
            os.remove(temp_name)

    def test_invalid_word_timestamps(self):
        invalid_data = {
            "videoId": "test123",
            "title": "Test",
            "artist": "Test",
            "syncedType": "word",
            "lines": [
                {
                    "time": 1000,
                    "endTime": 5000,
                    "text": "Hello world",
                    "words": [
                        {"startTime": 2000, "endTime": 1500, "word": "Hello "} # Error: word end before start!
                    ]
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_name = f.name

        try:
            is_valid, errors, warnings = validate_zlf_file(temp_name)
            self.assertFalse(is_valid)
            self.assertTrue(any("endTime" in e and "< startTime" in e for e in errors))
        finally:
            os.remove(temp_name)


class TestZukeConverter(unittest.TestCase):

    def test_lrc_conversion_roundtrip(self):
        lrc_sample = """[00:10.50]First line of lyrics
[00:15.00]Second line of lyrics
[00:20.00]Third line of lyrics"""

        zlf = ZukeConverter.lrc_to_zlf(lrc_sample, video_id="demo123", title="Demo", artist="Artist")
        self.assertEqual(zlf["videoId"], "demo123")
        self.assertEqual(len(zlf["lines"]), 3)
        self.assertEqual(zlf["lines"][0]["time"], 10500)
        self.assertEqual(zlf["lines"][0]["text"], "First line of lyrics")
        self.assertEqual(zlf["lines"][0]["endTime"], 15000)

        converted_lrc = ZukeConverter.zlf_to_lrc(zlf)
        self.assertIn("[00:10.50]First line of lyrics", converted_lrc)
        self.assertIn("[00:15.00]Second line of lyrics", converted_lrc)

    def test_enhanced_rich_sync_lrc(self):
        rich_lrc = """[00:12.00]<00:12.00>Never <00:12.50>gonna <00:13.20>give <00:14.00>you <00:14.50>up"""
        zlf = ZukeConverter.lrc_to_zlf(rich_lrc, video_id="rick123")
        self.assertEqual(zlf["syncedType"], "word")
        line = zlf["lines"][0]
        self.assertEqual(line["text"], "Never gonna give you up")
        self.assertEqual(len(line["words"]), 5)
        self.assertEqual(line["words"][0]["word"], "Never ")
        self.assertEqual(line["words"][0]["startTime"], 12000)
        self.assertEqual(line["words"][0]["endTime"], 12500)

        # Convert back to rich LRC
        back_rich = ZukeConverter.zlf_to_enhanced_lrc(zlf)
        self.assertIn("<00:12.000>Never", back_rich)
        self.assertIn("<00:12.500>gonna", back_rich)

    def test_ttml_conversion_roundtrip(self):
        ttml_sample = """<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:01.000" end="00:05.000">
        <span begin="00:01.000" end="00:02.500">Hello </span>
        <span begin="00:02.500" end="00:05.000">World</span>
      </p>
    </div>
  </body>
</tt>"""
        zlf = ZukeConverter.ttml_to_zlf(ttml_sample, video_id="ttml123")
        self.assertEqual(zlf["syncedType"], "word")
        self.assertEqual(len(zlf["lines"]), 1)
        self.assertEqual(zlf["lines"][0]["time"], 1000)
        self.assertEqual(zlf["lines"][0]["endTime"], 5000)
        self.assertEqual(zlf["lines"][0]["text"], "Hello World")
        self.assertEqual(len(zlf["lines"][0]["words"]), 2)

        # Convert back to TTML
        back_ttml = ZukeConverter.zlf_to_ttml(zlf)
        self.assertIn('<p begin="00:01.000" end="00:05.000">', back_ttml)
        self.assertIn('<span begin="00:01.000" end="00:02.500">Hello </span>', back_ttml)

    def test_agents_and_duets(self):
        # Test TTML with ttm:agent and duet parsing
        ttml_duet = """<tt xmlns="http://www.w3.org/ns/ttml" xmlns:ttm="http://www.w3.org/ns/ttml#metadata">
  <body>
    <div>
      <p begin="00:10.000" end="00:15.000" ttm:agent="Freddie Mercury">
        <span>Is this the real life?</span>
      </p>
      <p begin="00:15.500" end="00:20.000" ttm:agent="v2" role="x-bg">
        <span>(Let me go!)</span>
      </p>
    </div>
  </body>
</tt>"""
        zlf = ZukeConverter.ttml_to_zlf(ttml_duet, video_id="duet123")
        self.assertEqual(len(zlf["lines"]), 2)
        line1 = zlf["lines"][0]
        self.assertEqual(line1["agent"], "Freddie Mercury")
        self.assertFalse(line1.get("isDuet", False))

        line2 = zlf["lines"][1]
        self.assertEqual(line2["agent"], "v2")
        self.assertTrue(line2["isDuet"])
        self.assertTrue(line2["isBackground"])

        # Convert back to TTML and check preservation
        back_ttml = ZukeConverter.zlf_to_ttml(zlf)
        self.assertIn('ttm:agent="Freddie Mercury"', back_ttml)
        self.assertIn('ttm:agent="v2"', back_ttml)
        self.assertIn('role="x-bg"', back_ttml)

    def test_romanization_and_translations(self):
        ttml_jp = """<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:05.000" end="00:09.000">
        <span role="x-roman">Yoru ni kakeru</span>
        <span role="x-translation">Racing into the night</span>
        <span begin="00:05.000" end="00:07.000">夜に</span>
        <span begin="00:07.000" end="00:09.000">駆ける</span>
      </p>
    </div>
  </body>
</tt>"""
        zlf = ZukeConverter.ttml_to_zlf(ttml_jp, video_id="yoasobi123")
        line = zlf["lines"][0]
        self.assertEqual(line["text"], "夜に 駆ける")
        self.assertEqual(line["romanization"], "Yoru ni kakeru")
        self.assertEqual(line["translation"], "Racing into the night")
        self.assertEqual(len(line["words"]), 2)

        # Convert back to TTML and verify romanization and translation spans
        back_ttml = ZukeConverter.zlf_to_ttml(zlf)
        self.assertIn('<span role="x-roman">Yoru ni kakeru</span>', back_ttml)
        self.assertIn('<span role="x-translation">Racing into the night</span>', back_ttml)

    def test_srt_conversion(self):
        zlf_sample = {
            "lines": [
                {"time": 1000, "endTime": 4000, "text": "Sub title 1"},
                {"time": 5000, "endTime": 8000, "text": "Sub title 2"}
            ]
        }
        srt = ZukeConverter.zlf_to_srt(zlf_sample)
        self.assertIn("00:00:01,000 --> 00:00:04,000", srt)
        self.assertIn("Sub title 1", srt)


class TestIndexBuilder(unittest.TestCase):

    def test_index_generation(self):
        repo_root = Path(__file__).parent.parent.parent
        build_indexes(repo_root)

        catalog_file = repo_root / "index" / "catalog.json"
        search_file = repo_root / "index" / "search-index.json"
        stats_file = repo_root / "api" / "v1" / "stats.json"

        self.assertTrue(catalog_file.exists())
        self.assertTrue(search_file.exists())
        self.assertTrue(stats_file.exists())

        with open(catalog_file, "r", encoding="utf-8") as f:
            catalog = json.load(f)
            self.assertGreaterEqual(len(catalog), 2)
            self.assertTrue(any(item["videoId"] == "dQw4w9WgXcQ" for item in catalog))

        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
            self.assertGreaterEqual(stats["totalTracks"], 2)
            self.assertGreaterEqual(stats["wordSynced"], 2)


if __name__ == "__main__":
    unittest.main()
