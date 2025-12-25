"""
Fake Data Generator for MassGen Visualization Prototypes

Generates realistic coordination events for testing visualization components.
"""

import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class FakeAgent:
    """Represents a fake agent."""

    agent_id: str
    backend: str
    think_time_range: tuple[float, float]  # Min, max thinking time in seconds


class FakeCoordinationSession:
    """Generates fake coordination events."""

    def __init__(
        self,
        num_agents: int = 3,
        question: str = "What are the pros and cons of renewable energy?",
        enable_restarts: bool = True,
        enable_tool_calls: bool = True,
        restart_probability: float = 0.3,
        tool_call_probability: float = 0.4,
        seed: Optional[int] = None,
    ):
        """
        Args:
            num_agents: Number of agents (2-5)
            question: User question
            enable_restarts: Whether agents can restart
            enable_tool_calls: Whether agents can use tools
            restart_probability: Probability of agent triggering restart
            tool_call_probability: Probability of agent using tools
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

        self.question = question
        self.num_agents = max(2, min(5, num_agents))
        self.enable_restarts = enable_restarts
        self.enable_tool_calls = enable_tool_calls
        self.restart_probability = restart_probability
        self.tool_call_probability = tool_call_probability

        # Create fake agents
        backends = ["gpt5nano", "gemini2.5flash", "grok3mini", "claude3.5sonnet", "gpt4o"]
        self.agents = [
            FakeAgent(
                agent_id=backends[i % len(backends)],
                backend=backends[i % len(backends)],
                think_time_range=(2.0, 8.0),
            )
            for i in range(self.num_agents)
        ]

        # Track session state
        self.events: List[Dict[str, Any]] = []
        self.current_time = time.time()
        self.iteration = 0
        self.agent_rounds = {agent.agent_id: 0 for agent in self.agents}
        self.agent_answers = {agent.agent_id: [] for agent in self.agents}
        self.agent_votes = []
        self.final_winner: Optional[str] = None

    def generate_session(self) -> Dict[str, Any]:
        """Generate complete coordination session."""
        # Session start
        self._add_event("session_start", None, f"Started with agents: {[a.agent_id for a in self.agents]}")

        # First iteration - all agents provide initial answers
        self._start_iteration()

        # All agents get context and think
        for agent in self.agents:
            self._agent_receives_context(agent, [])
            self._agent_thinks_and_answers(agent)

        # Voting round
        self._voting_round()

        # Possible restart cascade
        if self.enable_restarts and random.random() < self.restart_probability:
            restart_agent = random.choice(self.agents)
            self._agent_triggers_restart(restart_agent)

            # Affected agents restart
            for agent in self.agents:
                if agent != restart_agent:
                    self._agent_completes_restart(agent)

            # New iteration after restart
            self._end_iteration("restart_triggered")
            self._start_iteration()

            # Agents provide new answers with context
            available_answers = {a.agent_id: self.agent_answers[a.agent_id][-1] for a in self.agents if self.agent_answers[a.agent_id]}
            for agent in self.agents:
                self._agent_receives_context(agent, list(available_answers.keys()))
                self._agent_thinks_and_answers(agent, with_tools=self.enable_tool_calls)

            # Another voting round
            self._voting_round()

        # Select winner
        self._end_iteration("voting_complete")
        winner = self._select_winner()

        # Final presentation
        self._final_presentation(winner)

        # Session end
        self._add_event("session_end", None, f"Session completed in {self.current_time - self.events[0]['timestamp']:.1f}s")

        return {
            "session_metadata": {
                "user_prompt": self.question,
                "agent_ids": [a.agent_id for a in self.agents],
                "start_time": self.events[0]["timestamp"],
                "end_time": self.current_time,
                "final_winner": self.final_winner,
            },
            "events": self.events,
        }

    def _add_event(
        self,
        event_type: str,
        agent_id: Optional[str],
        details: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Add an event to the session."""
        if context is None:
            context = {}

        context["iteration"] = self.iteration
        context["round"] = self.agent_rounds.get(agent_id, 0) if agent_id else max(self.agent_rounds.values(), default=0)

        event = {
            "timestamp": self.current_time,
            "event_type": event_type,
            "agent_id": agent_id,
            "details": details,
            "context": context,
        }
        self.events.append(event)

    def _advance_time(self, duration: float):
        """Advance simulation time."""
        self.current_time += duration

    def _start_iteration(self):
        """Start a new iteration."""
        self.iteration += 1
        available_labels = []
        for agent in self.agents:
            if self.agent_answers[agent.agent_id]:
                agent_num = self.agents.index(agent) + 1
                answer_num = len(self.agent_answers[agent.agent_id])
                available_labels.append(f"agent{agent_num}.{answer_num}")

        self._add_event(
            "iteration_start",
            None,
            f"Starting coordination iteration {self.iteration}",
            {"iteration": self.iteration, "available_answers": available_labels},
        )
        self._advance_time(0.1)

    def _end_iteration(self, reason: str):
        """End current iteration."""
        self._add_event(
            "iteration_end",
            None,
            f"Iteration {self.iteration} ended: {reason}",
            {"iteration": self.iteration, "end_reason": reason},
        )
        self._advance_time(0.1)

    def _agent_receives_context(self, agent: FakeAgent, available_agent_ids: List[str]):
        """Agent receives context."""
        # Build answer labels
        answer_labels = []
        for aid in available_agent_ids:
            if self.agent_answers[aid]:
                agent_idx = next(i for i, a in enumerate(self.agents) if a.agent_id == aid)
                agent_num = agent_idx + 1
                answer_num = len(self.agent_answers[aid])
                answer_labels.append(f"agent{agent_num}.{answer_num}")

        anon_ids = [f"agent{self.agents.index(a) + 1}" for aid in available_agent_ids for a in self.agents if a.agent_id == aid]

        self._add_event(
            "context_received",
            agent.agent_id,
            f"Received context with {len(available_agent_ids)} answers",
            {
                "available_answers": anon_ids,
                "available_answer_labels": answer_labels,
                "answer_count": len(available_agent_ids),
                "has_conversation_history": False,
            },
        )
        self._advance_time(0.1)

    def _agent_thinks_and_answers(self, agent: FakeAgent, with_tools: bool = False):
        """Agent thinks and provides answer."""
        # Status change to streaming
        self._add_event("status_change", agent.agent_id, "Changed to status: streaming")

        # Simulate thinking time
        think_time = random.uniform(*agent.think_time_range)
        self._advance_time(think_time)

        # Tool calls (if enabled)
        if with_tools and random.random() < self.tool_call_probability:
            num_tools = random.randint(1, 3)
            tool_names = ["web_search", "calculate", "analyze_data", "summarize", "translate"]
            for _ in range(num_tools):
                tool = random.choice(tool_names)
                self._add_event(
                    "tool_call",
                    agent.agent_id,
                    f"Using tool: {tool}",
                    {"tool_name": tool},
                )
                self._advance_time(random.uniform(0.5, 2.0))

        # Provide answer
        agent_num = self.agents.index(agent) + 1
        answer_num = len(self.agent_answers[agent.agent_id]) + 1
        label = f"agent{agent_num}.{answer_num}"

        answer_content = self._generate_fake_answer(agent, answer_num)
        self.agent_answers[agent.agent_id].append(answer_content)

        self._add_event(
            "new_answer",
            agent.agent_id,
            f"Provided answer {label}",
            {"label": label},
        )
        self._advance_time(0.5)

        # Status change to answered
        self._add_event("status_change", agent.agent_id, "Changed to status: answered")
        self._advance_time(0.1)

    def _voting_round(self):
        """All agents vote."""
        for agent in self.agents:
            # Status change to streaming (voting)
            self._add_event("status_change", agent.agent_id, "Changed to status: streaming")
            self._advance_time(random.uniform(1.0, 3.0))

            # Vote for someone (potentially themselves)
            voted_for = random.choice(self.agents)
            agent_num = self.agents.index(voted_for) + 1
            answer_num = len(self.agent_answers[voted_for.agent_id])
            voted_label = f"agent{agent_num}.{answer_num}" if answer_num > 0 else "unknown"

            available_labels = []
            for a in self.agents:
                if self.agent_answers[a.agent_id]:
                    num = self.agents.index(a) + 1
                    ans_num = len(self.agent_answers[a.agent_id])
                    available_labels.append(f"agent{num}.{ans_num}")

            reason = random.choice([
                "Most comprehensive answer",
                "Better structured response",
                "More accurate information",
                "Clearer explanation",
                "Best addresses the question",
            ])

            self.agent_votes.append({
                "voter": agent.agent_id,
                "voted_for": voted_for.agent_id,
                "voted_label": voted_label,
                "reason": reason,
            })

            self._add_event(
                "vote_cast",
                agent.agent_id,
                f"Voted for {voted_label}",
                {
                    "voted_for": voted_for.agent_id,
                    "voted_for_label": voted_label,
                    "reason": reason,
                    "available_answers": available_labels,
                },
            )
            self._advance_time(0.5)

            # Status change to voted
            self._add_event("status_change", agent.agent_id, "Changed to status: voted")
            self._advance_time(0.1)

    def _agent_triggers_restart(self, agent: FakeAgent):
        """Agent triggers a restart."""
        affected = [a.agent_id for a in self.agents if a != agent]
        self._add_event(
            "restart_triggered",
            agent.agent_id,
            f"Triggered restart affecting {len(affected)} agents",
            {
                "affected_agents": affected,
                "triggering_agent": agent.agent_id,
            },
        )
        self._advance_time(0.5)

    def _agent_completes_restart(self, agent: FakeAgent):
        """Agent completes restart."""
        self.agent_rounds[agent.agent_id] += 1
        new_round = self.agent_rounds[agent.agent_id]

        self._add_event(
            "restart_completed",
            agent.agent_id,
            f"Completed restart - now in round {new_round}",
            {"agent_round": new_round},
        )
        self._advance_time(0.3)

    def _select_winner(self) -> FakeAgent:
        """Select winner based on votes."""
        # Count votes
        vote_counts = {agent.agent_id: 0 for agent in self.agents}
        for vote in self.agent_votes:
            vote_counts[vote["voted_for"]] += 1

        # Find winner
        max_votes = max(vote_counts.values())
        winners = [aid for aid, count in vote_counts.items() if count == max_votes]
        winner_id = winners[0]  # First in case of tie

        winner = next(a for a in self.agents if a.agent_id == winner_id)
        self.final_winner = winner_id

        # Get all answers
        all_answers = {}
        for agent in self.agents:
            if self.agent_answers[agent.agent_id]:
                agent_num = self.agents.index(agent) + 1
                answer_num = len(self.agent_answers[agent.agent_id])
                label = f"agent{agent_num}.{answer_num}"
                all_answers[label] = self.agent_answers[agent.agent_id][-1]

        vote_summary = ", ".join([f"{aid}: {count}" for aid, count in vote_counts.items()])

        self._add_event(
            "final_agent_selected",
            winner_id,
            "Selected as final presenter",
            {
                "vote_summary": vote_summary,
                "all_answers": list(all_answers.keys()),
                "answers_for_context": all_answers,
            },
        )
        self._advance_time(0.5)

        return winner

    def _final_presentation(self, winner: FakeAgent):
        """Winner provides final presentation."""
        # Start final round
        final_round = max(self.agent_rounds.values()) + 1
        self.agent_rounds[winner.agent_id] = final_round

        self._add_event(
            "final_round_start",
            winner.agent_id,
            f"Starting final presentation round {final_round}",
            {"round_type": "final", "final_round": final_round},
        )
        self._advance_time(0.5)

        # Status change to streaming
        self._add_event("status_change", winner.agent_id, "Changed to status: streaming")

        # Simulate final presentation time
        self._advance_time(random.uniform(3.0, 6.0))

        # Final answer
        agent_num = self.agents.index(winner) + 1
        final_label = f"agent{agent_num}.final"

        final_answer = self._generate_fake_final_answer(winner)

        self._add_event(
            "final_answer",
            winner.agent_id,
            f"Presented final answer {final_label}",
            {"label": final_label},
        )
        self._advance_time(0.5)

        # Status change to completed
        self._add_event("status_change", winner.agent_id, "Changed to status: completed")

    def _generate_fake_answer(self, agent: FakeAgent, answer_num: int) -> str:
        """Generate fake answer content."""
        templates = [
            "Renewable energy offers significant environmental benefits including reduced carbon emissions...",
            "The advantages of renewable energy include sustainability, reduced pollution, and energy independence...",
            "Renewable sources like solar and wind provide clean energy but face challenges with storage...",
            "While renewables reduce environmental impact, they require significant upfront investment...",
        ]
        return random.choice(templates)

    def _generate_fake_final_answer(self, agent: FakeAgent) -> str:
        """Generate fake final answer."""
        return """After considering all perspectives, here's a comprehensive analysis of renewable energy:

**Pros:**
1. Environmental sustainability - reduces carbon emissions
2. Energy independence - reduces reliance on fossil fuels
3. Long-term cost savings - after initial investment
4. Job creation in green technology sectors

**Cons:**
1. High upfront costs for infrastructure
2. Intermittency issues (solar/wind depend on weather)
3. Energy storage challenges
4. Geographic limitations for some sources

The transition to renewable energy is essential for long-term sustainability, despite current challenges."""


