from pymavlink import mavutil
import serial.tools.list_ports


def find_telemetry_port_name_old(debug=False):
    ports = serial.tools.list_ports.comports()
    print("ports: ", ports)
    target_strings = ["0403", "6015", "D308LTJDA"]
    for port in ports:
        # Telemetry hardware VID:PID=0403:6015", "SER=D308LTJDA
        print(f"port: {port}, hwid: {port.hwid}, port.device: {port.device}")
        if all(target in port.hwid for target in target_strings):
            return port.device
        


def find_telemetry_port_name(debug=False):
    ports = serial.tools.list_ports.comports()
    
    telemetry_radio_identity = {
        "vid": 0x0403,
        "pid": 0x6015,
        "serial_number": "D308LTJDA"
    }

    pixhawk4_identity = {
        "vid": 0x1209,
        "pid": 0x5740,
        "serial_number": "29003F001951383433393139"
    }
    
    for port in ports:
        if debug:
            # example output for Pixhawk4 serial connection: port: /dev/ttyACM0 - Pixhawk4, vid: 4617, pid: 22336, serial_number: 29003F001951383433393139, port.device: /dev/ttyACM0, port.hwid: USB VID:PID=1209:5740 SER=29003F001951383433393139 LOCATION=2-2:1.0
            print(f"port: {port}, vid: {port.vid}, pid: {port.pid}, serial_number: {port.serial_number}, port.device: {port.device}, port.hwid: {port.hwid}")
        
        if (port.vid == pixhawk4_identity["vid"] and port.pid == pixhawk4_identity["pid"] and port.serial_number == pixhawk4_identity["serial_number"]):
            """ 
                NOTE: we're returning the first device file string. But you should know that there can be
                multiple device file related to one serial port connection.

                For example, both /dev/ttyACM0 and /dev/ttyACM1 are created for a serial connection with Pixhawk4.
                If you have to choose the right file among the two, you should consult ardupilot documentation.
            """
            if debug:
                print("Pixhawk4 serial port")
            return port.device
        elif (port.vid == telemetry_radio_identity["vid"] and port.pid == telemetry_radio_identity["pid"] and port.serial_number == telemetry_radio_identity["serial_number"]):
            if debug:
                print("Telemetry radio serial port")
            return port.device
        

    if debug:
        print("ERROR: Couldn't connect to the rover using a serial port.")

if __name__ == "__main__":
    find_telemetry_port_name(debug=True)

