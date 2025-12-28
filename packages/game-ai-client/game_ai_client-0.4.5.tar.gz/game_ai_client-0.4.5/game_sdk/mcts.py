import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


class GameEnv(Protocol):
    """
    Protocol that defines the interface for game environments.
    Now matches TurnBasedGame interface - methods work on self instead of state parameter.
    Any TurnBasedGame automatically satisfies this protocol.
    """
    def current_player(self) -> int: ...
    def get_legal_actions(self) -> List[Any]: ...
    def move(self, action: Any) -> "GameEnv": ...
    def is_game_over(self) -> bool: ...
    def game_result(self) -> float: ...


@dataclass
class Node:
    state: Any
    player_to_move: int
    parent: Optional["Node"] = None
    move_from_parent: Optional[Any] = None

    children: Dict[Any, "Node"] = field(default_factory=dict)
    unexpanded_moves: List[Any] = field(default_factory=list)

    visits: int = 0
    value_sum: float = 0.0

    # RAVE (Rapid Action Value Estimation) statistics
    # Tracks value of moves regardless of when they're played
    rave_visits: Dict[Any, int] = field(default_factory=dict)
    rave_value_sum: Dict[Any, float] = field(default_factory=dict)

    # MCTS Solver fields
    # Marks nodes with proven outcomes (certain win/loss/draw)
    is_solved: bool = False
    solved_value: float = 0.0  # The proven value from this node's perspective

    def q_value(self) -> float:
        """Get average value from this node's perspective."""
        if self.is_solved:
            return self.solved_value
        return self.value_sum / self.visits if self.visits > 0 else 0.0

    def rave_q_value(self, move_key: Any) -> float:
        """Get RAVE Q-value for a specific move."""
        visits = self.rave_visits.get(move_key, 0)
        if visits == 0:
            return 0.0
        return self.rave_value_sum.get(move_key, 0.0) / visits

@dataclass
class MCTSContext:
    """
    Holds all data shared across MCTS phases during a single iteration.
    Used by the State pattern for Selection/Expansion/Simulation/Backprop.
    Note: env is no longer needed since game states are GameEnv objects themselves.
    """
    root: Node
    root_player: int

    selection_strategy: "SelectionStrategy"
    expansion_strategy: "ExpansionStrategy"
    simulation_strategy: "SimulationStrategy"
    backpropagation_strategy: "BackpropagationStrategy"

    current_node: Optional[Node] = None
    reward: float = 0.0
    simulation_moves: List[Any] = field(default_factory=list)  # For RAVE







# Strategy Interfaces for MCTS Phases

class SelectionStrategy(ABC):
    """Strategy for selecting a node to expand during tree traversal."""

    @abstractmethod
    def select(self, node: Node) -> Node:
        """
        Select a node from the tree for expansion.

        Args:
            node: The current node to select from (node.state is the game)

        Returns:
            The selected node
        """
        pass


class ExpansionStrategy(ABC):
    """Strategy for expanding a node by adding a new child."""

    @abstractmethod
    def expand(self, node: Node) -> Optional[Node]:
        """
        Expand a node by adding a new child.

        Args:
            node: The node to expand (node.state is the game)

        Returns:
            The newly created child node, or None if node cannot be expanded
        """
        pass


class SimulationStrategy(ABC):
    """Strategy for simulating a game from a given node."""

    @abstractmethod
    def simulate(self, node: Node, root_player: int) -> float:
        """
        Simulate a game from the given node to a terminal state.

        Args:
            node: The node to simulate from (node.state is the game)
            root_player: The player from whose perspective to evaluate

        Returns:
            The reward for the root player
        """
        pass


class BackpropagationStrategy(ABC):
    """Strategy for backpropagating simulation results through the tree."""

    @abstractmethod
    def backpropagate(
        self,
        node: Node,
        reward: float,
        root_player: int = 0,
        simulation_moves: Optional[List[Any]] = None
    ) -> None:
        """
        Backpropagate the simulation result through the tree.

        Args:
            node: The node to start backpropagation from
            reward: The reward to backpropagate (from root_player's perspective)
            root_player: The player index from whose perspective the reward is given
            simulation_moves: Optional list of moves played during simulation (for RAVE)
        """
        pass


