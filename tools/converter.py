#!/usr/bin/env python3
"""
ZukeLyrics Universal Format Converter
Bidirectional conversion between ZLF v1, TTML (Apple Music/AMLL style), Enhanced LRC, Standard LRC, and SRT/VTT.
"""

import sys
import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path

TIME_REGEX = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{2,3}))?\]")
RICH_WORD_REGEX = re.compile(r"<(\d{1,2}):(\d{2})\.(\d{2,3})>([^<]*)")

def ms_to_timestamp(ms, sep="."):
    total_sec = ms // 1000
    minutes = total_sec // 60
    seconds = total_sec % 60
    millis = ms % 1000
    return f"{minutes:02d}:{seconds:02d}{sep}{millis:03d}"

def ms_to_srt_timestamp(ms):
    total_sec = ms // 1000
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def ms_to_lrc_timestamp(ms):
    total_sec = ms // 1000
    minutes = total_sec // 60
    seconds = total_sec % 60
    centis = (ms % 1000) // 10
    return f"[{minutes:02d}:{seconds:02d}.{centis:02d}]"

def parse_lrc_timestamp(min_str, sec_str, ms_str):
    m = int(min_str)
    s = int(sec_str)
    if ms_str:
        if len(ms_str) == 2:
            ms = int(ms_str) * 10
        else:
            ms = int(ms_str)
    else:
        ms = 0
    return (m * 60 + s) * 1000 + ms

def parse_iso_or_clock_time(time_str):
    time_str = time_str.strip().rstrip("s")
    if ":" in time_str:
        parts = time_str.split(":")
        if len(parts) == 2:
            m = int(parts[0])
            sec_parts = parts[1].split(".")
            s = int(sec_parts[0])
            ms = int(sec_parts[1]) if len(sec_parts) > 1 else 0
            if len(sec_parts) > 1 and len(sec_parts[1]) == 2:
                ms *= 10
            return (m * 60 + s) * 1000 + ms
    try:
        return int(float(time_str) * 1000)
    except:
        return 0

