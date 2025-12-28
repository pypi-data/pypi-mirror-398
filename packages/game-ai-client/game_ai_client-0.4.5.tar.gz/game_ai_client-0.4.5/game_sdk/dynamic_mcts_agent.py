from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Type, Optional, Callable, Dict

# Import from the mcts module in this package
from .mcts import (
    MCTS,
    RandomSimulationStrategy,
    get_selection_strategy,
    get_expansion_strategy,
    get_simulation_strategy,
    get_backpropagation_strategy,
)

# Import StatefulGameAdapter for wrapping dict states
from .ai_client import StatefulGameAdapter


# ---------------------------------------------------------------------------
# Performance tracking (how well the HUMAN is doing)
# ---------------------------------------------------------------------------

@dataclass
class PerformanceTracker:
    """
    Tracks a rolling window of game results from the HUMAN's perspective.

    Can track either:
    1. Game outcomes (reward convention):
        +1 = human win
         0 = draw
        -1 = human loss
    2. Heuristic values from the game state's get_heuristic() method
       - move_heuristics: Track per-move heuristics for real-time adaptation
       - game_heuristics: Track end-of-game heuristics
    """
    window_size: int = 10
    move_window_size: int = 5  # Smaller window for move-by-move tracking
    results: List[float] = field(default_factory=list)
    game_heuristics: List[float] = field(default_factory=list)
    move_heuristics: List[float] = field(default_factory=list)
    use_heuristics: bool = False

    def record_move(self, heuristic: float) -> None:
        """
        Record a heuristic value after a move for real-time adaptation.

        Args:
            heuristic: Heuristic value from the game state after the move
        """
        if heuristic is not None:
            self.move_heuristics.append(heuristic)
            if len(self.move_heuristics) > self.move_window_size:
                self.move_heuristics.pop(0)
            self.use_heuristics = True

    def record_result(self, reward: float, heuristic: Optional[float] = None) -> None:
        """
        Record a game result and optionally a heuristic value at game end.

        Args:
            reward: Game outcome (+1 for human win, 0 for draw, -1 for human loss)
            heuristic: Optional heuristic value from the game state
        """
        self.results.append(reward)
        if len(self.results) > self.window_size:
            self.results.pop(0)

        # Track game-level heuristic if provided
        if heuristic is not None:
            self.game_heuristics.append(heuristic)
            if len(self.game_heuristics) > self.window_size:
                self.game_heuristics.pop(0)
            self.use_heuristics = True

    @property
    def avg_move_heuristic(self) -> float:
        """
        Get average heuristic from recent moves for real-time adaptation.
        """
        if self.move_heuristics:
            return sum(self.move_heuristics) / len(self.move_heuristics)
        return 0.0

    @property
    def avg_result(self) -> float:
        """
        Get average performance metric at game level.

        Returns game heuristic average if available, otherwise returns game outcome average.
        """
        # Prefer game-level heuristic values if they're being tracked
        if self.use_heuristics and self.game_heuristics:
            return sum(self.game_heuristics) / len(self.game_heuristics)

        # Fall back to game outcomes
        if not self.results:
            return 0.0
        return sum(self.results) / len(self.results)


# ---------------------------------------------------------------------------
# Difficulty State base class
# ---------------------------------------------------------------------------

class DifficultyState(ABC):
    """
    Base class for all difficulty levels.

    The Context is DynamicMCTSAgent.
    Each concrete state:
      - creates a fresh MCTS instance for each move (to avoid reuse bugs)
      - implements how to pick a move
      - decides when to transition to another state
    """

    def __init__(self, agent: DynamicMCTSAgent):
        self.agent = agent

    @abstractmethod
    def _create_mcts(self) -> MCTS:
        """
        Create a fresh MCTS instance configured for this difficulty.

        Note: This should be called for EACH move to avoid MCTS reuse bugs.
        """
        ...

    @abstractmethod
    def select_move(self, state: Any) -> Any:
        """Choose a move at this difficulty level."""
        ...

    def on_move_made(self, heuristic: Optional[float] = None) -> None:
        """
        Called after each move to track performance and potentially adjust difficulty mid-game.

        Args:
            heuristic: Heuristic value from the game state after the move
        """
        if heuristic is not None:
            self.agent.performance.record_move(heuristic)
            # Check if difficulty should change based on recent move performance
            self._check_move_based_transition()

    @abstractmethod
    def _check_move_based_transition(self) -> None:
        """
        Check if difficulty should transition based on recent move heuristics.
        Each difficulty level implements its own transition logic.
        """
        ...

    @abstractmethod
    def on_game_finished(self, human_reward: float, heuristic: Optional[float] = None) -> None:
        """
        Update performance + possibly transition to another difficulty state.

        Args:
            human_reward: +1 (human win), 0 (draw), -1 (human loss)
            heuristic: Optional heuristic value from the game's get_heuristic() method
        """
        ...


