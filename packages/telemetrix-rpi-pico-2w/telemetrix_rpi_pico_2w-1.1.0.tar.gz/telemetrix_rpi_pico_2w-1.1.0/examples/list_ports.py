import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

for port in ports:
    # if port.description == "Pico 2W - Pico Serial":
    print(f'Description: {port.description}  Device:{port.device}  pid={port.pid}  vid={port.vid}')
