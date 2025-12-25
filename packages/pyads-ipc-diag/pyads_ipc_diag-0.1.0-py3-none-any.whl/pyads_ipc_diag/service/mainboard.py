"""
mainboard.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 23.12.2025 9.32

"""
from dataclasses import dataclass

from .mdp_service import MDPService
from ..areas import CONFIG_AREA

@dataclass
class MainboardInfo:
    mainboard_type: str
    serial_number: str
    production_date: str

    boot_count: int
    operating_time_minutes: int

    min_board_temperature: int
    max_board_temperature: int

    min_input_voltage: int
    max_input_voltage: int

    board_temperature: int

class Mainboard(MDPService):
    MODULE = CONFIG_AREA.MAINBOARD

    def __init__(self, ipc):
        self.ipc = ipc
        self._mainboard_type = None
        self._serial_number = None
        self._production_date = None
        self._boot_count = None
        self._operating_time_minutes = None
        self._min_board_temperature = None
        self._max_board_temperature = None
        self._min_input_voltage = None
        self._max_input_voltage = None
        self._board_temperature = None

    @property
    def mainboard_type(self) -> str:
        """Mainboard type (VISIBLE STRING)"""
        if self._mainboard_type is None:
            self._mainboard_type = self._string(1)
        return self._mainboard_type

    @property
    def serial_number(self) -> str:
        """Serial number (VISIBLE STRING)"""
        if self._serial_number is None:
            self._serial_number = self._string(2)
        return self._serial_number

    @property
    def production_date(self) -> str:
        """Production date (VISIBLE STRING)"""
        if self._production_date is None:
            self._production_date = self._string(3)
        return self._production_date

    @property
    def boot_count(self) -> int:
        """Boot count (UNSIGNED32)"""
        if self._boot_count is None:
            self._boot_count = self._u32(4)
        return self._boot_count

    @property
    def operating_time_minutes(self) -> int:
        """Operating time in minutes (UNSIGNED32)"""
        if self._operating_time_minutes is None:
            self._operating_time_minutes = self._u32(5)
        return self._operating_time_minutes

    @property
    def min_board_temperature(self) -> int:
        """Minimum board temperature (SIGNED32, °C)"""
        if self._min_board_temperature is None:
            self._min_board_temperature = self._s32(6)
        return self._min_board_temperature

    @property
    def max_board_temperature(self) -> int:
        """Maximum board temperature (SIGNED32, °C)"""
        if self._max_board_temperature is None:
            self._max_board_temperature = self._s32(7)
        return self._max_board_temperature

    @property
    def min_input_voltage(self) -> int:
        """Minimum input voltage (SIGNED32, mV)"""
        if self._min_input_voltage is None:
            self._min_input_voltage = self._s32(8)
        return self._min_input_voltage

    @property
    def max_input_voltage(self) -> int:
        """Maximum input voltage (SIGNED32, mV)"""
        if self._max_input_voltage is None:
            self._max_input_voltage = self._s32(9)
        return self._max_input_voltage

    @property
    def board_temperature(self) -> int:
        """Current board temperature (SIGNED16, °C)"""
        if self._board_temperature is None:
            self._board_temperature = self._s16(10)
        return self._board_temperature

    def info(self) -> MainboardInfo:
        """Return all mainboard information as a dataclass"""
        return MainboardInfo(
            mainboard_type=self.mainboard_type,
            serial_number=self.serial_number,
            production_date=self.production_date,
            boot_count=self.boot_count,
            operating_time_minutes=self.operating_time_minutes,
            min_board_temperature=self.min_board_temperature,
            max_board_temperature=self.max_board_temperature,
            min_input_voltage=self.min_input_voltage,
            max_input_voltage=self.max_input_voltage,
            board_temperature=self.board_temperature,
        )

    def refresh(self):
        """Force re-reading all mainboard values from IPC"""
        self._mainboard_type = None
        self._serial_number = None
        self._production_date = None
        self._boot_count = None
        self._operating_time_minutes = None
        self._min_board_temperature = None
        self._max_board_temperature = None
        self._min_input_voltage = None
        self._max_input_voltage = None
        self._board_temperature = None
