"""
cpu.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 23.12.2025 9.31

"""
from dataclasses import dataclass

from .mdp_service import MDPService
from ..areas import CONFIG_AREA

@dataclass
class CPUInfo:
    frequency: int
    usage: int
    temperature: int

class CPU(MDPService):
    MODULE = CONFIG_AREA.CPU

    def __init__(self, ipc):
        self.ipc = ipc
        self._frequency = None
        self._usage = None
        self._temperature = None

    @property
    def frequency(self) -> int:
        """CPU frequency (UNSIGNED32)"""
        if self._frequency is None:
            self._frequency = self._u32(1)
        return self._frequency

    @property
    def usage(self) -> int:
        """CPU usage in percent (UNSIGNED16)"""
        if self._usage is None:
            self._usage = self._u16(2)
        return self._usage

    @property
    def temperature(self) -> int:
        """CPU temperature (SIGNED16)"""
        if self._temperature is None:
            self._temperature = self._s16(3)
        return self._temperature

    def info(self) -> CPUInfo:
        """Return all CPU information as a dataclass"""
        return CPUInfo(
            frequency=self.frequency,
            usage=self.usage,
            temperature=self.temperature,
        )

    def refresh(self):
        """Force re-reading all CPU values from IPC"""
        self._frequency = None
        self._usage = None
        self._temperature = None
