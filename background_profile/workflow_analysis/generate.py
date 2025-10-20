import random

class LogEntry:
    def __init__(self, agent_name, upstream, arrive_time, finish_time):
        self.agent_name = agent_name
        self.upstream = upstream
        self.arrive_time = arrive_time
        self.finish_time = finish_time

    def __repr__(self):
        return (f"Log(Agent: {self.agent_name}, Upstream: {self.upstream}, "
                f"Arrive: {self.arrive_time:.1f}, Finish: {self.finish_time:.1f})")


def generate_dynamic_branch_log():
    logs = []
    logs.append(LogEntry('A', None, 0, 1.0))

    if random.choice([True, False]):
        logs.append(LogEntry('B', 'A', 1.1, 2.5))
    else:
        logs.append(LogEntry('C', 'A', 1.1, 3.0))

    return logs


def generate_sequential_log():
    logs = []
    logs.append(LogEntry('A', None, 0, 1.0))
    logs.append(LogEntry('B', 'A', 1.1, 3.0))
    logs.append(LogEntry('C', 'A', 3.1, 4.0))
    logs.append(LogEntry('D', 'A', 4.1, 6.0))
    return logs


def generate_parallel_log():
    logs = []
    logs.append(LogEntry('A', None, 0, 1.0))

    logs.append(LogEntry('B1', 'A', 1.1, 2.0))
    logs.append(LogEntry('B2', 'A', 1.2, 3.0))
    logs.append(LogEntry('B3', 'A', 1.3, 5.0))

    logs.append(LogEntry('C', 'B2', 3.1, 5.0))

    logs.append(LogEntry('D', 'B3', 5.1, 6.0))
    return logs

def generate_simple_chain_log():
    logs = []

    logs.append(LogEntry('A', None, 0, 1.0))
    logs.append(LogEntry('B', 'A', 1.1, 2.0))
    logs.append(LogEntry('C', 'B', 2.1, 3.0))
    return logs

def generate_feedback_loop_log():
    logs = []

    logs.append(LogEntry('A', None, 0, 1.0))
    logs.append(LogEntry('B', 'A', 1.1, 2.0))
    logs.append(LogEntry('C', 'B', 2.1, 3.0))
    logs.append(LogEntry('B', 'C', 3.1, 4.0))
    return logs

def generate_complex_log():
    logs = []

    logs.append(LogEntry('A', None, 0, 1.0))

    logs.append(LogEntry('B1', 'A', 1.1, 2.5))
    logs.append(LogEntry('B2', 'A', 1.2, 4.0))
    logs.append(LogEntry('B3', 'A', 1.3, 3.0))


    logs.append(LogEntry('E', 'B2', 4.1, 5.0))
    logs.append(LogEntry('F', 'B2', 5.1, 6.0))

    logs.append(LogEntry('C', 'A', 4.1, 5.5))

    logs.append(LogEntry('G', 'C', 5.6, 6.5))
    logs.append(LogEntry('H1', 'C', 6.6, 7.7))
    logs.append(LogEntry('H2', 'C', 6.7, 8.2))

    logs.append(LogEntry('D', 'A', 5.6, 7.5))

    logs.append(LogEntry('I', 'D', 7.6, 8.5))

    return logs