# ---------------------------------------------------------------------------
# Easy difficulty
# ---------------------------------------------------------------------------

class EasyState(DifficultyState):
    """
    Easy difficulty:
      - Very low computational budget (10 iterations)
      - Mostly random moves for variety (85%)
      - RAVE selection, Progressive widening, Solver backprop

    NOTE: For Tic-Tac-Toe, this needs to be VERY weak to avoid always drawing.
    The game tree is so small that even 100 iterations plays near-perfectly.
    """

    def _create_mcts(self) -> MCTS:
        selection = get_selection_strategy("rave", exploration_c=1.4)
        expansion = get_expansion_strategy("progressive_widening")
        simulation = RandomSimulationStrategy(track_moves=True)  # Enable move tracking for RAVE
        backprop = get_backpropagation_strategy("solver")

        return MCTS(
            exploration_c=1.4,
            selection_strategy=selection,
            expansion_strategy=expansion,
            simulation_strategy=simulation,
            backpropagation_strategy=backprop,
        )

    def select_move(self, state: Any) -> Any:
        # Wrap dict state in adapter to satisfy GameEnv Protocol
        game_adapter = StatefulGameAdapter(state, self.agent.apply_move_fn)
        legal = game_adapter.get_legal_actions()
        if not legal:
            return None

        # 85% of the time: random move for variety (was 50%, increased for weaker play)
        if random.random() < 0.85:
            return random.choice(legal)

        # Use MCTS with very low computational budget (was 100, reduced to 10)
        mcts = self._create_mcts()
        return mcts.search(game_adapter, iterations=100)

    def _check_move_based_transition(self) -> None:
        """Check if human is consistently making strong moves → upgrade to Medium."""
        avg_move = self.agent.performance.avg_move_heuristic

        # Human making consistently strong moves on Easy → upgrade to Medium
        # Positive heuristic values indicate favorable positions for the human
        if avg_move > 0.5:  # More strict threshold for move-by-move
            self.agent.transition_to(MediumState(self.agent))

    def on_game_finished(self, human_reward: float, heuristic: Optional[float] = None) -> None:
        self.agent.performance.record_result(human_reward, heuristic)
        avg = self.agent.performance.avg_result

        # Human consistently doing well on Easy → upgrade to Medium
        # When using heuristics, positive values indicate human is winning
        if avg > 0.30:
            self.agent.transition_to(MediumState(self.agent))


# ---------------------------------------------------------------------------
# Medium difficulty
# ---------------------------------------------------------------------------

class MediumState(DifficultyState):
    """
    Medium difficulty:
      - Moderate computational budget (1000 iterations)
      - No random moves - purely MCTS-based decisions
      - RAVE selection, Progressive widening, Solver backprop
    """

    def _create_mcts(self) -> MCTS:
        selection = get_selection_strategy("rave", exploration_c=1.4)
        expansion = get_expansion_strategy("progressive_widening")
        simulation = RandomSimulationStrategy(track_moves=True)  # Enable move tracking for RAVE
        backprop = get_backpropagation_strategy("solver")

        return MCTS(
            exploration_c=1.4,
            selection_strategy=selection,
            expansion_strategy=expansion,
            simulation_strategy=simulation,
            backpropagation_strategy=backprop,
        )

    def select_move(self, state: Any) -> Any:
        # Wrap dict state in adapter to satisfy GameEnv Protocol
        game_adapter = StatefulGameAdapter(state, self.agent.apply_move_fn)
        legal = game_adapter.get_legal_actions()
        if not legal:
            return None

        # Use MCTS with moderate computational budget (create fresh instance)
        mcts = self._create_mcts()
        return mcts.search(game_adapter, iterations=1000)

    def _check_move_based_transition(self) -> None:
        """Check move quality → transition to Hard or Easy."""
        avg_move = self.agent.performance.avg_move_heuristic

        # Human making consistently strong moves → upgrade to Hard
        if avg_move > 0.7:
            self.agent.transition_to(HardState(self.agent))
        # Human struggling with moves → downgrade to Easy
        elif avg_move < -0.7:
            self.agent.transition_to(EasyState(self.agent))

    def on_game_finished(self, human_reward: float, heuristic: Optional[float] = None) -> None:
        self.agent.performance.record_result(human_reward, heuristic)
        avg = self.agent.performance.avg_result

        # Human is crushing Medium → go Hard
        # When using heuristics, positive values indicate human is winning
        if avg > 0.40:
            self.agent.transition_to(HardState(self.agent))
        # Human is struggling on Medium → go Easy
        elif avg < -0.40:
            self.agent.transition_to(EasyState(self.agent))