# Default Strategy Implementations

class UCBSelectionStrategy(SelectionStrategy):
    """UCB1-based selection strategy with First Play Urgency."""

    def __init__(self, exploration_c: float = 1.4, fpu_reduction: float = 0.0):
        """
        Args:
            exploration_c: UCB exploration constant (default: 1.4)
            fpu_reduction: First Play Urgency reduction (default: 0.0)
                          If > 0, unvisited nodes get parent_value - fpu_reduction
                          instead of infinity. Typical values: 0.1-0.5
        """
        self.exploration_c = exploration_c
        self.fpu_reduction = fpu_reduction

    def select(self, node: Node) -> Node:
        """Select child using UCB1 formula."""
        current = node

        while True:
            if current.state.is_game_over():
                return current

            # If node has unexpanded moves OR no children, return it for expansion
            if current.unexpanded_moves or not current.children:
                return current

            # Otherwise, select best child using UCB
            current = self._ucb_select_child(current)

    def _ucb_select_child(self, node: Node) -> Node:
        """Select child with highest UCB value using FPU for unvisited nodes."""
        assert node.children, "Cannot select child of leaf without children"

        log_N = math.log(node.visits + 1)
        parent_value = node.q_value()  # For FPU

        def ucb(child: Node) -> float:
            # Solved nodes get infinite value (wins) or very negative (losses)
            if child.is_solved:
                # From parent's perspective, opponent's win is our loss
                if child.player_to_move != node.player_to_move:
                    return -child.solved_value * 1000  # Amplify to ensure selection
                else:
                    return child.solved_value * 1000

            if child.visits == 0:
                # First Play Urgency: use parent value - reduction
                if self.fpu_reduction > 0:
                    return parent_value - self.fpu_reduction
                else:
                    return float("inf")  # Standard UCB behavior

            # Child q_value is from child's perspective
            # If child is opponent, negate it to get value from parent's perspective
            if child.player_to_move != node.player_to_move:
                exploit = -child.q_value()  # Opponent's loss is our gain
            else:
                exploit = child.q_value()  # Same player (shouldn't happen in 2-player)

            explore = self.exploration_c * math.sqrt(log_N / child.visits)
            return exploit + explore

        _, best_child = max(
            node.children.items(),
            key=lambda item: ucb(item[1])
        )
        return best_child


class RAVESelectionStrategy(SelectionStrategy):
    """
    UCB + RAVE hybrid selection strategy with FPU and Solver support.

    RAVE (Rapid Action Value Estimation) combines:
    - UCB statistics (actual move performance)
    - AMAF statistics (All Moves As First - move performance regardless of when played)

    This makes MCTS much stronger with random rollouts by sharing information
    across similar positions.
    """

    def __init__(self, exploration_c: float = 1.4, rave_constant: float = 300, fpu_reduction: float = 0.0):
        """
        Args:
            exploration_c: UCB exploration constant (default: 1.4)
            rave_constant: Controls mixing between UCB and RAVE (default: 300)
                          Higher = trust RAVE more early on
            fpu_reduction: First Play Urgency reduction (default: 0.0)
        """
        self.exploration_c = exploration_c
        self.rave_constant = rave_constant
        self.fpu_reduction = fpu_reduction

    def select(self, node: Node) -> Node:
        """Select child using UCB + RAVE hybrid formula."""
        current = node

        while True:
            if current.state.is_game_over():
                return current

            # If node has unexpanded moves OR no children, return for expansion
            if current.unexpanded_moves or not current.children:
                return current

            current = self._rave_select_child(current)

    def _rave_select_child(self, node: Node) -> Node:
        """Select child with highest UCB+RAVE value, with FPU and Solver support."""
        assert node.children, "Cannot select child of leaf without children"

        log_N = math.log(node.visits + 1)
        parent_value = node.q_value()  # For FPU

        def rave_ucb(move_key: Any, child: Node) -> float:
            # Solved nodes get infinite value
            if child.is_solved:
                if child.player_to_move != node.player_to_move:
                    return -child.solved_value * 1000
                else:
                    return child.solved_value * 1000

            if child.visits == 0:
                # First Play Urgency
                if self.fpu_reduction > 0:
                    return parent_value - self.fpu_reduction
                else:
                    return float("inf")

            # UCB component (standard exploitation + exploration)
            if child.player_to_move != node.player_to_move:
                ucb_exploit = -child.q_value()
            else:
                ucb_exploit = child.q_value()

            ucb_explore = self.exploration_c * math.sqrt(log_N / child.visits)
            ucb_value = ucb_exploit + ucb_explore

            # RAVE component (AMAF statistics)
            rave_visits = node.rave_visits.get(move_key, 0)
            if rave_visits > 0:
                rave_q = node.rave_q_value(move_key)

                # Beta: mixing parameter (transitions from RAVE to UCB as visits increase)
                # Formula: beta = sqrt(k / (3N + k)) where k is rave_constant
                beta = math.sqrt(
                    self.rave_constant / (3 * child.visits + self.rave_constant)
                )

                # Weighted average: beta * RAVE + (1-beta) * UCB
                if child.player_to_move != node.player_to_move:
                    rave_q = -rave_q  # Flip for opponent

                combined = beta * rave_q + (1 - beta) * ucb_exploit + ucb_explore
                return combined
            else:
                # No RAVE stats yet, use pure UCB
                return ucb_value

        best_move_key, best_child = max(
            node.children.items(),
            key=lambda item: rave_ucb(item[0], item[1])
        )
        return best_child


