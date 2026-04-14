# Arena.AI Python MCTS Bot

A Monte Carlo Tree Search (MCTS) based AI bot for the Arena.AI tactical battle game.

## Overview

This Python bot connects to the Arena.AI C# server and plays battles using a sophisticated MCTS algorithm. The bot can:

- Connect to the server via HTTP REST API
- Receive real-time battle state information
- Analyze available moves and attacks using MCTS
- Select optimal actions based on simulated game outcomes
- Play complete battles against other bots or players

## Architecture

```
┌──────────────────────────┐
│ Arena.AI C# Server       │
│ (Battle Logic & State)   │
└────────────┬─────────────┘
             │ HTTP REST API
             │
┌────────────┴─────────────┐
│ Python MCTS Bot          │
│ ├─ API Client            │
│ ├─ Game State Parser     │
│ ├─ Simulator             │
│ ├─ Distance Calc         │
│ ├─ Damage Calc           │
│ └─ MCTS Engine           │
└──────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. Navigate to the python_bot directory:
```bash
cd python_bot
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to adjust:

- **SERVER_URL**: Address of the Arena.AI server (default: http://localhost:5222)
- **MCTS_ITERATIONS**: Number of MCTS simulations per move (default: 1000)
- **UCB1_C_CONSTANT**: Exploration/exploitation balance (default: 1.414)
- **SIMULATION_DEPTH**: Max playout depth (None = full game)
- **VERBOSE**: Enable detailed logging

## Usage

Run the bot against the local Arena.AI server:

```bash
cd python_bot
python main.py
```

The bot will automatically create a PvB invite, connect to the `/play` SignalR hub, and join the battle.

To play multiple games in a row:

```bash
python main.py 5
# or equivalently
python main.py --games 5
```

Optional arguments:
- `--heuristic-config`: path to heuristic JSON overrides
- `--summary-json`: path to write summary JSON
- `--quiet-actions`: hide action logs and suppress SignalR event output

## Game Mechanics

### Board
- 20x20 arena grid
- Positions labeled A1-T20

### Units
5 types with different stats:
- **Light**: Balanced attacker
- **Heavy**: Strong defense
- **Fast**: High movement
- **ShortRange**: Melee specialist
- **LongRange**: Ranged specialist

### Actions (per turn)
1. **Move**: Relocate to adjacent cell
2. **Attack**: Hit enemy within range (+ potential counter-attack)
3. **Skip**: End turn without action

### Combat System
- Damage = Attacker.Attack - Defender.Defence + randomness
- Type-specific bonuses and penalties
- Counter-attacks at ~50% damage
- Units eliminated when Health ≤ 0
- Battle ends when one team eliminated

## MCTS Algorithm

The bot uses Monte Carlo Tree Search with UCB1 formula:

**Selection Phase**
- Navigate from root using UCB1 selection
- Balance exploitation (win rate) vs exploration (uncertainty)

**Expansion Phase**
- Create child nodes for untried actions
- Use lazy expansion for efficiency

**Simulation Phase**
- Run random playout from expanded node
- Simulate game to completion or depth limit
- Record winner

**Backpropagation Phase**
- Update visit counts and reward values
- Propagate results up the tree

**Selection**
- After all iterations, pick action with most visits

## Performance

| Parameter | Value |
|-----------|-------|
| Iterations/move | 1000-5000 |
| Time/move | 2-10 seconds |
| Memory | <500MB |
| Win rate vs SimplePlayer1 | ~60%+ |

## Command-Line Interface

```bash
# Offline simulation
python main.py

# Connect to existing battle
python main.py ABC123DEF456

# Custom config (experimental)
set MCTS_ITERATIONS=2000
python main.py
```

## Project Structure

```
python_bot/
├── main.py                 # Entry point
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── README.md              # This file
├── bot/
│   ├── __init__.py
│   ├── api_client.py      # Server communication
│   ├── game_state.py      # Data models
│   ├── simulator.py       # Game simulation
│   ├── distance.py        # Movement calculations
│   ├── damage.py          # Combat calculations
│   ├── mcts.py           # MCTS algorithm
│   └── action_mapper.py   # Action conversion
├── tests/
│   ├── test_distance.py
│   ├── test_damage.py
│   ├── test_simulator.py
│   └── test_mcts.py
└── logs/
    └── bot.log
```

## Logging

The bot logs all actions to both console and `logs/bot.log`. Adjust LOG_LEVEL in config.py:

```python
LOG_LEVEL = "DEBUG"   # Verbose
LOG_LEVEL = "INFO"    # Normal
LOG_LEVEL = "WARNING" # Quiet
```

## Troubleshooting

### Server Connection Issues
```
Error: Cannot connect to server
→ Check SERVER_URL in config.py
→ Ensure Arena.AI server is running
→ Check firewall/SSL settings
```

### Slow Performance
```
Problem: Bot takes too long to decide
→ Reduce MCTS_ITERATIONS in config.py
→ Set SIMULATION_DEPTH to limit playout length
→ Check system resources
```

### Wrong Move Selection
```
Problem: Bot makes suboptimal decisions
→ Increase MCTS_ITERATIONS for better accuracy
→ Adjust UCB1_C_CONSTANT (higher = more exploration)
→ Check game rule implementation in simulator.py
```

## Future Improvements

- [ ] Alpha-beta pruning for faster evaluation
- [ ] Transposition tables for state caching
- [ ] Parallel MCTS with multiple threads
- [ ] Neural network value function
- [ ] Opening book for early game
- [ ] End-game heuristics
- [ ] WebSocket support for real-time updates
- [ ] Bot vs bot tournament mode

## License

Part of Arena.AI project

## Contact

For issues or improvements, contact the Arena.AI development team.
