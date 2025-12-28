"""
Event publisher for the gaming platform.

This module handles publishing typed events to RabbitMQ with proper
exchange and routing key configuration compatible with the Java backend.
"""

try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False
    pika = None

import os
import json
from typing import Optional
from uuid import UUID

from .events import (
    DomainEvent,
    GameStartedEvent,
    GameEndedEvent,
)


class EventPublisherConfig:
    """Configuration for event publishing."""

    def __init__(
        self,
        exchange_name: str = "game.events",
        exchange_type: str = "topic",
        rabbitmq_host: Optional[str] = None,
        rabbitmq_port: Optional[int] = None,
        rabbitmq_user: Optional[str] = None,
        rabbitmq_password: Optional[str] = None,
    ):
        """
        Initialize publisher configuration.

        Args:
            exchange_name: RabbitMQ exchange name (default: "game.events")
            exchange_type: Exchange type (default: "topic" for routing key patterns)
            rabbitmq_host: RabbitMQ host (default: from env or localhost)
            rabbitmq_port: RabbitMQ port (default: from env or 6000)
            rabbitmq_user: Username (default: from env or "user")
            rabbitmq_password: Password (default: from env or "password")
        """
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.host = rabbitmq_host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = rabbitmq_port or int(os.getenv('RABBITMQ_PORT', 5672))
        self.user = rabbitmq_user or os.getenv('RABBITMQ_USER', 'user')
        self.password = rabbitmq_password or os.getenv('RABBITMQ_PASSWORD', 'password')


class EventPublisher:
    """
    Publishes typed events to RabbitMQ with proper routing.

    This publisher:
    - Uses topic exchanges for flexible routing
    - Declares queues and bindings automatically
    - Maps event types to routing keys
    - Handles graceful degradation if RabbitMQ unavailable
    """

    # Routing configuration for outgoing events
    ROUTING_CONFIG = {
        GameStartedEvent: {
            "queue": "game.started",
            "routing_key": "sdk.game.started.v1"
        },
        GameEndedEvent: {
            "queue": "game.ended",
            "routing_key": "sdk.game.ended.v1"
        },
    }

    def __init__(self, config: Optional[EventPublisherConfig] = None):
        """
        Initialize event publisher.

        Args:
            config: Publisher configuration (uses defaults if None)
        """
        self.config = config or EventPublisherConfig()
        self.connection = None
        self.channel = None
        self.connected = False

        if not PIKA_AVAILABLE:
            print("WARNING: pika not available, events will be printed to stdout")
            return

        try:
            self._connect()
            self._setup_infrastructure()
        except Exception as e:
            print(f"WARNING: Failed to connect to RabbitMQ: {e}")
            print("Events will be printed to stdout instead")
            self.connected = False

    def _connect(self):
        """Establish connection to RabbitMQ."""
        credentials = pika.PlainCredentials(self.config.user, self.config.password)
        parameters = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.connected = True

    def _setup_infrastructure(self):
        """
        Declare exchange, queues, and bindings.

        This ensures all infrastructure exists before publishing.
        """
        if not self.channel:
            return

        # Declare the main exchange
        self.channel.exchange_declare(
            exchange=self.config.exchange_name,
            exchange_type=self.config.exchange_type,
            durable=True
        )

        # Declare queues and bindings for each event type
        for event_class, routing in self.ROUTING_CONFIG.items():
            queue_name = routing["queue"]
            routing_key = routing["routing_key"]

            # Declare queue
            self.channel.queue_declare(queue=queue_name, durable=True)

            # Bind queue to exchange with routing key
            self.channel.queue_bind(
                exchange=self.config.exchange_name,
                queue=queue_name,
                routing_key=routing_key
            )

    def publish(self, event: DomainEvent):
        """
        Publish a typed event.

        Args:
            event: Event instance to publish

        Raises:
            ValueError: If event type has no routing configuration
        """
        event_class = type(event)

        # Get routing configuration
        if event_class not in self.ROUTING_CONFIG:
            raise ValueError(f"No routing configuration for {event_class.__name__}")

        routing = self.ROUTING_CONFIG[event_class]
        routing_key = routing["routing_key"]

        # Serialize event
        message_body = event.to_json()

        # Publish to RabbitMQ or fallback to stdout
        if self.connected and self.channel:
            self._publish_to_rabbitmq(routing_key, message_body)
        else:
            self._print_to_stdout(event_class.__name__, routing_key, message_body)

    def _publish_to_rabbitmq(self, routing_key: str, message_body: str):
        """Publish message to RabbitMQ."""
        self.channel.basic_publish(
            exchange=self.config.exchange_name,
            routing_key=routing_key,
            body=message_body.encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json'
            )
        )
        print(f"✓ Published event: {routing_key}")

    def _print_to_stdout(self, event_name: str, routing_key: str, message_body: str):
        """Fallback: print event to stdout."""
        print(f"\n[EVENT] {event_name}")
        print(f"  Routing Key: {routing_key}")
        print(f"  Body: {message_body}")

    def publish_game_started(
        self,
        session_id: str,
        lobby_id: UUID,
        game_id: str,
        player_ids: list[str],
        mode: str
    ):
        """
        Convenience method to publish GameStartedEvent.

        Args:
            session_id: Game session ID
            lobby_id: Lobby UUID
            game_id: Game identifier
            player_ids: List of player IDs
            mode: "PvP" or "PvE"
        """
        from .events import create_game_started_event

        event = create_game_started_event(
            session_id=session_id,
            lobby_id=lobby_id,
            game_id=game_id,
            player_ids=player_ids,
            mode=mode
        )
        self.publish(event)

    def publish_game_ended(
        self,
        session_id: str,
        lobby_id: UUID,
        game_id: str,
        winner_id: Optional[str],
        reason: str,
        final_state: Optional[dict] = None
    ):
        """
        Convenience method to publish GameEndedEvent.

        Args:
            session_id: Game session ID
            lobby_id: Lobby UUID
            game_id: Game identifier
            winner_id: Winner's player ID (None for draws)
            reason: "win", "draw", "forfeit", "disconnect"
            final_state: Optional game state data
        """
        from .events import create_game_ended_event

        event = create_game_ended_event(
            session_id=session_id,
            lobby_id=lobby_id,
            game_id=game_id,
            winner_id=winner_id,
            reason=reason,
            final_state=final_state
        )
        self.publish(event)

    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.connected = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