# Predefined scenarios for testing

SCENARIOS = {
    "simple": {
        "description": "Simple 3-agent coordination, no restarts",
        "params": {
            "num_agents": 3,
            "enable_restarts": False,
            "enable_tool_calls": False,
            "seed": 42,
        },
    },
    "complex": {
        "description": "Complex 4-agent coordination with restarts and tool calls",
        "params": {
            "num_agents": 4,
            "enable_restarts": True,
            "enable_tool_calls": True,
            "restart_probability": 0.5,
            "tool_call_probability": 0.6,
            "seed": 42,
        },
    },
    "minimal": {
        "description": "Minimal 2-agent coordination",
        "params": {
            "num_agents": 2,
            "enable_restarts": False,
            "enable_tool_calls": False,
            "seed": 42,
        },
    },
    "chaotic": {
        "description": "Chaotic 5-agent coordination with frequent restarts",
        "params": {
            "num_agents": 5,
            "enable_restarts": True,
            "enable_tool_calls": True,
            "restart_probability": 0.8,
            "tool_call_probability": 0.8,
            "seed": 42,
        },
    },
}


def generate_scenario(scenario_name: str = "simple") -> Dict[str, Any]:
    """Generate a predefined scenario."""
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Choose from: {list(SCENARIOS.keys())}")

    scenario = SCENARIOS[scenario_name]
    print(f"📊 Generating scenario: {scenario['description']}")

    session = FakeCoordinationSession(**scenario["params"])
    data = session.generate_session()

    print(f"✅ Generated {len(data['events'])} events with {len(data['session_metadata']['agent_ids'])} agents")
    return data


def save_scenario(scenario_name: str, output_dir: Path):
    """Generate and save a scenario to JSON file."""
    data = generate_scenario(scenario_name)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"fake_session_{scenario_name}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"💾 Saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    import sys

    # Generate all scenarios
    output_dir = Path(__file__).parent / "fake_sessions"

    if len(sys.argv) > 1:
        # Generate specific scenario
        scenario = sys.argv[1]
        save_scenario(scenario, output_dir)
    else:
        # Generate all scenarios
        print("Generating all scenarios...\n")
        for scenario_name in SCENARIOS:
            save_scenario(scenario_name, output_dir)
            print()

        print(f"✨ All scenarios saved to: {output_dir}")