# ---------------------------------------------------------------------------
# Hard difficulty
# ---------------------------------------------------------------------------

class HardState(DifficultyState):
    """
    Hard difficulty:
      - High computational budget (5000 iterations)
      - No random moves - purely MCTS-based decisions
      - RAVE selection, Progressive widening, Solver backprop
    """

    def _create_mcts(self) -> MCTS:
        selection = get_selection_strategy("rave", exploration_c=1.4)
        expansion = get_expansion_strategy("progressive_widening")
        simulation = RandomSimulationStrategy(track_moves=True)  # Enable move tracking for RAVE
        backprop = get_backpropagation_strategy("solver")

        return MCTS(
            exploration_c=1.4,
            selection_strategy=selection,
            expansion_strategy=expansion,
            simulation_strategy=simulation,
            backpropagation_strategy=backprop,
        )

    def select_move(self, state: Any) -> Any:
        # Wrap dict state in adapter to satisfy GameEnv Protocol
        game_adapter = StatefulGameAdapter(state, self.agent.apply_move_fn)
        # Use MCTS with high computational budget (create fresh instance each time)
        mcts = self._create_mcts()
        return mcts.search(game_adapter, iterations=5000)

    def _check_move_based_transition(self) -> None:
        """Check if human is struggling with moves → downgrade to Medium."""
        avg_move = self.agent.performance.avg_move_heuristic

        # Human making consistently weak moves on Hard → downgrade to Medium
        # Negative heuristic values indicate unfavorable positions for the human
        if avg_move < -0.5:
            self.agent.transition_to(MediumState(self.agent))

    def on_game_finished(self, human_reward: float, heuristic: Optional[float] = None) -> None:
        self.agent.performance.record_result(human_reward, heuristic)
        avg = self.agent.performance.avg_result

        # Human is losing badly on Hard → drop back to Medium
        # When using heuristics, negative values indicate human is losing
        if avg < -0.30:
            self.agent.transition_to(MediumState(self.agent))


# ---------------------------------------------------------------------------
# Context: DynamicMCTSAgent
# ---------------------------------------------------------------------------

