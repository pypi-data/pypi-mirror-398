from .diskusage import DiskUsage
from typing import Literal
from pathlib import Path
import json
import csv
import pandas as pd

# =====================
# Zulässige Formate
# =====================
FORMATE = Literal["json", "csv", "excel"]

# =====================
# Export-Funktion
# =====================
ALLOWED_CLASSES = (DiskUsage,)

def export(obj: object, format: FORMATE, filename: str | Path) -> None:
    """
    Exportiert nur erlaubte Klassen in JSON, CSV oder Excel.

    Parameter:
        obj: Instanz der erlaubten Klasse
        format: "json", "csv", "excel"
        filename: Ziel-Datei
    """
    if not isinstance(obj, ALLOWED_CLASSES):
        raise TypeError(f"{obj.__class__.__name__} ist nicht exportierbar.")

    filename = Path(filename)
    format = format.lower()

    # JSON
    if format == "json":
        data = obj.__json__()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # CSV
    elif format == "csv":
        data = obj.__csv__()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if isinstance(data, dict):
                writer.writerow(["Key", "Value"])
                for k, v in data.items():
                    writer.writerow([k, v])
            elif isinstance(data, list):
                for row in data:
                    writer.writerow(row)

    # Excel
    elif format == "excel":
        data = obj.__excel__()
        if isinstance(data, dict):
            df = pd.DataFrame(list(data.items()), columns=["Key", "Value"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        df.to_excel(filename, index=False)

    else:
        raise ValueError(f"Unbekanntes Format: {format}")

    print(f"Export erfolgreich: {filename}")
