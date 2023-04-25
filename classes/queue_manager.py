from queue import Queue

class QueueManager():
    def __init__(self):
        self.queues = {
            "sync_cmd": Queue(maxsize=10),
            "sync_cmd_ack": Queue(maxsize=10),
            "async_cmd": Queue(maxsize=100),
            "async_cmd_ack": Queue(maxsize=100),
            "mission_message": Queue(maxsize=100),
            "measurement_request": Queue(maxsize=10),
            "logging": Queue(maxsize=1000)
        }
        
    def put(self, queue_name: str, item, **kwargs):
        self._check_key_error(queue_name)
        self.queues[queue_name].put(item, **kwargs)

    def get(self, queue_name: str, **kwargs):
        self._check_key_error(queue_name)
        return self.queues[queue_name].get(**kwargs)
    
    def empty(self, queue_name: str) -> bool:
        self._check_key_error(queue_name)
        return self.queues[queue_name].empty()
    
    def full(self, queue_name: str) -> bool:
        self._check_key_error(queue_name)
        return self.queues[queue_name].full()
    
    def _check_key_error(self, queue_name: str):
        if queue_name not in self.queues:
            raise KeyError(f"Queue '{queue_name}' not found.")
        