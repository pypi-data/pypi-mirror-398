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

from telemetrix_rpi_pico_2w_serial import telemetrix_rpi_pico_2w_serial

"""
Run a motor using runSpeedToPosition
"""

EXIT_FLAG = 0
# Create a Telemetrix instance.
board = telemetrix_rpi_pico_2w_serial.TelemetrixRpiPico2wSerial()


def the_callback(data):
    global EXIT_FLAG
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[2]))
    print(f'Motor {data[1]} runSpeedToPosition motion completed at: {date}.')
    EXIT_FLAG = 1


# create an accelstepper instance for a TB6600 motor driver
motor = board.set_pin_mode_stepper(interface=1, pin1=0, pin2=1)

# set the max speed and target position
board.stepper_set_max_speed(motor, 800)
board.stepper_move_to(motor, 2000)

# set the motor speed
board.stepper_set_speed(motor, 400)

print('Running speed to position...')
# run the motor
board.stepper_run_speed_to_position(motor, completion_callback=the_callback)


# keep application running
while EXIT_FLAG == 0:
    try:
        time.sleep(.1)
    except KeyboardInterrupt:
        board.shutdown()
        sys.exit(0)

board.shutdown()
sys.exit(0)
