"""Concept chunks chain for CSV output."""

import csv
import io

from rewindlearn.chains.base import BaseChain


class ChunksChain(BaseChain):
    """Extract concept chunks for video splitting."""

    def post_process(self, result: str) -> str:
        """Validate and clean CSV output."""
        result = super().post_process(result)

        # Remove markdown code fences if present
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        # Parse and re-format as clean CSV
        lines = result.strip().split("\n")
        output = io.StringIO()
        writer = csv.writer(output)

        # Ensure header row
        header_written = False
        expected_header = ["concept", "description", "start_time", "end_time"]

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                reader = csv.reader([line])
                row = next(reader)

                # Check if this is a header row
                if not header_written:
                    if row[0].lower() == "concept":
                        writer.writerow(expected_header)
                        header_written = True
                        continue
                    else:
                        writer.writerow(expected_header)
                        header_written = True

                # Write data row if it has enough columns
                if len(row) >= 4:
                    writer.writerow(row[:4])
            except Exception:
                continue

        return output.getvalue()
