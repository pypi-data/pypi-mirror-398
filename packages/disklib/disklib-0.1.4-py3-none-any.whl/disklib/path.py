"""Utility module providing a small `Path` helper class for filesystem operations.

Dieses Modul enthält die Klasse `Path`, eine leichte Alternative zu
`pathlib.Path` mit einigen komfortablen Methoden zum Lesen/Schreiben,
Kopieren, Verschieben und Abfragen von Dateien und Verzeichnissen.

Die Docstrings in dieser Datei sind bewusst ausführlich gehalten, damit
Entwickler die Funktionsweise der Methoden schnell verstehen können.
"""

from __future__ import annotations
import os
import shutil
import time
from typing import Iterable


class Path:
    """
    Eine einfache Pfad-Klasse zur Dateisystem-Interaktion.
    Parameter:
        path (str): Der Pfad als String.
    Methoden:
        join(*parts: str) -> Path: Verbindet den aktuellen Pfad mit weiteren Teilen.
        absolute() -> Path: Gibt den absoluten Pfad zurück.
        resolve() -> Path: Gibt den aufgelösten Pfad zurück.
        exists() -> bool: Prüft, ob der Pfad existiert.
        is_file() -> bool: Prüft, ob der Pfad eine Datei ist.
        is_dir() -> bool: Prüft, ob der Pfad ein Verzeichnis ist.
        mkdir(parents=False, exist_ok=True) -> None: Erstellt ein Verzeichnis.
        list() -> Iterable[Path]: Listet den Inhalt eines Verzeichnisses auf.
        read_text(encoding="utf-8") -> str: Liest den Inhalt einer Textdatei.
        write_text(text: str, encoding="utf-8", append=False) -> None: Schreibt Text in eine Datei.
        read_bytes() -> bytes: Liest den Inhalt einer Binärdatei.
        write_bytes(data: bytes) -> None: Schreibt Binärdaten in eine Datei.
        delete(recursive=False) -> None: Löscht die Datei oder das Verzeichnis.
        copy_to(target: Path) -> None: Kopiert die Datei oder das Verzeichnis zu einem Ziel.
        move_to(target: Path) -> None: Verschiebt die Datei oder das Verzeichnis zu einem Ziel.
        size() -> int: Gibt die Größe der Datei oder des Verzeichnisses in Bytes zurück.
        modified_time() -> float: Gibt die letzte Änderungszeit als Timestamp zurück.
        modified_time_str() -> str: Gibt die letzte Änderungszeit als lesbaren String zurück.
    Raises:
        TypeError: Wenn der Pfad kein String ist.
    Example:
        >>> p = Path("example.txt")
        >>> p.write_text("Hallo Welt")
        >>> print(p.read_text())
        Hallo Welt
    """
    def __init__(self, path: str):
        if not isinstance(path, str):
            raise TypeError("path muss ein String sein")
        self._path = os.path.normpath(path)

    def __str__(self) -> str:
        """
        Gibt den Pfad als String zurück.
        Returns:
            str: Der Pfad als String.
        """
        return self._path

    def __repr__(self) -> str:
        """
        Gibt eine offizielle String-Darstellung des Pfads zurück.
        Returns:
            str: Offizielle String-Darstellung.
        """
        return f"Path({self._path!r})"

    def __eq__(self, other: Path) -> bool:
        """
        Vergleicht zwei Path-Objekte.
        Returns:
            bool: True, wenn die beiden Pfade gleich sind.
        """
        return isinstance(other, Path) and self.absolute()._path == other.absolute()._path

    @property
    def path(self) -> str:
        """
        Gibt den Pfad als String zurück.
        Returns:
            str: Der Pfad als String.
        """
        return self._path

    @property
    def name(self) -> str:
        """
        Gibt den Namen der Datei oder des Verzeichnisses zurück.
        Returns:
            str: Der Name der Datei oder des Verzeichnisses.
        """
        return os.path.basename(self._path)

    @property
    def stem(self) -> str:
        """
        Gibt den Dateinamen ohne Erweiterung zurück.
        Returns:
            str: Der Dateiname ohne Erweiterung.
        """
        return os.path.splitext(self.name)[0]

    @property
    def suffix(self) -> str:
        """
        Gibt die Dateierweiterung zurück.
        Returns:
            str: Die Dateierweiterung.
        """
        return os.path.splitext(self._path)[1]

    @property
    def parent(self) -> Path:
        """
        Gibt das Elternverzeichnis zurück.
        Returns:
            Path: Das Elternverzeichnis.
        """
        return Path(os.path.dirname(self._path))

    def join(self, *parts: str) -> Path:
        """Erstellt einen neuen `Path`, der den aktuellen Pfad mit
        zusätzlichen Pfadteilen verbindet.

        Args:
            *parts: Beliebig viele Strings, die an den aktuellen Pfad
                angehängt werden.

        Returns:
            Path: Ein neues `Path`-Objekt mit dem kombinierten Pfad.
        """
        return Path(os.path.join(self._path, *parts))

    def absolute(self) -> Path:
        """Gibt einen absoluten Pfad zurück.

        Nutzt `os.path.abspath` um symbolische Referenzen wie `.` und `..`
        aufzulösen, liefert aber keine Auflösung von Symlinks (siehe
        `resolve`).

        Returns:
            Path: Ein neues `Path`-Objekt mit dem absoluten Pfad.
        """
        return Path(os.path.abspath(self._path))

    def resolve(self) -> Path:
        """Löst den Pfad vollständig auf und folgt symbolischen Links.

        Dies entspricht `os.path.realpath` und ist nützlich, wenn echte
        Dateisystempfade benötigt werden (z. B. für Vergleiche oder
        Hardlinks).

        Returns:
            Path: Ein neues `Path`-Objekt mit dem aufgelösten Pfad.
        """
        return Path(os.path.realpath(self._path))

    def exists(self) -> bool:
        """Prüft, ob der Pfad im Dateisystem existiert.

        Returns:
            bool: `True`, wenn die Datei oder das Verzeichnis existiert,
            sonst `False`.
        """
        return os.path.exists(self._path)

    def is_file(self) -> bool:
        """Prüft, ob der Pfad auf eine reguläre Datei zeigt.

        Returns:
            bool: `True`, wenn der Pfad eine Datei ist, sonst `False`.
        """
        return os.path.isfile(self._path)

    def is_dir(self) -> bool:
        """Prüft, ob der Pfad ein Verzeichnis ist.

        Returns:
            bool: `True`, wenn der Pfad ein Verzeichnis ist, sonst
            `False`.
        """
        return os.path.isdir(self._path)

    def mkdir(self, parents: bool = False, exist_ok: bool = True) -> None:
        """Erstellt ein Verzeichnis am Pfad.

        Args:
            parents: Wenn `True`, werden fehlende übergeordnete
                Verzeichnisse ebenfalls erstellt (ähnlich wie
                `mkdir -p`).
            exist_ok: Wenn `True`, wird kein Fehler ausgelöst, falls das
                Verzeichnis bereits existiert.

        Raises:
            OSError: Wenn das Verzeichnis nicht erstellt werden kann und
                `exist_ok` `False` ist.
        """
        if parents:
            os.makedirs(self._path, exist_ok=exist_ok)
        else:
            if exist_ok and self.exists():
                return
            os.mkdir(self._path)

    def list(self) -> Iterable[Path]:
        """Listet alle Einträge in diesem Verzeichnis auf.

        Returns:
            Iterable[Path]: Eine Liste von `Path`-Objekten für jeden
            Namen im Verzeichnis.

        Raises:
            NotADirectoryError: Wenn `self` kein Verzeichnis ist.
        """
        if not self.is_dir():
            raise NotADirectoryError(self._path)
        return [self.join(name) for name in os.listdir(self._path)]

    def read_text(self, encoding: str = "utf-8") -> str:
        """Liest den gesamten Textinhalt der Datei und gibt ihn als
        String zurück.

        Args:
            encoding: Die Textkodierung, die beim Lesen verwendet wird.

        Returns:
            str: Der gelesene Text.

        Raises:
            FileNotFoundError: Wenn die Datei nicht existiert.
            UnicodeDecodeError: Wenn die Datei nicht mit der angegebenen
                Kodierung decodiert werden kann.
        """
        with open(self._path, "r", encoding=encoding) as f:
            return f.read()

    def write_text(self, text: str, encoding: str = "utf-8", append: bool = False) -> None:
        """Schreibt Text in die Datei.

        Args:
            text: Der zu schreibende Text.
            encoding: Die zu verwendende Textkodierung.
            append: Wenn `True`, wird an die Datei angehängt, sonst wird
                überschrieben.

        Notes:
            Die Methode stellt sicher, dass das Elternverzeichnis existiert
            und legt es bei Bedarf an.
        """
        mode = "a" if append else "w"
        self.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, mode, encoding=encoding) as f:
            f.write(text)

    def read_bytes(self) -> bytes:
        """Liest die Datei im Binärmodus und gibt die rohen Bytes zurück.

        Returns:
            bytes: Der Dateiinhalt als Bytes.
        """
        with open(self._path, "rb") as f:
            return f.read()

    def write_bytes(self, data: bytes) -> None:
        """Schreibt rohe Bytes in die Datei.

        Args:
            data: Die zu schreibenden Bytes.

        Notes:
            Erzeugt das Elternverzeichnis, falls nötig.
        """
        self.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "wb") as f:
            f.write(data)

    def delete(self, recursive: bool = False) -> None:
        """Löscht die Datei oder das Verzeichnis.

        Args:
            recursive: Wenn `True` und `self` ein Verzeichnis ist, wird
                der Inhalt rekursiv gelöscht.

        Raises:
            OSError: Wenn das Entfernen fehlschlägt (z. B. Verzeichnis nicht
                leer und `recursive` ist False).
        """
        if self.is_file():
            os.remove(self._path)
        elif self.is_dir():
            if recursive:
                shutil.rmtree(self._path)
            else:
                os.rmdir(self._path)

    def copy_to(self, target: Path) -> None:
        """Kopiert diese Datei oder dieses Verzeichnis zu `target`.

        Args:
            target: Ein `Path`-Objekt, das das Ziel repräsentiert.

        Notes:
            - Bei Dateien wird `shutil.copy2` verwendet, um Metadaten zu
              erhalten.
            - Bei Verzeichnissen wird `shutil.copytree` mit
              `dirs_exist_ok=True` verwendet, um bestehende Verzeichnisse
              zu überschreiben/zu ergänzen.
        """
        if self.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._path, target._path)
        elif self.is_dir():
            shutil.copytree(self._path, target._path, dirs_exist_ok=True)

    def move_to(self, target: Path) -> None:
        """Verschiebt diese Datei oder dieses Verzeichnis zu `target`.

        Args:
            target: Ziel-`Path`. Falls nötig, wird das Elternverzeichnis des
                Ziels angelegt.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(self._path, target._path)

    def size(self) -> int:
        """Gibt die Größe der Datei oder des Verzeichnisses in Bytes
        zurück.

        Returns:
            int: Bei Dateien die Dateigröße, bei Verzeichnissen die Summe
            aller Dateien unterhalb des Verzeichnisses.
        """
        if self.is_file():
            return os.path.getsize(self._path)

        total = 0
        for root, _, files in os.walk(self._path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        return total

    def modified_time(self) -> float:
        """Gibt die letzte Änderungszeit als POSIX-Timestamp zurück.

        Returns:
            float: POSIX-Timestamp der letzten Änderung (wie von
            `os.path.getmtime`).
        """
        return os.path.getmtime(self._path)

    def modified_time_str(self) -> str:
        """Gibt die letzte Änderungszeit als lesbaren String zurück.

        Beispiel: 'Wed Dec 24 12:34:56 2025'

        Returns:
            str: Menschlich lesbare Darstellung der letzten Änderung.
        """
        return time.ctime(self.modified_time())
