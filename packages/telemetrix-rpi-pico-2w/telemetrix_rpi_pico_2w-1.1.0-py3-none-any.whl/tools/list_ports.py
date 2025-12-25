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

import serial.tools.list_ports

"""
This utility will list all comports, their description(i.e. Pico 2W - Pico Serial),
and pid and vid.

Sample output:
Description: n/a  Device:/dev/ttyS0  pid=None  vid=None
Description: Pico 2W - Pico Serial  Device:/dev/ttyACM0  pid=61455  vid=11914

"""

ports = serial.tools.list_ports.comports()

for port in ports:
    print(f'Description: {port.description}  Device:{port.device}  pid={port.pid}  vid={port.vid}')
