import threading
import queue
import time

def worker_consumer(terminate_event, message_queue, condition):
    while not terminate_event.is_set():
        with condition:
            while message_queue.empty() and not terminate_event.is_set():
                condition.wait()
            if terminate_event.is_set():
                break
            message = message_queue.get()
            condition.notify_all()
        # Continue processing 
        # ...
        # ...

def worker_producer(terminate_event, message_queue, condition):
    while not terminate_event.is_set():
        message = from_external_resource()
        with condition:
            while message_queue.full() and not terminate_event.is_set():
                condition.wait()
            if terminate_event.is_set():
                break
            message_queue.put(message)
            condition.notify_all()
        # Continue processing
        # ...
        # ...

def main():
    terminate_event = threading.Event()
    condition = threading.Condition()
    message_queue = queue.Queue(maxsize=1000)
    
    workers = []
    workers.append(threading.Thread(target=worker_consumer, daemon=True, 
                args=(terminate_event, message_queue, condition)))
    workers.append(threading.Thread(target=worker_producer, daemon=True, 
                args=(terminate_event, message_queue, condition)))
    
    for worker in workers:
        worker.start()
    
    # imitate main process running for awhile
    time.sleep(100)

    # terminate worker threads
    terminate_event.set()
    condition.notify_all()

    while any(worker.is_alive() for worker in workers):
        for worker in workers:
            worker.join(timeout=1)