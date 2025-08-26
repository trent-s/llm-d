#!/usr/bin/env python3
"""
Normalize or read the nightly date used in requirements/tpu.txt.

- If --set-date YYYYMMDD is provided, rewrites all `.devYYYYMMDD` occurrences
  on torch / torchvision / torch_xla lines to that date.
- Otherwise, detects the first `.devYYYYMMDD` present on those lines.

Outputs JSON to stdout:
  { "nightly_date": "YYYYMMDD", "patched": true|false, "file": "<path>" }

Optional: --out-env writes a shell file containing:
  export VLLM_NIGHTLY_DATE="YYYYMMDD"
"""

from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import sys

SCOPE_LINE = re.compile(r'^\s*(?:torch(?:vision)?==|torch_xla)\b')
DATE_PAT   = re.compile(r'\.dev([0-9]{8})')  # captures YYYYMMDD
DATE_ONLY  = re.compile(r'^[0-9]{8}$')

def read_text(p: pathlib.Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: {p} not found", file=sys.stderr)
        sys.exit(2)

def write_text_atomic(p: pathlib.Path, txt: str) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(txt, encoding="utf-8")
    os.replace(tmp, p)

def detect_first_date(txt: str) -> str:
    for line in txt.splitlines():
        if SCOPE_LINE.search(line):
            m = DATE_PAT.search(line)
            if m:
                return m.group(1)
    return ""

def patch_dates(txt: str, nightly: str) -> tuple[str, int]:
    """Rewrite .devYYYYMMDD -> .dev<nightly> only on scoped lines."""
    out_lines = []
    replaced = 0
    for line in txt.splitlines(keepends=False):
        if SCOPE_LINE.search(line):
            new_line, n = DATE_PAT.subn(r'.dev' + nightly, line)
            out_lines.append(new_line)
            replaced += n
        else:
            out_lines.append(line)
    # preserve trailing newline if original had one
    return ("\n".join(out_lines) + ("\n" if txt.endswith("\n") else "")), replaced

def main() -> None:
    ap = argparse.ArgumentParser(description="Manage TPU nightly date in requirements.")
    ap.add_argument("--file", default="requirements/tpu.txt",
                    help="path to TPU requirements file (default: requirements/tpu.txt)")
    ap.add_argument("--set-date", dest="set_date",
                    help="YYYYMMDD nightly date to set across the file")
    ap.add_argument("--out-env",
                    help="write a shell exports file (e.g., /tmp/vllm_tpu.env) containing VLLM_NIGHTLY_DATE")
    ap.add_argument("--json-out",
                    help="write JSON to this file instead of stdout")
    ap.add_argument("--no-write", action="store_true",
                    help="do not modify the requirements even if --set-date is given")
    args = ap.parse_args()

    req_path = pathlib.Path(args.file)
    txt = read_text(req_path)

    if args.set_date:
        if not DATE_ONLY.fullmatch(args.set_date):
            print("error: --set-date must be YYYYMMDD", file=sys.stderr)
            sys.exit(1)
        nightly = args.set_date
        new_txt, nrep = patch_dates(txt, nightly)
        if not args.no_write and new_txt != txt:
            write_text_atomic(req_path, new_txt)
        patched = (nrep > 0)
    else:
        nightly = detect_first_date(txt)
        if not nightly:
            print("error: no .devYYYYMMDD found on torch/torchvision/torch_xla lines", file=sys.stderr)
            sys.exit(1)
        patched = False

    # optional env file
    if args.out_env:
        pathlib.Path(args.out_env).write_text(
            f'export VLLM_NIGHTLY_DATE="{nightly}"\n', encoding="utf-8"
        )

    result = {
        "nightly_date": f"dev{nightly}",
        "patched": patched,
        "file": str(req_path),
    }

    out = json.dumps(result, indent=2, sort_keys=True)
    if args.json_out:
        pathlib.Path(args.json_out).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)

if __name__ == "__main__":
    main()
