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
from classes.custom_exceptions import SyncCommandFailedException


sensor_measurement_finished_event = threading.Event()

def worker_mission_operation(rover, terminate_event, queue_manager, mission_manager):
    while not terminate_event.is_set():
        mission_msg = None
        try:
            mission_msg = queue_manager.get("mission_message", block=True, timeout=1)
        except queue.Empty:
            continue
        mission_manager.update_status(mission_msg)
        
        
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
        counter = 0
        success = False
        while counter < 5:
            if mav_cmd_tuple[0] == "COMMAND_LONG":
                rover.mav.command_long_send(*mav_cmd_tuple[1:])
            command_ack = queue_manager.get("sync_cmd_ack", block=True, timeout=2)
            if command_ack is None:
                # have to resend the command
                counter += 1
                continue 
            elif command_ack.command == mav_cmd_tuple[3]:
                # command is processed by the ardupilot
                if command_ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                    sucess = True
                break
        if not success:
            raise SyncCommandFailedException(f"Failed to send a sync-type command: {mav_cmd_tuple[3]}")
        queue_manager.put("sync_cmd_result", success)

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
    from classes import MessageDistributor
    message_distributor = MessageDistributor(queue_manager)
    while not terminate_event.is_set():
        message = rover.recv_match(blocking=True, timeout=5)
        if message is not None:
            message_distributor.distribute(message)

def generate_message_filename() -> str:
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = "mission" + current_time + ".json"
    return filename

def run(rover_serial, queue_manager, mission_manager):
    threads_terminate_event = threading.Event()
    worker_threads = []
    worker_threads.append(threading.Thread(target=worker_recv_messages, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_mission_operation, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager, mission_manager)))
    worker_threads.append(threading.Thread(target=worker_send_mav_cmd_sync, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_send_mav_cmd_async, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    worker_threads.append(threading.Thread(target=worker_sensor_measurement_mgmt, daemon=True, args=(rover_serial, threads_terminate_event, queue_manager)))
    
    return worker_threads, threads_terminate_event
    