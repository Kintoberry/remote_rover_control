import rpyc
from rpyc.utils.server import ThreadedServer
from classes import Rover, MissionManager, MissionBlueprint, QueueManager
from classes.custom_exceptions import ExistingSerialConnectionException
from library import auxiliary_functions as aux


class RoverService(rpyc.Service):
    def __init__(self, rover_instance):
        super().__init__()
        self.rover.instance = rover_instance

    def on_connect(self, conn):
        pass
    
    def on_disconnect(self, conn):
        pass
    
    def exposed_initiate_rover(self) -> bool:
        isInitialized = self.rover.initiate()
        if isInitialized:
            return True
        return False
    
    def exposed_connect_to_rover(self):
        try:
            rover_serial = aux.connect_to_rover()
            self.rover_instance.set_rover_serial(rover_serial)
            return {"status_code": 200, "message": "Rover is successfully initialized."}
        except ExistingSerialConnectionException as e:
            return {"status_code": 400, "message": str(e)}  # Bad Request
        except Exception as e:
            return {"status_code": 500, "message": str(e)}  # Internal Server Error


def main():
    queue_manager = QueueManager()
    mission_blueprint = MissionBlueprint()
    mission_manager = MissionManager(queue_manager, mission_blueprint)
    rover = Rover(queue_manager, mission_manager)
    
    rover_service = RoverService(rover_instance=rover)
    server = ThreadedServer(service=rover_service, port=20000)
    print("Rover Service has started..")
    server.start()

if __name__ == "__main__":
    main()




