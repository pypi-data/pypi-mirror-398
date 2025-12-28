# Game AI Client SDK

A Python SDK for integrating AI into turn-based board games using Monte Carlo Tree Search (MCTS). This framework provides a generic interface that allows game developers to add AI opponents to their games with minimal coupling to game-specific logic.

## Features

- **Generic Game Interface**: Implement any turn-based game with a simple protocol
- **MCTS AI Engine**: Powerful AI using Monte Carlo Tree Search with customizable strategies
- **AI vs AI Gameplay**: Built-in support for AI vs AI matches with configurable difficulty levels
- **Three Difficulty Levels**: Easy, Medium, and Hard AI opponents with different playing strengths
- **Design Patterns**: Built with Strategy and State patterns for extensibility
- **Event Logging**: Optional match and move logging via RabbitMQ
- **Minimal Integration**: Keep full control of your game logic

## Installation

```bash
pip install game-ai-client==0.1.2
```

## Quick Start

### Basic Usage

Import the SDK:
```python
from game_sdk import AIGameClient
from game_sdk.utils import build_generic_state
```

### AI vs AI Quick Start

For games implementing `TurnBasedGame`, you can immediately run AI vs AI matches:

```python
from your_game import YourGame, state_to_game, game_to_state

# Create initial game
game = YourGame(initial_board, players, starting_player)

# Run AI vs AI match
result = game.ai_vs_ai_difficulty_selection(
    difficulty1="medium",
    difficulty2="hard",
    state_to_game_fn=state_to_game,
    game_to_state_fn=game_to_state,
    game_id="your_game"
)

print(f"Winner: {result['winner']}")
```

Available difficulties: `"easy"`, `"medium"`, `"hard"`

## RabbitMQ Setup (Optional)

The SDK includes built-in event logging to RabbitMQ. To enable it, start RabbitMQ using Docker:

```bash
docker-compose up -d
```

This will start RabbitMQ on:
- AMQP port: 5672
- Management UI: http://localhost:15672

Configure via environment variables:
```bash
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_USER=guest
export RABBITMQ_PASS=guest
```

If RabbitMQ is unavailable, the SDK gracefully falls back to stdout logging.

## Integration Guide

You keep full control over your game logic. To use the framework, you only need to provide:

1. **Players list**
2. **Legal moves function**
3. **Apply-move function** for AI state transitions

- Players list:
```python
players = [
    {"id": "P1", "type": "human",  "symbol": "X"},
    {"id": "P2", "type": "ai_mcts","symbol": "O"},
]
```
- Legal moves function
Return all legal moves for the current player, as a list of dicts:
```python
def compute_legal_moves(board, players, current_player_symbol):
    player_index = next(i for i, p in enumerate(players)
                        if p["symbol"] == current_player_symbol)
    moves = []
    for r in range(len(board)):
        for c in range(len(board[0])):
            if board[r][c].strip() == "":
                moves.append({
                    "id": f"PLACE_{r}_{c}",         # string id is recommended
                    "player_index": player_index,   # index in players[]
                    "type": "PLACE_MARK",
                    "position": {"row": r, "col": c},
                })
    return moves
```
### Apply-Move Function

This is the only function needed from your game to enable AI. It takes a generic state and move, returns a new state:

