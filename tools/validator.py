#!/usr/bin/env python3
"""
ZukeLyrics Validation Engine
Validates ZLF (ZukeLyrics Format) JSON files against schema and temporal consistency rules.
"""

import os
import sys
import json
from pathlib import Path

def validate_zlf_file(file_path):
    errors = []
    warnings = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSON Parse Error: {e}"], []
    except UnicodeDecodeError as e:
        return False, [f"Encoding Error: Not valid UTF-8 ({e})"], []
    except Exception as e:
        return False, [f"File read error: {e}"], []

    # Required top-level fields
    required_fields = ["videoId", "title", "artist", "syncedType", "lines"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    synced_type = data.get("syncedType")
    if synced_type not in ["word", "line", "plain", "instrumental"]:
        errors.append(f"Invalid syncedType: '{synced_type}'. Must be 'word', 'line', 'plain', or 'instrumental'")

    lines = data.get("lines", [])
    if not isinstance(lines, list):
        errors.append("'lines' must be an array")
        return False, errors, warnings

    if synced_type in ["word", "line"] and len(lines) == 0:
        warnings.append(f"Track has syncedType '{synced_type}' but 'lines' array is empty.")

    prev_line_time = -1

    for line_idx, line in enumerate(lines):
        if not isinstance(line, dict):
            errors.append(f"Line [{line_idx}]: must be an object")
            continue

        l_time = line.get("time")
        l_end = line.get("endTime")
        l_text = line.get("text")

        if l_time is None or not isinstance(l_time, int) or l_time < 0:
            errors.append(f"Line [{line_idx}]: 'time' must be a non-negative integer")
        if l_end is None or not isinstance(l_end, int) or l_end < 0:
            errors.append(f"Line [{line_idx}]: 'endTime' must be a non-negative integer")
        if l_text is None or not isinstance(l_text, str):
            errors.append(f"Line [{line_idx}]: 'text' must be a string")

        if l_time is not None and l_end is not None:
            if l_end < l_time:
                errors.append(f"Line [{line_idx}]: endTime ({l_end}ms) is less than time ({l_time}ms)")
            if l_time < prev_line_time:
                warnings.append(f"Line [{line_idx}]: time ({l_time}ms) is out of chronological order (prev line was {prev_line_time}ms)")
            prev_line_time = l_time

        # Validate words if present
        words = line.get("words")
        if words is not None:
            if not isinstance(words, list):
                errors.append(f"Line [{line_idx}]: 'words' must be an array")
            else:
                prev_word_end = -1
                for w_idx, w in enumerate(words):
                    if not isinstance(w, dict):
                        errors.append(f"Line [{line_idx}] Word [{w_idx}]: must be an object")
                        continue
                    w_start = w.get("startTime")
                    w_end = w.get("endTime")
                    w_token = w.get("word")

                    if w_start is None or not isinstance(w_start, int) or w_start < 0:
                        errors.append(f"Line [{line_idx}] Word [{w_idx}]: 'startTime' must be a non-negative integer")
                    if w_end is None or not isinstance(w_end, int) or w_end < 0:
                        errors.append(f"Line [{line_idx}] Word [{w_idx}]: 'endTime' must be a non-negative integer")
                    if w_token is None or not isinstance(w_token, str):
                        errors.append(f"Line [{line_idx}] Word [{w_idx}]: 'word' must be a string")

                    if w_start is not None and w_end is not None:
                        if w_end < w_start:
                            errors.append(f"Line [{line_idx}] Word [{w_idx}] ('{w_token}'): endTime ({w_end}ms) < startTime ({w_start}ms)")
                        if w_start < prev_word_end:
                            warnings.append(f"Line [{line_idx}] Word [{w_idx}] ('{w_token}'): starts at {w_start}ms before previous word ended at {prev_word_end}ms")
                        prev_word_end = w_end

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else "lyrics-database"
    target = Path(target_path)

    if not target.exists():
        print(f"Error: Target path does not exist: {target_path}")
        sys.exit(1)

    files_to_check = []
    if target.is_file():
        files_to_check.append(target)
    else:
        files_to_check.extend(target.rglob("*.json"))

    print(f"==================================================")
    print(f" ZukeLyrics Format (ZLF v1) Validator")
    print(f" Target: {target}")
    print(f" Checking {len(files_to_check)} files...")
    print(f"==================================================")

    total_checked = 0
    total_passed = 0
    all_failures = []

    for file_path in files_to_check:
        total_checked += 1
        valid, errors, warnings = validate_zlf_file(file_path)

        rel = os.path.relpath(file_path, os.getcwd())
        if valid:
            total_passed += 1
            status = "PASS"
            if warnings:
                status += f" (with {len(warnings)} warnings)"
            print(f"[{status}] {rel}")
            for w in warnings:
                print(f"   ⚠️  {w}")
        else:
            print(f"[FAIL] {rel}")
            for e in errors:
                print(f"   ❌ {e}")
            for w in warnings:
                print(f"   ⚠️  {w}")
            all_failures.append((rel, errors))

    print(f"\nSummary:")
    print(f"Total: {total_checked} | Passed: {total_passed} | Failed: {len(all_failures)}")

    if all_failures:
        print("\n❌ Validation FAILED.")
        sys.exit(1)
    else:
        print("\n✅ All files PASSED validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
