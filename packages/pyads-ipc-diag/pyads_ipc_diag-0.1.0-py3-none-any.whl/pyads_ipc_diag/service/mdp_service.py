"""
mdp_service.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 22.12.2025 13.51

"""
from typing import Union
from pyads_ipc_diag import data_types as dtypes


class MDPService:
    """High level class for reading MDP data """
    TABLE_BASE = 0x8001 # Usually device properties

    def _read(self, subindex, var_type) -> Union[int, str, None] :
        return self.ipc.read(self.MODULE, self.TABLE_BASE, subindex, var_type)

    def _u16(self, subindex: int) -> int:
        return self._read(subindex, dtypes.UNSIGNED16)

    def _s16(self, subindex: int) -> int:
        return self._read(subindex, dtypes.SIGNED16)

    def _u32(self, subindex: int) -> int:
        return self._read(subindex, dtypes.UNSIGNED32)

    def _s32(self, subindex: int) -> int:
        return self._read(subindex, dtypes.SIGNED32)

    def _u64(self, subindex: int) -> int:
        return self._read(subindex, dtypes.UNSIGNED64)

    def _string(self, subindex: int) -> str:
        return self._read(subindex, dtypes.VISIBLE_STRING)

    def _bool(self, subindex: int) -> bool:
        return self._read(subindex, dtypes.BOOL)