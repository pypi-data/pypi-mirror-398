# Beckhoff IPC Diagnostics

**pyads-ipc-diag** is a Python library for reading IPC Diagnostics information from Beckhoff IPCs and EPCs.

IPC Diagnostics have been available on Beckhoff IPC/EPC devices for years. The data can be accessed via ADS, OPC UA, or C#.  
This library focuses on **ADS access using Python**.

For detailed documentation, see the Beckhoff Information System:  
https://infosys.beckhoff.com/content/1033/devicemanager/index.html?id=7887654213086576625

The library uses [**pyads**](https://github.com/stlehmann/pyads) for ADS communication. pyads is supported on multiple platforms, including Windows, Linux, and FreeBSD.

**This project is still under development and may be unstable.**

---

## Installation

At the moment, the package is not yet published on PyPI.  
You can install it directly from GitHub.

### Install using pip (recommended)

```bash
pip install git+https://github.com/dewabe/pyads-ipc-diag.git
```

### Clone from source

```bash
git clone https://github.com/dewabe/pyads-ipc-diag.git
cd pyads-ipc-diag
pip install -e .
```

---

## Features

- Read all IPC Diagnostics data via ADS
- Read TwinCAT, CPU, and Mainboard information
- Designed with a clean, extensible API

---

## Basic usage

```python
import pyads
from pyads_ipc_diag import MDP, CPU, CONFIG_AREA

with MDP("10.10.10.11.1.1") as ipc:
    cpu = CPU(ipc)
    print(cpu.info())
    # CPU_Info(
    #   frequency=1917,
    #   usage=3,
    #   temperature=43
    #   )
    mac_address = ipc.read(CONFIG_AREA.NIC, 0x8001, 1, pyads.PLCTYPE_STRING)
    print(mac_address) # nn:nn:nn:nn:nn:nn
```

---

## Requirements

- Python 3.9+
- pyads
- Beckhoff IPC/EPC with IPC Diagnostics available


## To Do

* All "High level MDP Service Classes", such a Memory, NIC, UPS etc.
* Possibility to write data (i.e. change IP address)
* Optimize code
* Write tests
* Write documentation
