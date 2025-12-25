"""
__init__.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 22.12.2025 8.50

"""
from .areas import CONFIG_AREA
from .mdp import MDP
from .service import *

__all__ = [
    'CONFIG_AREA',
    'MDP',
    'TwinCAT',
    'CPU',
    'Mainboard',
    'Memory',
    'Fan',
    'NIC',
    'OS',
]
