from __future__ import annotations

from pathlib import Path


PYTHON_EXTENSIONS = {".py"}
C_EXTENSIONS = {".c", ".h"}


def detect_language(file_path: str, source: str) -> str:
    ext = Path(file_path).suffix.lower()

    if ext in PYTHON_EXTENSIONS:
        return "python"

    if ext in C_EXTENSIONS:
        return "c"

    snippet = source[:2000]

    python_markers = [
        "def ",
        "class ",
        "import ",
        "from ",
        "async def ",
        "if __name__ ==",
    ]
    c_markers = [
        "#include",
        "int main(",
        "void ",
        "printf(",
        "typedef ",
        "struct ",
    ]

    py_score = sum(1 for marker in python_markers if marker in snippet)
    c_score = sum(1 for marker in c_markers if marker in snippet)

    if py_score > c_score:
        return "python"
    if c_score > py_score:
        return "c"

    return "unknown"