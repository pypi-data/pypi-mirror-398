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
Run a motor continuously without acceleration


Motor used to test is a NEMA-17 size - 200 steps/rev, 12V 350mA.
And the driver is a TB6600 4A 9-42V Nema 17 Stepper Motor Driver.

The driver was connected as follows:
VCC 12 VDC
GND Power supply ground
ENA- Not connected
ENA+ Not connected
DIR- GND
DIR+ GPIO Pin 1
PUL- GND
PUL+ GPIO Pin 0 
A-, A+ Coil 1 stepper motor
B-, B+ Coil 2 stepper motor

"""


# GPIO Pins
PULSE_PIN = 0
DIRECTION_PIN = 1

# flag to keep track of the number of times the callback
# was called. When == 2, exit program


async def the_callback(data):
    print('This should never be called')
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[2]))
    print(f'Run motor {data[1]} completed motion at: {date}.')


async def step_continuous(board):
    # create an accelstepper instance for a TB6600 motor driver
    motor = await board.set_pin_mode_stepper(interface=1, pin1=0, pin2=1)

    # if you are using a 28BYJ-48 Stepper Motor with ULN2003
    # comment out the line above and uncomment out the line below.
    # motor = board.set_pin_mode_stepper(interface=8, pin1=8, pin2=10, pin3=9, pin4=11)

    # set the max speed and speed
    await board.stepper_set_max_speed(motor, 900)
    await board.stepper_set_speed(motor, 500)

    # run the motor
    await board.stepper_run_speed(motor)

    # keep application running
    while True:
        try:
            await asyncio.sleep(.1)
        except KeyboardInterrupt:
            await board.shutdown()
            sys.exit(0)


# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix
my_board = telemetrix_rpi_pico_2w_wifi_aio.TelemetrixRpiPico2WiFiAio(ip_address='192.168.2.212', loop=loop)

try:
    # start the main function
    loop.run_until_complete(step_continuous(my_board))
    loop.run_until_complete(my_board.shutdown())

except KeyboardInterrupt:
    loop.run_until_complete(my_board.shutdown())
    sys.exit(0)