class DefaultExpansionStrategy(ExpansionStrategy):
    """Default expansion strategy that expands one unexpanded move."""

    def expand(self, node: Node) -> Optional[Node]:
        """Expand by creating a child for one unexpanded move."""
        if not node.unexpanded_moves:
            return None

        move = node.unexpanded_moves.pop()
        next_game = node.state.move(move)
        child = Node(
            state=next_game,
            player_to_move=next_game.current_player(),
            parent=node,
            move_from_parent=move,
            unexpanded_moves=next_game.get_legal_actions(),
        )

        # Use a hashable key for the children dict
        if isinstance(move, dict):
            move_key = move.get("id", repr(move))
        else:
            move_key = move  # assume already hashable (e.g. tuple, int, str)

        node.children[move_key] = child
        return child


class ProgressiveWideningExpansionStrategy(ExpansionStrategy):
    """
    Progressive Widening expansion strategy.

    Only expands a subset of moves initially, gradually widening as the node
    gets more visits. This focuses computational effort on the most promising moves.

    Formula: max_children = min(total_moves, base + widening_constant * visits^alpha)
    """

    def __init__(self, base: int = 1, widening_constant: float = 1.0, alpha: float = 0.5):
        """
        Args:
            base: Minimum number of children to expand (default 1)
            widening_constant: Scaling factor for widening (default 1.0)
            alpha: Exponent for visit count (default 0.5 for square root)
        """
        self.base = base
        self.widening_constant = widening_constant
        self.alpha = alpha

    def expand(self, node: Node) -> Optional[Node]:
        """
        Expand by creating a child, but only if we haven't exceeded the
        progressive widening threshold.
        """
        if not node.unexpanded_moves:
            return None

        # Calculate how many children we're allowed to have at this visit count
        total_moves = len(node.unexpanded_moves) + len(node.children)
        max_children = min(
            total_moves,
            self.base + int(self.widening_constant * (node.visits ** self.alpha))
        )

        # Only expand if we haven't reached the limit
        if len(node.children) >= max_children:
            return None

        # Expand one unexpanded move
        move = node.unexpanded_moves.pop()
        next_game = node.state.move(move)
        child = Node(
            state=next_game,
            player_to_move=next_game.current_player(),
            parent=node,
            move_from_parent=move,
            unexpanded_moves=next_game.get_legal_actions(),
        )

        # Use a hashable key for the children dict
        if isinstance(move, dict):
            move_key = move.get("id", repr(move))
        else:
            move_key = move  # assume already hashable (e.g. tuple, int, str)

        node.children[move_key] = child
        return child


