"""Transcript file processor for .txt, .vtt, .srt files."""

import re
from pathlib import Path

import webvtt

from rewindlearn.processors.base import BaseProcessor, ProcessedContent


class TranscriptProcessor(BaseProcessor):
    """Process transcript files with optional timestamp extraction."""

    supported_extensions = [".txt", ".vtt", ".srt"]

    def process(self, path: Path) -> ProcessedContent:
        """Process a transcript file."""
        ext = path.suffix.lower()

        if ext == ".txt":
            return self._process_txt(path)
        elif ext in [".vtt", ".srt"]:
            return self._process_vtt(path)
        else:
            raise ValueError(f"Unsupported transcript format: {ext}")

    def _process_txt(self, path: Path) -> ProcessedContent:
        """Process plain text transcript."""
        text = path.read_text(encoding="utf-8")
        timestamps = self._extract_inline_timestamps(text)

        return ProcessedContent(
            raw_text=text,
            timestamps=timestamps,
            metadata={
                "format": "txt",
                "has_timestamps": len(timestamps) > 0,
                "char_count": len(text),
            }
        )

    def _process_vtt(self, path: Path) -> ProcessedContent:
        """Process VTT/SRT subtitle file."""
        try:
            captions = webvtt.read(str(path))
        except Exception as e:
            raise ValueError(f"Error parsing VTT/SRT file: {e}")

        timestamps = []
        full_text_parts = []

        for caption in captions:
            timestamps.append({
                "text": caption.text,
                "start": caption.start,
                "end": caption.end
            })
            full_text_parts.append(f"[{caption.start}] {caption.text}")

        return ProcessedContent(
            raw_text="\n".join(full_text_parts),
            timestamps=timestamps,
            metadata={
                "format": path.suffix.lower(),
                "caption_count": len(captions),
                "has_timestamps": True,
            }
        )

    def _extract_inline_timestamps(self, text: str) -> list[dict[str, str]]:
        """Extract timestamps from inline format like [00:01:23] or (00:01:23)."""
        timestamps = []

        # Pattern: [HH:MM:SS] or (HH:MM:SS) followed by text
        pattern = r'[\[\(](\d{1,2}:\d{2}:\d{2})[\]\)]\s*(.+?)(?=[\[\(]\d{1,2}:\d{2}:\d{2}[\]\)]|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        for i, (timestamp, content) in enumerate(matches):
            # Calculate end time (use next timestamp or add 30s)
            if i + 1 < len(matches):
                end_time = matches[i + 1][0]
            else:
                end_time = self._add_seconds(timestamp, 30)

            timestamps.append({
                "text": content.strip(),
                "start": timestamp,
                "end": end_time
            })

        return timestamps

    def _add_seconds(self, timestamp: str, seconds: int) -> str:
        """Add seconds to a timestamp string."""
        parts = timestamp.split(":")
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        total_seconds = h * 3600 + m * 60 + s + seconds
        return f"{total_seconds // 3600:02d}:{(total_seconds % 3600) // 60:02d}:{total_seconds % 60:02d}"
