from pymavlink import mavutil
import json

MISSION_MESSAGE_TYPES = [
    "MISSION_CURRENT",
    "MISSION_ITEM_REACHED",
    "STATUSTEXT",
]

MESSAGE_TYPES = [
    # 'GLOBAL_POSITION_INT', 
    # 'GPS_RAW_INT', 
    'VFR_HUD', 
    # 'ATTITUDE',
    # 'RC_CHANNELS', 
    # 'SERVO_OUTPUT_RAW',
    'HEARTBEAT', 
    'COMMAND_ACK',
    'MISSION_CURRENT', 
    'MISSION_ITEM_REACHED',
    'MAV_MISSION_TYPE,'
    'NAV_CONTROLLER_OUTPUT',
    'STATUSTEXT', # IMPORTANT FOR MISSION TRACKING
    # 'SYS_STATUS',
    # 'POWER_STATUS',
]


# https://mavlink.io/en/messages/common.html#mav_commands

# Find each MAV_CMD enum here:
# https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py
# WARNING: haven't cross-checked if all these MAV_CMD exists in the rover.
# Check here: https://ardupilot.org/rover/docs/parameters.html
MAV_CMD_NUM_TO_NAME = {
    16: "MAV_CMD_NAV_WAYPOINT", # Navigate to MISSION.
    17: "MAV_CMD_NAV_LOITER_UNLIM", # Loiter around this MISSION an unlimited amount of time
    19: "MAV_CMD_NAV_LOITER_TIME", 
    20: "MAV_CMD_NAV_RETURN_TO_LAUNCH",
    112: "MAV_CMD_CONDITION_DELAY",
    114: "MAV_CMD_CONDITION_DISTANCE",
    115: "MAV_CMD_CONDITION_YAW",
    176: "MAV_CMD_DO_SET_MODE",
    177: "MAV_CMD_DO_JUMP",
    178: "MAV_CMD_DO_CHANGE_SPEED",
    179: "MAV_CMD_DO_SET_HOME",
    180: "MAV_CMD_DO_SET_PARAMETER",
    183: "MAV_CMD_DO_SET_SERVO",
    184: "MAV_CMD_DO_REPEAT_SERVO",
    224: "MAV_CMD_DO_SET_MISSION_CURRENT",
    300: "MAV_CMD_MISSION_START",
    400: "MAV_CMD_COMPONENT_ARM_DISARM",
}

def pretty_dict(message_dict: dict) -> str:
    return json.dumps(message_dict, indent=4)

def find_and_call(msg) -> dict:
    human_readable_message_dict = {}
    if msg.get_type() == "HEARTBEAT":
        human_readable_message_dict = heartbeat(msg)
    elif msg.get_type() == "COMMAND_ACK":
        human_readable_message_dict = command_ack(msg)
    elif msg.get_type() == "MISSION_ITEM_REACHED":
        human_readable_message_dict = mission_item_reached(msg)
    elif msg.get_type() == "MISSION_CURRENT":
        human_readable_message_dict = mission_current(msg)
    elif msg.get_type() == "STATUSTEXT":
        human_readable_message_dict = statustext(msg)
    elif msg.get_type() == "SYS_STATUS":
        human_readable_message_dict = sys_status(msg)
    elif msg.get_type() == "VFR_HUD":
        human_readable_message_dict = vfr_hud(msg)
    elif msg.get_type() == "NAV_CONTROLLER_OUTPUT":
        human_readable_message_dict = nav_controller_output(msg)
    
    return human_readable_message_dict

"""
    IMPORTANT NOTE: It looks like you can also query the rover for STATUSTEXT (MAVLINK_MSG_ID_STATUSTEXT = 253)
    TODO: Try to send MAVLINK_MSG_ID_STATUSTEXT = 253 and analyze the returned message.

    STATUSTEXT examples:
        STATUSTEXT {severity : 4, text : Finished active loiter, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Mission: 3 WP, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Reached waypoint #3, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Mission: 4 LoitUnlim, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Reached waypoint #4, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Reached waypoint #1, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Mission: 2 LoitTime, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Reached waypoint #2. Loiter for 5 seconds, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 4, text : Finished active loiter, id : 0, chunk_seq : 0}
        STATUSTEXT {severity : 6, text : Mission: 3 WP, id : 0, chunk_seq : 0}
    
    Check statustext_encode function at: https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py


    Explanation of each key:
        STATUSTEXT: https://mavlink.io/en/messages/common.html#STATUSTEXT
            severity: https://mavlink.io/en/messages/common.html#MAV_SEVERITY
            text: Status text message, without null termination character
            id: Unique (opaque) identifier for this statustext message. May be used to reassemble a logical long-statustext message from a sequence of chunks. A value of zero indicates this is the only chunk in the sequence and the message can be emitted immediately.
            chunk_seq: This chunk's sequence number; indexing is from zero. Any null character in the text field is taken to mean this was the last chunk.
"""