class RandomSimulationStrategy(SimulationStrategy):
    """Random rollout simulation strategy."""

    def __init__(self, track_moves: bool = False):
        """
        Args:
            track_moves: If True, stores moves in a moves_played attribute for RAVE
        """
        self.track_moves = track_moves
        self.moves_played: List[Any] = []

    def simulate(self, node: Node, root_player: int) -> float:
        """Simulate game with random moves until terminal state."""
        game = node.state
        self.moves_played = []

        while not game.is_game_over():
            moves = game.get_legal_actions()
            if not moves:
                break
            move = random.choice(moves)
            if self.track_moves:
                self.moves_played.append(move)
            game = game.move(move)

        # Convert game_result to reward from root_player's perspective
        result = game.game_result()
        # game_result() returns result from current player's perspective
        # We need to convert it to root_player's perspective
        if game.current_player() == root_player:
            return result
        else:
            return -result


class HeuristicSimulation(SimulationStrategy):
    """
    Generic smart simulation that uses a move evaluator function.

    Works for any game by accepting a custom move evaluation function
    that ranks moves based on game-specific tactics.
    """

    def __init__(self, move_evaluator: Optional[callable] = None):
        """
        Args:
            move_evaluator: Optional function (game, moves) -> best_move
                           If None, falls back to random selection
        """
        self.move_evaluator = move_evaluator

    def simulate(self, node: Node, root_player: int) -> float:
        """Simulate with smart or random move selection."""
        game = node.state
        max_depth = 100  # Prevent infinite loops
        depth = 0

        while not game.is_game_over() and depth < max_depth:
            moves = game.get_legal_actions()
            if not moves:
                break

            if self.move_evaluator:
                move = self.move_evaluator(game, moves)
            else:
                move = random.choice(moves)

            game = game.move(move)
            depth += 1

        # Convert game_result to reward from root_player's perspective
        result = game.game_result()
        if game.current_player() == root_player:
            return result
        else:
            return -result


def get_simulation_strategy(name: str, move_evaluator: Optional[callable] = None) -> SimulationStrategy:
    """
    Factory function to create simulation strategy instances by name.

    Args:
        name: Strategy name - "random" or "heuristic"
        move_evaluator: Optional move evaluator function for heuristic strategy
                       (game, moves) -> best_move


    Returns:
        SimulationStrategy instance

    Raises:
        ValueError: If strategy name is unknown
    """
    name_lower = name.lower()

    if name_lower == "random":
        return RandomSimulationStrategy()
    elif name_lower == "heuristic":
        return HeuristicSimulation(move_evaluator=move_evaluator)
    else:
        available = "random, heuristic"
        raise ValueError(
            f"Unknown simulation strategy '{name}'. "
            f"Available options: {available}"
        )


def get_selection_strategy(name: str, exploration_c: float = 1.4) -> SelectionStrategy:
    """
    Factory function to create selection strategy instances by name.

    Args:
        name: Strategy name - "ucb" or "rave"
        exploration_c: Exploration constant for UCB

    Returns:
        SelectionStrategy instance

    Raises:
        ValueError: If strategy name is unknown
    """
    strategies = {
        "ucb": lambda: UCBSelectionStrategy(exploration_c),
        "rave": lambda: RAVESelectionStrategy(exploration_c),
    }

    name_lower = name.lower()
    if name_lower not in strategies:
        available = ", ".join(strategies.keys())
        raise ValueError(
            f"Unknown selection strategy '{name}'. "
            f"Available options: {available}"
        )

    return strategies[name_lower]()


def get_backpropagation_strategy(name: str) -> BackpropagationStrategy:
    """
    Factory function to create backpropagation strategy instances by name.

    Args:
        name: Strategy name - "default", "rave", or "solver"

    Returns:
        BackpropagationStrategy instance

    Raises:
        ValueError: If strategy name is unknown
    """
    strategies = {
        "default": DefaultBackpropagationStrategy,
        "rave": RAVEBackpropagationStrategy,
        "solver": SolverBackpropagationStrategy,
    }

    name_lower = name.lower()
    if name_lower not in strategies:
        available = ", ".join(strategies.keys())
        raise ValueError(
            f"Unknown backpropagation strategy '{name}'. "
            f"Available options: {available}"
        )

    return strategies[name_lower]()


