from classes.mission_blueprint import MissionBlueprint
import threading
from .custom_exceptions import MissionCompleteException, AlreadyInLastWaypointException
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
        self.loitering = False
        self.loiter_time = None
    


        self.current_cmd = None
        self.current_command = None
        self.loitering_waypoint = None

    # TODO: need to reset mission status after finished the mission, and when it's ready to repeat the mission
    # Maybe throttle disarm should signal this state change
    # def reset_mission_status(self):
        # pass

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
                if self.mission_blueprint.is_waypoint(message.seq):
                    self.target_waypoint = message.seq
                elif self.mission_blueprint.is_loiter_unlimited_cmd(message.seq):
                    self.loitering = True 
                    self.loiter_time = -1

            elif message_type == "MISSION_ITEM_RECHEAD":
                if self.mission_blueprint.is_waypoint(message.seq):
                    self.current_waypoint = message.seq
                    if message.seq == self.final_waypoint:
                        self.target_waypoint = self.final_waypoint
                        self.mission_complete = True
                elif self.mission_blueprint.is_loiter_unlimited_cmd(message.seq):
                    self.loitering = False 
                    self.loiter_time = None
            # TODO: Need to find out if we need to parse STATUSTEXT
            # elif message_type == "STATUSTEXT":
                
    def _is_unlimited_loiter_in_progress(self.statustext_text) -> Tuple[bool, int]:
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

    def move_to_next_waypoint(self) -> bool:
        # move to the next waypoint regardless of what it's doing now
        with self.thread_lock:
            if self.mission_blueprint.is_mission_complete(self.current_waypoint):
                raise MissionCompleteException("Cannot move to the next waypoint. Mission already complete.")
            next_waypoint = self.mission_blueprint.get_next_waypoint(self.current_waypoint)
            if next_waypoint == self.mission_blueprint.get_final_waypoint():
                raise AlreadyInLastWaypointException("There is no next waypoint.")
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

