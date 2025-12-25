##########################################################################################
# Copyright (c) 2024 Nordic Semiconductor
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
##########################################################################################

import threading
import serial
import time
import queue
import os
import sys
import re
import psutil

sys.path.append(os.getcwd())
from ciatools.logger import get_logger
from typing import Union

DEFAULT_WAIT_FOR_STR_TIMEOUT = 60 * 10

logger = get_logger()


class UartLogTimeout(Exception):
    pass


class Uart:
    def __init__(
        self,
        uart: str,
        baudrate: int = 115200,
        name: str = "",
        serial_timeout: int = 1,
    ) -> None:
        """Initialize a UART connection to the specified device path."""
        check_uart_usage(uart)
        self.baudrate = baudrate
        self.uart = uart
        self.name = name
        self.serial_timeout = serial_timeout
        self.log = ""
        self.whole_log = ""
        self._evt = threading.Event()
        self._writeq = queue.Queue()
        self._t = threading.Thread(target=self._uart)
        self._t.start()

    @classmethod
    def from_serial(
        cls,
        serial_number: Union[str, int],
        baudrate: int = 115200,
        name: str = "",
        serial_timeout: int = 1,
    ) -> "Uart":
        """
        Create a Uart instance by searching for a device with the given serial number.
        
        Args:
            serial_number: The serial number to search for (can be str or int)
            baudrate: Baud rate for the serial connection
            name: Optional name for logging
            serial_timeout: Serial read timeout in seconds
            
        Returns:
            A Uart instance connected to the device with the matching serial number
            
        Raises:
            RuntimeError: If no device containing the serial number is found
        """
        serial_str = str(serial_number)
        logger.info(f"Searching for device with serial number '{serial_str}'...")
        uart_path = find_uart_by_serial(serial_str)
        logger.info(f"Found device: {uart_path}")
        return cls(
            uart=uart_path,
            baudrate=baudrate,
            name=name,
            serial_timeout=serial_timeout,
        )

    def write(self, data: bytes) -> None:
        """Write data to the UART device."""
        chunked = False
        self._writeq.put((data, chunked))

    def write_chunked(self, data: bytes) -> None:
        """Write data to the UART device in small chunks to avoid buffer overflows."""
        chunked = True
        self._writeq.put((data, chunked))

    def at_cmd_write(self, cmd: str) -> None:
        """Send an AT command and wait for 'OK' response."""
        start = time.time()
        log_index = len(self.log)
        count = 0
        while not self._evt.is_set():
            if count % 10 == 0:
                self.write(cmd.encode("utf-8") + b"\r\n")
                log_index = len(self.log)
            count += 1
            time.sleep(0.2)
            if "OK" in self.log[log_index:]:
                break
            if start + 10 < time.time():
                raise UartLogTimeout(f'AT command "{cmd}" timed out')

    def xfactoryreset(self) -> None:
        """Perform a factory reset via AT commands."""
        try:
            self.at_cmd_write("at AT")
            self.write("att_network disconnect\r\n")
            self.at_cmd_write("at AT+CFUN=4")
            self.at_cmd_write("at AT%XFACTORYRESET=0")
        except UartLogTimeout:
            logger.error("AT FACTORYRESET failed, continuing")

    def _uart(self) -> None:
        """Internal thread function that handles UART read/write operations."""
        data = None
        s = serial.Serial(
            self.uart, baudrate=self.baudrate, timeout=self.serial_timeout
        )

        if s.in_waiting:
            logger.warning(
                f"Uart {self.uart} has {s.in_waiting} bytes of unread data, resetting input buffer"
            )
            s.reset_input_buffer()

        if s.out_waiting:
            logger.warning(
                f"Uart {self.uart} has {s.out_waiting} bytes of unwritten data, resetting output buffer"
            )
            s.reset_output_buffer()

        line = ""
        while not self._evt.is_set():
            if not self._writeq.empty():
                try:
                    write_data, chunked = self._writeq.get_nowait()
                    if isinstance(write_data, str):
                        write_data = write_data.encode("utf-8")
                    if chunked:
                        # Write in chunks to avoid buffer overflows
                        chunk_size = 16
                        chunks = [
                            write_data[i : i + chunk_size]
                            for i in range(0, len(write_data), chunk_size)
                        ]
                        for chunk in chunks:
                            s.write(chunk)
                            time.sleep(0.1)
                    else:
                        s.write(write_data)
                    logger.debug(f"UART write {self.name}: {write_data}")
                except queue.Empty:
                    pass

            try:
                read_byte = s.read(1)
                data = read_byte.decode("utf-8")
            except UnicodeDecodeError:
                logger.debug(f"{self.name}: Got unexpected UART value")
                logger.debug(f"{self.name}: Not decodeable data: {hex(ord(read_byte))}")
                continue
            except serial.serialutil.SerialException:
                logger.error(f"{self.name}: Caught SerialException, restarting")
                s.close()
                while True:
                    time.sleep(2)
                    if self._evt.is_set():
                        return
                    try:
                        s = serial.Serial(
                            self.uart,
                            baudrate=self.baudrate,
                            timeout=self.serial_timeout,
                        )
                    except FileNotFoundError:
                        logger.warning(f"{self.uart} not available, retrying")
                        continue
                    break
                continue
            if not data:
                continue

            line = line + data
            if data != "\n":
                continue
            # Full line received
            line = line.strip()
            logger.debug(f"{self.name}: {line}")
            self.log = self.log + "\n" + line
            self.whole_log = self.whole_log + "\n" + line
            line = ""
        s.close()

    def flush(self) -> None:
        """Clear the current log buffer."""
        self.log = ""

    def stop(self) -> None:
        """Stop the UART connection and terminate the read/write thread."""
        self._evt.set()
        self._t.join()

    def start(self) -> None:
        """Start the UART thread after it has been stopped."""
        self._evt = threading.Event()
        self._writeq = queue.Queue()
        self._t = threading.Thread(target=self._uart)
        self._t.start()


    def get_size(self) -> int:
        """Return the current size of the log buffer."""
        return len(self.log)

    def wait_for_str_ordered(
        self,
        msgs: list,
        error_msg: str = "",
        timeout: int = DEFAULT_WAIT_FOR_STR_TIMEOUT,
    ) -> None:
        """Wait for a list of strings to appear in the log in the specified order."""
        start_t = time.time()
        while True:
            missing = None
            pos = 0
            for msg in msgs:
                try:
                    pos = self.log.index(msg, pos)
                except ValueError:
                    missing = msg
                    break
                pos += 1
            else:
                break
            if start_t + timeout < time.time():
                raise AssertionError(
                    f"{missing if missing else msgs} missing in UART log in the expected order. {error_msg}"
                )
            if self._evt.is_set():
                raise RuntimeError(f"Uart thread stopped, log:\n{self.log}")
            time.sleep(1)

    def wait_for_str(
        self,
        msgs: Union[str, list],
        error_msg: str = "",
        timeout: int = DEFAULT_WAIT_FOR_STR_TIMEOUT,
        start_pos: int = 0,
    ) -> None:
        """Wait for one or more strings to appear in the log (order not required)."""
        start_t = time.time()
        msgs = msgs if isinstance(msgs, (list, tuple)) else [msgs]

        while True:
            missing_msgs = [x for x in msgs if x not in self.log[start_pos:]]
            if missing_msgs == []:
                return self.get_size()
            if start_t + timeout < time.time():
                raise AssertionError(
                    f"{missing_msgs} missing in UART log. {error_msg}\n"
                )
            if self._evt.is_set():
                raise RuntimeError(f"Uart thread stopped, log:\n{self.log}")
            time.sleep(1)

    def wait_for_str_re(
        self,
        pattern: str,
        error_msg: str = "",
        timeout: int = DEFAULT_WAIT_FOR_STR_TIMEOUT,
        start_pos: int = 0,
    ):
        """Wait for a regex pattern to match in the log and return the match."""
        start_t = time.time()
        regex = re.compile(pattern)

        while True:
            match = regex.search(self.log[start_pos:])
            if match:
                # Return the first group if groups exist, else the whole match
                return match.groups() if match.groups() else match.group(0)
            if start_t + timeout < time.time():
                raise AssertionError(
                    f"Pattern '{pattern}' not found in UART log. {error_msg}\n"
                )
            if self._evt.is_set():
                raise RuntimeError(f"Uart thread stopped, log:\n{self.log}")
            time.sleep(1)

    def extract_value(self, pattern: str, start_pos: int = 0):
        """Extract values from the log using a regex pattern without waiting."""
        pattern = re.compile(pattern)
        match = pattern.search(self.log[start_pos:])
        if match:
            return match.groups()
        return None

    def wait_for_str_with_retries(
        self,
        msgs: Union[str, list],
        max_retries: int = 2,
        timeout: int = DEFAULT_WAIT_FOR_STR_TIMEOUT,
        error_msg: str = "",
        reset_func=None,
    ) -> None:
        """Wait for strings with automatic retries and optional reset function."""
        retries = 0
        while retries <= max_retries:
            try:
                return self.wait_for_str(msgs, error_msg=error_msg, timeout=timeout)
            except AssertionError as e:
                retries += 1
                if retries <= max_retries:
                    logger.error(f"Waiting for string failed, e: {e}")
                    logger.info(f"Retrying... (attempt {retries}/{max_retries})")
                    if reset_func:
                        reset_func()
                else:
                    logger.error(
                        f"Failed waiting for {msgs} after {max_retries} retries"
                    )
                    raise


