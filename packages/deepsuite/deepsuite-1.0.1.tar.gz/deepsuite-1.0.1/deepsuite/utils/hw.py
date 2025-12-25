"""Hardware- und Systeminformationen.

Dieses Modul stellt die Klasse HWInfo bereit, um CPU-, GPU-, RAM-, OS- und
Python-Informationsstrings abzufragen. Die Methoden cachen die Ergebnisse
für wiederholte Zugriffe.
"""

from __future__ import annotations

import platform
import sys

import cpuinfo
import psutil
import torch


class HWInfo:
    """Sammelt Hardware- und Systeminformationen.

    Die Abfragen sind fehlertolerant und geben "unknown" zurück, falls
    Informationen nicht ermittelbar sind.
    """

    _cpu_info: str | None
    _gpu_info: str | None
    _ram_info: str | None
    _os_info: str | None
    _python_info: str | None

    def __init__(self) -> None:
        self._cpu_info = None
        self._gpu_info = None
        self._ram_info = None
        self._os_info = None
        self._python_info = None

    def __str__(self) -> str:
        """Liefert eine kompakte Darstellung aller Infos als String."""
        return (
            f"CPU: {self.get_cpu_info()}\n"
            f"GPU: {self.get_gpu_info()}\n"
            f"RAM: {self.get_ram_info()}\n"
            f"OS: {self.get_os_info()}\n"
            f"Python: {self.get_python_info()}"
        )

    def __repr__(self) -> str:
        """Liefert die formale Repräsentation mit allen Feldern."""
        return (
            f"HWInfo(cpu={self.get_cpu_info()}, "
            f"gpu={self.get_gpu_info()}, "
            f"ram={self.get_ram_info()}, "
            f"os={self.get_os_info()}, "
            f"python={self.get_python_info()})"
        )

    def get_cpu_info(self) -> str:
        """Gibt CPU-Informationen (z. B. Markenname) zurück.

        Returns:
            str: Bevorzugt der Markenname, sonst "unknown".
        """
        if self._cpu_info is None:
            try:
                info = cpuinfo.get_cpu_info()
                self._cpu_info = (
                    info.get("brand_raw", "unknown")
                    .replace("(R)", "")
                    .replace("CPU ", "")
                    .replace("@ ", "")
                )
            except Exception:
                self._cpu_info = "unknown"
        return self._cpu_info

    def get_gpu_info(self, index: int = 0) -> str:
        """Gibt GPU-Informationen für das angegebene Gerät zurück.

        Args:
            index: CUDA-Geräteindex.

        Returns:
            str: Gerätestring mit Name und geschätztem Speicher oder "unknown".
        """
        if self._gpu_info is None:
            try:
                properties = torch.cuda.get_device_properties(index)
                self._gpu_info = f"{properties.name}, {properties.total_memory / (1 << 20):.0f}MiB"
            except Exception:
                self._gpu_info = "unknown"
        return self._gpu_info

    def get_ram_info(self) -> str:
        """Gibt den gesamten RAM als String in GB zurück."""
        if self._ram_info is None:
            try:
                ram = psutil.virtual_memory()
                self._ram_info = f"{ram.total / (1 << 30):.2f} GB"
            except Exception:
                self._ram_info = "unknown"
        return self._ram_info

    def get_os_info(self) -> str:
        """Gibt Betriebssysteminformationen zurück."""
        if self._os_info is None:
            try:
                self._os_info = platform.platform()
            except Exception:
                self._os_info = "unknown"
        return self._os_info

    def get_python_info(self) -> str:
        """Gibt die Python-Versionsnummer als String zurück."""
        if self._python_info is None:
            try:
                self._python_info = sys.version.split()[0]
            except Exception:
                self._python_info = "unknown"
        return self._python_info
