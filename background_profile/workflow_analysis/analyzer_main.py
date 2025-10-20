from analyzer import WorkflowAnalyzer
from generate import *
from auto_generator import WorkflowGenerator
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def demo():
    dynamic_logs = generate_dynamic_branch_log()
    analyzer1 = WorkflowAnalyzer(dynamic_logs)
    analyzer1.analyze()
    analyzer1.print_report()
    analyzer1.plot_workflow_summary()
    analyzer1.plot_dependency_dag(title='Workflow Example')

    sequential_logs = generate_sequential_log()
    analyzer2 = WorkflowAnalyzer(sequential_logs)
    analyzer2.analyze()
    analyzer2.print_report()
    analyzer2.plot_workflow_summary()
    analyzer2.plot_dependency_dag(title='Workflow Example')

    parallel_logs = generate_parallel_log()
    analyzer3 = WorkflowAnalyzer(parallel_logs)
    analyzer3.analyze()
    analyzer3.print_report()
    analyzer3.plot_workflow_summary()
    analyzer3.plot_dependency_dag(title='Workflow Example')

    chain_logs = generate_simple_chain_log()
    analyzer4 = WorkflowAnalyzer(chain_logs)
    analyzer4.analyze()
    analyzer4.print_report()
    analyzer4.plot_workflow_summary()
    analyzer4.plot_dependency_dag(title='Workflow Example')

    loop_logs = generate_feedback_loop_log()
    analyzer5 = WorkflowAnalyzer(loop_logs)
    analyzer5.analyze()
    analyzer5.print_report()
    analyzer5.plot_workflow_summary()
    analyzer5.plot_dependency_dag(title='Workflow Example')

    complex_logs = generate_complex_log()
    analyzer_complex = WorkflowAnalyzer(complex_logs)
    analyzer_complex.analyze()
    analyzer_complex.print_report()
    analyzer_complex.plot_workflow_summary()
    analyzer_complex.plot_dependency_dag(title='Complex Workflow Example')

def auto():
    fig = plt.figure(figsize=(32, 18))
    fig.suptitle('Workflow Generation & Analysis Dashboard', fontsize=22, weight='bold')
    gs = gridspec.GridSpec(2, 2, figure=fig)

    gs_left = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[:, 0], height_ratios=[1, 1])
    ax_blueprint = fig.add_subplot(gs_left[0])
    ax_reconstructed = fig.add_subplot(gs_left[1])

    gs_right = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[:, 1], height_ratios=[2, 1])
    ax_gantt = fig.add_subplot(gs_right[0])
    ax_concurrency = fig.add_subplot(gs_right[1], sharex=ax_gantt)

    auto_generator = WorkflowGenerator()
    auto_generator.auto_generate()
    generated_logs = auto_generator.get_logs()
    for log in generated_logs:
        print(log)

    auto_generator.visualize_graph(title='Automatically Generated Workflow', ax=ax_blueprint)

    analyzer = WorkflowAnalyzer(generated_logs)
    analyzer.analyze()
    analyzer.print_report()
    analyzer.plot_workflow_summary(axes=(ax_gantt, ax_concurrency))
    analyzer.plot_dependency_dag(title='Workflow Analysis', ax=ax_reconstructed)

    plt.setp(ax_gantt.get_xticklabels(), visible=False)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("auto_workflow.png", dpi=400)

if __name__ == "__main__":
    demo()