import threading
from library import utility_functions as helper
from library import auxiliary_functions as aux
from workers import workers
from .queue_manager import AbstractQueueManager
from .custom_exceptions import ExistingSerialConnectionException


class Rover:
    def __init__(self, queue_manager: AbstractQueueManager, mission_manager) -> None:
        self.queue_manager = queue_manager
        self.mission_manager = mission_manager
        self.thread_lock = threading.Lock()
        self.rover_serial = None
        self.rover_initiated = False
        self.threads_initiated = False
        self.worker_threads = None
        self.threads_terminate_event = None

    # Setter Injection 
    def set_rover_serial(self, rover_serial, force=False):
        if not self.rover_serial or force:
            self.rover_serial = rover_serial
            self._inject_rover_serial_to_mission_manager()
        else:
            raise ExistingSerialConnectionException("Serial connection to the UGV already exists. Use `force` parameter if you must.")

    def _inject_rover_serial_to_mission_manager(self):
        self.mission_manager.set_rover_serial(self.rover_serial, force=True)

    def initiate(self, reinitiate=False) -> bool:
        # make initial connection here
        with self.thread_lock:
            # Don't repeat initialization process if we already have a serial connection
            if not reinitiate and self.rover_serial is not None:
                print("Rover is already initalized.")
                return True
            
            if reinitiate and self.rover_initiated:
                self._cleanup_resources()

            # if not self._connect_to_rover():
            #     return False
            
            self._initiate_threads()
            self.initiated = True
        return True
    
    # def _connect_to_rover(self) -> bool:
    #     print("Initiating Rover..")

    #     portname, baud_rate = aux.find_port_name()
    #     if portname is None:
    #         print("ERROR: Cannot find the port for the telemetry radio.")
    #         return False
        
    #     rover_serial = helper.connect_flight_controller(portname, baud_rate)
    #     if rover_serial is None:
    #         print("ERROR: connect_flight_controller func returned None")
    #         return False
    #     self.rover_serial = rover_serial

    #     return True
    
    def _initiate_threads(self):
        if self.threads_initiated:
            print("ERROR: worker threads are already initiated.")
            return
        
        self.worker_threads, self.threads_terminate_event = workers.run(self.rover_serial. self.queue_manager)
        for thread in self.worker_threads:
            thread.start()
    
        self.threads_initiated = True
        print("Worker Threads are initiated")

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
    
