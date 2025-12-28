import sys
from pathlib import Path

# Projekt-Root in sys.path aufnehmen
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from disklib import DiskUsage


def run_tests():
    print("DiskUsage – Tests starten")

    disk = DiskUsage("D:/")
    unit = disk.get_einheit_auto(update=True)

    assert unit in ("B", "KB", "MB", "GB", "TB")
    print("✓ Auto-Einheit")

    free = disk.free_on()
    used = disk.usage_on()
    total = disk.total_on()

    assert free > 0
    assert used > 0
    assert total > 0
    assert free + used <= total * 1.01
    print("✓ Werte plausibel")

    text = disk.free_print("EN")
    assert "Free disk space" in text
    print("✓ Print-Funktion")

    print("Alle Tests OK")


if __name__ == "__main__":
    run_tests()
