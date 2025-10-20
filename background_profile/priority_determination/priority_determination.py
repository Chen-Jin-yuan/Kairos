import json
from datetime import datetime
import random
import numpy as np
from scipy.stats import wasserstein_distance
from sklearn.manifold import MDS


def convert_result(result):
    agent_requests = {}
    time_map = {}

    for msg_id, agent_times in result.items():
        for agent, time in agent_times.items():
            req_name = f"{agent}_{msg_id}"
            if agent not in agent_requests:
                agent_requests[agent] = []
            agent_requests[agent].append(req_name)
            time_map[req_name] = time

    return agent_requests, time_map


def agent_wasserstein_mds_sort(agent_requests, time_map):
    agents = list(agent_requests.keys())
    distributions = {}

    # 1
    for agent in agents:
        distributions[agent] = np.array([time_map[req] for req in agent_requests[agent] if req in time_map])

    # 2
    ideal_name = "Ideal"
    ideal_dist = np.zeros(50)
    distributions[ideal_name] = ideal_dist

    # 3
    all_agents = agents + [ideal_name]
    n = len(all_agents)
    distance_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i != j:
                d1 = distributions[all_agents[i]]
                d2 = distributions[all_agents[j]]
                distance_matrix[i, j] = wasserstein_distance(d1, d2)

    # 4
    mds = MDS(n_components=1, dissimilarity='precomputed', random_state=42, normalized_stress="auto")
    positions = mds.fit_transform(distance_matrix).flatten()

    # 5
    ideal_index = all_agents.index(ideal_name)
    ideal_position = positions[ideal_index]

    agent_positions = {
        agent: abs(positions[all_agents.index(agent)] - ideal_position)
        for agent in agents
    }

    # 6
    sorted_agents = sorted(agent_positions.items(), key=lambda x: x[1])
    sorted_agents = [agent for agent, _ in sorted_agents]
    return agent_positions, sorted_agents


def get_priority(agentscope_res, autogen_res, metagpt_res):
    agentscope_agent_requests, agentscope_time_map = convert_result(agentscope_res)
    autogen_agent_requests, autogen_time_map = convert_result(autogen_res)
    metagpt_agent_requests, metagpt_time_map = convert_result(metagpt_res)

    # merge requests
    merged_agent_requests = {}
    merged_agent_requests.update(agentscope_agent_requests)
    merged_agent_requests.update(autogen_agent_requests)
    merged_agent_requests.update(metagpt_agent_requests)

    # merge time_map
    merged_time_map = {}
    merged_time_map.update(agentscope_time_map)
    merged_time_map.update(autogen_time_map)
    merged_time_map.update(metagpt_time_map)

    agent_positions, sorted_agents = agent_wasserstein_mds_sort(merged_agent_requests, merged_time_map)
    print("positions: ", agent_positions)
    print("order: ", sorted_agents)
