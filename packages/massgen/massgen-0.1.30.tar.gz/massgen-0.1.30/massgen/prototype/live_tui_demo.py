"""
Live TUI Demo for MassGen Visualization

Demonstrates real-time visualization of agent coordination using Textual.
Plays back fake coordination events to simulate live execution.

Usage:
    python -m massgen.prototype.live_tui_demo [scenario]

    Where scenario is one of: simple, complex, minimal, chaotic
    Default: complex
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Static


class AgentCard(Static):
    """Widget representing a single agent."""

    status = reactive("waiting")
    answer_count = reactive(0)
    vote_count = reactive(0)
    is_thinking = reactive(False)
    round_num = reactive(0)

    def __init__(self, agent_id: str, backend: str, agent_num: int, **kwargs):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.backend = backend
        self.agent_num = agent_num

    def render(self) -> RenderableType:
        """Render the agent card."""
        # Status emoji and color
        status_map = {
            "waiting": ("⏸", "dim"),
            "streaming": ("⚡", "yellow"),
            "thinking": ("🧠", "cyan"),
            "answered": ("✅", "green"),
            "voted": ("🗳️", "blue"),
            "completed": ("🎉", "magenta"),
            "tool_use": ("🔧", "orange1"),
        }
        emoji, color = status_map.get(self.status, ("❓", "white"))

        # Build status line
        status_text = Text()
        status_text.append(f"{emoji} ", style=color)
        status_text.append(self.status.replace("_", " ").title(), style=f"bold {color}")

        # Build stats
        stats = []
        if self.answer_count > 0:
            stats.append(f"📝 {self.answer_count} answer{'s' if self.answer_count != 1 else ''}")
        if self.vote_count > 0:
            stats.append(f"🗳️ {self.vote_count} vote{'s' if self.vote_count != 1 else ''}")
        if self.round_num > 0:
            stats.append(f"🔄 Round {self.round_num}")

        stats_text = " | ".join(stats) if stats else "No activity yet"

        # Build card content
        table = Table.grid(padding=(0, 1))
        table.add_column(justify="left")

        table.add_row(
            Text(f"Agent {self.agent_num}", style="bold cyan")
        )
        table.add_row(Text(self.backend, style="dim"))
        table.add_row("")
        table.add_row(status_text)
        table.add_row(Text(stats_text, style="dim italic"))

        # Card border color based on status
        border_style = "yellow" if self.is_thinking else color

        return Panel(
            table,
            border_style=border_style,
            title=f"[bold]Agent {self.agent_num}[/bold]",
            title_align="left",
        )

    def update_status(self, new_status: str):
        """Update agent status."""
        self.status = new_status
        self.is_thinking = new_status in ["streaming", "thinking", "tool_use"]

    def increment_answers(self):
        """Increment answer count."""
        self.answer_count += 1

    def increment_votes(self):
        """Increment vote count."""
        self.vote_count += 1

    def set_round(self, round_num: int):
        """Set round number."""
        self.round_num = round_num


class EventFeed(Static):
    """Scrolling feed of recent events."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events: List[Text] = []
        self.max_events = 10

    def add_event(self, event_text: Text):
        """Add an event to the feed."""
        self.events.append(event_text)
        if len(self.events) > self.max_events:
            self.events.pop(0)
        self.refresh()

    def render(self) -> RenderableType:
        """Render the event feed."""
        table = Table.grid(padding=(0, 1))
        table.add_column()

        if not self.events:
            table.add_row(Text("Waiting for events...", style="dim italic"))
        else:
            for event in self.events:
                table.add_row(event)

        return Panel(
            table,
            title="[bold cyan]Recent Events[/bold cyan]",
            border_style="cyan",
        )


