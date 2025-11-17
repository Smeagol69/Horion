"""Generate image snapshots for every sheet in an Excel workbook.

This script loads an .xlsx file and writes a PNG image for each sheet to
an output directory. Sheet tables are rendered with Matplotlib to keep the
workflow headless-friendly.

Dependencies: pandas and matplotlib.
"""
from __future__ import annotations

import argparse
import pathlib
import re
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a folder with PNG screenshots for each sheet in an Excel workbook."
        )
    )
    parser.add_argument(
        "workbook",
        type=pathlib.Path,
        help="Path to the .xlsx file to process.",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        help=(
            "Directory to place screenshots. Defaults to '<workbook>_screenshots' "
            "next to the workbook."
        ),
    )
    return parser.parse_args()


def read_workbook(workbook_path: pathlib.Path) -> Dict[str, pd.DataFrame]:
    """Read all sheets from the workbook as string-friendly DataFrames."""
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    sheets = pd.read_excel(workbook_path, sheet_name=None, dtype=str)
    normalized_sheets: Dict[str, pd.DataFrame] = {}
    for name, frame in sheets.items():
        # Ensure blank cells show as empty strings instead of NaN.
        cleaned = frame.fillna("")
        if cleaned.empty:
            cleaned = pd.DataFrame({" ": ["(sheet is empty)"]})
        normalized_sheets[name] = cleaned
    return normalized_sheets


def sanitize_name(name: str) -> str:
    """Return a file-system-safe representation of a sheet name."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return cleaned or "sheet"


def dataframe_to_image(df: pd.DataFrame, output_path: pathlib.Path, title: str) -> None:
    """Save a DataFrame as a PNG image using Matplotlib."""
    # Rough sizing based on table dimensions for readability.
    width = max(6, 0.8 * (len(df.columns) + 1))
    height = max(3, 0.5 * (len(df) + 2))

    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off")
    ax.set_title(title, fontsize=12, pad=10)

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 1.3)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", dpi=200)
    plt.close(fig)


def build_output_dir(workbook_path: pathlib.Path, override: pathlib.Path | None) -> pathlib.Path:
    if override:
        return override
    return workbook_path.with_name(f"{workbook_path.stem}_screenshots")


def main() -> None:
    args = parse_args()
    workbook_path: pathlib.Path = args.workbook
    output_dir = build_output_dir(workbook_path, args.output_dir)

    sheets = read_workbook(workbook_path)
    for sheet_name, frame in sheets.items():
        safe_name = sanitize_name(sheet_name)
        output_path = output_dir / f"{safe_name}.png"
        dataframe_to_image(frame, output_path, title=sheet_name)
        print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
