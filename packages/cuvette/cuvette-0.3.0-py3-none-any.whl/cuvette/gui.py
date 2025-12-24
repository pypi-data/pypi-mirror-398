import curses
import itertools
import queue
import random
import subprocess
import textwrap
import threading
import time
from typing import Optional, Callable, Union

from cuvette.constants.clusters import CLUSTERS
from cuvette.figlet import Figlet
from cuvette.constants.quotes import HEADER_QUOTES
from cuvette.utils.subproccesses import create_process


class ClusterSelector:
    def __init__(self, max_width=80):
        self.clusters = CLUSTERS
        self.current_selection = 0
        self.figlet = Figlet()
        self.max_width = max_width
        fonts = ["rozzo"]
        random.shuffle(fonts)
        self.figlet.setFont(font=fonts[0])
        self.bg_color = curses.COLOR_BLACK
        self.is_dark_mode = False
        self.final_output_lines = []

    def setup_colors(self):
        # Define colors based on theme
        self.bg_color = curses.COLOR_BLACK if self.is_dark_mode else -1
        if not self.is_dark_mode:
            curses.use_default_colors()

        # Set up color pairs
        curses.init_pair(1, curses.COLOR_GREEN, self.bg_color)  # Regular text
        curses.init_pair(2, curses.COLOR_MAGENTA, self.bg_color)  # Headers/controls
        curses.init_pair(3, curses.COLOR_MAGENTA, self.bg_color)  # Borders
        curses.init_pair(4, curses.COLOR_MAGENTA, self.bg_color)  # Selected item
        curses.init_pair(5, curses.COLOR_MAGENTA, self.bg_color)  # ASCII art

    def draw_ascii_header(self, window):
        max_y, max_x = window.getmaxyx()

        header = self.figlet.renderText("BEAKER")

        # Calculate the width of the ASCII art for centering
        lines = header.split("\n")
        max_width = max(len(line.rstrip()) for line in lines)
        x_offset = (max_x - max_width) // 2

        y = 1
        for line in lines:
            if line.strip():
                try:
                    window.addstr(y, x_offset, line.rstrip(), curses.color_pair(5))
                except curses.error:
                    pass
                y += 1
        return y + 1

    def draw_menu(self, window, start_y: int):
        # Get window dimensions
        max_y, max_x = window.getmaxyx()
        # Use the smaller of max_width or actual terminal width
        display_width = min(self.max_width, max_x)

        # Calculate left offset to center everything
        left_offset = (max_x - display_width) // 2

        # Center the text based on display width
        window.addstr(
            start_y,
            left_offset,
            "Select a Cluster (https://beaker-docs.apps.allenai.org/compute/clusters.html)".center(
                display_width
            ),
            curses.color_pair(2) | curses.A_BOLD,
        )
        window.addstr(start_y + 1, left_offset, "=" * display_width, curses.color_pair(2))

        # Calculate menu dimensions using display width
        menu_width = display_width // 2 - 2

        # Draw the menu box
        for y in range(start_y + 2, max_y - 2):
            window.addstr(y, left_offset, "│" + " " * menu_width + "│", curses.color_pair(3))
        window.addstr(start_y + 2, left_offset, "┌" + "─" * menu_width + "┐", curses.color_pair(3))
        window.addstr(max_y - 2, left_offset, "└" + "─" * menu_width + "┘", curses.color_pair(3))

        # Draw the description box
        desc_x = left_offset + menu_width + 2
        for y in range(start_y + 2, max_y - 2):
            window.addstr(y, desc_x, "│" + " " * menu_width + "│", curses.color_pair(3))
        window.addstr(start_y + 2, desc_x, "┌" + "─" * menu_width + "┐", curses.color_pair(3))
        window.addstr(max_y - 2, desc_x, "└" + "─" * menu_width + "┘", curses.color_pair(3))

        # Draw the clusters
        for idx, cluster in enumerate(self.clusters):
            style = (
                curses.color_pair(4) | curses.A_BOLD
                if idx == self.current_selection
                else curses.color_pair(1)
            )
            window.addstr(
                start_y + 3 + idx,
                left_offset + 2,
                f"{'●' if idx == self.current_selection else '○'} {cluster.name}",
                style,
            )

        # Draw the description
        description = self.clusters[self.current_selection].description
        desc_lines = textwrap.wrap(description, width=menu_width - 4)
        for idx, line in enumerate(desc_lines):
            window.addstr(start_y + 3 + idx, desc_x + 2, line, curses.color_pair(1))

        # Update the controls text to show number key option
        controls = (
            "select [tab] | navigate [up / down] | press [1-8] for GPUs | [q]uit | [t]oggle theme"
        )
        window.addstr(max_y - 1, left_offset, controls.center(display_width), curses.color_pair(2))

    def draw_process_output(
        self,
        window,
        launch_command: Union[str, Callable],
        quick_start_command: str,
        cluster_name: Optional[str | list] = None,
        host_name: Optional[str | list] = None,
        num_gpus: int = 0,
        on_output_line: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[int, list, str], tuple[Optional[str], bool]]] = None,
    ):
        max_y, max_x = window.getmaxyx()

        # Clear screen but keep header
        window.clear()
        header_height = self.draw_ascii_header(window)

        # Center the text based on display width
        max_y, max_x = window.getmaxyx()
        display_width = max_x - 5

        # Wrap the quote text
        quote = random.choice(HEADER_QUOTES)
        wrapped_quote = textwrap.wrap(quote, width=display_width)

        # Display each line of the wrapped quote
        for i, line in enumerate(wrapped_quote):
            window.addstr(header_height + i, 3, line, curses.color_pair(2) | curses.A_ITALIC)
        header_height += len(wrapped_quote)

        # Draw the output box
        box_width = max_x - 6
        box_height = max_y - header_height - 2

        # Draw box borders
        window.addstr(header_height, 2, "┌" + "─" * box_width + "┐", curses.color_pair(3))
        for y in range(header_height + 1, header_height + box_height):
            window.addstr(y, 2, "│" + " " * box_width + "│", curses.color_pair(3))
        window.addstr(
            header_height + box_height, 2, "└" + "─" * box_width + "┘", curses.color_pair(3)
        )

        # Draw quick start command
        window.addstr(
            header_height + 1,
            4,
            f"Quick start command: {quick_start_command}",
            curses.color_pair(2) | curses.A_BOLD,
        )

        # Check Tailscale
        try:
            tailscale_output = subprocess.check_output(
                ["tailscale", "status"], stderr=subprocess.STDOUT, text=True
            )
            if "failed to connect to local Tailscale service" in tailscale_output:
                raise subprocess.CalledProcessError(1, "tailscale status")
        except subprocess.CalledProcessError:
            window.addstr(
                header_height + 1,
                4,
                "Error: Tailscale service is not running!",
                curses.color_pair(1),
            )
            window.addstr(max_y - 1, 2, "Press any key to continue...", curses.color_pair(2))
            window.refresh()
            window.getch()
            return False

        output_queue = queue.Queue()
        spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        last_spin_time = time.time()
        
        process = create_process(launch_command)

        def enqueue_output(out, queue):
            for line in iter(out.readline, ""):
                queue.put(line)
            out.close()

        # Start threads to read stdout and stderr
        threading.Thread(
            target=enqueue_output, args=(process.stdout, output_queue), daemon=True
        ).start()
        threading.Thread(
            target=enqueue_output, args=(process.stderr, output_queue), daemon=True
        ).start()

        # Display output
        lines = []
        max_lines = box_height - 4  # Leave room for header and borders

        window.nodelay(1)  # Make getch non-blocking

        while process.poll() is None or not output_queue.empty():
            try:
                line = output_queue.get_nowait()
                lines.append(line.strip())
                if len(lines) > max_lines:
                    lines.pop(0)

                # Only update the new line instead of clearing everything
                current_line_count = len(lines)
                display_line = lines[-1]
                try:
                    self.add_colored_str(
                        window,
                        header_height + 2 + min(current_line_count - 1, max_lines - 1),
                        4,
                        display_line[: box_width - 6],
                        curses.color_pair(1),
                    )
                except curses.error:
                    pass

                # Call callback if provided
                if on_output_line:
                    on_output_line(display_line)

                # Update spinner every 100ms while process is still running
                current_time = time.time()
                if current_time - last_spin_time > 0.1:
                    try:
                        if process.poll() is None:  # Only show spinner if process is still running
                            window.addstr(
                                max_y - 3,
                                4,
                                f"{next(spinner)} Launching session...",
                                curses.color_pair(2),
                            )
                        else:
                            window.addstr(max_y - 3, 4, "✓ Session launched!", curses.color_pair(2))
                        last_spin_time = current_time
                    except curses.error:
                        pass

                window.refresh()
            except queue.Empty:
                # Update spinner even when there's no output
                current_time = time.time()
                if current_time - last_spin_time > 0.1:
                    try:
                        window.addstr(
                            max_y - 3,
                            4,
                            f"{next(spinner)} Launching session...",
                            curses.color_pair(2),
                        )
                        last_spin_time = current_time
                    except curses.error:
                        pass
                    window.refresh()
                time.sleep(0.01)  # Prevent CPU spinning

            # Check for 'q' key press to allow canceling
            try:
                if window.getch() == ord("q"):
                    process.terminate()
                    return None
            except curses.error:
                pass

        window.nodelay(0)  # Reset to blocking mode

        # Wait for user to press any key before returning
        window.addstr(max_y - 3, 4, "✓ Session launched!    ", curses.color_pair(2))

        # Extract session ID from the output
        session_id = None
        for line in lines:
            if "Starting session" in line:
                session_id = line.split()[2]  # Gets the session ID from "Starting session {id} ..."
                break

        # Call completion callback if provided
        host_name = None
        if on_complete and session_id:
            host_name, port_success = on_complete(process.returncode, lines, session_id)
            if port_success:
                # Handle port update display
                update_port_command = f"bport {session_id}"
                port_output_queue = queue.Queue()
                port_process = subprocess.Popen(
                    update_port_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1,
                    shell=True,
                    executable="/bin/zsh",
                )

                threading.Thread(
                    target=enqueue_output,
                    args=(port_process.stdout, port_output_queue),
                    daemon=True,
                ).start()
                threading.Thread(
                    target=enqueue_output,
                    args=(port_process.stderr, port_output_queue),
                    daemon=True,
                ).start()

                port_lines = lines
                max_port_lines = box_height - 4
                spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
                last_spin_time = time.time()

                window.nodelay(1)

                while port_process.poll() is None or not port_output_queue.empty():
                    try:
                        line = port_output_queue.get_nowait()
                        port_lines.append(line.strip())
                        if len(port_lines) > max_port_lines:
                            port_lines.pop(0)

                        # Display all visible lines
                        for idx, display_line in enumerate(port_lines[-max_port_lines:]):
                            try:
                                window.addstr(
                                    header_height + 3 + idx,
                                    4,
                                    " " * (box_width - 6),
                                    curses.color_pair(1),
                                )
                                self.add_colored_str(
                                    window,
                                    header_height + 3 + idx,
                                    4,
                                    display_line[: box_width - 6],
                                    curses.color_pair(1),
                                )
                            except curses.error:
                                pass

                        current_time = time.time()
                        if current_time - last_spin_time > 0.1:
                            try:
                                if port_process.poll() is None:
                                    window.addstr(
                                        max_y - 3,
                                        4,
                                        f"{next(spinner)} Updating ports...",
                                        curses.color_pair(2),
                                    )
                                last_spin_time = current_time
                            except curses.error:
                                pass

                        window.refresh()
                    except queue.Empty:
                        current_time = time.time()
                        if current_time - last_spin_time > 0.1:
                            try:
                                window.addstr(
                                    max_y - 3,
                                    4,
                                    f"{next(spinner)} Updating ports...",
                                    curses.color_pair(2),
                                )
                                last_spin_time = current_time
                            except curses.error:
                                pass
                            window.refresh()
                        time.sleep(0.01)

                    try:
                        if window.getch() == ord("q"):
                            port_process.terminate()
                            return None
                    except curses.error:
                        pass

                window.nodelay(0)

                if port_process.returncode == 0:
                    window.addstr(
                        max_y - 3, 4, f"✓ Session launched on {host_name}", curses.color_pair(2)
                    )
                else:
                    window.addstr(
                        max_y - 3, 4, f"! Port update failed ({session_id})", curses.color_pair(1)
                    )

        # Store all output lines for later display
        self.final_output_lines = lines

        window.addstr(max_y - 1, 2, "Press any key to continue...", curses.color_pair(2))
        window.refresh()
        window.getch()

        return process.returncode == 0

    def setup(self, stdscr):
        # Setup colors
        curses.start_color()
        self.setup_colors()

        # Set background color based on theme
        if not self.is_dark_mode:
            stdscr.bkgd(" ", curses.color_pair(1))

        # Hide the cursor
        curses.curs_set(0)

    def run_direct(
        self,
        stdscr,
        launch_command,
        quick_start_command,
        cluster_name,
        host_name,
        num_gpus,
        on_output_line,
        on_complete,
    ):
        self.setup(stdscr)
        return self.draw_process_output(
            stdscr,
            launch_command,
            quick_start_command,
            cluster_name,
            host_name,
            num_gpus,
            on_output_line,
            on_complete,
        )

    def run(self, stdscr, on_cluster_selected: Callable):
        self.setup(stdscr)

        while True:
            stdscr.clear()

            # Draw the interface
            header_height = self.draw_ascii_header(stdscr)
            self.draw_menu(stdscr, header_height)

            # Refresh the screen
            stdscr.refresh()

            # Handle input
            key = stdscr.getch()
            if key == ord("q"):
                break
            elif key == ord("t"):
                self.is_dark_mode = not self.is_dark_mode
                self.setup_colors()
            elif key == curses.KEY_UP and self.current_selection > 0:
                self.current_selection -= 1
            elif key == curses.KEY_DOWN and self.current_selection < len(self.clusters) - 1:
                self.current_selection += 1
            # Add number key handling
            elif key in [ord(str(i)) for i in range(1, 9)]:  # Handle keys 1-8
                num_gpus = int(chr(key))
                cluster = self.clusters[self.current_selection]
                on_cluster_selected(stdscr, cluster.clusters, None, num_gpus)
            # Add enter key handling with defaults
            elif key in [ord("\n"), ord(" ")]:
                cluster = self.clusters[self.current_selection]
                # Default to 1 GPU for GPU clusters, 0 for CPU clusters
                num_gpus = 1 if cluster.has_gpus else 0
                on_cluster_selected(stdscr, cluster.clusters, None, num_gpus)

    def parse_ansi_color(self, text):
        # ANSI color code mapping to curses colors
        ansi_to_curses = {
            "30": self.bg_color,
            "31": curses.COLOR_RED,
            "32": curses.COLOR_GREEN,
            "33": curses.COLOR_YELLOW,
            "34": curses.COLOR_BLUE,
            "35": curses.COLOR_MAGENTA,
            "36": curses.COLOR_CYAN,
            "37": curses.COLOR_WHITE,
        }

        parts = []
        current_pos = 0
        current_color = None

        while True:
            # Find next color code
            esc_pos = text.find("\033[", current_pos)
            if esc_pos == -1:
                # Add remaining text with current color
                if current_pos < len(text):
                    parts.append((text[current_pos:], current_color))
                break

            # Add text before escape code
            if esc_pos > current_pos:
                parts.append((text[current_pos:esc_pos], current_color))

            # Find end of escape code
            m_pos = text.find("m", esc_pos)
            if m_pos == -1:
                break

            # Parse color code
            color_code = text[esc_pos + 2 : m_pos]
            if color_code == "00":
                current_color = None
            else:
                current_color = ansi_to_curses.get(color_code)

            current_pos = m_pos + 1

        return parts

    def add_colored_str(self, window, y, x, text, default_color):
        current_x = x
        for text_part, color in self.parse_ansi_color(text):
            try:
                if color is not None:
                    # Create a new color pair for this color if needed
                    pair_num = color + 10  # Offset to avoid conflicts with existing pairs
                    curses.init_pair(pair_num, color, self.bg_color)
                    window.addstr(y, current_x, text_part, curses.color_pair(pair_num))
                else:
                    window.addstr(y, current_x, text_part, default_color)
                current_x += len(text_part)
            except curses.error:
                pass