def statustext(msg) -> dict:
    status = {'message-type': msg.get_type()}
    if msg.severity == mavutil.mavlink.MAV_SEVERITY_EMERGENCY:
        status['severity'] = "MAV_SEVERITY_EMERGENCY"
        status['severity-description'] = "System is unusable. This is a 'panic' condition."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_ALERT:
        status['severity'] = "MAV_SEVERITY_ALERT"
        status['severity-description'] = "Action should be taken immediately. Indicates error in non-critical systems."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_CRITICAL:
        status['severity'] = "MAV_SEVERITY_CRITICAL"
        status['severity-description'] = "Action must be taken immediately. Indicates failure in a primary system."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_ERROR:
        status['severity'] = "MAV_SEVERITY_ERROR"
        status['severity-description'] = "Indicates an error in secondary/redundant systems."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_WARNING:
        status['severity'] = "MAV_SEVERITY_WARNING"
        status['severity-description'] = "Indicates about a possible future error if this is not resolved within a given timeframe. Example would be a low battery warning."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_NOTICE:
        status['severity'] = "MAV_SEVERITY_NOTICE"
        status['severity-description'] = "An unusual event has occurred, though not an error condition. This should be investigated for the root cause."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_INFO:
        status['severity'] = "MAV_SEVERITY_INFO"
        status['severity-description'] = "Normal operational messages. Useful for logging. No action is required for these messages."
    elif msg.severity == mavutil.mavlink.MAV_SEVERITY_DEBUG:
        status['severity'] = "MAV_SEVERITY_DEBUG"
        status['severity-description'] = "Useful non-operational messages that can assist in debugging. These should not occur during normal operation."
    status['text'] = msg.text

    return status

"""
    Example for MISSION_ITEM_REACHED:
        MISSION_ITEM_REACHED {seq : 1}

    https://mavlink.io/en/messages/common.html#MISSION_ITEM_REACHED
    
"""
def mission_item_reached(msg) -> dict:
    mir = {'message-type': msg.get_type()}
    mir['seq'] = int(msg.seq)
    mir['description'] = f'Mission Item # {msg.seq} has been reached or completed.'
    return mir

"""
    Example:
        MISSION_CURRENT {seq : 1}
    https://mavlink.io/en/messages/common.html#MISSION_CURRENT
"""
def mission_current(msg) -> dict:
    mc = {'message-type': msg.get_type()}
    mc['seq'] = msg.seq
    return mc

