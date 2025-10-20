import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.balancer import MetricsManager

if __name__ == "__main__":
    metrics_manager = MetricsManager(['http://{ip}:{port1}/generate', 'http://{ip}:{port2}/generate'])
    while True:
        input()
        print(metrics_manager.get_all_metrics())
        print(metrics_manager.get_llm_metrics('http://{ip}:{port1}/generate'))
