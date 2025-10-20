from enum import Enum


class AgentReplicaStatus(Enum):
    READY = 1
    BUSY = 2
    DOWN = 3