"""
    MISSION_ACK:
    https://mavlink.io/en/messages/common.html#NAV_CONTROLLER_OUTPUT
    MISSION_ACK message example:
    
    Check mission_ack_output_encode function and enum values at:
    https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

    Explanation for each key (We're only going to use some of them):
    type: See MAV_MISSION_RESULT enum (uint8_t)
    mission_type: See MAV_MISSION_TYPE enum

"""
def mission_ack(msg) -> dict:
    ack = {'message-type': msg.get_type()}
    if msg.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
        ack['type'] = "[MAV_MISSION_ACCEPTED] mission accepted OK"
    elif msg.type == mavutil.mavlink.MAV_MISSION_ERROR:
        ack['type'] = "[MAV_MISSION_ERROR] Generic error / not accepting mission commands at all right now."
    elif msg.type == mavutil.mavlink.MAV_MISSION_UNSUPPORTED_FRAME:
        ack['type'] = "[MAV_MISSION_UNSUPPORTED_FRAME] Coordinate frame is not supported."
    elif msg.type == mavutil.mavlink.MAV_MISSION_UNSUPPORTED:
        ack['type'] = "[MAV_MISSION_UNSUPPORTED] Command is not supported."
    elif msg.type == mavutil.mavlink.MAV_MISSION_NO_SPACE:
        ack['type'] = "[MAV_MISSION_NO_SPACE] Mission items exceed storage space.."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID:
        ack['type'] = "[MAV_MISSION_INVALID] One of the parameters has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM1:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM1] param1 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM2:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM2] param2 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM3:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM3] param3 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM4:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM4] param4 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM5_X:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM5_X] x / param5 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM6_Y:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM6_Y] y / param6 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_PARAM7:
        ack['type'] = "[MAV_MISSION_INVALID_PARAM7] z / param7 has an invalid value."
    elif msg.type == mavutil.mavlink.MAV_MISSION_INVALID_SEQUENCE:
        ack['type'] = "[MAV_MISSION_INVALID_SEQUENCE] Mission item received out of sequence"
    elif msg.type == mavutil.mavlink.MAV_MISSION_DENIED:
        ack['type'] = "[MAV_MISSION_DENIED] Not accepting any mission commands from this communication partner."
    elif msg.type == mavutil.mavlink.MAV_MISSION_OPERATION_CANCELLED:
        ack['type'] = "[MAV_MISSION_OPERATION_CANCELLED] Current mission operation cancelled (e.g. mission upload, mission download)."
    
    if msg.mission_type == mavutil.mavlink.MAV_MISSION_TYPE_MISSION:
        ack['mission_type'] = "[MAV_MISSION_TYPE_MISSION] MAV_MISSION_TYPE_MISSION"
    elif msg.mission_type == mavutil.mavlink.MAV_MISSION_TYPE_FENCE:
        ack['mission_type'] = "[MAV_MISSION_TYPE_FENCE] Specifies GeoFence area(s). Items are MAV_CMD_NAV_FENCE_ GeoFence items."
    elif msg.mission_type == mavutil.mavlink.	MAV_MISSION_TYPE_RALLY:
        ack['mission_type'] = "[MAV_MISSION_TYPE_RALLY] Specifies the rally points for the vehicle. Rally points are alternative RTL points. Items are MAV_CMD_NAV_RALLY_POINT rally point items."
    elif msg.mission_type == mavutil.mavlink.MAV_MISSION_TYPE_ALL:
        ack['mission_type'] = "[MAV_MISSION_TYPE_ALL] Only used in MISSION_CLEAR_ALL to clear all mission types."
    return ack


"""
    NAV_CONTROLLER_OUTPUT:
    https://mavlink.io/en/messages/common.html#NAV_CONTROLLER_OUTPUT
    NAV_CONTROLLER_OUTPUT message example:
    NAV_CONTROLLER_OUTPUT {nav_roll : 0.0, nav_pitch : 0.0, nav_bearing : 256, target_bearing : 90, wp_dist : 2, alt_error : 0.0, aspd_error : 0.0, xtrack_error : 0.0}

    
    Check nav_controller_output_encode function and enum values at:
    https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

    Explanation for each key (We're only going to use some of them):
    target_bearing: Bearing to current MISSION/target in degrees (int16_t)
    wp_dist: Distance to active MISSION in meters (uint16_t)

"""

def nav_controller_output(msg) -> dict:
    nav = {'message-type': msg.get_type()}
    nav['target_bearing'] = f"{msg.target_bearing} degress (Bearing to current waypoint/target)"
    nav['wp_dist'] = f"{msg.wp_dist} meters from the waypoint"
    return nav

"""
    SYS_STATUS:
    https://mavlink.io/en/messages/common.html#SYS_STATUS
    SYS_STATUS message example:
    SYS_STATUS {onboard_control_sensors_present : 321969199, onboard_control_sensors_enabled : 52485167, onboard_control_sensors_health : 53533999, load : 131, voltage_battery : 7081, current_battery : 0, battery_remaining : 100, drop_rate_comm : 0, errors_comm : 0, errors_count1 : 0, errors_count2 : 0, errors_count3 : 0, errors_count4 : 0}

    
    Check sys_status_encode function and enum values at:
    https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

    Explanation for each key (We're only going to use some of them):
    load: https://mavlink.io/en/messages/common.html#SYS_STATUS
    

"""

def sys_status(msg) -> dict:
    sys = {'message-type': msg.get_type()}
    sys['load'] = f"{msg.load} [0-1000] (mainloop time usage)"
    sys['voltage_battery'] = f"{msg.voltage_battery}mV"
    sys['current_battery'] = f"{msg.current_battery}cA (100cA = 1A)"
    sys['battery_remaining'] = f"{msg.battery_remaining}% [0-100]"
    sys['drop_rate_comm'] = f"{msg.drop_rate_comm}c%"
    sys['errors_comm'] = f"{msg.errors_comm} dropped packets"
    return sys