```python
from typing import Dict, Any, List
from game_sdk.utils import build_generic_state

State = Dict[str, Any]
Move = Dict[str, Any]

def apply_move_my_game(state: State, move: Move) -> State:
    players: List[Dict[str, Any]] = state["players"]

    # --- decode board from generic state ---
    board_info = state["board"]
    int_board = board_info["cells"]              # 2D ints
    symbol_map = {0: " "}
    for idx, p in enumerate(players):
        symbol_map[idx + 1] = p["symbol"]

    board = [[symbol_map[v] for v in row] for row in int_board]

    # --- apply the move ---
    r = move["position"]["row"]
    c = move["position"]["col"]
    player_index = move["player_index"]
    symbol = players[player_index]["symbol"]
    board[r][c] = symbol

    # --- next player ---
    next_player_index = (player_index + 1) % len(players)
    next_symbol = players[next_player_index]["symbol"]

    # --- terminal & result: YOUR logic here ---
    # is_terminal_and_winner() should be implemented by you and return:
    #   (finished: bool, winner_symbol: Optional[str])
    finished, winner_symbol = is_terminal_and_winner(board)

    result_map = None
    if finished:
        # winner_to_results() should return (result_str, result_map)
        # e.g. result_map = {"P1": 1.0, "P2": -1.0}
        _, result_map = winner_to_results(winner_symbol, players)

    move_count = state["extra"].get("move_count", 0) + 1
    legal_moves = [] if finished else compute_legal_moves(board, players, next_symbol)

    # --- build and return the new state ---
    return build_generic_state(
        game_id=state["game_id"],
        board=board,
        players=players,
        current_player_symbol=next_symbol,
        move_count=move_count,
        finished=finished,
        legal_moves=legal_moves,
        result=result_map,
    )
```
# Building a state for the AI / logging
On each turn, describe the current position using build_generic_state:
```python
state = build_generic_state(
    game_id="my_game_id",
    board=board,                        # 2D list of symbols, e.g. [["X"," ","O"], ...]
    players=players,
    current_player_symbol=current_sym,  # whose turn it is
    move_count=move_count,
    finished=False,                     # or True if you know it’s over
    legal_moves=compute_legal_moves(board, players, current_sym),
    result=None,                        # for terminal state: {player_id: score}
)
```
# Using AIGameClient in your loop

Create client and start match:
```python
client = AIGameClient(
    game_id="my_game_id",
    api_key="demo-key",
    apply_move_fn=apply_move_my_game,
)

match_id = client.start_match(players=players, metadata={"mode": "casual"})

```

Each turn:
```python
while not finished:
    current_sym = ...                 # your turn logic
    legal_moves = compute_legal_moves(board, players, current_sym)

    state = build_generic_state(
        game_id="my_game_id",
        board=board,
        players=players,
        current_player_symbol=current_sym,
        move_count=move_count,
        finished=False,
        legal_moves=legal_moves,
    )

    current_player = next(p for p in players if p["symbol"] == current_sym)

    if current_player["type"] == "ai_mcts":
        # ---- AI turn ----
        client.send_state(match_id, state)
        move = client.best_move(match_id, iterations=800)
    else:
        # ---- human turn ----
        move = get_human_move_somehow(legal_moves)

    # Apply move in your game
    apply_move_on_real_board(board, move, current_sym)
    
    # log the move 
    client.log_move(match_id=match_id, state=state, move=move)

    # Update finished / winner using your own logic
    finished, winner_symbol = is_terminal_and_winner(board)
    move_count += 1
```

End the match:
```python
result_str, result_map = winner_to_results(winner_symbol, players)

final_state = build_generic_state(
    game_id="my_game_id",
    board=board,
    players=players,
    current_player_symbol=current_sym,
    move_count=move_count,
    finished=True,
    legal_moves=[],
    result=result_map,
)

client.end_match(
    match_id=match_id,
    result=result_str,
    final_state=final_state,
)
```

## Architecture

### Design Patterns

The SDK implements multiple design patterns for extensibility and maintainability:

#### Strategy Pattern (MCTS Customization)

The MCTS algorithm is decomposed into four pluggable strategies:

```python
from game_sdk.mcts import (
    MCTSStrategy,
    DefaultSelectionStrategy,
    DefaultExpansionStrategy,
    DefaultSimulationStrategy,
    DefaultBackpropagationStrategy,
)

# Use custom strategies
custom_mcts = MCTSStrategy(
    selection_strategy=DefaultSelectionStrategy(),
    expansion_strategy=DefaultExpansionStrategy(),
    simulation_strategy=DefaultSimulationStrategy(),
    backpropagation_strategy=DefaultBackpropagationStrategy(),
)
```

