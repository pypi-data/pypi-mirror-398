"""
Event listener for the gaming platform.

This module handles listening to typed events from RabbitMQ and dispatching
them to registered callback functions.
"""

try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False
    pika = None

import os
import json
import threading
from typing import Callable, Optional, Dict
from uuid import UUID

from .events import (
    LobbyOfOnePlayerIsReadyToPlayPveEvent,
    LobbyOfTwoPlayersIsReadyToPlayPvPEvent,
    parse_event,
)


class EventListenerConfig:
    """Configuration for event listening."""

    def __init__(
        self,
        exchange_name: str = "platform.events",
        exchange_type: str = "topic",
        rabbitmq_host: Optional[str] = None,
        rabbitmq_port: Optional[int] = None,
        rabbitmq_user: Optional[str] = None,
        rabbitmq_password: Optional[str] = None,
    ):
        """
        Initialize listener configuration.

        Args:
            exchange_name: RabbitMQ exchange name (default: "platform.events")
            exchange_type: Exchange type (default: "topic")
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


class EventListener:
    """
    Listens to typed events from RabbitMQ and dispatches to callbacks.

    This listener:
    - Subscribes to platform events (lobby ready events)
    - Automatically parses JSON to typed event objects
    - Dispatches to registered callback functions
    - Runs in background thread for async listening
    """

    # Routing configuration for incoming events
    ROUTING_CONFIG = {
        "pve_lobby": {
            "queue": "lobby.ready.pve",
            "routing_key": "platform.lobby.pve.ready.*",
            "event_type": "lobby_pve_ready"
        },
        "pvp_lobby": {
            "queue": "lobby.ready.pvp",
            "routing_key": "platform.lobby.pvp.ready.*",
            "event_type": "lobby_pvp_ready"
        },
    }

    def __init__(self, config: Optional[EventListenerConfig] = None):
        """
        Initialize event listener.

        Args:
            config: Listener configuration (uses defaults if None)
        """
        self.config = config or EventListenerConfig()
        self.connection = None
        self.channel = None
        self.connected = False

        # Callback registry
        self._callbacks: Dict[str, Callable] = {}

        # Threading
        self._consumer_thread = None
        self._consuming = False

        if not PIKA_AVAILABLE:
            print("WARNING: pika not available, event consumption disabled")
            return

    def _connect(self):
        """Establish connection to RabbitMQ."""
        credentials = pika.PlainCredentials(self.config.user, self.config.password)
        parameters = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.connected = True

    def _setup_infrastructure(self):
        """
        Declare exchange, queues, and bindings.

        This ensures all infrastructure exists before consuming.
        """
        if not self.channel:
            return

        # Declare the platform exchange
        self.channel.exchange_declare(
            exchange=self.config.exchange_name,
            exchange_type=self.config.exchange_type,
            durable=True
        )

        # Declare queues and bindings for each event type
        for config_key, routing in self.ROUTING_CONFIG.items():
            queue_name = routing["queue"]
            routing_key = routing["routing_key"]

            # Declare queue
            self.channel.queue_declare(queue=queue_name, durable=True)

            # Bind queue to exchange with routing key pattern
            self.channel.queue_bind(
                exchange=self.config.exchange_name,
                queue=queue_name,
                routing_key=routing_key
            )

    def on_pve_lobby_ready(self, callback: Callable[[LobbyOfOnePlayerIsReadyToPlayPveEvent], None]):
        """
        Register callback for PvE lobby ready events.

        Args:
            callback: Function that accepts LobbyOfOnePlayerIsReadyToPlayPveEvent

        Example:
            def handle_pve(event: LobbyOfOnePlayerIsReadyToPlayPveEvent):
                print(f"PvE lobby ready: {event.playerId} vs AI ({event.aiDifficulty})")
                # Create game session...

            listener.on_pve_lobby_ready(handle_pve)
        """
        self._callbacks["pve_lobby"] = callback

    def on_pvp_lobby_ready(self, callback: Callable[[LobbyOfTwoPlayersIsReadyToPlayPvPEvent], None]):
        """
        Register callback for PvP lobby ready events.

        Args:
            callback: Function that accepts LobbyOfTwoPlayersIsReadyToPlayPvPEvent

        Example:
            def handle_pvp(event: LobbyOfTwoPlayersIsReadyToPlayPvPEvent):
                print(f"PvP lobby ready: {event.player1Name} vs {event.player2Name}")
                # Create game session...

            listener.on_pvp_lobby_ready(handle_pvp)
        """
        self._callbacks["pvp_lobby"] = callback

    def _create_message_handler(self, event_type_key: str):
        """
        Create a message handler for a specific event type.

        Args:
            event_type_key: Key in ROUTING_CONFIG ("pve_lobby" or "pvp_lobby")

        Returns:
            Callback function for pika consumption
        """
        def handler(ch, method, properties, body):
            try:
                # Parse JSON message
                message_str = body.decode('utf-8')

                # Get event type for parsing
                routing = self.ROUTING_CONFIG[event_type_key]
                event_type = routing["event_type"]

                # Parse to typed event
                event = parse_event(message_str, event_type)

                # Dispatch to registered callback
                if event_type_key in self._callbacks:
                    callback = self._callbacks[event_type_key]
                    callback(event)
                else:
                    print(f"WARNING: No callback registered for {event_type_key}")

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print(f"ERROR processing message: {e}")
                # Reject and requeue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        return handler

    def start(self, blocking: bool = False):
        """
        Start consuming events.

        Args:
            blocking: If True, blocks current thread. If False, runs in background thread.

        Raises:
            RuntimeError: If no callbacks registered
        """
        if not self._callbacks:
            raise RuntimeError("No callbacks registered. Use on_pve_lobby_ready() or on_pvp_lobby_ready()")

        if not PIKA_AVAILABLE:
            print("WARNING: Cannot start consumer - pika not available")
            return

        try:
            self._connect()
            self._setup_infrastructure()
        except Exception as e:
            print(f"ERROR: Failed to connect to RabbitMQ: {e}")
            return

        # Set up consumers for each registered callback
        for event_type_key, callback in self._callbacks.items():
            routing = self.ROUTING_CONFIG[event_type_key]
            queue_name = routing["queue"]

            # Create message handler
            handler = self._create_message_handler(event_type_key)

            # Start consuming
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=handler,
                auto_ack=False  # Manual acknowledgement for reliability
            )

            print(f"✓ Consuming {event_type_key} events from queue: {queue_name}")

        self._consuming = True

        # Start consumption
        if blocking:
            print("Starting event consumption (blocking)...")
            self.channel.start_consuming()
        else:
            self._consumer_thread = threading.Thread(
                target=self._consume_in_thread,
                daemon=True
            )
            self._consumer_thread.start()
            print("✓ Event consumption started in background thread")

    def _consume_in_thread(self):
        """Run consumption in background thread."""
        try:
            print("Background consumer thread started")
            self.channel.start_consuming()
        except Exception as e:
            print(f"Consumer thread error: {e}")
        finally:
            self._consuming = False

    def stop(self):
        """Stop consuming events."""
        if self._consuming and self.channel:
            print("Stopping event consumption...")
            self.channel.stop_consuming()
            self._consuming = False

        if self._consumer_thread and self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=5)

    def close(self):
        """Close RabbitMQ connection."""
        self.stop()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.connected = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
