from classes.mission_blueprint import MissionBlueprint
import threading

class MissionManager:
    def __init__(self, rover_serial):
        self.rover_serial = rover_serial
        self.mission_blueprint = MissionBlueprint(self.rover_serial)
        self.current_waypoint = None
        self.current_command = None
        self.loitering_waypoint = None
        self.lock = threading.lock()

    def load_mission(self):
        self.mission_blueprint.download_mission()

    def move_to_next_waypoint(self):
        # move to the next waypoint regardless of what it's doing now
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

