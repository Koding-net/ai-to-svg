#!/usr/bin/env python3
"""
Convert an Adobe Illustrator (.ai) file to SVG.

Modern .ai files are PDF-compatible. We use MuPDF (via PyMuPDF / fitz) to
extract the vector artwork from the best page as a clean, scalable SVG.

Usage:
    Single file:
        ai_to_svg.py <input.ai> <output.svg>

    Batch (one process for many files — used by the Pro bulk converter):
        ai_to_svg.py --batch <input_dir> <output_dir>
        # Converts every *.ai in input_dir to <stem>.svg in output_dir and
        # prints a JSON report to stdout: {"converted": [...], "failed": [...]}.

Exit codes (single-file mode):
    0  success
    2  bad arguments
    3  could not open file (not a valid AI/PDF)
    4  no usable vector content found
    5  unexpected error

Batch mode always exits 0 if it ran (per-file outcomes are in the JSON report);
non-zero only on a fatal setup error (e.g. PyMuPDF missing, bad arguments).
"""
import json
import os
import sys

# Self-bootstrap: add the sibling `ai-libs` directory (populated by
# bin/setup-ai-converter.sh via `pip install --target`) to the import path,
# so PyMuPDF resolves without a venv or PYTHONPATH on the production server.
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIBS = os.path.join(_HERE, "ai-libs")
if os.path.isdir(_LIBS) and _LIBS not in sys.path:
    sys.path.insert(0, _LIBS)


def pick_best_page(doc):
    """
    Choose the page that holds the real artwork.

    AI files often contain an oversized artboard/bleed page (e.g. 14400x14400)
    in addition to the artwork page. We prefer the smallest non-trivial page
    that actually contains drawing operations, falling back to page 0.
    """
    candidates = []
    for i in range(doc.page_count):
        page = doc[i]
        rect = page.rect
        area = abs(rect.width * rect.height)
        # Count vector drawings on the page
        try:
            drawings = len(page.get_drawings())
        except Exception:
            drawings = 0
        candidates.append((i, area, drawings))

    # Prefer pages with drawings; among those, the smallest reasonable area.
    with_drawings = [c for c in candidates if c[2] > 0]
    pool = with_drawings if with_drawings else candidates

    # Sort: most drawings first, then smallest area.
    pool.sort(key=lambda c: (-c[2], c[1]))
    return pool[0][0] if pool else 0


class ConvertError(Exception):
    """Raised when a single file cannot be converted. `code` mirrors the
    single-file exit codes (3 = unreadable, 4 = no vector content)."""

    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def convert_one(fitz, src, dst):
    """Convert one .ai file to SVG at `dst`. Raises ConvertError on failure."""
    try:
        doc = fitz.open(src)
    except Exception as e:
        raise ConvertError(f"cannot open file: {e}", 3)

    if doc.page_count == 0:
        raise ConvertError("file has no pages", 4)

    try:
        idx = pick_best_page(doc)
        svg = doc[idx].get_svg_image(text_as_path=True)
    except Exception as e:
        raise ConvertError(f"render failed: {e}", 5)

    if not svg or "<svg" not in svg:
        raise ConvertError("no SVG produced", 4)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)


def import_fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"PyMuPDF not available: {e}\n")
        sys.exit(5)


def run_single(src, dst):
    fitz = import_fitz()
    try:
        convert_one(fitz, src, dst)
    except ConvertError as e:
        sys.stderr.write(str(e) + "\n")
        return e.code
    except Exception as e:
        sys.stderr.write(f"unexpected error: {e}\n")
        return 5
    return 0


def run_batch(input_dir, output_dir):
    """Convert every *.ai in input_dir; write a JSON report to stdout."""
    fitz = import_fitz()

    if not os.path.isdir(input_dir):
        sys.stderr.write(f"input dir not found: {input_dir}\n")
        return 2
    os.makedirs(output_dir, exist_ok=True)

    converted = []
    failed = []

    names = sorted(
        n for n in os.listdir(input_dir)
        if n.lower().endswith(".ai") and os.path.isfile(os.path.join(input_dir, n))
    )

    for name in names:
        src = os.path.join(input_dir, name)
        stem = os.path.splitext(name)[0]
        out_name = stem + ".svg"
        dst = os.path.join(output_dir, out_name)
        try:
            convert_one(fitz, src, dst)
            converted.append({"input": name, "output": out_name})
        except ConvertError as e:
            failed.append({"input": name, "reason": str(e)})
        except Exception as e:  # pragma: no cover
            failed.append({"input": name, "reason": f"unexpected error: {e}"})

    json.dump({"converted": converted, "failed": failed}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def main():
    args = sys.argv[1:]

    if len(args) == 3 and args[0] == "--batch":
        return run_batch(args[1], args[2])

    if len(args) == 2:
        return run_single(args[0], args[1])

    sys.stderr.write(
        "usage:\n"
        "  ai_to_svg.py <input.ai> <output.svg>\n"
        "  ai_to_svg.py --batch <input_dir> <output_dir>\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
