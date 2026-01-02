"""Chat log processor for Zoom, Teams, and generic formats."""

import json
import re
from pathlib import Path
from typing import Any

from rewindlearn.processors.base import BaseProcessor, ProcessedContent


class ChatProcessor(BaseProcessor):
    """Process chat log files."""

    supported_extensions = [".txt", ".json"]

    def process(self, path: Path) -> ProcessedContent:
        """Process a chat log file."""
        ext = path.suffix.lower()

        if ext == ".json":
            return self._process_json(path)
        elif ext == ".txt":
            return self._process_txt(path)
        else:
            raise ValueError(f"Unsupported chat format: {ext}")

    def _process_txt(self, path: Path) -> ProcessedContent:
        """Process plain text chat (Zoom format)."""
        text = path.read_text(encoding="utf-8")
        messages = self._parse_zoom_chat(text)

        return ProcessedContent(
            raw_text=text,
            timestamps=[
                {"text": m["text"], "start": m["timestamp"], "end": m["timestamp"]}
                for m in messages if "timestamp" in m
            ],
            metadata={
                "format": "zoom_txt",
                "message_count": len(messages),
                "participants": list({m.get("sender", "Unknown") for m in messages}),
            }
        )

    def _process_json(self, path: Path) -> ProcessedContent:
        """Process JSON chat export."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict) and "messages" in data:
            messages = data["messages"]
        else:
            messages = [data]

        # Build text representation
        text_parts = []
        timestamps = []

        for msg in messages:
            sender = msg.get("sender", msg.get("from", msg.get("author", "Unknown")))
            content = msg.get("text", msg.get("content", msg.get("message", "")))
            timestamp = msg.get("timestamp", msg.get("time", ""))

            text_parts.append(f"[{timestamp}] {sender}: {content}")
            if timestamp:
                timestamps.append({
                    "text": f"{sender}: {content}",
                    "start": str(timestamp),
                    "end": str(timestamp)
                })

        return ProcessedContent(
            raw_text="\n".join(text_parts),
            timestamps=timestamps,
            metadata={
                "format": "json",
                "message_count": len(messages),
            }
        )

    def _parse_zoom_chat(self, text: str) -> list[dict[str, Any]]:
        """Parse Zoom chat format: HH:MM:SS From Name to Everyone: message"""
        messages = []

        # Zoom format pattern
        pattern = r'(\d{2}:\d{2}:\d{2})\s+From\s+(.+?)\s+to\s+(.+?):\s*(.+?)(?=\d{2}:\d{2}:\d{2}\s+From|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        for timestamp, sender, recipient, content in matches:
            messages.append({
                "timestamp": timestamp,
                "sender": sender.strip(),
                "recipient": recipient.strip(),
                "text": content.strip()
            })

        # If no Zoom format found, try generic line-by-line
        if not messages:
            for line in text.strip().split("\n"):
                if line.strip():
                    messages.append({"text": line.strip()})

        return messages