Each strategy can be independently customized:
- **SelectionStrategy**: How to traverse the tree (default: UCB1)
- **ExpansionStrategy**: How to add nodes (default: single unexpanded move)
- **SimulationStrategy**: How to simulate games (default: random rollout)
- **BackpropagationStrategy**: How to update values (default: visit counts + rewards)

#### State Pattern (MCTS Phases)

MCTS iterations follow a state machine:
- Selection Phase → Expansion Phase → Simulation Phase → Backpropagation Phase → Complete

Each phase handles its work and transitions to the next state, providing clean separation of concerns.

### Protocol-Based Design

The SDK uses Python protocols for game integration. Implement the `TurnBasedGame` protocol for compile-time type checking:

```python
from game_sdk.ai_client import TurnBasedGame, Move
from typing import List

class MyGame(TurnBasedGame):
    def get_legal_actions(self) -> List[Move]:
        # Return all legal moves
        pass

    def is_game_over(self) -> bool:
        # Check if game is finished
        pass

    def game_result(self) -> int:
        # Return result: 1 (win), -1 (loss), 0 (draw) from current player perspective
        pass

    def move(self, action: Move) -> "MyGame":
        # Apply move and return new game state
        pass
```

### Component Overview

```
┌─────────────────────────────────────────────┐
│   Game Implementation                       │
│   - Your game logic                         │
│   - TurnBasedGame protocol                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   AIGameClient                              │
│   - State management                        │
│   - MCTS integration                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   MCTS Engine (Strategy Pattern)            │
│   - Selection → Expansion                   │
│   - Simulation → Backpropagation            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   Event Logging (RabbitMQ)                  │
│   - Match lifecycle events                  │
│   - Move logging                            │
└─────────────────────────────────────────────┘
```

## Advanced Usage

### Customizing MCTS Parameters

Control the AI strength and behavior:

```python
# More iterations = stronger AI (but slower)
move = client.best_move(match_id, iterations=1000)

# Fewer iterations = faster but weaker AI
move = client.best_move(match_id, iterations=100)
```

### AI vs AI Gameplay with Difficulty Levels

The SDK provides built-in support for AI vs AI matches with three difficulty levels:

- **Easy**: 100 MCTS iterations, 50% random moves (beginner-friendly)
- **Medium**: 1000 MCTS iterations, pure MCTS strategy (intermediate)
- **Hard**: 5000 MCTS iterations, near-perfect play (expert)

#### Using the TurnBasedGame Protocol

Any game implementing the `TurnBasedGame` protocol automatically gets AI vs AI functionality:

```python
from game_sdk.ai_client import TurnBasedGame
from typing import List, Dict, Any

class MyGame(TurnBasedGame):
    def get_legal_actions(self) -> List[Dict[str, Any]]:
        # Return list of legal moves
        pass

    def is_game_over(self) -> bool:
        # Check if game has ended
        pass

    def game_result(self) -> int:
        # Return 1 (win), -1 (loss), or 0 (draw) from current player's perspective
        pass

    def move(self, action: Dict[str, Any]) -> "MyGame":
        # Apply move and return new game state (immutable)
        pass
```

#### Running AI vs AI Matches

Once your game implements `TurnBasedGame`, you can run AI vs AI matches:

```python
# Create initial game state
game = MyGame(initial_board, players, current_player_symbol)

# Play AI vs AI with different difficulties
result = game.ai_vs_ai_difficulty_selection(
    difficulty1="easy",      # First AI plays at easy difficulty
    difficulty2="hard",      # Second AI plays at hard difficulty
    state_to_game_fn=state_to_game_converter,
    game_to_state_fn=game_to_state_converter,
    game_id="my_game",
    verbose=True            # Print game progress
)

# Check results
print(f"Winner: {result['winner']}")
print(f"Total moves: {result['move_count']}")
print(f"Move history: {result['move_history']}")
```

#### Converter Functions

You need two adapter functions to convert between your game and the generic SDK state:

