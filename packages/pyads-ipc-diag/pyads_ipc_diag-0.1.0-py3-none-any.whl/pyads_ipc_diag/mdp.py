"""
mdp.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 22.12.2025 11.40

"""
from typing import Union

import pyads

from .areas import DEVICE_AREA
from .constants import COE_ADDRESS
from .data_types import UNSIGNED16, UNSIGNED32


class MDP:
    """ MDP class to read the IPC diagnostics data via ADS / pyads"""
    mdp = dict()

    def __init__(self, ams_net_id):
        """ Initialize the class
        :param ams_net_id: ams net id"""
        self._plc = pyads.Connection(ams_net_id, 10000)

    def open(self):
        """ Open ADS conncetion to the device"""
        self._plc.open()
        # Update module information automatically
        if self._plc.is_open:
            self.update_modules()

    def close(self):
        """ Close ADS connection to the device"""
        self._plc.close()

    def __enter__(self):
        """ Open ADS connection to the device"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Close ADS connection to the device"""
        self.close()

    def _read(self, offset, plc_type):
        """ Read data from device trough pyads
         :param offset: start address of data
         :plc_type: pyads type"""
        try:
            if self._plc.is_open:
                return self._plc.read(
                    COE_ADDRESS,
                    offset,
                    plc_type
                )
        except Exception as e:
            return None

    def _get_module_count(self):
        """ Get module count """
        return self._read(DEVICE_AREA.MODULE_ID_LIST << 16, UNSIGNED16)

    def update_modules(self):
        """ Update all available modules"""
        module_count = self._get_module_count()
        for i in range(1, module_count + 1):
            mdp_module = self._read((DEVICE_AREA.MODULE_ID_LIST << 16) + i, UNSIGNED32)
            mdp_type = (mdp_module & 0xFFFF0000) >> 16
            if mdp_type not in self.mdp:
                self.mdp.update({
                    mdp_type:
                    mdp_module
                })

    def read(self, module, table_base, subindex, plc_type) -> Union[int, str]:
        """ Read the actual values of the table and subindex
        :param module: module id
        :param table_base: table base
        :param subindex: subindex
        :param plc_type: pyads type"""
        if module not in self.mdp:
            try:
                mpd_addr = (module << 16) | subindex
                return self._read(mpd_addr, plc_type)
            except Exception as e:
                return None

        mpd_id = self.mdp[module] & 0x0000FFFF
        mpd_addr = (mpd_id << 20) | (table_base << 16) | subindex
        return self._read(mpd_addr, plc_type)
