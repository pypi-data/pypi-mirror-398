"""
ML Client for Win Probability Predictions

This module provides a client for interacting with the ML model API
to get win probability predictions for game states.
"""

import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class MLPredictionClient:
    """
    Client for making predictions using the ML model API.

    Example:
        >>> client = MLPredictionClient(base_url="http://localhost:8000")
        >>> board = [[1, 0, 0], [0, 2, 0], [0, 0, 0]]
        >>> probs = client.predict_win_probability(
        ...     board_cells=board,
        ...     turn_index=0,
        ...     model_type="hybrid"
        ... )
        >>> print(f"Win: {probs['win']:.1%}, Loss: {probs['loss']:.1%}, Draw: {probs['draw']:.1%}")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 5,
    ):
        """
        Initialize the ML prediction client.

        Args:
            base_url: Base URL of the ML API service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def predict_win_probability(
        self,
        board_cells: List[List[int]],
        turn_index: int,
        model_type: str = "hybrid"
    ) -> Dict[str, float]:
        """
        Get win/loss/draw probabilities for the current game state.

        Args:
            board_cells: 3x3 board where 0=empty, 1=player1 (X), 2=player2 (O)
            turn_index: Current player's turn (0 for player1/X, 1 for player2/O)
            model_type: "hybrid" (Rules + ML) or "baseline" (Pure ML)

        Returns:
            Dictionary with 'win', 'loss', 'draw' probabilities (0.0 to 1.0)

        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the response format is invalid
        """
        if model_type not in ["hybrid", "baseline"]:
            raise ValueError(f"model_type must be 'hybrid' or 'baseline', got: {model_type}")

        endpoint = f"{self.base_url}/win-probability/{model_type}"

        payload = {
            "state": {
                "board": {"cells": board_cells},
                "turn_index": turn_index
            }
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            data = response.json()

            # Validate response format
            required_keys = ['win', 'loss', 'draw']
            if not all(key in data for key in required_keys):
                raise ValueError(f"Invalid response format. Expected keys: {required_keys}")

            return {
                'win': data['win'],
                'loss': data['loss'],
                'draw': data['draw'],
                'model_type': data.get('model_type', model_type)
            }

        except requests.Timeout:
            logger.error(f"Request timeout after {self.timeout}s")
            raise
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid response format: {e}")
            raise

    def predict_move(
        self,
        board_cells: List[List[int]],
        turn_index: int,
        model_type: str = "catboost"
    ) -> Dict[str, Any]:
        """
        Get the best move prediction from the policy models.

        Args:
            board_cells: 3x3 board where 0=empty, 1=player1 (X), 2=player2 (O)
            turn_index: Current player's turn (0 for player1/X, 1 for player2/O)
            model_type: "decision-tree", "catboost", or "xgboost"

        Returns:
            Dictionary with 'predicted_move' (0-8), 'predicted_position' (row, col),
            'probability', and 'model_type'

        Raises:
            requests.RequestException: If the API request fails
        """
        if model_type not in ["decision-tree", "catboost", "xgboost"]:
            raise ValueError(
                f"model_type must be 'decision-tree', 'catboost', or 'xgboost', got: {model_type}"
            )

        endpoint = f"{self.base_url}/predict/{model_type}"

        payload = {
            "state": {
                "board": {"cells": board_cells},
                "turn_index": turn_index
            }
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Move prediction failed: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the ML API service.

        Returns:
            Dictionary with service health information
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            raise

    def is_available(self) -> bool:
        """
        Quick check if the ML API service is available.

        Returns:
            True if service is responding, False otherwise
        """
        try:
            self.health_check()
            return True
        except:
            return False


def convert_board_to_cells(board: List[List[str]], symbol_map: Optional[Dict[str, int]] = None) -> List[List[int]]:
    """
    Convert a board with string symbols to numeric cells for ML API.

    Args:
        board: Board with string symbols (e.g., 'X', 'O', '')
        symbol_map: Optional mapping from symbols to numbers
                   Default: {'X': 1, 'O': 2, '': 0}

    Returns:
        Board with numeric values (0=empty, 1=player1, 2=player2)

    Example:
        >>> board = [['X', '', ''], ['', 'O', ''], ['', '', '']]
        >>> cells = convert_board_to_cells(board)
        >>> print(cells)
        [[1, 0, 0], [0, 2, 0], [0, 0, 0]]
    """
    if symbol_map is None:
        symbol_map = {'X': 1, 'O': 2, '': 0, ' ': 0}

    return [
        [symbol_map.get(cell, 0) for cell in row]
        for row in board
    ]
