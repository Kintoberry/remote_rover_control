import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time
import threading
from library import utility_functions as helper
from library import auxiliary_functions as aux



class Rover:
    def __init__(self) -> None:
        self.thread_lock = threading.Lock()
        self.rover_serial = None
        self.initiated = False
    def initiate(self, reinitiate=False) -> bool:
        # make initial connection here
        with self.thread_lock:
            # Don't repeat initialization process if we already have a serial connection
            if not reinitiate and self.rover_serial is not None:
                return True
            if self.initiated:
                cleanup_resources()
            print("Initiating Rover..")
            portname, baud_rate = aux.find_port_name()
            if portname is None:
                print("ERROR: Cannot find the port for the telemetry radio.")
                return False
            rover_serial = None
            try:
                rover_serial = helper.connect_flight_controller(portname, baud_rate)
            except Exception as e:
                print("e: ", e)
                print("e.args: ", e.args)
                print("e__context__: ", e.__context__)
                exit()
            self.rover_serial = rover_serial
            self.initiated = True
        return True
    
    def cleanup_resources():
        # Call RTL function to put the rover back to the launch point
        # cleanup non-main threads
        pass
    

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
    rover = Rover()
    if rover.initiate():
        print("Rover is connected.")