class ZukeConverter:

    @staticmethod
    def lrc_to_zlf(lrc_text, video_id="unknown", title="Unknown Title", artist="Unknown Artist"):
        lines = []
        raw_lines = lrc_text.strip().split("\n")
        parsed_entries = []

        for line in raw_lines:
            line = line.strip()
            if not line or line.startswith("[ti:") or line.startswith("[ar:") or line.startswith("[al:") or line.startswith("[by:") or line.startswith("[offset:"):
                continue

            time_match = TIME_REGEX.search(line)
            if not time_match:
                continue

            start_ms = parse_lrc_timestamp(time_match.group(1), time_match.group(2), time_match.group(3))
            content = line[time_match.end():].strip()

            # Check for enhanced inline rich sync: <00:12.34>word1 <00:13.10>word2
            rich_matches = list(RICH_WORD_REGEX.finditer(content))
            words = []
            if rich_matches:
                for idx, rm in enumerate(rich_matches):
                    w_start = parse_lrc_timestamp(rm.group(1), rm.group(2), rm.group(3))
                    w_text = rm.group(4)
                    if idx + 1 < len(rich_matches):
                        next_rm = rich_matches[idx + 1]
                        w_end = parse_lrc_timestamp(next_rm.group(1), next_rm.group(2), next_rm.group(3))
                    else:
                        w_end = w_start + 1000
                    words.append({"startTime": w_start, "endTime": w_end, "word": w_text})
                clean_text = re.sub(r"<\d{1,2}:\d{2}\.\d{2,3}>", "", content).strip()
            else:
                clean_text = content

            if clean_text:
                parsed_entries.append({
                    "time": start_ms,
                    "text": clean_text,
                    "words": words
                })

        # Calculate line endTimes
        has_word_sync = any(len(e["words"]) > 0 for e in parsed_entries)
        for i, entry in enumerate(parsed_entries):
            if entry["words"]:
                line_end = entry["words"][-1]["endTime"]
            elif i + 1 < len(parsed_entries):
                line_end = parsed_entries[i + 1]["time"]
            else:
                line_end = entry["time"] + 4000

            entry["endTime"] = line_end

        return {
            "$schema": "https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/schemas/zlf-v1.schema.json",
            "version": 1,
            "videoId": video_id,
            "title": title,
            "artist": artist,
            "syncedType": "word" if has_word_sync else "line",
            "lines": parsed_entries
        }

    @staticmethod
    def ttml_to_zlf(ttml_text, video_id="unknown", title="Unknown Title", artist="Unknown Artist"):
        p_pattern = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.DOTALL)
        span_pattern = re.compile(r"<span\b([^>]*)>(.*?)</span>(\s*)", re.DOTALL)
        attr_pattern = re.compile(r'(\w+(?::\w+)?)=["\']([^"\']*)["\']')

        lines = []
        for p_match in p_pattern.finditer(ttml_text):
            p_attrs_raw = p_match.group(1)
            p_content = p_match.group(2)

            p_attrs = dict(attr_pattern.findall(p_attrs_raw))
            begin_ms = parse_iso_or_clock_time(p_attrs.get("begin", "0"))
            end_ms = parse_iso_or_clock_time(p_attrs.get("end", "0"))
            agent = p_attrs.get("ttm:agent", p_attrs.get("agent", ""))
            is_duet = "v2" in agent.lower()

            words = []
            text_builder = []

            for s_match in span_pattern.finditer(p_content):
                s_attrs_raw = s_match.group(1)
                s_text = re.sub(r"<[^>]+>", "", s_match.group(2)).strip()
                trailing = s_match.group(3)
                norm_trailing = " " if trailing and trailing.strip() == "" else (" " if trailing else "")

                s_attrs = dict(attr_pattern.findall(s_attrs_raw))
                w_begin = parse_iso_or_clock_time(s_attrs.get("begin", str(begin_ms / 1000)))
                w_end = parse_iso_or_clock_time(s_attrs.get("end", str(end_ms / 1000)))

                words.append({
                    "startTime": w_begin,
                    "endTime": w_end,
                    "word": s_text + norm_trailing
                })
                text_builder.append(s_text + norm_trailing)

            if words:
                full_text = re.sub(r"\s+", " ", "".join(text_builder)).strip()
            else:
                full_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p_content)).strip()

            if full_text:
                line_obj = {
                    "time": begin_ms,
                    "endTime": end_ms if end_ms > begin_ms else (words[-1]["endTime"] if words else begin_ms + 4000),
                    "text": full_text
                }
                if words:
                    line_obj["words"] = words
                if is_duet:
                    line_obj["isDuet"] = True
                lines.append(line_obj)

        has_word_sync = any("words" in l and len(l["words"]) > 0 for l in lines)
        return {
            "$schema": "https://raw.githubusercontent.com/dwip-the-dev/ZukeLyrics/main/schemas/zlf-v1.schema.json",
            "version": 1,
            "videoId": video_id,
            "title": title,
            "artist": artist,
            "syncedType": "word" if has_word_sync else "line",
            "lines": lines
        }

    @staticmethod
    def zlf_to_ttml(zlf_data):
        lines = zlf_data.get("lines", [])
        sb = ['<tt xmlns="http://www.w3.org/ns/ttml">', '  <body>', '    <div>']

        for line in lines:
            b_str = ms_to_timestamp(line["time"])
            e_str = ms_to_timestamp(line["endTime"])
            agent_attr = ' ttm:agent="v2"' if line.get("isDuet") else ""

            sb.append(f'      <p begin="{b_str}" end="{e_str}"{agent_attr}>')
            words = line.get("words", [])
            if words:
                for w in words:
                    wb = ms_to_timestamp(w["startTime"])
                    we = ms_to_timestamp(w["endTime"])
                    w_escaped = w["word"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    sb.append(f'        <span begin="{wb}" end="{we}">{w_escaped}</span>')
            else:
                l_escaped = line["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                sb.append(f'        {l_escaped}')
            sb.append('      </p>')

        sb.extend(['    </div>', '  </body>', '</tt>'])
        return "\n".join(sb)

    @staticmethod
    def zlf_to_enhanced_lrc(zlf_data):
        out = []
        for line in zlf_data.get("lines", []):
            time_tag = ms_to_lrc_timestamp(line["time"])
            words = line.get("words", [])
            if words:
                word_parts = []
                for w in words:
                    min_sec_ms = ms_to_timestamp(w["startTime"]).split(":")
                    m = min_sec_ms[0]
                    s_ms = min_sec_ms[1]
                    word_parts.append(f"<{m}:{s_ms}>{w['word']}")
                out.append(f"{time_tag}{''.join(word_parts)}")
            else:
                out.append(f"{time_tag}{line['text']}")
        return "\n".join(out)

    @staticmethod
    def zlf_to_lrc(zlf_data):
        out = []
        for line in zlf_data.get("lines", []):
            time_tag = ms_to_lrc_timestamp(line["time"])
            out.append(f"{time_tag}{line['text']}")
        return "\n".join(out)

    @staticmethod
    def zlf_to_srt(zlf_data):
        out = []
        for idx, line in enumerate(zlf_data.get("lines", []), 1):
            start = ms_to_srt_timestamp(line["time"])
            end = ms_to_srt_timestamp(line["endTime"])
            out.append(f"{idx}\n{start} --> {end}\n{line['text']}\n")
        return "\n".join(out)


def main():
    if len(sys.argv) < 3:
        print("Usage: converter.py <command> <input_file> [output_file] [options]")
        print("Commands:")
        print("  lrc2zlf      Convert LRC / Enhanced LRC to ZLF JSON")
        print("  ttml2zlf     Convert TTML XML to ZLF JSON")
        print("  zlf2ttml     Convert ZLF JSON to TTML XML")
        print("  zlf2lrc      Convert ZLF JSON to Standard LRC")
        print("  zlf2richlrc  Convert ZLF JSON to Enhanced Rich-Sync LRC")
        print("  zlf2srt      Convert ZLF JSON to SubRip (SRT)")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    in_file = sys.argv[2]
    out_file = sys.argv[3] if len(sys.argv) > 3 else None

    with open(in_file, "r", encoding="utf-8") as f:
        in_content = f.read()

    result = None
    if cmd == "lrc2zlf":
        data = ZukeConverter.lrc_to_zlf(in_content)
        result = json.dumps(data, indent=2, ensure_ascii=False)
    elif cmd == "ttml2zlf":
        data = ZukeConverter.ttml_to_zlf(in_content)
        result = json.dumps(data, indent=2, ensure_ascii=False)
    elif cmd == "zlf2ttml":
        data = json.loads(in_content)
        result = ZukeConverter.zlf_to_ttml(data)
    elif cmd == "zlf2richlrc":
        data = json.loads(in_content)
        result = ZukeConverter.zlf_to_enhanced_lrc(data)
    elif cmd == "zlf2lrc":
        data = json.loads(in_content)
        result = ZukeConverter.zlf_to_lrc(data)
    elif cmd == "zlf2srt":
        data = json.loads(in_content)
        result = ZukeConverter.zlf_to_srt(data)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Wrote converted output to {out_file}")
    else:
        print(result)

if __name__ == "__main__":
    main()
