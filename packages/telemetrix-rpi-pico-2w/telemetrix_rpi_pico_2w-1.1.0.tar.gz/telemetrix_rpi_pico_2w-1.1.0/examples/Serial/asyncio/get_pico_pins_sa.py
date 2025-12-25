"""
 Copyright (c) 2021-2025 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,f
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 DHT support courtesy of Martyn Wheeler
 Based on the DHTNew library - https://github.com/RobTillaart/DHTNew
"""

import asyncio
import sys

from telemetrix_rpi_pico_2w_serial_aio import telemetrix_rpi_pico_2w_serial_aio


async def dummy_callback(data):
    pass


async def get_pin_report(the_board):
    # set some pins to different modes
    await the_board.set_pin_mode_digital_output(4)
    await the_board.set_pin_mode_digital_input(6, callback=dummy_callback)
    await the_board.set_pin_mode_analog_input(1, callback=dummy_callback)
    await the_board.set_pin_mode_digital_input_pullup(9, callback=dummy_callback)
    await the_board.set_pin_mode_neopixel(14)
    await the_board.set_pin_mode_i2c(0, 4, 5)

    print(await the_board.get_pico_pins())

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate pymata_express
try:
    board = telemetrix_rpi_pico_2w_serial_aio.TelemetrixRpiPico2WSerialAIO(loop=loop)
except (KeyboardInterrupt, RuntimeError):
    # loop.run_until_complete(board.reset_board())
    sys.exit()

try:
    # start the main function
    loop.run_until_complete(get_pin_report(board))
    loop.run_until_complete(board.reset_board())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
except RuntimeError:
    sys.exit(0)
