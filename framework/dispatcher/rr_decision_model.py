from .base_decision_model import BaseDecisionModel

class RRDecisionModel(BaseDecisionModel):
    def __init__(self):
        self.last_sent = 0

    def decide(self, agent_replicas, buffer_queue, logger):
        if agent_replicas:
            replica_ids = list(agent_replicas.keys())
            num_replicas = len(replica_ids)

            while buffer_queue:
                request = buffer_queue.pop(0)

                selected_replica_id = replica_ids[self.last_sent % num_replicas]

                agent_replicas[selected_replica_id]["queue"].enqueue(request)

                logger.log(f"'RRDecisionModel' Request id={request.get_id()}, service_name={request.get_service_name()} "
                            f"sent to Replica ID: {selected_replica_id}")

                self.last_sent += 1
