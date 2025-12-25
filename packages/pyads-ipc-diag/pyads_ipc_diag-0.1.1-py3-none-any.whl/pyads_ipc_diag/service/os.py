"""
os.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 23.12.2025 12.21

"""

from dataclasses import dataclass

from .mdp_service import MDPService
from ..areas import CONFIG_AREA


@dataclass
class OSInfo:
    major_version: int
    minor_version: int
    build: int
    csd_version: str


class OS(MDPService):
    MODULE = CONFIG_AREA.OS

    def __init__(self, ipc):
        self.ipc = ipc
        self._major_version = None
        self._minor_version = None
        self._build = None
        self._csd_version = None

    @property
    def major_version(self) -> int:
        """OS Major Version (UNSIGNED32)"""
        if self._major_version is None:
            self._major_version = self._u32(1)
        return self._major_version

    @property
    def minor_version(self) -> int:
        """OS Minor Version (UNSIGNED32)"""
        if self._minor_version is None:
            self._minor_version = self._u32(2)
        return self._minor_version

    @property
    def build(self) -> int:
        """OS Build (UNSIGNED32)"""
        if self._build is None:
            self._build = self._u32(3)
        return self._build

    @property
    def csd_version(self) -> str:
        """CSD Version (VISIBLE STRING)"""
        if self._csd_version is None:
            self._csd_version = self._string(4)
        return self._csd_version

    def info(self) -> OSInfo:
        """Return all OS information as a dataclass"""
        return OSInfo(
            major_version=self.major_version,
            minor_version=self.minor_version,
            build=self.build,
            csd_version=self.csd_version,
        )

    def refresh(self):
        """Force re-reading all OS values from IPC"""
        self._major_version = None
        self._minor_version = None
        self._build = None
        self._csd_version = None
