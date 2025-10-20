import random
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
from generate import LogEntry

class WorkflowGenerator:
    def __init__(self, start_node='A'):
        self.start_node = start_node
        self.logical_graph = defaultdict(list)
        self.logs = []
        self.node_finish_times = {}
        self._node_name_counter = 1
        self._add_log_entry(start_node, None, 0.0)

    def _get_next_node_name(self):
        if self._node_name_counter >= 26:
            return None
        name = chr(ord('A') + self._node_name_counter)
        self._node_name_counter += 1
        return name
    def _random_duration(self):
        return random.uniform(1.0, 3.0)

    def _add_log_entry(self, agent_name, upstream_instance, start_time):
        instance_name = f"{agent_name}"

        delay = random.uniform(0.1, 0.5)
        arrive_time = start_time + delay
        finish_time = arrive_time + self._random_duration()

        self.logs.append(LogEntry(instance_name, upstream_instance, arrive_time, finish_time))
        self.node_finish_times[instance_name] = finish_time
        return instance_name, finish_time

    def add_sequence(self, source_node_name, new_nodes_names):
        source_instance = f"{source_node_name}"
        current_trigger_time = self.node_finish_times[source_instance]

        for name in new_nodes_names:
            self.logical_graph[source_node_name].append((name, 'sequential'))
            _, new_finish_time = self._add_log_entry(name, source_instance, current_trigger_time)
            current_trigger_time = new_finish_time
        return self

    def add_parallel(self, source_node_name, new_nodes_names):
        source_instance = f"{source_node_name}"
        start_time = self.node_finish_times[source_instance]

        for name in new_nodes_names:
            self.logical_graph[source_node_name].append((name, 'parallel'))
            self._add_log_entry(name, source_instance, start_time)
        return self

    def add_feedback(self, source_node_name, target_node_name):
        self.logical_graph[source_node_name].append((target_node_name, 'feedback'))

        source_instance = f"{source_node_name}"
        start_time = self.node_finish_times[source_instance]

        self._add_log_entry(target_node_name, source_instance, start_time)
        return self

    def add_parallel_then_sequence(self, source_node_name, parallel_nodes, sequential_nodes):
        source_instance = f"{source_node_name}"
        parallel_start_time = self.node_finish_times[source_instance]

        parallel_finish_times = []
        for name in parallel_nodes:
            self.logical_graph[source_node_name].append((name, 'parallel'))
            _, finish_time = self._add_log_entry(name, source_instance, parallel_start_time)
            parallel_finish_times.append(finish_time)

        sync_time = max(parallel_finish_times)

        current_trigger_time = sync_time
        for name in sequential_nodes:
            self.logical_graph[source_node_name].append((name, 'sequential'))
            _, new_finish_time = self._add_log_entry(name, source_instance, current_trigger_time)
            current_trigger_time = new_finish_time

        return self

    def get_logs(self):
        return self.logs

    def auto_generate(self):
        total_depth = random.randint(2, 5)

        nodes_at_current_level = [self.start_node]
        for depth in range(total_depth - 1):
            print(f"depth: {depth}")
            nodes_at_next_level = []
            for parent_node in nodes_at_current_level:
                if self._node_name_counter >= 26:
                    continue

                num_children = random.choice([1, 2, 3])

                if self._node_name_counter + num_children > 26:
                    num_children = 26 - self._node_name_counter

                if num_children <= 0: continue

                children_names = [self._get_next_node_name() for _ in range(num_children)]

                possible_patterns = []
                if num_children == 1:
                    possible_patterns = ['sequential']
                elif num_children == 2:
                    possible_patterns = ['sequential', 'parallel']
                elif num_children >= 3:
                    possible_patterns = ['sequential', 'parallel', 'parallel_then_sequence']

                pattern = random.choice(possible_patterns)

                if pattern == 'parallel':
                    self.add_parallel(parent_node, children_names)
                elif pattern == 'sequential':
                    self.add_sequence(parent_node, children_names)
                elif pattern == 'parallel_then_sequence':
                    num_parallel = num_children - 1
                    parallel_part = children_names[:num_parallel]
                    sequential_part = children_names[num_parallel:]
                    self.add_parallel_then_sequence(parent_node, parallel_part, sequential_part)

                nodes_at_next_level.extend(children_names)

            if not nodes_at_next_level: break
            nodes_at_current_level = nodes_at_next_level

        return self

    def visualize_graph(self, title='Generated Workflow Logic', ax=None):
        show_plot = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 7))
            show_plot = True

        graph_to_plot = self.logical_graph
        all_nodes_in_graph = set(graph_to_plot.keys())
        for children_list in graph_to_plot.values():
            for child, _ in children_list:
                all_nodes_in_graph.add(child)

        feedback_edges = set()
        path, visited = set(), set()

        def detect_cycle_util(node):
            path.add(node)
            visited.add(node)
            for neighbor_tuple in graph_to_plot.get(node, []):
                neighbor, _ = neighbor_tuple
                if neighbor in path:
                    feedback_edges.add((node, neighbor))
                elif neighbor not in visited:
                    detect_cycle_util(neighbor)
            path.remove(node)

        for node in all_nodes_in_graph:
            if node not in visited:
                detect_cycle_util(node)

        layout_graph = {u: [v_tuple[0] for v_tuple in v_list if (u, v_tuple[0]) not in feedback_edges]
                        for u, v_list in graph_to_plot.items()}

        inv_graph = defaultdict(list)
        for parent, children_list in layout_graph.items():
            for child in children_list:
                inv_graph[child].append(parent)

        node_levels = {}

        def get_level(node):
            if node in node_levels: return node_levels[node]
            parents = inv_graph.get(node, [])
            level = 0 if not parents else 1 + max(get_level(p) for p in parents)
            node_levels[node] = level
            return level

        for node in all_nodes_in_graph:
            if node not in node_levels: get_level(node)

        nodes_by_level = defaultdict(list)
        for node, level in node_levels.items():
            nodes_by_level[level].append(node)
        pos = {}
        for level, nodes in nodes_by_level.items():
            nodes.sort()
            y_coords = np.linspace(len(nodes) / 2, -len(nodes) / 2, len(nodes))
            for i, node in enumerate(nodes):
                pos[node] = (level, y_coords[i])

        ax.set_title(title, fontsize=16)

        for u, edges in graph_to_plot.items():
            children_count = sum(1 for _, etype in edges)

            for v_tuple in edges:
                v, edge_type = v_tuple
                if u not in pos or v not in pos: continue

                pos_u, pos_v = pos[u], pos[v]

                arrow_color = "gray"
                connectionstyle = "arc3,rad=0.1"

                if edge_type == 'parallel':
                    arrow_color = "red"
                elif edge_type == 'sequential':
                    if children_count > 1:
                        arrow_color = "blue"
                    else:
                        arrow_color = "gray"
                elif edge_type == 'feedback':
                    arrow_color = "gray"
                    connectionstyle = f"angle3,angleA=-90,angleB=180"

                ax.annotate("", xy=pos_v, xytext=pos_u,
                            arrowprops=dict(arrowstyle="->", lw=2, color=arrow_color,
                                            shrinkA=30, shrinkB=30,
                                            connectionstyle=connectionstyle))

        for node, (x, y) in pos.items():
            ax.scatter(x, y, s=30 ** 2, color='skyblue', ec='black', zorder=5)
            ax.text(x, y, node, ha='center', va='center', fontsize=10, weight='bold', zorder=10)

        all_y_coords = [y for x, y in pos.values()]
        y_min, y_max = min(all_y_coords), max(all_y_coords)
        ax.set_ylim(y_min - 0.8, y_max + 0.8)

        max_level = max(node_levels.values()) if node_levels else 0
        ax.set_xlim(-0.5, max_level + 0.5)
        ax.axis('off')
        if show_plot: plt.show()

