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
 """

import sys
import time
import asyncio

from telemetrix_rpi_pico_2w_serial_aio import telemetrix_rpi_pico_2w_serial_aio

"""
This is an example program for HC-SR04 type distance sensors.

"""


# some globals
TRIGGER_PIN = 4
ECHO_PIN = 5

# indices into callback data
TRIGGER = 1
DISTANCE_IN_CENTIMETERS = 2
TIME_STAMP = 3

MAX_TIME_TO_WAIT_FOR_REPORT = 3  # in seconds

# initialize to current time
last_report_received = time.time()


async def the_callback(data):
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[TIME_STAMP]))

    global last_report_received
    last_report_received = time.time()

    print(f'{date}\t Trigger Pin::\t{data[TRIGGER]}\t Distance(cm):\t'
          f'{data[DISTANCE_IN_CENTIMETERS]}')


async def get_distance(my_board):
    try:
        # instantiate HC-SR04 devices
        await my_board.set_pin_mode_sonar(TRIGGER_PIN, ECHO_PIN, the_callback)

        while True:
            try:
                # do nothing but sleep while the reports come in.
                await asyncio.sleep(1)
                current_time = time.time()
                if current_time - last_report_received > MAX_TIME_TO_WAIT_FOR_REPORT:
                    print("No response from HC-SR04")
                    await my_board.shutdown()
                    sys.exit(0)
            except KeyboardInterrupt:
                await my_board.shutdown()
                sys.exit(0)

    except KeyboardInterrupt:
        await my_board.shutdown()
        sys.exit(0)

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    board = telemetrix_rpi_pico_2w_serial_aio.TelemetrixRpiPico2WSerialAIO(loop=loop)
except KeyboardInterrupt:
    sys.exit()

try:
    # start the main function
    loop.run_until_complete(get_distance(board))
    loop.run_until_complete(board.reset_board())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
except RuntimeError:
    sys.exit(0)
