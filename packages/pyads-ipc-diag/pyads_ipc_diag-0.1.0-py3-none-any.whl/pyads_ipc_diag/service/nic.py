"""
nic.py

Project: pyads-ipc-diag
:author: Teemu Vartiainen
:license: MIT
:created on: 23.12.2025 11.35

"""
from dataclasses import dataclass

from .mdp_service import MDPService
from ..areas import CONFIG_AREA

@dataclass
class NICInfo:
    mac_address: str
    ipv4_address: str
    ipv4_netmask: str
    dhcp_enabled: bool
    ipv4_gateway: str
    ipv4_dns: str # Not available on Windows CE
    virtual_device_name: str # Ony for Windows
    ipv4_dns_servers_active: str # Only for TwinCAT/BSD and TC/RTOS

class NIC(MDPService):
    MODULE = CONFIG_AREA.NIC

    def __init__(self, ipc):
        self.ipc = ipc
        self._mac_address = None
        self._ipv4_address = None
        self._ipv4_netmask = None
        self._dhcp_enabled = None
        self._ipv4_gateway = None
        self._ipv4_dns = None
        self._virtual_device_name = None
        self._ipv4_dns_servers_active = None

    @property
    def mac_address(self) -> str:
        """MAC address (VISIBLE STRING)"""
        if self._mac_address is None:
            self._mac_address = self._string(1)
        return self._mac_address

    @property
    def ipv4_address(self) -> str:
        """IPv4 address (VISIBLE STRING)"""
        if self._ipv4_address is None:
            self._ipv4_address = self._string(2)
        return self._ipv4_address

    @property
    def ipv4_netmask(self) -> str:
        """IPv4 netmask (VISIBLE STRING)"""
        if self._ipv4_netmask is None:
            self._ipv4_netmask = self._string(3)
        return self._ipv4_netmask

    @property
    def dhcp_enabled(self) -> bool:
        """DHCP enabled (BOOL / UNSIGNED16 depending on device)"""
        if self._dhcp_enabled is None:
            self._dhcp_enabled = bool(self._bool(4))
        return self._dhcp_enabled

    @property
    def ipv4_gateway(self) -> str:
        """IPv4 gateway (VISIBLE STRING)"""
        if self._ipv4_gateway is None:
            self._ipv4_gateway = self._string(5)
        return self._ipv4_gateway

    @property
    def ipv4_dns(self) -> str:
        """Primary IPv4 DNS server (VISIBLE STRING)"""
        if self._ipv4_dns is None:
            self._ipv4_dns = self._string(6)
        return self._ipv4_dns

    @property
    def virtual_device_name(self) -> str:
        """Virtual device name (VISIBLE STRING)"""
        if self._virtual_device_name is None:
            self._virtual_device_name = self._string(7)
        return self._virtual_device_name

    @property
    def ipv4_dns_servers_active(self) -> int:
        """Number of active IPv4 DNS servers (UNSIGNED16)"""
        if self._ipv4_dns_servers_active is None:
            self._ipv4_dns_servers_active = self._string(8)
        return self._ipv4_dns_servers_active

    def refresh(self):
        """Force re-reading all NIC values from IPC"""
        self._mac_address = None
        self._ipv4_address = None
        self._ipv4_netmask = None
        self._dhcp_enabled = None
        self._ipv4_gateway = None
        self._ipv4_dns = None
        self._virtual_device_name = None
        self._ipv4_dns_servers_active = None


