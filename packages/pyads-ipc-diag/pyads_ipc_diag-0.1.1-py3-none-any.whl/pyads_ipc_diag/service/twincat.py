"""
twincat.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 23.12.2025 9.30

"""
from dataclasses import dataclass

from .mdp_service import MDPService
from ..areas import CONFIG_AREA


@dataclass
class TwinCATInfo:
    major: int
    minor: int
    build: int
    ams_net_id: str
    reg_level: int
    status: int
    run_as_device: int
    show_target_visu: int
    log_file_size: int
    log_file_path: str
    system_id: str
    revision: int
    seconds_since_status_change: int

class TwinCAT(MDPService):
    MODULE = CONFIG_AREA.TWINCAT
    TABLE_BASE = 0x8001

    def __init__(self, ipc):
        self.ipc = ipc
        self._major = None
        self._minor = None
        self._build = None
        self._ams_net_id = None
        self._reg_level = None
        self._status = None
        self._run_as_device = None
        self._show_target_visu = None
        self._log_file_size = None
        self._log_file_path = None
        self._system_id = None
        self._revision = None
        self._seconds_since_status_change = None

    @property
    def major(self) -> int:
        """Major Version (UNSIGNED16)"""
        if self._major is None:
            self._major = self._u16(1)
        return self._major

    @property
    def minor(self) -> int:
        """Minor Version (UNSIGNED16)"""
        if self._minor is None:
            self._minor = self._u16(2)
        return self._minor

    @property
    def build(self) -> int:
        """Build (UNSIGNED16)"""
        if self._build is None:
            self._build = self._u16(3)
        return self._build

    @property
    def ams_net_id(self) -> str:
        """Ams Net ID (VISIBLE STRING)"""
        if self._ams_net_id is None:
            self._ams_net_id = self._string(4)
        return self._ams_net_id

    @property
    def reg_level(self) -> int:
        """Reg Level (UNSIGNED32) - only for TwinCAT 2"""
        if self._reg_level is None:
            self._reg_level = self._u32(5)
        return self._reg_level

    @property
    def status(self) -> int:
        """TwinCAT Status (UNSIGNED16)"""
        if self._status is None:
            self._status = self._u16(6)
        return self._status

    @property
    def run_as_device(self) -> int:
        """RunAsDevice (UNSIGNED16) - only for Windows CE"""
        if self._run_as_device is None:
            self._run_as_device = self._u16(7)
        return self._run_as_device

    @property
    def show_target_visu(self) -> int:
        """ShowTargetVisu (UNSIGNED16) - only for Windows CE"""
        if self._show_target_visu is None:
            self._show_target_visu = self._u16(8)
        return self._show_target_visu

    @property
    def log_file_size(self) -> int:
        """Log File size (UNSIGNED32) - only for Windows CE"""
        if self._log_file_size is None:
            self._log_file_size = self._u32(9)
        return self._log_file_size

    @property
    def log_file_path(self) -> str:
        """Log File Path (VISIBLE STRING) - only for Windows CE"""
        if self._log_file_path is None:
            self._log_file_path = self._string(10)
        return self._log_file_path

    @property
    def system_id(self) -> str:
        """TwinCAT System ID (VISIBLE STRING) - MDP v1.6+"""
        if self._system_id is None:
            self._system_id = self._string(11)
        return self._system_id

    @property
    def revision(self) -> int:
        """TwinCAT Revision (UNSIGNED16)"""
        if self._revision is None:
            self._revision = self._u16(12)
        return self._revision

    @property
    def seconds_since_status_change(self) -> int:
        """Seconds since last TwinCAT status change (UNSIGNED64)"""
        if self._seconds_since_status_change is None:
            self._seconds_since_status_change = self._u64(13)
        return self._seconds_since_status_change

    def info(self) -> TwinCATInfo:
        """Return all TwinCAT information as a dataclass"""
        return TwinCATInfo(
            major=self.major,
            minor=self.minor,
            build=self.build,
            ams_net_id=self.ams_net_id,
            reg_level=self.reg_level,
            status=self.status,
            run_as_device=self.run_as_device,
            show_target_visu=self.show_target_visu,
            log_file_size=self.log_file_size,
            log_file_path=self.log_file_path,
            system_id=self.system_id,
            revision=self.revision,
            seconds_since_status_change=self.seconds_since_status_change,
        )

    def version(self):
        """Convenience: return (major, minor, build)"""
        return self.major, self.minor, self.build

    def refresh(self):
        """Force re-reading all TwinCAT values from IPC"""
        self._major = None
        self._minor = None
        self._build = None
        self._ams_net_id = None
        self._reg_level = None
        self._status = None
        self._run_as_device = None
        self._show_target_visu = None
        self._log_file_size = None
        self._log_file_path = None
        self._system_id = None
        self._revision = None
        self._seconds_since_status_change = None
