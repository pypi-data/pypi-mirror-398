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

import sys
import time

from telemetrix_rpi_pico_2w_wifi import telemetrix_rpi_pico_2w_wifi

"""
Monitor a potentiometer connected to ADC1 and the internal reference voltage
"""

ADC = 1  # temperature sensor ADC

# Callback data indices
CB_PIN_MODE = 0
CB_PIN = 1
CB_VALUE = 2
CB_TIME = 3


def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the differential is exceeded
    :param data: [report_type, ADC#, current reported value, timestamp]
    """
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))
    # value =
    print(f'ADC Report Type: {data[CB_PIN_MODE]} ADC: {data[CB_PIN]} '
          f'Value: {data[CB_VALUE]} Time Stamp: {date}')


def analog_in(my_board, adc):
    """
     This function establishes the pin as an
     analog input. Any changes on this pin will
     be reported through the call back function.

     :param my_board: a pymata4 instance
     :param adc: ADC number
     """

    # set the pin mode
    my_board.set_pin_mode_analog_input(adc, differential=10, callback=the_callback)

    print('Enter Control-C to quit.')
    try:
        time.sleep(5)
        print('Disabling reporting for 3 seconds.')
        my_board.disable_analog_reporting(adc)
        time.sleep(3)
        print('Re-enabling reporting.')
        my_board.enable_analog_reporting(adc)
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        board.shutdown()
        sys.exit(0)


board = telemetrix_rpi_pico_2w_wifi.TelemetrixRpiPico2WiFi(ip_address='192.168.2.212')
try:
    analog_in(board, ADC)
except KeyboardInterrupt:
    board.shutdown()
    sys.exit(0)
