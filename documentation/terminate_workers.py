import threading
import queue
import time

def worker_consumer(terminate_event, message_queue):
    while not terminate_event.is_set():
        message = None
        try:
            message = message_queue.get(block=True, timeout=1)
        except queue.Empty:
            continue
        # Continue processing 
				# ...
				# ...

def worker_producer(terminate_event, message_queue):
    while not terminate_event.is_set():
        message = from_external_resource()
        if message is not None:
            message_queue.put(message, block=True)
        # Continue processing
        # ...
        # ...

def main():
    terminate_event = threading.Event()
    message_queue = queue.Queue(maxsize=1000)
    
    workers = []
    workers.append(threading.Thread(target=worker_consumer, daemon=True, 
                args=(terminate_event, message_queue)))
    workers.append(threading.Thread(target=worker_producer, daemon=True, 
                args=(terminate_event, message_queue)))
    
    for worker in workers:
        worker.start()
    
    # imitate main process running for awhile
    time.sleep(100)

    # terminate worker threads
    terminate_event.set()

    while any(worker.is_alive() for worker in workers):
        for worker in workers:
            worker.join(timeout=1)