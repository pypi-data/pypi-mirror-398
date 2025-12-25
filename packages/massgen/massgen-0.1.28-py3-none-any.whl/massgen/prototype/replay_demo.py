"""
Terminal Replay Demo for MassGen Visualization

Post-execution replay with event navigation and inspection.
Step through coordination events with full control.

Usage:
    python -m massgen.prototype.replay_demo [scenario]

    Where scenario is one of: simple, complex, minimal, chaotic
    Default: simple
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Static


class EventViewer(Static):
    """Displays details of the current event."""

    current_event_idx = reactive(0)

    def __init__(self, events: List[Dict[str, Any]], **kwargs):
        super().__init__(**kwargs)
        self.events = events

    def render(self) -> RenderableType:
        """Render the current event details."""
        if not self.events or self.current_event_idx >= len(self.events):
            return Panel(
                Text("No event to display", style="dim italic"),
                title="Event Details",
                border_style="cyan",
            )

        event = self.events[self.current_event_idx]
        event_type = event["event_type"]
        agent_id = event.get("agent_id", "N/A")
        details = event.get("details", "")
        context = event.get("context", {})
        timestamp = event.get("timestamp", 0)

        # Build event details table
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", justify="right")
        table.add_column()

        # Event type with emoji
        emoji_map = {
            "session_start": "🎬",
            "session_end": "🎉",
            "iteration_start": "🔄",
            "iteration_end": "✅",
            "new_answer": "✨",
            "vote_cast": "🗳️",
            "restart_triggered": "🔄",
            "restart_completed": "✅",
            "tool_call": "🔧",
            "final_answer": "🎯",
            "final_agent_selected": "🏆",
            "status_change": "📊",
            "context_received": "📋",
        }
        emoji = emoji_map.get(event_type, "•")

        table.add_row("Type:", Text(f"{emoji} {event_type}", style="yellow bold"))
        table.add_row("Agent:", Text(agent_id if agent_id != "N/A" else "System", style="cyan"))
        table.add_row("Time:", Text(f"{timestamp:.2f}s", style="magenta"))
        table.add_row("")
        table.add_row("Details:", Text(details, style="white"))

        # Show relevant context fields
        if event_type == "new_answer":
            label = context.get("label", "unknown")
            table.add_row("")
            table.add_row("Label:", Text(label, style="green bold"))

        elif event_type == "vote_cast":
            voted_for = context.get("voted_for_label", "unknown")
            reason = context.get("reason", "")
            available = context.get("available_answers", [])

            table.add_row("")
            table.add_row("Voted For:", Text(voted_for, style="green bold"))
            table.add_row("Reason:", Text(reason, style="italic"))
            table.add_row("Available:", Text(", ".join(available), style="dim"))

        elif event_type == "restart_triggered":
            affected = context.get("affected_agents", [])
            table.add_row("")
            table.add_row("Affected:", Text(", ".join(affected), style="yellow"))

        elif event_type == "restart_completed":
            round_num = context.get("agent_round", 0)
            table.add_row("")
            table.add_row("New Round:", Text(str(round_num), style="cyan bold"))

        elif event_type == "tool_call":
            tool_name = context.get("tool_name", "unknown")
            table.add_row("")
            table.add_row("Tool:", Text(tool_name, style="orange1 bold"))

        elif event_type == "context_received":
            answer_labels = context.get("available_answer_labels", [])
            table.add_row("")
            table.add_row("Context:", Text(", ".join(answer_labels) if answer_labels else "Empty", style="cyan"))

        # Show iteration and round
        table.add_row("")
        iteration = context.get("iteration", 0)
        round_num = context.get("round", 0)
        table.add_row("Iteration:", Text(f"{iteration}", style="blue"))
        table.add_row("Round:", Text(f"{round_num}", style="blue"))

        title = f"[bold]Event {self.current_event_idx + 1} / {len(self.events)}[/bold]"
        return Panel(table, title=title, border_style="cyan")

    def next_event(self):
        """Go to next event."""
        if self.current_event_idx < len(self.events) - 1:
            self.current_event_idx += 1
            return True
        return False

    def prev_event(self):
        """Go to previous event."""
        if self.current_event_idx > 0:
            self.current_event_idx -= 1
            return True
        return False

    def first_event(self):
        """Go to first event."""
        self.current_event_idx = 0

    def last_event(self):
        """Go to last event."""
        self.current_event_idx = len(self.events) - 1


class ProgressBar(Static):
    """Visual progress bar showing position in event sequence."""

    current_position = reactive(0)
    total_events = reactive(1)

    def render(self) -> RenderableType:
        """Render the progress bar."""
        if self.total_events == 0:
            return Text()

        bar_width = 50
        filled = int((self.current_position / max(self.total_events - 1, 1)) * bar_width)

        bar = Text()
        bar.append("[", style="dim")
        bar.append("=" * filled, style="cyan")
        if filled < bar_width:
            bar.append("●", style="cyan bold")
            bar.append("─" * (bar_width - filled - 1), style="dim")
        bar.append("]", style="dim")

        percentage = int((self.current_position / max(self.total_events - 1, 1)) * 100)
        bar.append(f" {percentage}%", style="cyan")

        return bar


class AgentStatusGrid(Static):
    """Grid showing current status of all agents."""

    current_event_idx = reactive(0)

    def __init__(self, events: List[Dict[str, Any]], agent_ids: List[str], **kwargs):
        super().__init__(**kwargs)
        self.events = events
        self.agent_ids = agent_ids

    def render(self) -> RenderableType:
        """Render agent status grid."""
        # Calculate current state based on events up to current index
        agent_states = {aid: {"status": "waiting", "answers": 0, "votes": 0, "round": 0} for aid in self.agent_ids}

        for i in range(self.current_event_idx + 1):
            event = self.events[i]
            event_type = event["event_type"]
            agent_id = event.get("agent_id")
            context = event.get("context", {})

            if not agent_id or agent_id not in agent_states:
                continue

            if event_type == "new_answer":
                agent_states[agent_id]["answers"] += 1
                agent_states[agent_id]["status"] = "answered"
            elif event_type == "vote_cast":
                agent_states[agent_id]["votes"] += 1
                agent_states[agent_id]["status"] = "voted"
            elif event_type == "status_change":
                details = event.get("details", "")
                if "streaming" in details:
                    agent_states[agent_id]["status"] = "thinking"
                elif "completed" in details:
                    agent_states[agent_id]["status"] = "completed"
            elif event_type == "restart_completed":
                agent_states[agent_id]["round"] = context.get("agent_round", 0)

        # Build grid
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold")
        table.add_column()
        table.add_column()
        table.add_column()

        table.add_row(
            Text("Agent", style="bold underline"),
            Text("Status", style="bold underline"),
            Text("Answers", style="bold underline"),
            Text("Votes", style="bold underline"),
        )

        for i, agent_id in enumerate(self.agent_ids):
            state = agent_states[agent_id]
            status = state["status"]

            # Status emoji and color
            status_map = {
                "waiting": ("⏸", "dim"),
                "thinking": ("🧠", "yellow"),
                "answered": ("✅", "green"),
                "voted": ("🗳️", "blue"),
                "completed": ("🎉", "magenta"),
            }
            emoji, color = status_map.get(status, ("❓", "white"))

            status_text = Text()
            status_text.append(f"{emoji} ", style=color)
            status_text.append(status, style=color)

            table.add_row(
                Text(f"Agent {i+1}", style="cyan bold"),
                status_text,
                Text(str(state["answers"]), style="green"),
                Text(str(state["votes"]), style="blue"),
            )

        return Panel(table, title="[bold]Agent Status[/bold]", border_style="green")


class SessionInfo(Static):
    """Display session metadata."""

    def __init__(self, metadata: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.metadata = metadata

    def render(self) -> RenderableType:
        """Render session info."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", justify="right")
        table.add_column()

        table.add_row("Question:", Text(self.metadata.get("user_prompt", "N/A"), style="yellow"))
        table.add_row("Agents:", Text(str(len(self.metadata.get("agent_ids", []))), style="cyan"))

        start_time = self.metadata.get("start_time", 0)
        end_time = self.metadata.get("end_time", 0)
        duration = end_time - start_time if end_time > start_time else 0

        table.add_row("Duration:", Text(f"{duration:.1f}s", style="magenta"))
        table.add_row("Winner:", Text(self.metadata.get("final_winner", "TBD"), style="green bold"))

        return Panel(table, title="[bold]Session Info[/bold]", border_style="yellow")