class DynamicMCTSAgent:
    """
    Context for the difficulty State pattern.

    - Holds the apply_move function for wrapping dict states
    - Tracks human performance
    - Delegates to the current DifficultyState for:
        - select_move
        - on_game_finished (which may trigger transitions)
    """

    def __init__(
        self,
        apply_move_fn: Callable[[Dict[str, Any], Any], Dict[str, Any]],
        difficulty: Optional[str] = None,
        start_state_cls: Optional[Type[DifficultyState]] = None,
    ):
        """
        Initialize the dynamic MCTS agent.

        Args:
            apply_move_fn: Function that applies a move to a state dict and returns new state dict
                          (state, move) -> new_state
            difficulty: Starting difficulty level as string - "easy", "medium", or "hard"
                       (default: "medium")
            start_state_cls: Direct difficulty state class (overrides difficulty parameter)
                            Used for advanced usage or backward compatibility
        """
        self.apply_move_fn = apply_move_fn
        self.performance = PerformanceTracker()

        # Map difficulty strings to state classes
        difficulty_map = {
            "easy": EasyState,
            "medium": MediumState,
            "hard": HardState,
        }

        # Determine initial state class
        if start_state_cls is not None:
            # Direct class takes precedence (backward compatibility)
            initial_cls = start_state_cls
        elif difficulty is not None:
            # Use difficulty string
            difficulty_lower = difficulty.lower()
            if difficulty_lower not in difficulty_map:
                available = ", ".join(f'"{k}"' for k in difficulty_map.keys())
                raise ValueError(
                    f"Unknown difficulty '{difficulty}'. "
                    f"Available options: {available}"
                )
            initial_cls = difficulty_map[difficulty_lower]
        else:
            # Default to medium
            initial_cls = MediumState

        self.state: DifficultyState = initial_cls(self)

    def transition_to(self, new_state: DifficultyState) -> None:
        """
        Transition to a new difficulty state.
        You can hook logging / UI updates here if desired.
        """
        # Example: print or log difficulty change
        # print(f"Difficulty changed: {self.state.__class__.__name__} -> {new_state.__class__.__name__}")
        self.state = new_state

    def select_move(self, state: Any) -> Any:
        """

        Select a move by delegating to the current difficulty state.
        """
        return self.state.select_move(state)

    def select_move_at_difficulty(self, state: Any, difficulty: str) -> Any:
        """
        Select a move at a specific difficulty level without changing the agent's state.

        Useful for:
        - Self-play at different difficulties
        - Testing different difficulty levels
        - AI vs AI games with asymmetric difficulties

        Args:
            state: The game state to select a move from
            difficulty: Difficulty level as string - "easy", "medium", or "hard"

        Returns:
            The selected move

        Raises:
            ValueError: If difficulty is not recognized

        Example:
            agent = DynamicMCTSAgent(env)
            easy_move = agent.select_move_at_difficulty(state, "easy")
            hard_move = agent.select_move_at_difficulty(state, "hard")
        """
        # Map difficulty strings to state classes
        difficulty_map = {
            "easy": EasyState,
            "medium": MediumState,
            "hard": HardState,
        }

        difficulty_lower = difficulty.lower()
        if difficulty_lower not in difficulty_map:
            available = ", ".join(f'"{k}"' for k in difficulty_map.keys())
            raise ValueError(
                f"Unknown difficulty '{difficulty}'. "
                f"Available options: {available}"
            )

        # Create temporary state instance and use it to select move
        temp_state = difficulty_map[difficulty_lower](self)
        return temp_state.select_move(state)

    def on_move_made(self, state: Any) -> None:
        """
        Notify the agent that a move was made, enabling mid-game difficulty adaptation.

        This should be called after each move (by either player) to track move quality
        and potentially adjust difficulty in real-time.

        Args:
            state: The game state after the move (can be dict, TurnBasedGame, or StatefulGameAdapter)
        """
        heuristic = self.get_heuristic_from_state(state)
        self.state.on_move_made(heuristic)

    def on_game_finished(self, human_reward: float, heuristic: Optional[float] = None) -> None:
        """
        Notify the agent that a game finished.

        Args:
            human_reward: Game outcome from human's perspective
                +1 = human win
                 0 = draw
                -1 = human loss
            heuristic: Optional heuristic value from the game's get_heuristic() method
        """
        self.state.on_game_finished(human_reward, heuristic)

    def get_heuristic_from_state(self, state: Any) -> Optional[float]:
        """
        Extract heuristic value from a game state if available.

        Attempts to get heuristic from:
        1. TurnBasedGame objects with get_heuristic() method
        2. StatefulGameAdapter wrapping a dict state with heuristic value

        Args:
            state: Game state (can be dict, TurnBasedGame, or StatefulGameAdapter)

        Returns:
            Heuristic value if available, None otherwise
        """
        # Try to get heuristic from TurnBasedGame object
        if hasattr(state, 'get_heuristic'):
            return state.get_heuristic()

        # Try to get from StatefulGameAdapter's wrapped state
        if isinstance(state, StatefulGameAdapter):
            wrapped_state = getattr(state, '_state', None)
            if wrapped_state and isinstance(wrapped_state, dict):
                return wrapped_state.get('heuristic')

        # Try to get from dict state directly
        if isinstance(state, dict):
            return state.get('heuristic')

        return None

    def current_difficulty_name(self) -> str:
        """Return a simple string name of the current difficulty."""
        return self.state.__class__.__name__