def get_expansion_strategy(name: str, **kwargs) -> ExpansionStrategy:
    """
    Factory function to create expansion strategy instances by name.

    Args:
        name: Strategy name - "default" or "progressive_widening"
        **kwargs: Additional parameters for the strategy
            For progressive_widening:
                - base: int = 1 (minimum children)
                - widening_constant: float = 1.0 (scaling factor)
                - alpha: float = 0.5 (exponent for visit count)

    Returns:
        ExpansionStrategy instance

    Raises:
        ValueError: If strategy name is unknown
    """
    strategies = {
        "default": lambda: DefaultExpansionStrategy(),
        "progressive_widening": lambda: ProgressiveWideningExpansionStrategy(**kwargs),
    }

    name_lower = name.lower()
    if name_lower not in strategies:
        available = ", ".join(strategies.keys())
        raise ValueError(
            f"Unknown expansion strategy '{name}'. "
            f"Available options: {available}"
        )

    return strategies[name_lower]()


class DefaultBackpropagationStrategy(BackpropagationStrategy):
    """Default backpropagation strategy that updates visits and values."""

    def backpropagate(
        self,
        node: Node,
        reward: float,
        root_player: int = 0,
        simulation_moves: Optional[List[Any]] = None
    ) -> None:
        """
        Backpropagate reward up the tree from each node's player perspective.

        The reward comes from the simulation and represents the outcome from
        the root player's perspective. Each node stores value from its own
        player's perspective, so we flip the reward when the node's player
        differs from the root player.
        """
        current = node
        while current is not None:
            current.visits += 1

            # Convert reward to current node's player perspective
            if current.player_to_move == root_player:
                # Same player as root - use reward as-is
                current.value_sum += reward
            else:
                # Opponent of root player - flip reward
                current.value_sum += -reward

            current = current.parent


class RAVEBackpropagationStrategy(BackpropagationStrategy):
    """
    RAVE-aware backpropagation that updates both standard and RAVE statistics.

    For each node in the path from leaf to root, updates:
    - Standard visit/value statistics
    - RAVE statistics for all moves that appeared in the simulation
    """

    def backpropagate(
        self,
        node: Node,
        reward: float,
        root_player: int = 0,
        simulation_moves: Optional[List[Any]] = None
    ) -> None:
        """Backpropagate with RAVE updates."""
        if simulation_moves is None:
            simulation_moves = []

        # Create set of move keys for fast lookup
        move_keys = set()
        for move in simulation_moves:
            if isinstance(move, dict):
                move_key = move.get("id", repr(move))
            else:
                move_key = move
            move_keys.add(move_key)

        current = node
        while current is not None:
            # Standard backprop
            current.visits += 1

            if current.player_to_move == root_player:
                current.value_sum += reward
                player_reward = reward
            else:
                current.value_sum += -reward
                player_reward = -reward

            # RAVE backprop: update statistics for all simulation moves
            for move_key in move_keys:
                if move_key not in current.rave_visits:
                    current.rave_visits[move_key] = 0
                    current.rave_value_sum[move_key] = 0.0

                current.rave_visits[move_key] += 1
                current.rave_value_sum[move_key] += player_reward

            current = current.parent


