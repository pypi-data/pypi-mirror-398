"""A simple script to compare files by line count and byte size."""

from dataclasses import dataclass
from pathlib import Path

PATH_TO_FILES = Path("tests/bearbase/data")

FILE_NAME = "sample_database"

ALL_FILES: list[Path] = [f for f in PATH_TO_FILES.iterdir() if f.name.startswith(FILE_NAME)]


@dataclass
class CompareFile:
    extension: str
    line_length: int
    byte_size: int

    def __str__(self) -> str:
        return f"{self.extension}: {self.line_length} lines, {self.byte_size} bytes"


if __name__ == "__main__":
    compare_files: list[CompareFile] = []
    for file_path in ALL_FILES:
        with open(file_path, "rb") as f:
            content = f.read()
            line_count = content.count(b"\n") + 1
            byte_size = len(content)
            compare_files.append(CompareFile(file_path.suffix, line_count, byte_size))

    for compare_file in sorted(compare_files, key=lambda x: x.extension):
        print(compare_file)