class UartBinary(Uart):
    def __init__(
        self,
        uart: str,
        serial_timeout: int = 5,
        baudrate: int = 1000000,
    ) -> None:
        """Initialize a binary UART connection for reading raw binary data."""
        self.data = b""
        super().__init__(
            uart=uart,
            baudrate=baudrate,
            serial_timeout=serial_timeout,
        )

    @classmethod
    def from_serial(
        cls,
        serial_number: Union[str, int],
        serial_timeout: int = 5,
        baudrate: int = 1000000,
    ) -> "UartBinary":
        """
        Create a UartBinary instance by searching for a device with the given serial number.
        
        Args:
            serial_number: The serial number to search for (can be str or int)
            serial_timeout: Serial read timeout in seconds
            baudrate: Baud rate for the serial connection
            
        Returns:
            A UartBinary instance connected to the device with the matching serial number
            
        Raises:
            RuntimeError: If no device containing the serial number is found
        """
        serial_str = str(serial_number)
        logger.info(f"Searching for device with serial number '{serial_str}'...")
        uart_path = find_uart_by_serial(serial_str)
        logger.info(f"Found device: {uart_path}")
        return cls(
            uart=uart_path,
            serial_timeout=serial_timeout,
            baudrate=baudrate,
        )

    def _uart(self) -> None:
        """Internal thread function that handles binary UART read operations."""
        s = serial.Serial(
            self.uart, baudrate=self.baudrate, timeout=self.serial_timeout
        )
        if s.in_waiting:
            logger.warning(
                f"Uart {self.uart} has {s.in_waiting} bytes of unread data, resetting input buffer"
            )
            s.reset_input_buffer()

        if s.out_waiting:
            logger.warning(
                f"Uart {self.uart} has {s.out_waiting} bytes of unwritten data, resetting output buffer"
            )
            s.reset_output_buffer()

        while not self._evt.is_set():
            try:
                data = s.read(8192)
            except serial.serialutil.SerialException:
                logger.error("Caught SerialException, restarting")
                s.close()
                time.sleep(1)
                s = serial.Serial(
                    self.uart, baudrate=self.baudrate, timeout=self.serial_timeout
                )
                continue
            if not data:
                continue
            self.data = self.data + data
        s.close()

    def flush(self) -> None:
        """Clear the binary data buffer."""
        self.data = b""

    def save_to_file(self, filename: str) -> None:
        """Save the accumulated binary data to a file."""
        if len(self.data) == 0:
            logger.warning("No trace data to save")
            return
        with open(filename, "wb") as f:
            f.write(self.data)

    def get_size(self) -> int:
        """Return the current size of the binary data buffer."""
        return len(self.data)


