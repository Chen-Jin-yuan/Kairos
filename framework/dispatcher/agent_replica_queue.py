import threading

from .status import AgentReplicaStatus


class AgentReplicaQueue:
    def __init__(self, replica_name, message_handler, logger):
        self.replica_name = replica_name
        self.queue = []
        self.status = AgentReplicaStatus.READY
        self.message_handler = message_handler 
        self.queue_lock = threading.Lock()
        self.status_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.logger = logger
        threading.Thread(target=self.process_queue).start()
        self.logger.log(f"{self.replica_name} queue start")

    def set_status(self, status):
        with self.status_lock:
            self.status = status
        self.logger.log(f"update {self.replica_name} queue status to {status}")

    def is_ready(self):
        with self.status_lock:
            return self.status == AgentReplicaStatus.READY

    def enqueue(self, request):
        with self.queue_lock:
            self.queue.append(request)

    def dequeue(self):
        request = None
        with self.queue_lock:
            if self.queue:
                request = self.queue.pop(0)
        return request

    def process_queue(self):
        self.logger.log(f"{self.replica_name} queue process thread start")
        while not self.stop_event.is_set():
            if self.is_ready():
                request = self.dequeue()
                if request:
                    self.message_handler.send(message=request, target_name=self.replica_name)
                    self.logger.log(f"'AgentReplicaQueue' Sent request to agent replica {self.replica_name}, id={request.get_id()}")
                    self.set_status(AgentReplicaStatus.BUSY)
        
        self.logger.log(f"{self.replica_name} queue process thread stop")

    def stop(self):
        self.stop_event.set()
