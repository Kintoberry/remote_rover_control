from pymavlink import mavutil
# from library import auxiliary_functions as aux
import sys, os

class MissionBlueprint:
    def __init__(self, rover_serial):
        self.rover_serial = rover_serial
        self.mission_items = []
        self.waypoints = None
        self.mission_count = None

    def add_mission_item(self, item):
        self.mission_items.append(item)

    def save_waypoints(self) -> bool:
        if not self.mission_items:
            return False
        self.waypoints = [item for item in self.mission_items if item.command == mavutil.mavlink.MAV_CMD_NAV_WAYPOINT]
        return True
    
   
    def get_commands_related_to_waypoints(self):
        waypoint_commands = [
            mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM,
            mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,
            mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME,
            # Add other waypoint-related commands here
        ]
        return [item for item in self.mission_items if item.command in waypoint_commands]
    
    def download_mission(self):
        # Request the number of mission items
        self.rover_serial.mav.mission_request_list_send(self.rover_serial.target_system, self.rover_serial.target_component)
        self.mission_count = None

        # Wait for the mission count response
        while self.mission_count is None:
            msg = self.rover_serial.recv_match(type="MISSION_COUNT", blocking=True)
            self.mission_count = msg.count

        # Request each mission item
        for i in range(self.mission_count):
            self.rover_serial.mav.mission_request_int_send(self.rover_serial.target_system, self.rover_serial.target_component, i)
            msg = self.rover_serial.recv_match(type="MISSION_ITEM_INT", blocking=True)  # Use MISSION_ITEM_INT instead of MISSION_ITEM
            mission_blueprint.add_mission_item(msg)

        # Send MISSION_ACK after downloading all mission items
        self.rover_serial.mav.mission_ack_send(self.rover_serial.target_system, self.rover_serial.target_component, mavutil.mavlink.MAV_MISSION_ACCEPTED)
        if not self.save_waypoints():
            print("ERROR: cannot set the waypoints")


    def get_number_of_waypoints(self):
        return len(self.waypoints)
    
    def get_mission_item_summary(self):
        for index, item in enumerate(self.mission_items):
            print(f"index: {index}, item: {item}")

    def get_waypoints_summary(self):
        for index, item in enumerate(self.waypoints):
            print(f"index: {index}, item: {item}")

    def is_mission_complete(self, current_sequence):
        return current_sequence >= len(self.mission_items)

    def is_rover_loitering(self, current_command):
        loiter_commands = [
            mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM,
            mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,
            mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME,
            # Add other loiter-related commands here
        ]
        return current_command in loiter_commands

    
    



if __name__ == "__main__":
    # Add the project root directory to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(project_root)
    from library import auxiliary_functions as aux
    from library import utility_functions as helper
    

    portname, baud_rate = aux.find_port_name()
    if portname is None:
        print("ERROR: Cannot find the port for the telemetry radio.")
        exit()
    
    rover_serial = helper.connect_flight_controller(portname, baud_rate)
    if rover_serial is None:
        print("ERROR: connect_flight_controller func returned None")
        exit()

    rover_serial.wait_heartbeat()

    # Create a MissionBlueprint instance and download the mission
    mission_blueprint = MissionBlueprint(rover_serial)
    mission_blueprint.download_mission()

    print("waypoints number: ", mission_blueprint.get_number_of_waypoints())
    print(mission_blueprint.get_waypoints_summary())

    # # Example usage of the MissionBlueprint methods
    # print("Number of waypoints:", mission_blueprint.get_number_of_waypoints())

    # current_sequence = 3  # Assume the rover is currently executing mission sequence 3
    # print("Is mission complete?", mission_blueprint.is_mission_complete(current_sequence))

    # current_command = mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM  # Assume the rover is currently executing a loiter command
    # print("Is rover loitering?", mission_blueprint.is_rover_loitering(current_command))