"""
    POWER_STATUS:
    https://mavlink.io/en/messages/common.html#POWER_STATUS
    POWER_STATUS message example:
    POWER_STATUS {Vcc : 4980, Vservo : 6058, flags : 1}
    
    Check sys_status_encode function and enum values at:
    https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

    Explanation for each key (We're only going to use some of them):
    Vcc: (mV) 5V rail voltage.
    Vservo: (mV) Servo rail voltage.
    flags: Bitmap of power supply status flags.
"""

def power_status(msg) -> dict:
    power = {'message-type': msg.get_type()}
    power['Vcc'] = f"{msg.Vcc}mV (5V rail voltage)"
    power['Vservo'] = f"{msg.Vservo}mV (Servo rail voltage)"
    if msg.flags == mavutil.mavlink.MAV_POWER_STATUS_BRICK_VALID:
        power['flags'] = f"main brick power supply valid"
    elif msg.flags == mavutil.mavlink.MAV_POWER_STATUS_SERVO_VALID:
        power['flags'] = f"main servo power supply valid for FMU"
    elif msg.flags == mavutil.mavlink.MAV_POWER_STATUS_USB_CONNECTED:
        power['flags'] = f"USB power is connected"
    elif msg.flags == mavutil.mavlink.MAV_POWER_STATUS_PERIPH_OVERCURRENT:
        power['flags'] = f"peripheral supply is in over-current state"
    elif msg.flags == mavutil.mavlink.MAV_POWER_STATUS_PERIPH_HIPOWER_OVERCURRENT:
        power['flags'] = f"hi-power peripheral supply is in over-current state"
    elif msg.flags == mavutil.mavlink.MAV_POWER_STATUS_CHANGED:
        power['flags'] = f"Power status has changed since boot"
    return power

"""
    VFR_HUD:
    https://mavlink.io/en/messages/common.html#VFR_HUD
    VFR_HUD message example:
    VFR_HUD {airspeed : 0.03800000250339508, groundspeed : 0.010911336168646812, heading : 78, throttle : 0, alt : 48.59000015258789, climb : -0.01797836273908615}

    
    Check vfr_hud_encode function and enum values at:
    https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

    Explanation for each key:
    airspeed: https://mavlink.io/en/messages/common.html#VFR_HUD
    groundspeed: https://mavlink.io/en/messages/common.html#VFR_HUD
    heading: https://mavlink.io/en/messages/common.html#VFR_HUD
    throttle: https://mavlink.io/en/messages/common.html#VFR_HUD
    alt: https://mavlink.io/en/messages/common.html#VFR_HUD
    climb: https://mavlink.io/en/messages/common.html#VFR_HUD

"""
def vfr_hud(msg) -> dict:
    vfr = {'message-type': msg.get_type()}
    vfr['airspeed'] = msg.airspeed
    vfr['groundspeed'] = msg.groundspeed
    vfr['heading'] = f"{msg.heading} degrees (North = 0)"
    vfr['throttle'] = f"{msg.throttle}% (throttle setting)"
    vfr['alt'] = msg.alt
    vfr['climb'] = msg.climb
    return vfr


