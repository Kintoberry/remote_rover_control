import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time

class CounterThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.running = True

    def run(self):
        while self.running:
            self.counter += 1
            time.sleep(1)

    def stop(self):
        self.running = False

class ChildService(rpyc.Service):
    def on_connect(self, conn):
        self.counter_thread = CounterThread()
        self.counter_thread.start()

    def on_disconnect(self, conn):
        self.counter_thread.stop()
        self.counter_thread.join()

    def exposed_hello(self, name):
        return f"Hello, {name}!"

    def exposed_add(self, a, b):
        return a + b

    def exposed_subtract(self, a, b):
        return a - b

    def exposed_get_counter(self):
        return self.counter_thread.counter

def main():
    t = ThreadedServer(ChildService, port=18860)
    t.start()

if __name__ == "__main__":
    main()
