import uuid
import json
from typing import Any, Dict, List, Optional


def symbol_to_int(cell: str, players: List[Dict[str, Any]]) -> int:
    """
    Map a visual symbol from the game board (" ", "X", "O") to an int:

      0 = empty
      1 = player 1 piece
      2 = player 2 piece
      ...

    players is expected to contain "symbol" for each player:
      players = [
        {"id": "P1", "type": "human", "symbol": "X"},
        {"id": "P2", "type": "human", "symbol": "O"},
      ]
    """
    if cell.strip() == "":
        return 0

    for idx, p in enumerate(players):
        if p.get("symbol") == cell:
            return idx + 1

    return 0


def build_generic_state(
    game_id: str,
    board: List[List[str]],
    players: List[Dict[str, Any]],
    current_player_symbol: str,
    move_count: int,
    finished: bool,
    legal_moves: Optional[List[Dict[str, Any]]] = None,
    result: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    turn_index = 0
    for idx, p in enumerate(players):
        if p.get("symbol") == current_player_symbol:
            turn_index = idx
            break

    int_board = [
        [symbol_to_int(cell, players) for cell in row]
        for row in board
    ]

    status = "FINISHED" if finished else "IN_PROGRESS"

    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    state: Dict[str, Any] = {
        "game_id": game_id,
        "turn_index": turn_index,
        "players": players,
        "board": {
            "representation": "grid",
            "rows": rows,
            "cols": cols,
            "cells": int_board,
            "legend": {
                "0": "empty",
                "1": "player_1_piece",
                "2": "player_2_piece",
            },
        },
        "status": status,
        "is_terminal": finished,
        "extra": {
            "move_count": move_count,
        },
    }

    if legal_moves is not None:
        state["legal_moves"] = legal_moves

    if finished and result is not None:
        state["result"] = result

    fingerprint_payload = {
        "game_id": game_id,
        "turn_index": turn_index,
        "board": int_board,
        "status": status,
        "extra": state["extra"],
        "legal_moves": legal_moves,
        "result": result,
    }
    state["state_id"] = str(
        uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(fingerprint_payload, sort_keys=True))
    )

    return state


def detect_move(
    old_board: List[List[str]],
    new_board: List[List[str]],
    players: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Compare boards before and after a move and return the move dict.
    """
    rows = len(new_board)
    cols = len(new_board[0]) if rows > 0 else 0

    for r in range(rows):
        for c in range(cols):
            if old_board[r][c] != new_board[r][c]:
                symbol = new_board[r][c]
                # find the player index by symbol
                player_index = 0
                for idx, p in enumerate(players):
                    if p.get("symbol") == symbol:
                        player_index = idx
                        break

                return {
                    "player_index": player_index,
                    "position": {"row": r, "col": c},
                    "type": "PLACE_MARK",
                }

    return None


def simple_heuristic(
    board: List[List[str]],
    players: List[Dict[str, Any]],
) -> float:
    """
    Very simple heuristic: (#cells of P1 - #cells of P2).
    """
    if len(players) < 2:
        return 0.0

    sym1 = players[0].get("symbol")
    sym2 = players[1].get("symbol")

    p1 = sum(cell == sym1 for row in board for cell in row)
    p2 = sum(cell == sym2 for row in board for cell in row)
    return float(p1 - p2)