"""
    COMMAND_ACK:
    https://mavlink.io/en/messages/common.html#COMMAND_ACK
    COMMAND_ACK message example:
    COMMAND_ACK {command : 400, result : 0, progress : 0, result_param2 : 0, target_system : 255, target_component : 0}
    
    Check command_ack_encode function and enum values at:
    https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py

    Explanation for each key:
    command: https://mavlink.io/en/messages/common.html#mav_commands
    result: https://mavlink.io/en/messages/common.html#MAV_RESULT
    progress: 

"""
def command_ack(msg) -> dict:
    ack = {'message-type': msg.get_type()}
    try:
        ack['command'] = MAV_CMD_NUM_TO_NAME[msg.command]
    except KeyError:
        print("KeyError: msg: ", msg)
    if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        ack['result'] = "MAV_RESULT_ACCEPTED"
        ack['result-description'] = "Command is valid (is supported and has valid parameters), and was executed."
    elif msg.result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
        ack['result'] = "MAV_RESULT_TEMPORARILY_REJECTED"
        ack['result-description'] = "Command is valid, but cannot be executed at this time. (Omitted) Retrying later should work."
    elif msg.result == mavutil.mavlink.MAV_RESULT_DENIED:
        ack['result'] = "MAV_RESULT_DENIED"
        ack['result-description'] = "Command is invalid (is supported but has invalid parameters). (Omitted)"
    elif msg.result == mavutil.mavlink.MAV_RESULT_UNSUPPORTED:
        ack['result'] = "MAV_RESULT_UNSUPPORTED"
        ack['result-description'] = "Command is not supported (unknown)."
    elif msg.result == mavutil.mavlink.MAV_RESULT_FAILED:
        ack['result'] = "MAV_RESULT_FAILED"
        ack['result-description'] = "Command is valid, but execution has failed. This is used to indicate any non-temporary or unexpected problem. (Omitted)"
    elif msg.result == mavutil.mavlink.	MAV_RESULT_IN_PROGRESS:
        ack['result'] = "MAV_RESULT_IN_PROGRESS"
        ack['result-description'] = "Command is valid and is being executed. This will be followed by further progress updates. The COMMAND_ACK.progress field can be used to indicate the progress of the operation. (Omitted)"
    elif msg.result == mavutil.mavlink.MAV_RESULT_CANCELLED:
        ack['result'] = "MAV_RESULT_CANCELLED"
        ack['result-description'] = "Command has been cancelled (as a result of receiving a COMMAND_CANCEL message)."
    ack['progress'] = f"{msg.progress}% (may be percentage or may be an error enum code)"
    ack['result_param2'] = f"{msg.result_param2} (Additional parameter of the result, example: which parameter of MAV_CMD_NAV_WAYPOINT caused it to be denied.)"
    
    if msg.command == mavutil.mavlink.MAV_CMD_NAV_WAYPOINT:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_CONDITION_DELAY:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_CONDITION_DISTANCE:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_CONDITION_YAW:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_JUMP:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_SET_HOME:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_SET_PARAMETER:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_SET_SERVO:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_DO_REPEAT_SERVO:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_MISSION_START:
        dummy_func()
    elif msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
        dummy_func()
    return ack

def dummy_func():
    return


# HEARTBEAT messages look like the following:
# HEARTBEAT {type : 10, autopilot : 3, base_mode : 137, custom_mode : 10, system_status : 4, mavlink_version : 3}
# for specific parameters, look at: https://mavlink.io/en/messages/common.html

# look at heartbeat_encode function in: https://github.com/owenson/ardupilot-sdk-python/blob/master/pymavlink/dialects/v10/ardupilotmega.py 
# type: https://mavlink.io/en/messages/common.html#MAV_TYPE
# autopilot: https://mavlink.io/en/messages/common.html#MAV_AUTOPILOT
# custom_mode: https://ardupilot.org/rover/docs/parameters.html#mode1
# system_status: https://mavlink.io/en/messages/common.html#MAV_STATE

def heartbeat(msg, verbose=True) -> dict:
    hb = {'message-type': msg.get_type()}
    if msg.type == mavutil.mavlink.MAV_TYPE_GROUND_ROVER:
        hb['type'] = "Ground Rover"
    if msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
        hb['autopilot'] = "ArduPilot"
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED:
        # custom mode for the rover is enabled. i.e. we can find out the current flight mode in custom_mode field
        if msg.custom_mode == 0:
            hb['custom_type'] = 'Manual Mode'
        elif msg.custom_mode == 5:
            hb['custom_type'] = 'Loiter Mode' 
        elif msg.custom_mode == 10:
            hb['custom_type'] = 'Auto Mode'
        elif msg.custom_mode == 15:
            hb['custom_type'] = 'Guided Mode'
    if msg.system_status == mavutil.mavlink.MAV_STATE_UNINIT:
        hb['system_status'] = "Uninitialized system, state is unknown."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_BOOT:
        hb['system_status'] = "System is booting up."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_CALIBRATING:
        hb['system_status'] = "System is calibrating and not flight-ready."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_STANDBY:
        hb['system_status'] = "System is grounded and on standby. It can be launched any time."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_ACTIVE:
        hb['system_status'] = "System is active and might be already airborne. Motors are engaged."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_CRITICAL:
        hb['system_status'] = "System is in a non-normal flight mode. It can however still navigate."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_EMERGENCY:
        hb['system_status'] = "System is in a non-normal flight mode. It lost control over parts or over the whole airframe. It is in mayday and going down."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_POWEROFF:
        hb['system_status'] = "System just initialized its power-down sequence, will shut down now."
    elif msg.system_status == mavutil.mavlink.MAV_STATE_FLIGHT_TERMINATION:
        hb['system_status'] = "System is terminating itself."
    else:
        hb['system_status'] = "System status: Edit heartbeat handler to see the detail."
    
    return hb

