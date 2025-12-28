# cli.py
import argparse
import sys
from .diskusage import DiskUsage, NotValidPathError, NotValidLanguageError, NotValidEinheitError

def main():
    parser = argparse.ArgumentParser(description="Disk usage info")
    parser.add_argument("path", type=str, help="Pfad oder Laufwerk")
    parser.add_argument("--unit", type=str, choices=["B", "KB", "MB", "GB", "TB"], default="GB",
                        help="Einheit für Ausgabe (Standard: GB)")
    parser.add_argument("--language", type=str, choices=["DE", "EN", "FR", "IT"], default="EN",
                        help="Sprache der Ausgabe (Standard: EN)")
    parser.add_argument("--percent", action="store_true",
                        help="Zeigt prozentuale Auslastung des Laufwerks")
    args = parser.parse_args()

    try:
        du = DiskUsage(args.path, args.unit)
        du._refresh(args.unit)

        print(du.free_print(args.language))
        print(du.usage_print(args.language))
        print(du.total_print(args.language))

        if args.percent:
            percent_used = du.usage / du.total * 100  # type: ignore
            print(f"Percent used: {percent_used:.2f}%")

    except (NotValidPathError, NotValidLanguageError, NotValidEinheitError) as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
