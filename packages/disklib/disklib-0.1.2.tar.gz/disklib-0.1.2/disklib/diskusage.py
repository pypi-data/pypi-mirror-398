import shutil
from pathlib import Path
from typing import Literal
from __future__ import annotations

# =====================
# TYPEN
# =====================
EINHEITEN = Literal["B", "KB", "MB", "GB", "TB"]
LANGUAGES = Literal["DE", "EN", "FR", "IT"]

# =====================
# EXCEPTIONS
# =====================
class NotValidEinheitError(Exception):
    """Ausnahme für ungültige Einheiten (B, KB, MB, GB, TB)."""
    pass

class NotValidPathError(Exception):
    """Ausnahme für ungültige oder nicht existierende Pfade."""
    pass

class NotValidLanguageError(Exception):
    """Ausnahme für ungültige Sprachen (DE, EN, FR, IT)."""
    pass

# =====================
# INTERN
# =====================
_MULTIPLIER: dict[EINHEITEN, int] = {
    "B": 1,
    "KB": 1024,
    "MB": 1024**2,
    "GB": 1024**3,
    "TB": 1024**4,
}

# =====================
# DISK USAGE
# =====================
class DiskUsage:
    """
    Berechnet und liefert Informationen über den Speicherplatz eines Pfads (Ordner/Drive).

    Parameter:
        path (str | Path): Der Pfad, dessen Speicherplatz überprüft werden soll.
        einheit (EINHEITEN, optional): Standard-Einheit für die Ausgabe (B, KB, MB, GB, TB). Default ist "GB".

    Attributes:
        path (Path): Der überprüfte Pfad.
        einheit (EINHEITEN): Aktuell verwendete Einheit.
        free (float | None): Freier Speicherplatz in der aktuellen Einheit.
        usage (float | None): Belegter Speicherplatz in der aktuellen Einheit.
        total (float | None): Gesamter Speicherplatz in der aktuellen Einheit.

    Raises:
        NotValidPathError: Wenn der angegebene Pfad nicht existiert.

    Example:
        >>> du = DiskUsage("C:/")
        >>> du.free_on("GB")
        120.45
        >>> du.free_print("EN")
        'Free disk space: 120.45 GB'
    """
    def __init__(self, path: str | Path, einheit: EINHEITEN = "GB"):
        self.path = Path(path)
        self.einheit: EINHEITEN = einheit

        self.free: float | None = None
        self.usage: float | None = None
        self.total: float | None = None

        if not self.path.exists():
            raise NotValidPathError(f"Pfad existiert nicht: {self.path}")

    # =====================
    # INTERN
    # =====================
    def _convert(self, value: int, einheit: EINHEITEN) -> float:
        """Interne Methode: Konvertiert Bytes in die gewünschte Einheit."""
        try:
            return value / _MULTIPLIER[einheit]
        except KeyError:
            raise NotValidEinheitError(
                "Ungültige Einheit. Erlaubt: B, KB, MB, GB, TB."
            )

    def _require(self, value: float | None, name: str):
        """Prüft, ob ein Wert berechnet wurde, sonst Fehler."""
        if value is None:
            raise ValueError(f"{name} wurde noch nicht berechnet.")

    def _refresh(self, einheit: EINHEITEN | None = None):
        """Aktualisiert free, usage, total in der angegebenen Einheit."""
        unit = einheit or self.einheit
        usage = shutil.disk_usage(self.path)

        self.free = self._convert(usage.free, unit)
        self.usage = self._convert(usage.used, unit)
        self.total = self._convert(usage.total, unit)

        self.einheit = unit

    # =====================
    # ÖFFENTLICHE API
    # =====================
    def free_on(self, einheit: EINHEITEN | None = None) -> float:
        """
        Berechnet und gibt den freien Speicherplatz zurück.

        Parameter:
            einheit (EINHEITEN | None): Einheit für die Rückgabe. Wenn None, wird die aktuelle Einheit verwendet.

        Returns:
            float: Freier Speicherplatz in der gewählten Einheit.

        Raises:
            NotValidEinheitError: Wenn die Einheit ungültig ist.
            ValueError: Wenn der freie Speicherplatz nicht berechnet werden konnte.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.free_on("MB")
            123456.78
        """
        self._refresh(einheit)
        return self.free  # type: ignore

    def usage_on(self, einheit: EINHEITEN | None = None) -> float:
        """
        Berechnet und gibt den belegten Speicherplatz zurück.

        Parameter:
            einheit (EINHEITEN | None): Einheit für die Rückgabe. Wenn None, wird die aktuelle Einheit verwendet.

        Returns:
            float: Belegter Speicherplatz in der gewählten Einheit.

        Raises:
            NotValidEinheitError: Wenn die Einheit ungültig ist.
            ValueError: Wenn der belegte Speicherplatz nicht berechnet werden konnte.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.usage_on("GB")
            456.78
        """
        self._refresh(einheit)
        return self.usage  # type: ignore

    def total_on(self, einheit: EINHEITEN | None = None) -> float:
        """
        Berechnet und gibt den gesamten Speicherplatz zurück.

        Parameter:
            einheit (EINHEITEN | None): Einheit für die Rückgabe. Wenn None, wird die aktuelle Einheit verwendet.

        Returns:
            float: Gesamter Speicherplatz in der gewählten Einheit.

        Raises:
            NotValidEinheitError: Wenn die Einheit ungültig ist.
            ValueError: Wenn der gesamte Speicherplatz nicht berechnet werden konnte.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.total_on("GB")
            512.0
        """
        self._refresh(einheit)
        return self.total  # type: ignore

    def get_einheit_auto(self, update: bool = False) -> EINHEITEN:
        """
        Ermittelt die geeignetste Einheit für die aktuelle Disk-Größe.

        Parameter:
            update (bool): Wenn True, werden die Werte automatisch in der ermittelten Einheit aktualisiert.

        Returns:
            EINHEITEN: Die passende Einheit (B, KB, MB, GB, TB).

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.get_einheit_auto()
            'GB'
            >>> du.get_einheit_auto(update=True)
            'GB'
        """

        if self.total < 1024:
            unit: EINHEITEN = "B"
        elif self.total < 1024**2:
            unit = "KB"
        elif self.total < 1024**3:
            unit = "MB"
        elif self.total < 1024**4:
            unit = "GB"
        else:
            unit = "TB"

        if update:
            self._refresh(unit)

        return unit

    # =====================
    # PRINT
    # =====================
    def free_print(self, language: LANGUAGES) -> str:
        """
        Gibt den freien Speicherplatz als formatierte Zeichenkette aus.

        Parameter:
            language (LANGUAGES): Sprache für die Ausgabe (DE, EN, FR, IT).

        Returns:
            str: Formatiertes Ergebnis z.B. "Free disk space: 120.45 GB".

        Raises:
            NotValidLanguageError: Wenn die Sprache ungültig ist.
            ValueError: Wenn der freie Speicherplatz noch nicht berechnet wurde.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.free_on()
            >>> du.free_print("EN")
            'Free disk space: 120.45 GB'
        """
        self._require(self.free, "Freier Speicherplatz")

        match language:
            case "DE":
                return f"Freier Speicherplatz: {self.free:.2f} {self.einheit}"
            case "EN":
                return f"Free disk space: {self.free:.2f} {self.einheit}"
            case "FR":
                return f"Espace disque libre : {self.free:.2f} {self.einheit}"
            case "IT":
                return f"Spazio su disco libero: {self.free:.2f} {self.einheit}"
            case _:
                raise NotValidLanguageError("Ungültige Sprache.")

    def usage_print(self, language: LANGUAGES) -> str:
        """
        Gibt den belegten Speicherplatz als formatierte Zeichenkette aus.

        Parameter:
            language (LANGUAGES): Sprache für die Ausgabe (DE, EN, FR, IT).

        Returns:
            str: Formatiertes Ergebnis z.B. "Used disk space: 456.78 GB".

        Raises:
            NotValidLanguageError: Wenn die Sprache ungültig ist.
            ValueError: Wenn der belegte Speicherplatz noch nicht berechnet wurde.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.usage_on()
            >>> du.usage_print("DE")
            'Belegter Speicherplatz: 456.78 GB'
        """
        self._require(self.usage, "Belegter Speicherplatz")

        match language:
            case "DE":
                return f"Belegter Speicherplatz: {self.usage:.2f} {self.einheit}"
            case "EN":
                return f"Used disk space: {self.usage:.2f} {self.einheit}"
            case "FR":
                return f"Espace disque utilisé : {self.usage:.2f} {self.einheit}"
            case "IT":
                return f"Spazio su disco utilizzato: {self.usage:.2f} {self.einheit}"
            case _:
                raise NotValidLanguageError("Ungültige Sprache.")

    def total_print(self, language: LANGUAGES) -> str:
        """
        Gibt den gesamten Speicherplatz als formatierte Zeichenkette aus.

        Parameter:
            language (LANGUAGES): Sprache für die Ausgabe (DE, EN, FR, IT).

        Returns:
            str: Formatiertes Ergebnis z.B. "Total disk space: 512.00 GB".

        Raises:
            NotValidLanguageError: Wenn die Sprache ungültig ist.
            ValueError: Wenn der gesamte Speicherplatz noch nicht berechnet wurde.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.total_on()
            >>> du.total_print("FR")
            'Espace disque total : 512.00 GB'
        """
        self._require(self.total, "Gesamter Speicherplatz")

        match language:
            case "DE":
                return f"Gesamter Speicherplatz: {self.total:.2f} {self.einheit}"
            case "EN":
                return f"Total disk space: {self.total:.2f} {self.einheit}"
            case "FR":
                return f"Espace disque total : {self.total:.2f} {self.einheit}"
            case "IT":
                return f"Spazio su disco totale: {self.total:.2f} {self.einheit}"
            case _:
                raise NotValidLanguageError("Ungültige Sprache.")

    def __str__(self) -> str:
        """
        String-Repräsentation der Instanz.

        Returns:
            str: Alle Werte der Instanz in einem lesbaren Format.

        Example:
            >>> du = DiskUsage("C:/")
            >>> du.free_on()
            >>> str(du)
            'DiskUsage(path=C:/, einheit=GB, free=120.45, usage=456.78, total=512.00)'
        """
        parts = [f"path={self.path}", f"einheit={self.einheit}"]

        if self.free is not None:
            parts.append(f"free={self.free:.2f}")
        if self.usage is not None:
            parts.append(f"usage={self.usage:.2f}")
        if self.total is not None:
            parts.append(f"total={self.total:.2f}")

        return f"DiskUsage({', '.join(parts)})"

    def __add__(self, other: DiskUsage) -> DiskUsage:
        if isinstance(other, DiskUsage):
            new = DiskUsage(path=self.path, einheit=self.einheit)
            new.free = self.free_on() + other.free_on()
            new.usage = self.usage_on() + other.usage_on()
            new.total = self.total_on() + other.total_on()
            return new
        return NotImplemented

    def __sub__(self, other: DiskUsage) -> DiskUsage:
        if isinstance(other, DiskUsage):
            new = DiskUsage(path=self.path, einheit=self.einheit)
            new.free = self.free_on() - other.free_on()
            new.usage = self.usage_on() - other.usage_on()
            new.total = self.total_on() - other.total_on()
            return new
        return NotImplemented

    def __mul__(self, factor: float | int) -> DiskUsage:
        new = DiskUsage(path=self.path, einheit=self.einheit)
        new.free = self.free_on() * factor
        new.usage = self.usage_on() * factor
        new.total = self.total_on() * factor
        return new

    def __truediv__(self, factor: float | int) -> DiskUsage:
        new = DiskUsage(path=self.path, einheit=self.einheit)
        new.free = self.free_on() / factor
        new.usage = self.usage_on() / factor
        new.total = self.total_on() / factor
        return new
