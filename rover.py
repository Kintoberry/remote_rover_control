import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time
from library import utility_functions as helper
from library import auxiliary_functions as aux
import workers


class Rover:
    def __init__(self) -> None:
        self.thread_lock = threading.Lock()
        self.rover_serial = None
        self.rover_initiated = False
        self.threads_initiated = False
        self.worker_threads = None
        self.threads_terminate_event = None

    def initiate(self, reinitiate=False) -> bool:
        # make initial connection here
        with self.thread_lock:
            # Don't repeat initialization process if we already have a serial connection
            if not reinitiate and self.rover_serial is not None:
                return True
            if self.rover_initiated:
                self._cleanup_resources()
                pass
            if not self._connect_to_rover():
                return False
            
            self._initiate_threads()
            self.initiated = True
        return True
    
    def _connect_to_rover(self) -> bool:
        print("Initiating Rover..")

        portname, baud_rate = aux.find_port_name()
        if portname is None:
            print("ERROR: Cannot find the port for the telemetry radio.")
            return False
        
        rover_serial = helper.connect_flight_controller(portname, baud_rate)
        if rover_serial is None:
            print("ERROR: connect_flight_controller func returned None")
            return False
        self.rover_serial = rover_serial

        return True
    
    def _initiate_threads(self):
        if self.threads_initiated:
            print("ERROR: worker threads are already initiated.")
            return
        
        self.worker_threads, self.threads_terminate_event = workers.run(self.rover_serial)
        for thread in self.worker_threads:
            thread.start()
    
        self.threads_initiated = True

    def _kill_threads(self):
        self.threads_terminate_event.set()
        while any(thread.is_alive() for thread in self.worker_threads):
            for thread in self.worker_threads:
                thread.join(timeout=1)
    
    # TODO: needs to be implemented
    def _cleanup_resources(self):
        # Call RTL function to put the rover back to the launch point
        if self.threads_initiated:
            self._kill_threads()
            self.threads_initiated = False
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




