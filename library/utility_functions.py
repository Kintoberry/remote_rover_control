# https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

from pymavlink import mavutil
import serial.tools.list_ports



def cleanup(mavserial):
    set_disarm_state(mavserial)

def connect_flight_controller(connection_string, baud_rate, debug=False):
    return mavutil.mavlink_connection(connection_string, baud=baud_rate)

# TODO: Command to send MISSION_ITEM_INT message
# LINK:  https://mavlink.io/en/messages/common.html#MISSION_ITEM_INT

def set_guided_mode(mavserial, blocking=True, verbose=True) -> bool:
    MODE = 15 # GUIDED = 15, refer to https://ardupilot.org/rover/docs/parameters.html#mode1
    MAV_CMD = mavutil.mavlink.MAV_CMD_DO_SET_MODE
    mavserial.mav.command_long_send(
        mavserial.target_system,
        mavserial.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0, # Confirmation (default 0)
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        MODE, 
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0  # Reserved
    )
    if blocking:
        if (receive_message_from_ardupilot(mavserial, MAV_CMD, "COMMAND_ACK", custom_message="SET_GUIDED_MODE", verbose=verbose)):
            return True
        else:
            return False
    else:
        return True

def set_auto_mode(mavserial) -> int:
    AUTO_MODE = 10 # refer to https://ardupilot.org/rover/docs/parameters.html#mode1
    mavserial.mav.command_long_send(
        mavserial.target_system,
        mavserial.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0, # Confirmation (default 0)
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, # 
        AUTO_MODE, 
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0  # Reserved
    )
    return mavutil.mavlink.MAV_CMD_DO_SET_MODE

def set_manual_mode(mavserial) -> int:
    MANUAL_MODE = 0 # refer to https://ardupilot.org/rover/docs/parameters.html#mode1
    mavserial.mav.command_long_send(
        mavserial.target_system,
        mavserial.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0, # Confirmation (default 0)
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, # 
        MANUAL_MODE, 
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0  # Reserved
    )     
    return mavutil.mavlink.MAV_CMD_DO_SET_MODE

def set_param(mavserial, param_name, param_value):
    mavserial.mav.param_set_send(
        mavserial.target_system,
        mavserial.target_component,
        param_name,  # Convert the parameter name to bytes
        param_value,
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )

def check_heartbeat(mavserial):
    mavserial.wait_heartbeat()
    print("HEARTBEAT: The ardupilot is responsive (system %u component %u)" % (mavserial.target_system, mavserial.target_component))
    heartbeat = mavserial.recv_match(type=['HEARTBEAT'], blocking=True)
    print(heartbeat)
    # print("TYPE: %u, autopilot: %u, base_mode: %u, custom_mode: %u, system_status: %u, mavlink_version: %u" % (
    #     mavserial.type, mavserial.autopilot, mavserial.base_mode, mavserial.custom_mode, mavserial.system_Status, mavserial.mavlink_version
    # ))


def go_to_location(mavserial, latitude, longitude, altitude, verbose=True) -> bool:
    MAV_CMD = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
    # Send the MAV_CMD_NAV_WAYPOINT command using command_int_send
    mavserial.mav.command_int_send(
        mavserial.target_system,
        mavserial.target_component,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Global frame with relative altitude
        MAV_CMD,  # Waypoint coxmmand
        0,  # current, Not used.
        0,  # Autocontinue, Not used (set 0).
        0,  # Param1: Hold time in decimal seconds (unused for command_int_send)
        0,  # Param2: Acceptance radius in meters (unused for command_int_send)
        0,  # Param3: Pass through the waypoint (unused for command_int_send)
        0,  # Param4: Desired yaw angle (unused for command_int_send)
        int(latitude * 1e7),  # Latitude (degrees * 1E7)
        int(longitude * 1e7),  # Longitude (degrees * 1E7)
        altitude  # Altitude in meters
    )
    if (receive_message_from_ardupilot(mavserial, MAV_CMD, "COMMAND_ACK", custom_message="NAV_WAYPOINT", verbose=verbose)):
        return True
    else:
        return False

def receive_message_from_ardupilot(mavserial, MAV_COMMAND, *response_types, custom_message="CMD", verbose=False) -> bool:
    # response = mavserial.recv_match(type=list(message_types) if message_types else None, blocking=True)
    if len(response_types) == 0:
        response = mavserial.recv_match(blocking=True)
    else:
        response = mavserial.recv_match(type=list(response_types), blocking=True)
    # have to change this code to accomodate multiple response_types specified
    if response.command == MAV_COMMAND:
        if response.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            vprint(f"[{custom_message}] SUCCESS: MAV_RESULT_ACCEPTED.", verbose)
            return True
        elif response.result == mavutil.mavlink.MAV_RESULT_IN_PROGRESS:
            vprint(f"[{custom_message}] IN PROGRESS: MAV_RESULT_IN_PROGRESS.", verbose)
            return False
        elif response.result == mavutil.mavlink.MAV_RESULT_FAILED:
            vprint(f"[{custom_message}] ERROR: MAV_RESULT_FAILED.", verbose)
            return False
    else:
        vprint(f"[{custom_message}]ERROR: COMMAND_ACK for the given command is not returned from the ardupilot.", verbose)
        return False

def vprint(message, verbose):
    if verbose:
        print(message)

def set_arm_state(mavserial) -> int:
    mavserial.mav.command_long_send(
        mavserial.target_system,
        mavserial.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, # Confirmation
        1, # 0:disarm, 1:arm
        21196, # 0: arm-disarm unless prevented by safety checks, 21196: force arming or disarming
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0  # Reserved 
    )
    return mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM

    
def set_disarm_state(mavserial) -> int:
    mavserial.mav.command_long_send(
        mavserial.target_system,
        mavserial.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, # Confirmation
        0, # 0:disarm, 1:arm
        21196, # 0: arm-disarm unless prevented by safety checks, 21196: force arming or disarming
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0, # Reserved
        0  # Reserved
    )
    return mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM


if __name__ == "__main__":
    serial = connect_flight_controller("/dev/ttyACM0")
    check_heartbeat(serial)