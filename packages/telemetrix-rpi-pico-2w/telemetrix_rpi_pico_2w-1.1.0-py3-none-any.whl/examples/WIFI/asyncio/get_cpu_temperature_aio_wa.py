"""
 Copyright (c) 2022-2025 Alan Yorinks All rights reserved.

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
import asyncio
import sys
import time

from telemetrix_rpi_pico_2w_wifi_aio import telemetrix_rpi_pico_2w_wifi_aio

"""
Monitor the Pico internal temperature sensor and return the temperature
in celsius in the callback.
"""

# Callback data indices
CB_REPORT_TYPE = 0
CB_TEMP = 1
CB_TIME = 2


async def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the differential is exceeded
    :param data: [report_type, temperature, timestamp]
    """
    print(f'raw data = {data}')
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))

    print(f'CPU Temperature: {data[CB_TEMP ]} Date: {date}')


async def get_cpu_temp(my_board):
    """
     This function will request cpu temperature reports
     """
    # set the pin mode
    await my_board.get_cpu_temperature(threshold=.01, polling_interval=3000,
                              callback=the_callback)

    print('Enter Control-C to quit.')
    try:

        while True:
            await asyncio.sleep(.1)
    except KeyboardInterrupt:
        await my_board.shutdown()
        sys.exit(0)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

the_board = telemetrix_rpi_pico_2w_wifi_aio.TelemetrixRpiPico2WiFiAio(
    ip_address='192.168.2.212', loop=loop)

try:
    # start the main function
    loop.run_until_complete(get_cpu_temp(the_board))
    # time.sleep(3)
    loop.run_until_complete(board.shutdown())

except KeyboardInterrupt:
    loop.run_until_complete(the_board.shutdown())
    sys.exit(0)
