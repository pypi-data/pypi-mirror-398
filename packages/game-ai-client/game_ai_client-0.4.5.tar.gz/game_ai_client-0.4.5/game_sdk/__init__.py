from .client import GameClient
from .ai_client import AIGameClient
from .ml_client import MLPredictionClient, convert_board_to_cells
from .integration import GameIntegrationSpec, GenericGameAdapter, load_integration
from .mcts import (
    MCTS,
    GameEnv,
    # Strategy interfaces
    SearchAlgorithmStrategy,
    SelectionStrategy,
    ExpansionStrategy,
    SimulationStrategy,
    BackpropagationStrategy,
    # Strategy implementations
    MCTSStrategy,
    UCBSelectionStrategy,
    DefaultExpansionStrategy,
    RandomSimulationStrategy,
    DefaultBackpropagationStrategy,
)
from .utils import (
    symbol_to_int,
    build_generic_state,
    detect_move,
    simple_heuristic,
)
from .registration import (
    register_game,
    validate_integration,
    create_ai_integration_template,
)
from .events import (
    # Base event
    DomainEvent,
    # Outgoing events (Game → Platform)
    GameStartedEvent,
    GameEndedEvent,
    # Incoming events (Platform → Game)
    LobbyOfOnePlayerIsReadyToPlayPveEvent,
    LobbyOfTwoPlayersIsReadyToPlayPvPEvent,
    # ML Player events
    MLMoveRequestEvent,
    MLMoveResponseEvent,
    # Event utilities
    parse_event,
    create_game_started_event,
    create_game_ended_event,
)
from .event_publisher import EventPublisher, EventPublisherConfig
from .event_listener import EventListener, EventListenerConfig

__all__ = [
    # Clients
    "GameClient",
    "AIGameClient",
    "MLPredictionClient",
    "convert_board_to_cells",
    "GameIntegrationSpec",
    "GenericGameAdapter",
    "load_integration",
    # Registration helpers
    "register_game",
    "validate_integration",
    "create_ai_integration_template",
    # Main MCTS (backward compatible)
    "MCTS",
    "GameEnv",
    # Strategy interfaces
    "SearchAlgorithmStrategy",
    "SelectionStrategy",
    "ExpansionStrategy",
    "SimulationStrategy",
    "BackpropagationStrategy",
    # Strategy implementations
    "MCTSStrategy",
    "UCBSelectionStrategy",
    "DefaultExpansionStrategy",
    "RandomSimulationStrategy",
    "DefaultBackpropagationStrategy",
    # Utilities
    "symbol_to_int",
    "build_generic_state",
    "detect_move",
    "simple_heuristic",
    # Events
    "DomainEvent",
    "GameStartedEvent",
    "GameEndedEvent",
    "LobbyOfOnePlayerIsReadyToPlayPveEvent",
    "LobbyOfTwoPlayersIsReadyToPlayPvPEvent",
    "MLMoveRequestEvent",
    "MLMoveResponseEvent",
    "parse_event",
    "create_game_started_event",
    "create_game_ended_event",
    # Event messaging
    "EventPublisher",
    "EventPublisherConfig",
    "EventListener",
    "EventListenerConfig",
]
