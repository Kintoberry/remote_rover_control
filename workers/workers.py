import threading
import json
import queue
import re
from datetime import datetime
from typing import Tuple
from library import utility_functions as helper
import time
import os
from pymavlink import mavutil
from classes import QueueManager, MessageDistributor, AbstractQueueManager


sensor_measurement_finished_event = threading.Event()

def worker_mission_operation(rover, terminate_event, queue_manager):
    mission_status_dict = {
        'current_wp': 0,
        'target_wp': 1,
        'mission_item_num': 0,
        'loiter': False,
        'mission_status': "IDLE",
        'possible_mission_status': [
            "IDLE (PRIOR TO MISSION)",
            "MOVING TO TARGET WAYPOINT",
            "LOITER UNLIMITED",
            "LOITER LIMITED TIME",
            "MISSION COMPLETE",
        ]
    }
    
    while not terminate_event.is_set():
        mission_msg_dict = None
        try:
            mission_msg_dict = queue_manager.get("mission_message", block=True, timeout=1)
        except queue.Empty:
            continue
        try:
            if mission_msg_dict['message-type'] == "MISSION_CURRENT":
                mission_status_dict['target_wp'] = mission_msg_dict['seq']
                print(mission_msg_dict)
            elif mission_msg_dict['message-type'] == "MISSION_ITEM_RECHEAD":
                print("capture mission item reached")
                mission_status_dict['current_wp'] = mission_msg_dict['seq']
                # TODO: target_wp may not be +1 of 'current_wp'. `current_wp + 1` may be next MAV_CMD. Need to fix this.
                mission_status_dict['target_wp'] = mission_msg_dict['seq'] + 1
            elif mission_msg_dict['message-type'] == "STATUSTEXT":
                is_unlim_loiter, mission_item_num = is_unlimited_loiter_in_progress(mission_msg_dict['text'])
                if is_unlim_loiter:
                    print("Unlim lotering!!")
                    queue_manager.put("measurement_request", {"action": "START", 'mission_item_num': mission_item_num}, block=True)
                    mission_status_dict['loiter'] = True 
                    mission_status_dict['mission_item_num'] = mission_item_num

                else:
                    mission_status_dict['loiter'] = False
        except KeyError:
            # TODO: use logger here instead
            print("'message-type' key doesn't exist.")
            continue
        except Exception as e:
            print("Unknown error has ocurred while trying to access 'message-type' key.")
            continue
        # print(json.dumps(mission_msg_dict, indent=2))
        
def is_unlimited_loiter_in_progress2(statustext_text) -> Tuple[bool, int]:
    # to parse the value of 'text' in 'STATUSTEXT' message
    print("inside checking unlimloiter")
    print("text: ", statustext_text)
    if "LoitUnlim" in statustext_text:
        print("true")
        return True, 0
    else:
        print("false")
        return False, -1

def is_unlimited_loiter_in_progress(statustext_text) -> Tuple[bool, int]:
    # to parse the value of 'text' in 'STATUSTEXT' message
    pattern = r"(Mission:)\s*(\d+)\s*(\w+)"
    match = re.match(pattern, statustext_text)
    if match:
        # mission_text = match.group(1)
        mission_item_number = int(match.group(2))
        # LoitUnlim = match.group(3)
        return True, mission_item_number
    else:
        return False, -1

def worker_sensor_measurement_mgmt(rover, terminate_event, queue_manager):
    while not terminate_event.is_set():
        msg_dict = None
        try:
            msg_dict = queue_manager.get("measurement_request", block=True, timeout=1)
            print("worker_sensor_measurement_mgmt captured the command")
        except queue.Empty:
            continue
        if msg_dict['action'] == "START":
            print("worker sensor measure got the message 'START'")
            # send out the request for sensor control
            # make this a blocking operation
            while not sensor_measurement_finished_event.is_set():
                time.sleep(1)
            sensor_measurement_finished_event.clear()
            print("loiter deactivate signal has arrived!!")
            mav_cmd = ("COMMAND_LONG",
             rover.target_system,
             rover.target_component,
             mavutil.mavlink.MAV_CMD_DO_SET_MISSION_CURRENT,
             0,
             int(msg_dict['mission_item_num'] + 2),
             0,
             0, 0, 0, 0, 0
             )
            queue_manager.put("async_cmd", block=True)

def worker_send_mav_cmd_sync(rover, terminate_event, queue_manager):
    while not terminate_event.is_set():
        try:
            mav_cmd_tuple = queue_manager.get("sync_cmd", block=True, timeout=1)
        except queue.Empty:
            continue
        # TODO: put counter here so that after, say, 5 retransmission we exit the loop and report an error
        while True:
            if mav_cmd_tuple[0] == "COMMAND_LONG":
                rover.mav.command_long_send(*mav_cmd_tuple[1:])
            command_ack = queue_manager.get("sync_cmd_ack", block=True, timeout=2)
            if command_ack is None:
                # have to resend the command
                continue 
            elif command_ack.command == mav_cmd_tuple[3]:
                # command is processed by the ardupilot
                break

def worker_send_mav_cmd_async(rover, terminate_event, queue_manager):
    while not terminate_event.is_set():
        try:
            mav_cmd_tuple = queue_manager.get("async_cmd", block=True, timeout=1)
        except queue.Empty:
            continue
        if mav_cmd_tuple[0] == "COMMAND_LONG":
            rover.mav.command_long_send(*mav_cmd_tuple[1:])
        # NOTE: for now, we don't really care if async-type commands are acknowledged
        command_ack = queue_manager.get("async_cmd_ack", block=True, timeout=2)
        if command_ack is None:
            pass
        elif command_ack.command == mav_cmd_tuple[3]:
                # command is processed by the ardupilot
                pass

def worker_recv_messages(rover, terminate_event, queue_manager):
    message_distributor = MessageDistributor(queue_manager)
    while not terminate_event.is_set():
        message = rover.recv_match(blocking=True, timeout=5)
        if message is not None:
            message_distributor.distribute(message)

def generate_message_filename() -> str:
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = "mission" + current_time + ".json"
    return filename

def run(rover_serial, queue_manager: AbstractQueueManager):
    threads_terminate_event = threading.Event()

    worker_threads = []
    worker_threads.append(threading.Thread(target=worker_recv_messages, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_mission_operation, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_send_mav_cmd_sync, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_send_mav_cmd_async, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_sensor_measurement_mgmt, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    
    return worker_threads, threads_terminate_event
    