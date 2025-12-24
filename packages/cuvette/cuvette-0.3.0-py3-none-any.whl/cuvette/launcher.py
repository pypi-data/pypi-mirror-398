import argparse
import curses
import os
import sys
from typing import Optional

from cuvette.gui import ClusterSelector
from cuvette.session import ExperimentLauncher, Launcher, SessionLauncher

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

USE_SESSSIONS = True


def create_launcher(
    cluster_name: Optional[str | list] = None,
    host_name: Optional[str | list] = None,
    num_gpus: int = 0,
) -> Launcher:
    if USE_SESSSIONS:
        return SessionLauncher(cluster_name, host_name, num_gpus)
    return ExperimentLauncher(cluster_name, host_name, num_gpus)


def _print_final_output(selector):
    """Print final output lines if available."""
    if hasattr(selector, "final_output_lines"):
        for line in selector.final_output_lines:
            print(line)


def main():
    try:
        parser = argparse.ArgumentParser(description="Beaker Launch Tool")
        parser.add_argument("-c", "--clusters", nargs="+", help="Cluster names")
        parser.add_argument("-H", "--hosts", nargs="+", help="Host names")
        parser.add_argument("-g", "--gpus", type=int, help="Number of GPUs")
        args = parser.parse_args()

        selector = ClusterSelector(max_width=100)

        if args.clusters or args.hosts:
            # Direct launch with command line arguments
            num_gpus = args.gpus or 0
            launcher = create_launcher(
                args.clusters, 
                args.hosts, 
                num_gpus
            )

            success = curses.wrapper(
                selector.run_direct,
                launcher.launch_command,
                launcher.quick_start_command,
                args.clusters,
                args.hosts,
                num_gpus,
                on_output_line=None,
                on_complete=launcher.on_complete,
            )
            if success:
                _print_final_output(selector)
        else:
            # Interactive menu mode
            def run_interactive(stdscr):
                def on_cluster_selected_internal(stdscr_window, cluster_name, host_name, num_gpus):
                    launcher = create_launcher(
                        cluster_name, 
                        host_name, 
                        num_gpus
                    )
                    selector.draw_process_output(
                        stdscr_window,
                        launcher.launch_command,
                        launcher.quick_start_command,
                        cluster_name,
                        host_name,
                        num_gpus,
                        on_output_line=None,
                        on_complete=launcher.on_complete,
                    )

                selector.run(stdscr, on_cluster_selected_internal)

            curses.wrapper(run_interactive)
            _print_final_output(selector)
    except (KeyboardInterrupt, curses.error):
        sys.exit(0)  # Exit cleanly on Ctrl+C


if __name__ == "__main__":
    main()
