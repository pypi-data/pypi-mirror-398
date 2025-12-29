from enum import Enum
from pydantic import BaseModel, Field


class GameType(str, Enum):
    """Available game types."""
    FLIPFLOP_3X3 = "flipflop_3x3"
    FLIPFLOP_5X5 = "flipflop_5x5"
    FLIPFOUR = "flipfour"
    AMOEBA = "amoeba"


class PlayerSide(str, Enum):
    """The two sides in a game."""
    WHITE = "white"
    BLACK = "black"


class Move(BaseModel):
    """A move from one position to another."""
    from_pos: str
    to_pos: str


class PieceMovesInfo(BaseModel):
    """Info about a piece and where it can move."""
    name: str
    pos: str
    valid_moves: list[str]


class GameStateBase(BaseModel):
    """Common fields for all game states."""
    board: str
    current_turn: PlayerSide
    my_side: PlayerSide


class GameStateLoop(GameStateBase):
    """
    Game state during gameplay.

    Passed to on_move() - contains legal_moves for decision making.
    """
    legal_moves: list[PieceMovesInfo]


class GameStateEnd(GameStateBase):
    """
    Game state at game end.

    Passed to on_game_end() - contains winner (None if draw).
    """
    winner: PlayerSide | None = None


__all__ = [
    "GameType",
    "PlayerSide",
    "Move",
    "PieceMovesInfo",
    "GameStateBase",
    "GameStateLoop",
    "GameStateEnd",
]