class SolverBackpropagationStrategy(BackpropagationStrategy):
    """
    MCTS Solver: Detects and marks proven wins/losses/draws.

    A node is proven (solved) when:
    - It's terminal (immediate outcome known)
    - All children are solved and lead to same outcome
    - All children are expanded and best outcome is determined

    Proven nodes get infinite selection value, dramatically pruning the tree.
    """

    def backpropagate(
        self,
        node: Node,
        reward: float,
        root_player: int = 0,
        simulation_moves: Optional[List[Any]] = None
    ) -> None:
        """Backpropagate with solver detection."""
        current = node
        while current is not None:
            # Standard backprop
            current.visits += 1

            if current.player_to_move == root_player:
                current.value_sum += reward
            else:
                current.value_sum += -reward

            # Try to solve this node
            self._try_solve(current)

            current = current.parent

    def _try_solve(self, node: Node) -> None:
        """
        Attempt to mark this node as solved if all children lead to proven outcome.

        Solver rules (from node's player perspective):
        - If any child is a proven win for us → we can force a win
        - If all children are proven losses for us → this is a proven loss
        - If all children are solved and best is draw → this is a proven draw
        """
        # Can't solve if not all children expanded
        if node.unexpanded_moves:
            return

        # No children means terminal state (should be solved during expansion)
        if not node.children:
            return

        # Already solved
        if node.is_solved:
            return

        # Check if all children are solved
        all_solved = all(child.is_solved for child in node.children.values())
        if not all_solved:
            return

        # Collect child values from THIS node's perspective
        child_values = []
        for child in node.children.values():
            if child.player_to_move != node.player_to_move:
                # Opponent node: their win is our loss
                child_values.append(-child.solved_value)
            else:
                # Same player (unusual in 2-player games)
                child_values.append(child.solved_value)

        # Node value is the best outcome we can force
        best_value = max(child_values)

        # Mark as solved
        node.is_solved = True
        node.solved_value = best_value


class MCTSPhaseState(ABC):
    """
    State interface for a single phase of the MCTS iteration.
    Each concrete state performs its phase and returns the next state.
    """

    @abstractmethod
    def handle(self, context: MCTSContext) -> Optional["MCTSPhaseState"]:
        """
        Perform this phase's work on the context and return the next phase.
        Returning None indicates the iteration is finished.
        """
        pass


class SelectionPhaseState(MCTSPhaseState):
    """State for the Selection phase."""

    def handle(self, context: MCTSContext) -> Optional[MCTSPhaseState]:
        # Start at root each iteration, delegate to selection strategy
        node = context.selection_strategy.select(context.root)
        context.current_node = node
        return ExpansionPhaseState()


class ExpansionPhaseState(MCTSPhaseState):
    """State for the Expansion phase."""

    def handle(self, context: MCTSContext) -> Optional[MCTSPhaseState]:
        node = context.current_node
        if node is None:
            # Nothing to expand, go straight to simulation
            return SimulationPhaseState()

        expanded = context.expansion_strategy.expand(node)
        if expanded is not None:
            context.current_node = expanded

        return SimulationPhaseState()


class SimulationPhaseState(MCTSPhaseState):
    """State for the Simulation phase."""

    def handle(self, context: MCTSContext) -> Optional[MCTSPhaseState]:
        node = context.current_node
        if node is None:
            context.reward = 0.0
            context.simulation_moves = []
            return BackpropagationPhaseState()

        reward = context.simulation_strategy.simulate(
            node,
            context.root_player,
        )
        context.reward = reward

        # Extract moves from simulation if available (for RAVE)
        if hasattr(context.simulation_strategy, 'moves_played'):
            context.simulation_moves = context.simulation_strategy.moves_played
        else:
            context.simulation_moves = []

        return BackpropagationPhaseState()


class BackpropagationPhaseState(MCTSPhaseState):
    """State for the Backpropagation phase."""

    def handle(self, context: MCTSContext) -> Optional[MCTSPhaseState]:
        node = context.current_node
        if node is not None:
            context.backpropagation_strategy.backpropagate(
                node, context.reward, context.root_player, context.simulation_moves
            )

        # End this MCTS iteration
        return None






# Main Search Algorithm Strategy

class SearchAlgorithmStrategy(ABC):
    """Strategy interface for tree search algorithms."""

    @abstractmethod
    def search(self, root_state: Any, iterations: int, root_player: Optional[int] = None) -> Any:
        """
        Search for the best move from the given state.

        Args:
            root_state: The state to search from
            iterations: Number of search iterations to perform
            root_player: The player to search for (if None, determined from state)

        Returns:
            The best move found
        """
        pass


