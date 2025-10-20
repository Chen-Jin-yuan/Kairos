from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.patches as mpatches
import numpy as np
import math


class WorkflowAnalyzer:
    def __init__(self, logs):
        self.logs = sorted(logs, key=lambda log: log.arrive_time)
        self.agent_details = {log.agent_name: log for log in self.logs}
        self.graph = defaultdict(list)
        self.analysis_report = []
        self.analysis_results = {}

    def build_graph(self):
        for log in self.logs:
            if log.upstream:
                self.graph[log.upstream].append(log.agent_name)

    def analyze(self):
        self.build_graph()

        if not self.graph:
            self.analysis_report.append("检测到单节点工作流或无依赖关系。")
            if self.logs:
                self.analysis_report.append(f"根节点: {self.logs[0].agent_name}")
            return

        for upstream_agent, downstream_agents in self.graph.items():
            downstream_agents.sort(key=lambda agent: self.agent_details[agent].arrive_time)

            if len(downstream_agents) == 1:
                downstream_agent = downstream_agents[0]
                self.analysis_report.append(
                    f"检测到简单链接: {upstream_agent} -> {downstream_agent}"
                )
                edge = (upstream_agent, downstream_agents[0])
                self.analysis_results[edge] = 'simple'
                continue

            child_is_parallel = {child: False for child in downstream_agents}

            events = []
            for agent_name in downstream_agents:
                details = self.agent_details[agent_name]
                events.append((details.arrive_time, 1, agent_name))
                events.append((details.finish_time, -1, agent_name))
            events.sort()

            running_siblings = set()
            for _, event_type, agent_name in events:
                if event_type == 1:
                    if running_siblings:
                        child_is_parallel[agent_name] = True
                        for sibling in running_siblings:
                            child_is_parallel[sibling] = True
                    running_siblings.add(agent_name)
                else:
                    running_siblings.remove(agent_name)

            for child, is_parallel in child_is_parallel.items():
                pattern = 'parallel' if is_parallel else 'sequential'
                self.analysis_results[(upstream_agent, child)] = pattern

    def print_report(self):
        if not self.analysis_report:
            return

        for line in self.analysis_report:
            print(line)

        if not self.graph:
            print("{}")
        for k, v in self.graph.items():
            print(f"  '{k}': {v}")
        print("-----------------------\n")

    def plot_workflow_summary(self, axes=None):
        show_plot = False

        if axes is None:
            fig, (ax_gantt, ax_concurrency) = plt.subplots(
                2, 1, sharex=True, figsize=(12, 8),
                gridspec_kw={'height_ratios': [3, 1.5]}
            )
            fig.suptitle('Overall Workflow Execution Summary', fontsize=16, y=0.97)
            show_plot = True
        else:
            ax_gantt, ax_concurrency = axes

        parallel_intervals = []

        for upstream, downstream_agents in self.graph.items():
            if len(downstream_agents) < 2:
                continue

            local_events = []
            for agent in downstream_agents:
                details = self.agent_details[agent]
                local_events.append((details.arrive_time, 1))
                local_events.append((details.finish_time, -1))
            local_events.sort()

            active_local_tasks = 0
            for i in range(len(local_events) - 1):
                start_time = local_events[i][0]
                end_time = local_events[i + 1][0]
                active_local_tasks += local_events[i][1]

                if active_local_tasks >= 2:
                    parallel_intervals.append((start_time, end_time))


        ax_gantt.set_title('Task Execution Span (Gantt Chart)')
        all_agents = [log.agent_name for log in self.logs]
        y_ticks = range(len(all_agents))

        for i, log in enumerate(self.logs):
            duration = log.finish_time - log.arrive_time
            ax_gantt.barh(y=i, width=duration, left=log.arrive_time, height=0.6,
                          edgecolor='black', color='dodgerblue', alpha=0.9)

            if log.upstream:
                label_text = f"{log.agent_name} ← {log.upstream}"
            else:
                label_text = f"{log.agent_name} (Root)"
            ax_gantt.text(log.arrive_time + duration / 2, i, label_text,
                          ha='center', va='center', color='white', fontweight='bold')

        ax_gantt.set_yticks(y_ticks)
        ax_gantt.set_yticklabels(all_agents)
        ax_gantt.set_ylabel('Agents')
        ax_gantt.grid(axis='x', linestyle=':', alpha=0.7)

        ax_concurrency.set_title('Concurrent Tasks Profile')

        all_events = []
        for log in self.logs:
            all_events.append((log.arrive_time, 1))
            all_events.append((log.finish_time, -1))
        all_events.sort()

        plot_times = [0.0]
        plot_counts = [0]
        active_tasks = 0
        for time, event_type in all_events:
            if time > plot_times[-1]:
                plot_times.append(time)
                plot_counts.append(active_tasks)
            active_tasks += event_type
            plot_times.append(time)
            plot_counts.append(active_tasks)

        plot_times_np = np.array(plot_times)
        plot_counts_np = np.array(plot_counts)

        ax_concurrency.plot(plot_times_np, plot_counts_np, drawstyle='steps-post', color='black', linewidth=1.5)

        ax_concurrency.fill_between(plot_times_np, plot_counts_np, step='post', alpha=0.3, color='royalblue')

        for start, end in parallel_intervals:
            ax_concurrency.fill_between(plot_times_np, plot_counts_np, step='post', alpha=0.5, color='crimson',
                                        where=(plot_times_np >= start) & (plot_times_np <= end))

        legend_patches = [
            mpatches.Patch(color='royalblue', alpha=0.4, label='General Concurrency'),
            mpatches.Patch(color='crimson', alpha=0.6, label='Parallel Block Concurrency')
        ]
        ax_concurrency.legend(handles=legend_patches, loc='upper left')

        ax_concurrency.set_ylabel('Concurrent Tasks')
        ax_concurrency.set_xlabel('Time')
        ax_concurrency.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax_concurrency.set_ylim(bottom=0)
        ax_concurrency.grid(axis='both', linestyle=':', alpha=0.6)

        if show_plot:
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            plt.show()

    def plot_dependency_dag(self, title='Workflow Dependency DAG', ax=None):
        show_plot = False

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 7))
            show_plot = True

        if not self.graph: self.build_graph()


        inv_graph = defaultdict(list)
        for parent, children in self.graph.items():
            for child in children:
                inv_graph[child].append(parent)


        node_levels = {}
        visiting = set()

        def get_level(node):
            if node in node_levels:
                return node_levels[node]

            if node in visiting:
                return 0

            visiting.add(node)

            parents = inv_graph.get(node, [])
            if not parents:
                level = 0
            else:
                level = 1 + get_level(parents[0])

            visiting.remove(node)

            node_levels[node] = level
            return level

        all_nodes = list(self.agent_details.keys())
        for node in all_nodes: get_level(node)
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
        color_map = {'parallel': 'crimson', 'sequential': 'royalblue', 'simple': 'gray'}
        node_size_for_shrink = 30

        for upstream, downstream_agents in self.graph.items():
            sorted_children = sorted(downstream_agents, key=lambda agent: self.agent_details[agent].arrive_time)
            step_counter = 1
            i = 0
            while i < len(sorted_children):
                child = sorted_children[i]
                edge = (upstream, child)
                pattern = self.analysis_results.get(edge)

                if pattern == 'simple':
                    pos_u, pos_v = pos[upstream], pos[child]
                    ax.annotate("", xy=pos_v, xytext=pos_u,
                                arrowprops=dict(arrowstyle="->", lw=2, color=color_map['simple'],
                                                shrinkA=node_size_for_shrink, shrinkB=node_size_for_shrink,
                                                connectionstyle="arc3,rad=0.1"), zorder=1)
                    i += 1
                    continue

                if pattern == 'parallel':
                    parallel_batch = []
                    batch_midpoints = []
                    j = i
                    while j < len(sorted_children):
                        next_child_in_batch = sorted_children[j]
                        if self.analysis_results.get((upstream, next_child_in_batch)) == 'parallel':
                            parallel_batch.append(next_child_in_batch)
                            j += 1
                        else:
                            break

                    for parallel_child in parallel_batch:
                        pos_u, pos_v = pos[upstream], pos[parallel_child]
                        ax.annotate("", xy=pos_v, xytext=pos_u,
                                    arrowprops=dict(arrowstyle="->", lw=2, color=color_map['parallel'],
                                                    shrinkA=node_size_for_shrink, shrinkB=node_size_for_shrink,
                                                    connectionstyle="arc3,rad=0.1"), zorder=1)

                    middle_index = int(math.ceil((len(parallel_batch) - 1) / 2))
                    middle_child = parallel_batch[middle_index]

                    pos_u_mid, pos_v_mid = pos[upstream], pos[middle_child]
                    label_pos = ((pos_u_mid[0] + pos_v_mid[0]) / 2, (pos_u_mid[1] + pos_v_mid[1]) / 2)

                    label_text = str(step_counter)
                    ax.plot(label_pos[0], label_pos[1], marker='o', markersize=16,
                            markeredgecolor='black', markerfacecolor='white', zorder=2)
                    ax.text(label_pos[0], label_pos[1], label_text, ha='center', va='center',
                            fontsize=10, weight='bold', zorder=3)

                    i = j

                elif pattern == 'sequential':
                    pos_u, pos_v = pos[upstream], pos[child]
                    ax.annotate("", xy=pos_v, xytext=pos_u,
                                arrowprops=dict(arrowstyle="->", lw=2, color=color_map['sequential'],
                                                shrinkA=node_size_for_shrink, shrinkB=node_size_for_shrink,
                                                connectionstyle="arc3,rad=0.1"), zorder=1)
                    label_text = str(step_counter)
                    mid_point = ((pos_u[0] + pos_v[0]) / 2, (pos_u[1] + pos_v[1]) / 2)
                    ax.plot(mid_point[0], mid_point[1], marker='o', markersize=16,
                            markeredgecolor='black', markerfacecolor='white', zorder=2)
                    ax.text(mid_point[0], mid_point[1], label_text, ha='center', va='center',
                            fontsize=10, weight='bold', zorder=3)
                    i += 1

                step_counter += 1

        for node, (x, y) in pos.items():
            ax.scatter(x, y, s=node_size_for_shrink ** 2, color='skyblue', ec='black', zorder=5)
            ax.text(x, y, node, ha='center', va='center', fontsize=10, weight='bold', zorder=10)


        all_y_coords = [y for x, y in pos.values()]
        y_min, y_max = min(all_y_coords), max(all_y_coords)
        ax.set_ylim(y_min - 0.8, y_max + 0.8)

        max_level = max(node_levels.values()) if node_levels else 0
        ax.set_xlim(-0.5, max_level + 0.5)
        ax.axis('off')
        if show_plot:
            plt.show()