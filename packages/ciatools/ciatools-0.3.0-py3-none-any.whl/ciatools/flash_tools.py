##########################################################################################
# Copyright (c) 2024 Nordic Semiconductor
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
##########################################################################################

import os
import subprocess
import json
from ciatools.logger import get_logger
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.flash.eraser import FlashEraser
from pyocd.commands.commands import ResetCommand

logger = get_logger()

SEGGER = os.getenv("SEGGER_SERIAL")


def reset_device(serial=SEGGER, reset_kind="RESET_SYSTEM"):
    logger.info(f"Resetting device, segger: {serial}")
    try:
        subprocess.run(
            [
                "nrfutil",
                "device",
                "reset",
                "--serial-number",
                serial,
                "--reset-kind",
                reset_kind,
                "--json"
            ],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        logger.error("An error occurred while resetting the device.")
        logger.error("Error output:")
        logger.error(e.stderr)
        raise


def flash_device(hexfile, serial=SEGGER, extra_args=[]):
    # hexfile (str): Full path to file (hex or zip) to be programmed
    if not isinstance(hexfile, str):
        raise ValueError("hexfile cannot be None")
    logger.info(f"Flashing device, segger: {serial}, firmware: {hexfile}")
    try:
        subprocess.run(
            [
                "nrfutil",
                "device",
                "program",
                *extra_args,
                "--firmware",
                hexfile,
                "--serial-number",
                serial,
            ],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        logger.error("An error occurred while flashing the device.")
        logger.error("Error output:")
        logger.error(e.stderr)
        raise


def recover_device(serial=SEGGER, core="Application"):
    logger.info(f"Recovering device, segger: {serial}")
    try:
        subprocess.run(
            ["nrfutil", "device", "recover", "--serial-number", serial, "--core", core],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        logger.error("An error occurred while recovering the device.")
        logger.error("Error output:")
        logger.error(e.stderr)
        raise


def pyocd_flash_device(serial, hexfile, target_type="nrf91"):
    logger.debug(f"Flashing device, serial: {serial}, hexfile: {hexfile}")
    with ConnectHelper.session_with_chosen_probe(
        unique_id=serial, target_override=target_type
    ) as session:
        programmer = FileProgrammer(session)
        programmer.program(hexfile)


def pyocd_erase_device(serial, target_type="nrf91"):
    logger.debug(f"Erasing device, serial: {serial}")
    with ConnectHelper.session_with_chosen_probe(
        unique_id=serial, target_override=target_type
    ) as session:
        eraser = FlashEraser(session, FlashEraser.Mode.MASS)
        eraser.erase()


def pyocd_reset_device(serial, target_type="nrf91"):
    logger.debug(f"Resetting device, serial: {serial}")
    with ConnectHelper.session_with_chosen_probe(
        unique_id=serial, target_override=target_type, type="hardware"
    ) as session:
        ResetCommand(session)
