"""
 Copyright (c) 2021-2025 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import asyncio
import sys
from telemetrix_rpi_pico_2w_serial_aio import telemetrix_rpi_pico_2w_serial_aio

"""
Demo using an 8 LED NeoPixel strip
"""


"""
Demo using an 8 LED NeoPixel strip
"""


async def neopixel_demo(my_board):
    """
    Run
    :param my_board: Pico board instance
    """

    # enable neopixel support on the Pico pin 0
    await my_board.set_pin_mode_neopixel(pin_number=0)

    # set some values and the show them
    await my_board.neo_pixel_set_value(5, 255, 0, 0)
    await my_board.neo_pixel_set_value(1, 0, 64, 0)
    await my_board.neo_pixel_set_value(7, 0, 0, 64)
    await my_board.neopixel_show()

    await asyncio.sleep(1)

    # clear the NeoPixels
    await my_board.neopixel_clear()

    await asyncio.sleep(1)

    # fill the NeoPixels
    await my_board.neopixel_fill(50, 0, 120)

    await asyncio.sleep(1)

    # set pixel value and update immediately
    await my_board.neo_pixel_set_value(3, 0, 65, 64, True)
    await asyncio.sleep(1)

    await my_board.neopixel_clear()
    # pixel sequence
    for pixel in range(8):
        await my_board.neo_pixel_set_value(pixel, 0, 0, 64, True)
        await asyncio.sleep(.1)
        await my_board.neopixel_clear()
        await asyncio.sleep(.01)


# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

board = telemetrix_rpi_pico_2w_serial_aio.TelemetrixRpiPico2WSerialAIO(loop=loop)

# start the main function
try:
    loop.run_until_complete(neopixel_demo(board))
    loop.run_until_complete(board.neopixel_clear())
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.neopixel_clear())
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
except RuntimeError:
    sys.exit(0)

