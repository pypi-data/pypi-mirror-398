# MassGen Visualization Prototypes

Standalone prototypes for testing visualization concepts with fake data before full integration.

## Quick Start

### 1. Generate Fake Data

```bash
# Generate all scenarios
python -m massgen.prototype.fake_data

# Or generate a specific scenario
python -m massgen.prototype.fake_data simple
```

This creates fake coordination sessions in `massgen/prototype/fake_sessions/`:
- **simple** - 3 agents, no restarts (30 events)
- **complex** - 4 agents with restarts and tools (80 events)
- **minimal** - 2 agents, basic coordination (23 events)
- **chaotic** - 5 agents with frequent restarts (91 events)

### 2. Run Live TUI Demo

```bash
# Run with default (complex) scenario
python -m massgen.prototype.live_tui_demo

# Or specify a scenario
python -m massgen.prototype.live_tui_demo simple
python -m massgen.prototype.live_tui_demo chaotic
```

**Controls:**
- `p` - Pause/Resume playback
- `r` - Restart from beginning
- `1` - 0.5x speed
- `2` - 1x speed
- `3` - 2x speed
- `q` - Quit

### 3. Run Terminal Replay Demo

```bash
# Run with default scenario
python -m massgen.prototype.replay_demo

# Or specify a scenario
python -m massgen.prototype.replay_demo minimal
```

**Controls:**
- `→` / `l` - Next event
- `←` / `h` - Previous event
- `Space` - Play/Pause auto-advance
- `g` - Jump to first event
- `G` - Jump to last event
- `q` - Quit

### 4. Run CLI Demo

```bash
# See available commands
python -m massgen.prototype.cli_demo --help

# Run a coordination (simulated)
python -m massgen.prototype.cli_demo run "What are the pros and cons of AI?"

# Replay a session
python -m massgen.prototype.cli_demo replay simple

# List sessions
python -m massgen.prototype.cli_demo logs list
```

## What's Being Tested?

### Live TUI Demo
- **Agent cards** with real-time status updates
- **Timeline view** showing parallel execution
- **Event feed** with filtered, high-level events
- **Statistics panel** with session metrics
- **Interactive playback** controls

### Terminal Replay Demo
- **Event navigation** (step forward/back)
- **Timeline scrubbing** with visual indicators
- **Event filtering** by type or agent
- **Detail inspection** with full context
- **Playback controls** for auto-advance

### CLI Demo
- **Modern command structure** (Typer-based)
- **Subcommands** (run, replay, logs, serve)
- **Help system** with clear documentation
- **Backward compatibility** detection

## Visual Design Principles

1. **Focus on High-Level Actions**
   - Show: answers, votes, restarts, tool calls (high-level)
   - Hide: reasoning details, backend calls, internal state

2. **Agent-Centric View**
   - Each agent has clear visual identity
   - Status clearly communicated
   - Activity tracked independently

3. **Timeline for Context**
   - Shows parallelism and sequences
   - Easy to see "what happened when"
   - Visual markers for key events

4. **Progressive Disclosure**
   - Overview first, details on demand
   - Different verbosity modes
   - Expand events for full context

## Scenarios Explained

### Simple (30 events)
- 3 agents (gemini2.5flash, gpt5nano, grok3mini)
- No restarts
- No tool calls
- Linear flow: answer → vote → final
- **Use for:** Testing basic visualization

### Complex (80 events)
- 4 agents
- Restarts enabled (50% probability)
- Tool calls enabled (60% probability)
- Multiple iterations
- **Use for:** Testing dynamic features

### Minimal (23 events)
- 2 agents
- Simplest possible coordination
- **Use for:** Testing edge cases

### Chaotic (91 events)
- 5 agents
- Frequent restarts (80% probability)
- Frequent tool calls (80% probability)
- **Use for:** Stress testing visualization

## Feedback Questions

When testing the prototypes, consider:

1. **Visual Clarity**
   - Is it clear what's happening?
   - Can you follow the agent collaboration?
   - Are status changes obvious?

2. **Information Density**
   - Is there too much/too little information?
   - Are the right details visible?
   - Would you want more/less detail?

3. **Interactivity**
   - Are the controls intuitive?
   - Can you navigate easily?
   - What additional controls would help?

4. **Performance**
   - Does it feel responsive?
   - Any lag or delays?
   - How does it handle large sessions?

5. **Aesthetics**
   - Does it look good?
   - Are colors helpful or distracting?
   - Is spacing/layout comfortable?

## Next Steps

After validating the prototypes:

1. **Gather Feedback** - Share with team/users
2. **Iterate on Design** - Refine based on feedback
3. **Integrate with Real Data** - Connect to actual orchestrator
4. **Add Web Visualization** - Build React frontend
5. **Production Polish** - Error handling, docs, tests

## File Structure

```
massgen/prototype/
├── __init__.py
├── README.md (this file)
├── fake_data.py           # Generates fake coordination events
├── live_tui_demo.py       # Live TUI visualization
├── replay_demo.py         # Terminal replay interface
├── cli_demo.py            # CLI command structure demo
└── fake_sessions/         # Generated fake session data
    ├── fake_session_simple.json
    ├── fake_session_complex.json
    ├── fake_session_minimal.json
    └── fake_session_chaotic.json
```

## Dependencies

All prototypes use packages already in MassGen's dependencies:
- `textual` - TUI framework
- `rich` - Rich text formatting
- `typer` - CLI framework (for cli_demo.py)

## Tips

- **Start with 'simple'** scenario to understand basic flow
- **Use 'complex'** to test all features
- **Try 'chaotic'** to stress test visualization
- **Adjust playback speed** to see details or get overview
- **Pause frequently** to examine state at specific moments
