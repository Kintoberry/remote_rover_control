from classes import QueueManager
from library import message_handlers as handler
from collections import deque


class MessageDistributor():
    def __init__(self, queue_manager: QueueManager) -> None:
        self.queue_manager = queue_manager
        self.mission_message_types = [
            "MISSION_CURRENT",
            "MISSION_ITEM_REACHED",
            "STATUSTEXT"
        ]
        self.sync_mav_cmd = deque()

    def distribute(self, message):
        message_type = message.get_type()

        if message_type in self.mission_message_types:
            self.queue_manager.put("mission_message", message, block=True)
        
        if message_type == "COMMAND_ACK":
            if self.sync_mav_cmd:
                if message.command == self.sync_mav_cmd[0]:
                    self.queue_manager.put("sync_cmd_ack", self.sync_mav_cmd.popleft(), block=True)
            else:
                self.queue_manager.put("async_cmd_ack", message.command, block=True)
        
        # put every message received into `logging` queue
        self.queue_manager.put("logging", message)

    def register_sync_cmd(self, mav_cmd: int):
        self.sync_mav_cmd.append(mav_cmd)
        

# target_path = get_messages_folder_path(generate_message_filename())
#         with open(target_path, 'w') as fp:
#             json.dump(messages, fp, indent=2)    
#             fp.flush()    
#             pass

# def get_messages_folder_path(message_file_name: str) -> str:
#     return os.path.join(os.path.dirname(os.path.abspath(__file__)), "captured_messages", "mission_records",message_file_name)
