#!/usr/bin/env python3
"""
Color coding utilities for sync_listings.py
Supports both native Google Sheets (Sheets API) and Excel (.xlsx via Drive API).
"""

import requests

SPREADSHEET_ID = "10ll9ZxNfkD6PgAmjvEed_oj5Qg6AeZP6"


def hex_argb_to_float_rgb(hex_color):
    """Convert ARGB hex string (e.g. 'FFFF0000') to Sheets-style float RGB dict."""
    if not hex_color or hex_color in ("00000000", "FF000000", "FFFFFFFF", "00FFFFFF"):
        return {"red": 1, "green": 1, "blue": 1}  # treat as white/default
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 8:
        hex_color = hex_color[2:]  # strip alpha
    if len(hex_color) != 6:
        return {"red": 1, "green": 1, "blue": 1}
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    result = {}
    if r > 0.01: result["red"] = r
    if g > 0.01: result["green"] = g
    if b > 0.01: result["blue"] = b
    return result if result else {"red": 1, "green": 1, "blue": 1}


def fetch_cell_formatting_xlsx(wb, sheet_name, col_idx=2):
    """Fetch cell background colors from openpyxl workbook (Excel file).
    col_idx: 1-based column index (default 2 = column B)
    Returns: list of dict with row index and background color (Sheets-style float RGB)
    """
    # Find sheet (case-insensitive)
    ws = None
    if sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
    else:
        for name in wb.sheetnames:
            if name.lower() == sheet_name.lower():
                ws = wb[name]
                break
    if ws is None:
        return []

    colors = []
    for i, row in enumerate(ws.iter_rows(min_col=col_idx, max_col=col_idx)):
        cell = row[0]
        fill = cell.fill
        hex_color = None
        if fill and fill.fill_type not in (None, "none"):
            fg = fill.fgColor
            if fg.type == "rgb":
                hex_color = fg.rgb  # ARGB string
            # theme/indexed colors: skip (treat as default)
        colors.append({"row": i, "color": hex_argb_to_float_rgb(hex_color) if hex_color else None})
    return colors

def fetch_cell_formatting(token, sheet_name, range_suffix=""):
    """Fetch cell background colors from Google Sheets.
    
    Returns: list of dict with row index and background color
    """
    range_str = f"{sheet_name}!{range_suffix}" if range_suffix else f"{sheet_name}!B:B"
    
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "ranges": range_str,
        "fields": "sheets.data.rowData.values.effectiveFormat.backgroundColor"
    }
    
    resp = requests.get(url, headers=headers, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    
    colors = []
    sheet_data = data.get("sheets", [{}])[0].get("data", [{}])[0]
    row_data = sheet_data.get("rowData", [])
    
    for i, row in enumerate(row_data):
        if not row.get("values"):
            colors.append({"row": i, "color": None})
            continue
            
        bg = row["values"][0].get("effectiveFormat", {}).get("backgroundColor", {})
        colors.append({"row": i, "color": bg})
    
    return colors


def get_color_status(bg_color):
    """Map RGB color to listing status.
    
    Returns: tuple (is_active, is_hot, hot_reason)
    """
    if not bg_color:
        return True, False, None  # Default active
    
    # White: {red: 1, green: 1, blue: 1}
    if bg_color == {"red": 1, "green": 1, "blue": 1}:
        return True, False, None
    
    # Red: {red: 1}
    if bg_color == {"red": 1}:
        return False, False, None  # Sold
    
    # Yellow: {red: 1, green: 1}
    if bg_color == {"red": 1, "green": 1}:
        return False, False, None  # Cancelled
    
    # Cyan: blue+green dominant, little/no red
    if ("blue" in bg_color and "green" in bg_color and
        bg_color.get("red", 1) < 0.9):
        return True, True, "sheet"  # Hot sale

    # Green: green dominant, little/no red, little/no blue → Hot sale
    if ("green" in bg_color and
        bg_color.get("red", 0) < 0.5 and
        bg_color.get("blue", 0) < 0.5):
        return True, True, "sheet"  # Hot sale

    # Other colors - default active
    return True, False, None


def apply_color_to_listing(listing_data, color_status, existing_hot_reason=None):
    """Apply color-based status to listing data.
    
    Constraint: Don't overwrite user-set hot_reason='user'
    """
    is_active, is_hot, hot_reason = color_status
    
    # Update is_active based on color
    listing_data["is_active"] = is_active
    
    # Only update is_hot and hot_reason if not user-set
    if existing_hot_reason != "user":
        listing_data["is_hot"] = is_hot
        if hot_reason:
            listing_data["hot_reason"] = hot_reason
        elif is_hot and "hot_reason" in listing_data:
            # Clear hot_reason if not hot anymore
            listing_data["hot_reason"] = None
    
    return listing_data


if __name__ == "__main__":
    # Test the functions
    print("Testing color_coding module...")
    
    # Test color mapping
    test_colors = [
        ({"red": 1}, "Red"),
        ({"red": 1, "green": 1}, "Yellow"),
        ({"blue": 0.8, "green": 0.9, "red": 0.1}, "Cyan"),
        ({"green": 0.85}, "Green (pure)"),
        ({"green": 0.9, "red": 0.2, "blue": 0.1}, "Green (with hints)"),
        ({"red": 1, "green": 1, "blue": 1}, "White"),
    ]
    
    for color, name in test_colors:
        is_active, is_hot, hot_reason = get_color_status(color)
        print(f"{name}: active={is_active}, hot={is_hot}, reason={hot_reason}")
    
    print("\n✅ color_coding.py module ready!")