def wait_until_uart_available(name, timeout_seconds=60):
    """Wait for a UART device to become available by searching /dev/serial/by-id/."""
    base_path = "/dev/serial/by-id"
    while timeout_seconds > 0:
        try:
            serial_paths = [
                os.path.join(base_path, entry) for entry in os.listdir(base_path)
            ]
            for path in sorted(serial_paths):
                if name in path:
                    logger.info(f"UART found: {path}")
                    return path
        except (FileNotFoundError, PermissionError) as e:
            logger.info(f"Uart not available yet (error: {e}), retrying...")
        time.sleep(1)
        timeout_seconds -= 1
    logger.error(f"UART '{name}' not found within {timeout_seconds} seconds")
    return None


def find_uart_by_serial(serial_number: str) -> str:
    """
    Find a UART device by searching for the serial number in /dev/serial/by-id/.
    
    Args:
        serial_number: The serial number to search for
        
    Returns:
        The path to the device (symlink in /dev/serial/by-id/)
        
    Raises:
        RuntimeError: If no device containing the serial number is found
    """
    base_path = "/dev/serial/by-id"
    if not os.path.exists(base_path):
        raise RuntimeError(
            f"Cannot find UART device with serial '{serial_number}': "
            f"{base_path} does not exist"
        )
    
    matching_devices = [x for x in os.listdir(base_path) if serial_number in x]
    if not matching_devices:
        raise RuntimeError(
            f"No UART device found containing serial number '{serial_number}' in {base_path}"
        )
    return os.path.join(base_path, sorted(matching_devices)[0])


def check_uart_usage(uart):
    """Check if the UART device exists and is not already in use by another process."""
    if not os.path.exists(uart):
        raise RuntimeError(f"Uart {uart} does not exist!")

    # Resolve symlink to actual device path for comparison
    try:
        real_path = os.path.realpath(uart)
    except OSError:
        real_path = uart

    # Check all processes for open files matching the UART device
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                # Get all open files for this process
                open_files = proc.open_files()
                for file_info in open_files:
                    # Compare both the original path and resolved path
                    if file_info.path == uart or file_info.path == real_path:
                        raise RuntimeError(
                            f"Uart {uart} in use!\n"
                            f"Command: {proc.info['name']}, PID: {proc.info['pid']}, "
                            f"User: {proc.info['username']}"
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process may have terminated or we don't have permission
                continue
    except Exception as e:
        logger.error(f"Error checking UART usage: {e}")