```python
def state_to_game_converter(state: Dict[str, Any]) -> MyGame:
    """Convert SDK state dictionary to your game object."""
    board = extract_board_from_state(state)
    players = state["players"]
    current_player = players[state["turn_index"]]["symbol"]
    return MyGame(board, players, current_player)

def game_to_state_converter(game: MyGame, prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert your game object back to SDK state dictionary."""
    from game_sdk.utils import build_generic_state

    return build_generic_state(
        game_id=prev_state["game_id"],
        board=game.board,
        players=game.players,
        current_player_symbol=game.current_player_symbol,
        move_count=prev_state.get("extra", {}).get("move_count", 0) + 1,
        finished=game.is_game_over(),
        legal_moves=[] if game.is_game_over() else game.get_legal_actions(),
        result=compute_result_map(game) if game.is_game_over() else None
    )
```

#### Example: Running a Tournament

```python
from typing import Dict

def run_tournament(difficulty1: str, difficulty2: str, num_games: int = 10) -> Dict:
    """Run multiple AI vs AI games and collect statistics."""
    wins = {"Player1": 0, "Player2": 0, "Draw": 0}

    for i in range(num_games):
        game = MyGame(create_empty_board(), players, "X")

        result = game.ai_vs_ai_difficulty_selection(
            difficulty1=difficulty1,
            difficulty2=difficulty2,
            state_to_game_fn=state_to_game_converter,
            game_to_state_fn=game_to_state_converter,
            game_id="my_game",
            verbose=False  # Silent mode
        )

        if result['winner']:
            winner_idx = 0 if result['winner'] == "X" else 1
            key = f"Player{winner_idx + 1}"
            wins[key] += 1
        else:
            wins["Draw"] += 1

    return wins

# Run tournament
stats = run_tournament("medium", "hard", num_games=20)
print(f"Results: {stats}")
```

#### Complete Example Files

See the example files for complete working implementations:
- `ai_vs_ai_example.py`: Simple AI vs AI game examples
- `game_manager.py`: Full game management system with tournaments
- `tictactoe.py`: Complete Tic-Tac-Toe implementation with AI

### Generic State Format

The SDK uses a standardized state representation:

```json
{
  "game_id": "tictactoe",
  "state_id": "unique-uuid",
  "turn_index": 5,
  "players": [
    {"id": "P1", "type": "human", "symbol": "X"},
    {"id": "P2", "type": "ai_mcts", "symbol": "O"}
  ],
  "board": {
    "representation": "grid",
    "rows": 3,
    "cols": 3,
    "cells": [[1, 0, 2], [0, 1, 0], [2, 0, 0]],
    "legend": {
      "0": "empty",
      "1": "player_1_piece",
      "2": "player_2_piece"
    }
  },
  "status": "IN_PROGRESS",
  "is_terminal": false,
  "legal_moves": [...],
  "result": null,
  "extra": {"move_count": 5}
}
```

## Example Implementation

See `tictactoe.py` for a complete working example demonstrating:
- TurnBasedGame protocol implementation
- Human vs AI gameplay
- AI vs AI gameplay with multiple difficulty levels
- State management
- Event logging

## Changelog

### Version 0.1.7 (Latest)

**Bug Fixes:**
- Fixed winner determination logic in `ai_vs_ai_difficulty_selection()` method
  - Previously, winners were incorrectly attributed due to inverted logic in result interpretation
  - Hard difficulty now correctly demonstrates unbeatable play
  - Results are now properly assigned when `game_result()` returns `-1` (current player lost)

**Improvements:**
- Made RabbitMQ dependency optional
  - SDK now gracefully handles missing `pika` module
  - Falls back to stdout logging when RabbitMQ is unavailable
  - Allows usage without message bus infrastructure

**New Examples:**
- `ai_vs_ai_example.py`: Demonstrates AI vs AI gameplay
- `game_manager.py`: Tournament management system
- `test_difficulty_fix.py`: Validation tests for difficulty levels

## Requirements

- Python 3.9+
- pika 1.3.2 (optional, for RabbitMQ logging)

## Credits

Tic-Tac-Toe example adapted from: https://gist.github.com/qianguigui1104/edb3b11b33c78e5894aad7908c773353