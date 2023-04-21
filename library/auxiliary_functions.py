from pymavlink import mavutil
import serial.tools.list_ports


def find_telemetry_port_name(debug=False):
    ports = serial.tools.list_ports.comports()
    print("ports: ", ports)
    target_strings = ["0403", "6015", "D308LTJDA"]
    for port in ports:
        # VID:PID=0403:6015", "SER=D308LTJDA
        print(f"port: {port}, hwid: {port.hwid}, port.device: {port.device}")
        if all(target in port.hwid for target in target_strings):
            return port.device


if __name__ == "__main__":
    find_telemetry_port_name(debug=True)