import re
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

from src.config import FINCEN_SAR_WORKBOOKS, RAW_DATA_DIR, WORKBOOK_INVENTORY_FILE


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 Tennessee Financial Crime Intelligence Dashboard research script"
        "research script"
    )
}


def looks_like_excel_file(path: Path) -> bool:
    """
    Validate that a downloaded .xlsx file is a readable ZIP-based Excel file.
    """

    if not path.exists():
        return False

    if path.stat().st_size < 1_000:
        return False

    try:
        with zipfile.ZipFile(path, "r") as z:
            names = set(z.namelist())

            if "[Content_Types].xml" not in names:
                return False

            if not any(name.startswith("xl/worksheets/") for name in names):
                return False

        return True

    except zipfile.BadZipFile:
        return False
    except Exception:
        return False


def download_file(
    url: str,
    output_path: Path,
    overwrite: bool = False,
    max_retries: int = 3,
    retry_sleep: float = 1.5,
) -> Optional[Path]:
    """
    Download a file from a URL to a local path.

    If a URL fails, return None instead of crashing the full pipeline.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not overwrite:
        if looks_like_excel_file(output_path):
            print(f"Already exists: {output_path}")
            return output_path

        print(f"Existing file appears invalid and will be refreshed: {output_path}")
        output_path.unlink(missing_ok=True)

    print(f"Downloading: {url}")

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=REQUEST_HEADERS,
                timeout=90,
            )
            response.raise_for_status()

            content = response.content

            if not content or len(content) < 1_000:
                raise ValueError(
                    f"Downloaded file appears too small: {len(content)} bytes"
                )

            output_path.write_bytes(content)

            if not looks_like_excel_file(output_path):
                output_path.unlink(missing_ok=True)
                raise ValueError("Downloaded file is not a valid Excel workbook.")

            print(f"Saved: {output_path}")

            return output_path

        except Exception as exc:
            last_error = exc
            print(f"WARNING: Download attempt {attempt}/{max_retries} failed.")
            print(f"Reason: {exc}")

            if attempt < max_retries:
                time.sleep(retry_sleep)

    print(f"WARNING: Could not download {url}")
    print(f"Final reason: {last_error}")

    return None


def download_fincen_workbooks(overwrite: bool = False) -> Dict[str, Path]:
    """
    Download all configured FinCEN SAR Stats workbooks.

    Returns only successfully downloaded or already-existing workbooks.
    """

    downloaded = {}

    for key, meta in FINCEN_SAR_WORKBOOKS.items():
        output_path = RAW_DATA_DIR / meta["filename"]
        local_path = download_file(meta["url"], output_path, overwrite=overwrite)

        if local_path is not None:
            downloaded[key] = local_path
        else:
            print(f"Skipping failed workbook: {meta['industry_name']}")

    return downloaded


def list_workbook_sheets(workbook_path: Path) -> List[str]:
    """
    Return sheet names from an Excel workbook.
    """

    excel_file = pd.ExcelFile(workbook_path, engine="openpyxl")
    return excel_file.sheet_names


def inspect_workbooks() -> pd.DataFrame:
    """
    Inspect downloaded workbooks and save an inventory of sheet names.

    Returns
    -------
    pd.DataFrame
        Workbook inventory table.
    """

    rows = []

    for key, meta in FINCEN_SAR_WORKBOOKS.items():
        workbook_path = RAW_DATA_DIR / meta["filename"]

        if not workbook_path.exists():
            rows.append(
                {
                    "workbook_key": key,
                    "industry_name": meta["industry_name"],
                    "filename": meta["filename"],
                    "sheet_name": None,
                    "status": "missing",
                }
            )
            continue

        if not looks_like_excel_file(workbook_path):
            rows.append(
                {
                    "workbook_key": key,
                    "industry_name": meta["industry_name"],
                    "filename": meta["filename"],
                    "sheet_name": None,
                    "status": "invalid_excel_file",
                }
            )
            continue

        try:
            sheet_names = list_workbook_sheets(workbook_path)

            for sheet_name in sheet_names:
                rows.append(
                    {
                        "workbook_key": key,
                        "industry_name": meta["industry_name"],
                        "filename": meta["filename"],
                        "sheet_name": sheet_name,
                        "status": "available",
                    }
                )

        except Exception as exc:
            rows.append(
                {
                    "workbook_key": key,
                    "industry_name": meta["industry_name"],
                    "filename": meta["filename"],
                    "sheet_name": None,
                    "status": f"error: {exc}",
                }
            )

    inventory = pd.DataFrame(rows)
    inventory.to_csv(WORKBOOK_INVENTORY_FILE, index=False)

    print(f"Workbook inventory saved to: {WORKBOOK_INVENTORY_FILE}")

    return inventory


def normalize_text(value) -> str:
    """
    Normalize text values for matching labels inside messy Excel sheets.
    """

    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)

    return text


def read_sheet_raw(workbook_path: Path, sheet_name: str) -> pd.DataFrame:
    """
    Read a sheet without assuming headers.
    """

    if not looks_like_excel_file(workbook_path):
        raise ValueError(f"Invalid Excel workbook: {workbook_path}")

    return pd.read_excel(
        workbook_path,
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl",
    )