"""
memory.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 23.12.2025 9.32

"""
from dataclasses import dataclass
from typing import Optional

from .mdp_service import MDPService
from ..areas import CONFIG_AREA

@dataclass
class MemoryInfo:
    program_allocated_u32: int
    program_available_u32: int

    storage_allocated_u32: Optional[int]
    storage_available_u32: Optional[int]
    memory_division_u32: Optional[int]

    program_allocated_u64: Optional[int]
    program_available_u64: Optional[int]

class Memory(MDPService):
    MODULE = CONFIG_AREA.MEMORY

    def __init__(self, ipc):
        self.ipc = ipc
        self._program_allocated_u32 = None
        self._program_available_u32 = None
        self._storage_allocated_u32 = None
        self._storage_available_u32 = None
        self._memory_division_u32 = None
        self._program_allocated_u64 = None
        self._program_available_u64 = None

    # --- always available (per your table) ---

    @property
    def program_allocated_u32(self) -> int:
        """Program Memory Allocated (UNSIGNED32)"""
        if self._program_allocated_u32 is None:
            self._program_allocated_u32 = self._u32(1)
        return self._program_allocated_u32

    @property
    def program_available_u32(self) -> int:
        """Program Memory Available (UNSIGNED32)"""
        if self._program_available_u32 is None:
            self._program_available_u32 = self._u32(2)
        return self._program_available_u32

    # --- Windows CE only (may not exist on many targets) ---

    @property
    def storage_allocated_u32(self):
        """Storage Memory Allocated (UNSIGNED32) - only for Windows CE"""
        if self._storage_allocated_u32 is None:
            self._storage_allocated_u32 = self._u32(3)
        return self._storage_allocated_u32

    @property
    def storage_available_u32(self):
        """Storage Memory Available (UNSIGNED32) - only for Windows CE"""
        if self._storage_available_u32 is None:
            self._storage_available_u32 = self._u32(4)
        return self._storage_available_u32

    @property
    def memory_division_u32(self):
        """Memory Division (UNSIGNED32) - only for Windows CE (read-write)"""
        if self._memory_division_u32 is None:
            self._memory_division_u32 = self._u32(5)
        return self._memory_division_u32

    # --- MDP v1.7+ (64-bit counters) ---

    @property
    def program_allocated_u64(self):
        """Program Memory Allocated (UNSIGNED64) - MDP v1.7+"""
        if self._program_allocated_u64 is None:
            self._program_allocated_u64 = self._u64(6)
        return self._program_allocated_u64

    @property
    def program_available_u64(self):
        """Program Memory Available (UNSIGNED64) - MDP v1.7+"""
        if self._program_available_u64 is None:
            self._program_available_u64 = self._u64(7)
        return self._program_available_u64

    def info(self) -> MemoryInfo:
        """Return all memory information as a dataclass"""
        return MemoryInfo(
            program_allocated_u32=self.program_allocated_u32,
            program_available_u32=self.program_available_u32,
            storage_allocated_u32=self.storage_allocated_u32,
            storage_available_u32=self.storage_available_u32,
            memory_division_u32=self.memory_division_u32,
            program_allocated_u64=self.program_allocated_u64,
            program_available_u64=self.program_available_u64,
        )

    def refresh(self):
        """Force re-reading all memory values from IPC"""
        self._program_allocated_u32 = None
        self._program_available_u32 = None
        self._storage_allocated_u32 = None
        self._storage_available_u32 = None
        self._memory_division_u32 = None
        self._program_allocated_u64 = None
        self._program_available_u64 = None
