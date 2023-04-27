from classes.mission_blueprint import MissionBlueprint
import threading
from .custom_exceptions import MissionCompleteException
from .queue_manager import AbstractQueueManager
from .custom_exceptions import ExistingSerialConnectionException

class MissionManager:
    def __init__(self, queue_manager: AbstractQueueManager, mission_blueprint):
        self.rover_serial = None
        self.queue_manager = queue_manager
        self.mission_blueprint = mission_blueprint
        self.thread_lock = threading.Lock()
        self.target_waypoint = None
        self.current_waypoint = None
        self.final_waypoint = None
        self.mission_complete = False

        self.current_command = None
        self.loitering_waypoint = None

    # Setter Injection 
    def set_rover_serial(self, rover_serial, force=False):
        with self.thread_lock:
            self.rover_serial = rover_serial
        # if not self.rover_serial or force:
        #     self.rover_serial = rover_serial
        # else:
        #     raise ExistingSerialConnectionException("Serial connection to the UGV already exists. Use `force` parameter if you must.")

    def load_mission(self):
        with self.thread_lock:
            self.mission_blueprint.download_mission(self.rover_serial)
            self.current_waypoint = self.mission_blueprint.get_first_waypoint()
            self.final_waypoint = self.mission_blueprint.get_final_Waypoint()

    def is_mission_downloaded(self) -> bool:
        with self.thread_lock:
            return self.mission_blueprint.is_mission_downloaded()
    
    def update_status(self, message):
        with self.thread_lock:
            message_type = message.get_type()
            if message_type == "MISSION_CURRENT":
                if self.mission_blueprint.is_waypoint(seq):
                    self.target_waypoint = message.seq
            elif message_type == "MISSION_ITEM_RECHEAD":
                if self.mission_blueprint.is_waypoint(message.seq):
                    self.current_waypoint = message.seq
                    if message.seq == self.final_waypoint:
                        self.target_waypoint = self.final_waypoint
                        self.mission_complete = True
            elif message_type == "STATUSTEXT":
                
                    
        try:
            if mission_msg_dict['mavpackettype'] == "MISSION_CURRENT":
                mission_status_dict['target_wp'] = mission_msg_dict['seq']
            elif mission_msg_dict['mavpackettype'] == "MISSION_ITEM_RECHEAD":
                print("capture mission item reached")
                mission_status_dict['current_wp'] = mission_msg_dict['seq']
                # TODO: target_wp may not be +1 of 'current_wp'. `current_wp + 1` may be next MAV_CMD. Need to fix this.
                mission_status_dict['target_wp'] = mission_msg_dict['seq'] + 1
            elif mission_msg_dict['mavpackettype'] == "STATUSTEXT":
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
            print("'mavpackettype' key doesn't exist.")
            continue
        except Exception as e:
            print("Unknown error has ocurred while trying to access 'mavpackettype' key.")
            continue
        # print(json.dumps(mission_msg_dict, indent=2))
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

    def move_to_next_waypoint(self) -> bool:
        # move to the next waypoint regardless of what it's doing now
        with self.thread_lock:
            if self.mission_blueprint.is_mission_complete(self.current_waypoint):
                raise MissionCompleteException("Cannot move to the next waypoint. Mission already complete.")
            next_waypoint = self.mission_blueprint.get_next_waypoint(self.current_waypoint)
            if next_waypoint == -1: # no next waypoint
            # HERE!
        pass

    def handle_mission_messages(self):
        while True:
            msg = self.rover_serial.recv_match(blocking=True)
            if msg.get_type() == "MISSION_CURRENT":
                self.current_waypoint = msg.seq
                self.current_command = self.mission_blueprint.mission_items[self.current_waypoint].command
                if self.mission_blueprint.is_rover_loitering(self.current_command):
                    self.loitering_waypoint = self.current_waypoint
                else:
                    self.loitering_waypoint = None
            elif msg.get_type() == "MISSION_ITEM_REACHED":
                reached_waypoint = msg.seq
                print(f"Reached waypoint: {reached_waypoint}")
            elif msg.get_type() == "STATUSTEXT":
                print(f"Status text: {msg.text}")

    def cancel_loitering_and_move_to_next_waypoint(self):
        if self.loitering_waypoint is not None:
            next_waypoint = self.loitering_waypoint + 1
            self.rover_serial.mav.mission_set_current_send(self.rover_serial.target_system, self.rover_serial.target_component, next_waypoint)
            print(f"Canceling loitering and moving to waypoint: {next_waypoint}")
        else:
            print("The rover is not loitering.")
            
    def display_current_status(self):
        if self.mission_blueprint is None:
            print("Mission not loaded yet.")
            return

        if self.current_waypoint is None:
            print("No waypoint information received yet.")
        else:
            print(f"Current waypoint: {self.current_waypoint}")

            if self.loitering_waypoint is not None:
                print(f"Loitering at waypoint: {self.loitering_waypoint}")

            waypoints_remaining = self.mission_blueprint.get_number_of_waypoints() - self.current_waypoint
            print(f"Waypoints remaining: {waypoints_remaining}")

