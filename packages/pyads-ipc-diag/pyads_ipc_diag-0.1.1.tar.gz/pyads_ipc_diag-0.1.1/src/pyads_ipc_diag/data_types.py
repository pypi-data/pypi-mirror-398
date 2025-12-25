"""
data_types.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 22.12.2025 11.39

"""
import pyads

# Aliases for PLC types, based on Device Manager documentation
UNSIGNED16 = pyads.PLCTYPE_UINT
UNSIGNED32 = pyads.PLCTYPE_UDINT
UNSIGNED64 = pyads.PLCTYPE_ULINT

SIGNED16   = pyads.PLCTYPE_INT
SIGNED32   = pyads.PLCTYPE_DINT
SIGNED64   = pyads.PLCTYPE_LINT

BOOL       = pyads.PLCTYPE_BOOL
BYTE       = pyads.PLCTYPE_BYTE
WORD       = pyads.PLCTYPE_WORD
DWORD      = pyads.PLCTYPE_DWORD

REAL32     = pyads.PLCTYPE_REAL
REAL64     = pyads.PLCTYPE_LREAL

VISIBLE_STRING = pyads.PLCTYPE_STRING