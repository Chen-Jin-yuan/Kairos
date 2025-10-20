from abc import ABC, abstractmethod


class BaseDecisionModel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def decide(self, agent_replicas, request, logger):
        pass