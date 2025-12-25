# CIATools

Utilities for UART communication and device flashing.

## Features

- **UART**: Serial communication with support for device lookup by serial number
- **Flash Tools**: Device programming utilities
- **Logger**: Logging utilities

## Quick Start

```python
from ciatools import Uart

# Direct device path
uart = Uart("/dev/ttyACM0")

# Or find by serial number
uart = Uart.from_serial(12345)
```