class MCTSStrategy(SearchAlgorithmStrategy):
    """Monte Carlo Tree Search algorithm implementation using pluggable strategies."""

    def __init__(
        self,
        selection_strategy: Optional[SelectionStrategy] = None,
        expansion_strategy: Optional[ExpansionStrategy] = None,
        simulation_strategy: Optional[SimulationStrategy] = None,
        backpropagation_strategy: Optional[BackpropagationStrategy] = None,
        exploration_c: float = 1.4,
    ):
        self.selection_strategy = selection_strategy or UCBSelectionStrategy(exploration_c)
        self.expansion_strategy = expansion_strategy or DefaultExpansionStrategy()
        self.simulation_strategy = simulation_strategy or RandomSimulationStrategy()
        self.backpropagation_strategy = backpropagation_strategy or DefaultBackpropagationStrategy()

    def search(self, root_state: Any, iterations: int, root_player: Optional[int] = None) -> Any:
        """
        Execute MCTS search using the configured strategies.

        Args:
            root_state: A game object that satisfies the GameEnv Protocol (e.g., TurnBasedGame)
            iterations: Number of MCTS iterations to run
            root_player: Player index to search for (if None, determined from root_state)

        Returns:
            The best move found
        """
        if root_player is None:
            root_player = root_state.current_player()

        root = Node(
            state=root_state,
            player_to_move=root_state.current_player(),
            unexpanded_moves=root_state.get_legal_actions(),
        )

        # Shared context for all iterations
        context = MCTSContext(
            root=root,
            root_player=root_player,
            selection_strategy=self.selection_strategy,
            expansion_strategy=self.expansion_strategy,
            simulation_strategy=self.simulation_strategy,
            backpropagation_strategy=self.backpropagation_strategy,
        )

        for _ in range(iterations):
            # Start each iteration in the Selection phase
            state: Optional[MCTSPhaseState] = SelectionPhaseState()
            while state is not None:
                state = state.handle(context)

        if not root.children:
            return None

        # Pick child with most visits
        _, best_child = max(
            root.children.items(),
            key=lambda item: item[1].visits,
        )

        # Return the original move dict stored in the child
        return best_child.move_from_parent


class MCTS:
    """
    Monte Carlo Tree Search - Backward compatibility wrapper.

    This class wraps MCTSStrategy to maintain backward compatibility
    with existing code while using the new strategy pattern internally.

    For new code, consider using MCTSStrategy directly for more flexibility.
    """

    def __init__(
        self,
        env: Optional[GameEnv] = None,
        exploration_c: float = 1.4,
        selection_strategy: Optional[SelectionStrategy] = None,
        expansion_strategy: Optional[ExpansionStrategy] = None,
        simulation_strategy: Optional[SimulationStrategy] = None,
        backpropagation_strategy: Optional[BackpropagationStrategy] = None,
    ):
        """
        Initialize MCTS with optional custom strategies.

        Args:
            env: DEPRECATED - No longer needed. Game states are now GameEnv objects themselves.
            exploration_c: Exploration constant for UCB (default: 1.4)
            selection_strategy: Custom selection strategy (default: UCBSelectionStrategy)
            expansion_strategy: Custom expansion strategy (default: DefaultExpansionStrategy)
            simulation_strategy: Custom simulation strategy (default: RandomSimulationStrategy)
            backpropagation_strategy: Custom backpropagation strategy (default: DefaultBackpropagationStrategy)
        """
        if env is not None:
            import warnings
            warnings.warn("The 'env' parameter is deprecated and no longer used. "
                         "Pass TurnBasedGame objects directly to search().", DeprecationWarning)
        self.exploration_c = exploration_c
        self._strategy = MCTSStrategy(
            selection_strategy=selection_strategy,
            expansion_strategy=expansion_strategy,
            simulation_strategy=simulation_strategy,
            backpropagation_strategy=backpropagation_strategy,
            exploration_c=exploration_c,
        )

    def search(self, root_state: Any, iterations: int, root_player: Optional[int] = None) -> Any:
        """
        Search for the best move from the given state.

        Args:
            root_state: A game object that satisfies the GameEnv Protocol (e.g., TurnBasedGame)
            iterations: Number of search iterations to perform
            root_player: The player to search for (if None, determined from state)

        Returns:
            The best move found
        """
        return self._strategy.search(root_state, iterations, root_player)