class ReplayTUI(App):
    """Terminal replay interface for coordination sessions."""

    CSS = """
    #main {
        height: 100%;
    }

    #top-section {
        height: auto;
    }

    #middle-section {
        height: 1fr;
    }

    #bottom-section {
        height: auto;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("right", "next", "Next Event"),
        ("left", "prev", "Previous Event"),
        ("l", "next", "Next"),
        ("h", "prev", "Previous"),
        ("j", "next", "Next"),
        ("k", "prev", "Previous"),
        ("g", "first", "First Event"),
        ("G", "last", "Last Event"),
        ("space", "toggle_play", "Play/Pause"),
    ]

    def __init__(self, session_data: Dict[str, Any]):
        super().__init__()
        self.session_data = session_data
        self.event_viewer: Optional[EventViewer] = None
        self.progress_bar: Optional[ProgressBar] = None
        self.agent_grid: Optional[AgentStatusGrid] = None
        self.playing = False

    def compose(self) -> ComposeResult:
        """Compose the replay TUI."""
        metadata = self.session_data["session_metadata"]
        events = self.session_data["events"]

        yield Header()

        with Container(id="main"):
            # Top: Session info
            with Container(id="top-section"):
                yield SessionInfo(metadata)

            # Middle: Agent status and event details
            with Horizontal(id="middle-section"):
                self.agent_grid = AgentStatusGrid(events, metadata["agent_ids"])
                yield self.agent_grid

                self.event_viewer = EventViewer(events)
                yield self.event_viewer

            # Bottom: Progress bar
            with Container(id="bottom-section"):
                self.progress_bar = ProgressBar()
                self.progress_bar.total_events = len(events)
                self.progress_bar.current_position = 0
                yield self.progress_bar

        yield Footer()

    def action_next(self):
        """Go to next event."""
        if self.event_viewer.next_event():
            self._update_position()

    def action_prev(self):
        """Go to previous event."""
        if self.event_viewer.prev_event():
            self._update_position()

    def action_first(self):
        """Go to first event."""
        self.event_viewer.first_event()
        self._update_position()

    def action_last(self):
        """Go to last event."""
        self.event_viewer.last_event()
        self._update_position()

    def action_toggle_play(self):
        """Toggle auto-play."""
        self.playing = not self.playing
        if self.playing:
            self.set_interval(1.0, self._auto_advance)
            self.notify("Auto-play enabled")
        else:
            self.notify("Auto-play disabled")

    def _auto_advance(self):
        """Auto-advance to next event."""
        if self.playing:
            if not self.event_viewer.next_event():
                self.playing = False
                self.notify("Reached end of replay")
            else:
                self._update_position()

    def _update_position(self):
        """Update progress bar and agent grid."""
        self.progress_bar.current_position = self.event_viewer.current_event_idx
        self.agent_grid.current_event_idx = self.event_viewer.current_event_idx


def main():
    """Run the replay demo."""
    import sys

    # Get scenario from args
    scenario = "simple" if len(sys.argv) < 2 else sys.argv[1]

    # Load fake session data
    session_file = Path(__file__).parent / "fake_sessions" / f"fake_session_{scenario}.json"

    if not session_file.exists():
        print(f"❌ Scenario '{scenario}' not found.")
        print(f"Available scenarios: simple, complex, minimal, chaotic")
        sys.exit(1)

    with open(session_file, "r") as f:
        session_data = json.load(f)

    print(f"🎬 Starting Terminal Replay Demo with '{scenario}' scenario...")
    print(f"📊 {len(session_data['events'])} events, {len(session_data['session_metadata']['agent_ids'])} agents")
    print()

    # Run the TUI
    app = ReplayTUI(session_data)
    app.run()


if __name__ == "__main__":
    main()
