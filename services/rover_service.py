import rpyc
from rpyc.utils.server import ThreadedServer
from classes import Rover


class RoverService(rpyc.Service):
    def __init__(self, rover_instance):
        super().__init__()
        self.rover = rover_instance

    def on_connect(self, conn):
        pass
    
    def on_disconnect(self, conn):
        pass
    
    def exposed_initiate_rover(self) -> bool:
        isInitialized = self.rover.initiate()
        if isInitialized:
            return True
        return False


def main():
    rover = Rover()
    rover_service = RoverService(rover_instance=rover)
    server = ThreadedServer(service=rover_service, port=20000)
    print("Rover Service has started..")
    server.start()

if __name__ == "__main__":
    main()




