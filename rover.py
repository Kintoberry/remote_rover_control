import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time
import threading


class Rover:
    def __init__(self) -> None:
        self.thread_lock = threading.Lock()
        self.rover_serial = None
    def initiate(self) -> bool:
        # make initial connection here
        with self.thread_lock:
            print("Initiating Rover..")
        return True

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

    def exposed_hello(self, name):
        return f"Hello, {name}!"

    def exposed_add(self, a, b):
        return a + b

    def exposed_subtract(self, a, b):
        return a - b

    def exposed_get_counter(self):
        return self.counter_thread.counter

def main():
    rover = Rover()
    rover_service = RoverService(rover_instance=rover)
    server = ThreadedServer(service=rover_service, port=20000)
    print("Rover Service has started..")
    server.start()

if __name__ == "__main__":
    main()