class TimelineView(Static):
    """Timeline visualization of agent activity."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_timelines: Dict[str, List[tuple[float, str]]] = {}
        self.start_time: Optional[float] = None
        self.current_time: float = 0

    def add_agent(self, agent_id: str):
        """Add an agent to the timeline."""
        if agent_id not in self.agent_timelines:
            self.agent_timelines[agent_id] = []

    def add_event(self, agent_id: str, timestamp: float, event_type: str):
        """Add an event to an agent's timeline."""
        if self.start_time is None:
            self.start_time = timestamp

        if agent_id not in self.agent_timelines:
            self.add_agent(agent_id)

        relative_time = timestamp - self.start_time
        self.current_time = relative_time
        self.agent_timelines[agent_id].append((relative_time, event_type))
        self.refresh()

    def render(self) -> RenderableType:
        """Render the timeline."""
        if not self.agent_timelines:
            return Panel(
                Text("Timeline will appear here during coordination...", style="dim italic"),
                title="[bold cyan]Timeline[/bold cyan]",
                border_style="cyan",
            )

        # Symbols for events
        event_symbols = {
            "start": "●",
            "answer": "📝",
            "vote": "🗳️",
            "restart": "🔄",
            "tool": "🔧",
            "final": "🎯",
        }

        # Build timeline rows
        table = Table.grid(padding=(0, 1))
        table.add_column(width=10, justify="right")  # Agent name
        table.add_column()  # Timeline

        max_time = max(self.current_time, 1.0)
        timeline_width = 50  # Characters

        for agent_id, events in self.agent_timelines.items():
            # Agent label
            agent_label = Text(agent_id[:10], style="cyan")

            # Build timeline bar
            timeline = Text()
            timeline.append("│")

            # Add events at their positions
            positions = {}
            for rel_time, event_type in events:
                pos = int((rel_time / max_time) * timeline_width)
                if pos not in positions:
                    positions[pos] = []
                positions[pos].append(event_type)

            for i in range(timeline_width):
                if i in positions:
                    # Show event symbol
                    event_types = positions[i]
                    symbol = event_symbols.get(event_types[0], "•")
                    timeline.append(symbol, style="yellow bold")
                else:
                    timeline.append("─", style="dim")

            timeline.append("▶", style="cyan bold")

            table.add_row(agent_label, timeline)

        # Time labels
        time_row = Text(" " * 10)  # Offset for agent names
        time_row.append("│")
        time_markers = [0, max_time * 0.25, max_time * 0.5, max_time * 0.75, max_time]
        for i, t in enumerate(time_markers):
            pos = int(i * (timeline_width / 4))
            time_row.append(f"{t:.0f}s".center(timeline_width // 4), style="dim")

        table.add_row(Text(), Text())
        table.add_row(Text(), time_row)

        return Panel(
            table,
            title=f"[bold cyan]Timeline[/bold cyan] ({self.current_time:.1f}s elapsed)",
            border_style="cyan",
        )


class QuestionPanel(Static):
    """Panel showing the user question."""

    def __init__(self, question: str, **kwargs):
        super().__init__(**kwargs)
        self.question = question

    def render(self) -> RenderableType:
        """Render the question panel."""
        return Panel(
            Text(self.question, style="bold white"),
            title="[bold yellow]Question[/bold yellow]",
            border_style="yellow",
        )


class StatsPanel(Static):
    """Panel showing session statistics."""

    total_events = reactive(0)
    answers_count = reactive(0)
    votes_count = reactive(0)
    restarts_count = reactive(0)
    elapsed_time = reactive(0.0)

    def render(self) -> RenderableType:
        """Render stats panel."""
        stats = Table.grid(padding=(0, 2))
        stats.add_column(justify="right")
        stats.add_column()

        stats.add_row("Events:", Text(str(self.total_events), style="cyan bold"))
        stats.add_row("Answers:", Text(str(self.answers_count), style="green bold"))
        stats.add_row("Votes:", Text(str(self.votes_count), style="blue bold"))
        stats.add_row("Restarts:", Text(str(self.restarts_count), style="yellow bold"))
        stats.add_row("Time:", Text(f"{self.elapsed_time:.1f}s", style="magenta bold"))

        return Panel(
            stats,
            title="[bold]Stats[/bold]",
            border_style="white",
        )


class LiveCoordinationTUI(App):
    """Live TUI visualization of agent coordination."""

    CSS = """
    #main {
        height: 100%;
    }

    #agent-cards {
        height: auto;
        padding: 1;
    }

    #timeline {
        height: auto;
        padding: 1;
    }

    #event-feed {
        height: auto;
        padding: 1;
    }

    #top-section {
        height: auto;
    }

    #stats-panel {
        width: 30;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "toggle_pause", "Pause/Resume"),
        ("r", "restart", "Restart"),
        ("1", "speed_slow", "0.5x Speed"),
        ("2", "speed_normal", "1x Speed"),
        ("3", "speed_fast", "2x Speed"),
    ]

    def __init__(self, session_data: Dict[str, Any], playback_speed: float = 1.0):
        super().__init__()
        self.session_data = session_data
        self.playback_speed = playback_speed
        self.paused = False
        self.agent_cards: Dict[str, AgentCard] = {}
        self.event_feed: Optional[EventFeed] = None
        self.timeline: Optional[TimelineView] = None
        self.stats: Optional[StatsPanel] = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        metadata = self.session_data["session_metadata"]

        yield Header()

        with Container(id="main"):
            # Top section: Question and Stats
            with Horizontal(id="top-section"):
                yield QuestionPanel(metadata["user_prompt"])
                yield StatsPanel(id="stats-panel")

            # Agent cards
            with Horizontal(id="agent-cards"):
                for i, agent_id in enumerate(metadata["agent_ids"]):
                    card = AgentCard(
                        agent_id=agent_id,
                        backend=agent_id,  # In fake data, they're the same
                        agent_num=i + 1,
                    )
                    self.agent_cards[agent_id] = card
                    yield card

            # Timeline
            self.timeline = TimelineView(id="timeline")
            yield self.timeline

            # Event feed
            self.event_feed = EventFeed(id="event-feed")
            yield self.event_feed

        yield Footer()

    def on_mount(self) -> None:
        """Initialize after mounting."""
        self.stats = self.query_one(StatsPanel)

        # Add agents to timeline
        for agent_id in self.session_data["session_metadata"]["agent_ids"]:
            self.timeline.add_agent(agent_id)

        # Start playback
        self.play_events()

    @work(exclusive=True, thread=True)
    def play_events(self):
        """Play back events from the session."""
        import time as time_module

        # Give UI time to render before starting
        time_module.sleep(1.0)

        events = self.session_data["events"]
        start_time = events[0]["timestamp"] if events else 0

        for i, event in enumerate(events):
            if self.paused:
                # Wait while paused
                while self.paused:
                    time_module.sleep(0.1)

            # Calculate delay
            if i > 0:
                time_diff = event["timestamp"] - events[i - 1]["timestamp"]
                delay = time_diff / self.playback_speed
                time_module.sleep(delay)

            # Process event
            self.call_from_thread(self._process_event, event, start_time)

        # Pause at end so user can see final state
        self.call_from_thread(self.notify, "✅ Playback complete! Press 'r' to restart or 'q' to quit")

    def _process_event(self, event: Dict[str, Any], start_time: float):
        """Process a single event (called from worker thread)."""
        event_type = event["event_type"]
        agent_id = event.get("agent_id")
        details = event.get("details", "")
        context = event.get("context", {})

        # Update stats
        self.stats.total_events += 1
        self.stats.elapsed_time = event["timestamp"] - start_time

        # Map event type to display
        if event_type == "new_answer":
            if agent_id and agent_id in self.agent_cards:
                self.agent_cards[agent_id].increment_answers()
                self.agent_cards[agent_id].update_status("answered")
                self.timeline.add_event(agent_id, event["timestamp"], "answer")

            label = context.get("label", "unknown")
            event_text = Text()
            event_text.append("✨ ", style="yellow")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(f" answered {label}", style="white")
            self.event_feed.add_event(event_text)
            self.stats.answers_count += 1

        elif event_type == "vote_cast":
            if agent_id and agent_id in self.agent_cards:
                self.agent_cards[agent_id].increment_votes()
                self.agent_cards[agent_id].update_status("voted")
                self.timeline.add_event(agent_id, event["timestamp"], "vote")

            voted_for_label = context.get("voted_for_label", "unknown")
            event_text = Text()
            event_text.append("🗳️ ", style="blue")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(f" voted for {voted_for_label}", style="white")
            self.event_feed.add_event(event_text)
            self.stats.votes_count += 1

        elif event_type == "status_change":
            if agent_id and agent_id in self.agent_cards:
                # Extract status from details
                if "streaming" in details:
                    self.agent_cards[agent_id].update_status("streaming")
                elif "answered" in details:
                    pass  # Already handled by new_answer
                elif "voted" in details:
                    pass  # Already handled by vote_cast
                elif "completed" in details:
                    self.agent_cards[agent_id].update_status("completed")

        elif event_type == "restart_triggered":
            if agent_id and agent_id in self.agent_cards:
                self.timeline.add_event(agent_id, event["timestamp"], "restart")

            event_text = Text()
            event_text.append("🔄 ", style="yellow bold")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(" triggered restart", style="yellow")
            self.event_feed.add_event(event_text)
            self.stats.restarts_count += 1

        elif event_type == "restart_completed":
            if agent_id and agent_id in self.agent_cards:
                round_num = context.get("agent_round", 0)
                self.agent_cards[agent_id].set_round(round_num)

            event_text = Text()
            event_text.append("✅ ", style="green")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(" restart complete", style="green")
            self.event_feed.add_event(event_text)

        elif event_type == "tool_call":
            if agent_id and agent_id in self.agent_cards:
                self.agent_cards[agent_id].update_status("tool_use")
                self.timeline.add_event(agent_id, event["timestamp"], "tool")

            tool_name = context.get("tool_name", "unknown")
            event_text = Text()
            event_text.append("🔧 ", style="orange1")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(f" using {tool_name}", style="orange1")
            self.event_feed.add_event(event_text)

        elif event_type == "final_answer":
            if agent_id and agent_id in self.agent_cards:
                self.agent_cards[agent_id].update_status("completed")
                self.timeline.add_event(agent_id, event["timestamp"], "final")

            label = context.get("label", "unknown")
            event_text = Text()
            event_text.append("🎯 ", style="magenta bold")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(f" final answer {label}", style="magenta bold")
            self.event_feed.add_event(event_text)

        elif event_type == "final_agent_selected":
            event_text = Text()
            event_text.append("🏆 ", style="yellow bold")
            event_text.append(f"Agent{agent_id[-1] if agent_id else '?'}", style="cyan bold")
            event_text.append(" selected as winner!", style="yellow bold")
            self.event_feed.add_event(event_text)

        elif event_type == "session_start":
            # Initialize all agents
            for aid in self.agent_cards:
                self.agent_cards[aid].update_status("waiting")
                self.timeline.add_event(aid, event["timestamp"], "start")

            event_text = Text()
            event_text.append("🎬 ", style="green bold")
            event_text.append("Coordination started", style="green")
            self.event_feed.add_event(event_text)

        elif event_type == "session_end":
            event_text = Text()
            event_text.append("🎉 ", style="magenta bold")
            event_text.append("Coordination complete!", style="magenta bold")
            self.event_feed.add_event(event_text)

    def action_toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        status = "Paused" if self.paused else "Playing"
        self.notify(f"Playback {status}")

    def action_restart(self):
        """Restart playback."""
        # Reset all state
        for card in self.agent_cards.values():
            card.update_status("waiting")
            card.answer_count = 0
            card.vote_count = 0
            card.round_num = 0

        self.stats.total_events = 0
        self.stats.answers_count = 0
        self.stats.votes_count = 0
        self.stats.restarts_count = 0
        self.stats.elapsed_time = 0

        self.event_feed.events.clear()
        self.timeline.agent_timelines.clear()
        self.timeline.start_time = None
        self.timeline.current_time = 0

        # Restart playback
        self.paused = False
        self.play_events()
        self.notify("Playback restarted")

    def action_speed_slow(self):
        """Set playback speed to 0.5x."""
        self.playback_speed = 0.5
        self.notify("Speed: 0.5x")

    def action_speed_normal(self):
        """Set playback speed to 1x."""
        self.playback_speed = 1.0
        self.notify("Speed: 1x")

    def action_speed_fast(self):
        """Set playback speed to 2x."""
        self.playback_speed = 2.0
        self.notify("Speed: 2x")


def main():
    """Run the live TUI demo."""
    import sys

    # Get scenario from args
    scenario = "complex" if len(sys.argv) < 2 else sys.argv[1]

    # Load fake session data
    session_file = Path(__file__).parent / "fake_sessions" / f"fake_session_{scenario}.json"

    if not session_file.exists():
        print(f"❌ Scenario '{scenario}' not found.")
        print(f"Available scenarios: simple, complex, minimal, chaotic")
        sys.exit(1)

    with open(session_file, "r") as f:
        session_data = json.load(f)

    print(f"🎬 Starting Live TUI Demo with '{scenario}' scenario...")
    print(f"📊 {len(session_data['events'])} events, {len(session_data['session_metadata']['agent_ids'])} agents")
    print(f"⚡ Controls: [p]ause [r]estart [1/2/3]speed [q]uit")
    print()

    # Run the TUI - slower default speed so you can see what's happening
    app = LiveCoordinationTUI(session_data, playback_speed=0.5)  # 0.5x speed to see details
    app.run()


if __name__ == "__main__":
    main()
