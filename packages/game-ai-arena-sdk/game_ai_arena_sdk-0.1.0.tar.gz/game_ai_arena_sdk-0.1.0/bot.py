from abc import ABC, abstractmethod
from .types import GameStateLoop, GameStateEnd, Move


class Bot(ABC):
    """
    Abstract base class for bots.

    Subclass this and implement on_move() to create your bot.
    """

    def __init__(self, bot_id: str, api_key: str):
        self.id = bot_id
        self.api_key = api_key

    @abstractmethod
    async def on_move(self, state: GameStateLoop) -> Move:
        """
        Called when it's your turn. Return your move.

        Args:
            state: Current game state with:
                - board: str (board representation)
                - my_side: PlayerSide (your side)
                - current_turn: PlayerSide (whose turn - always yours here)
                - legal_moves: list[PieceMovesInfo] (pieces you can move)

        Returns:
            Move with from_pos and to_pos
        """
        pass

    # --- Optional lifecycle hooks ---

    async def on_ready(self) -> None:
        """Called when connected to matchmaker WebSocket."""
        pass

    async def on_queue_entry(self) -> None:
        """Called when joined the matchmaking queue."""
        pass

    async def on_queue_exit(self) -> None:
        """Called when leaving the queue (match found or cancelled)."""
        pass

    async def on_match_found(self, match_id: str) -> None:
        """Called when matched with an opponent."""
        pass

    async def on_room_joined(self, room_id: str) -> None:
        """Called when successfully joined a game room."""
        pass

    async def on_game_start(self, state: GameStateLoop) -> None:
        """Called when game starts (before first on_move)."""
        pass

    async def on_game_end(self, winner: str | None, state: GameStateEnd) -> None:
        """
        Called when game ends.

        Args:
            winner: "white", "black", or None (draw)
            state: Final game state with winner field
        """
        pass

    async def on_disconnect(self, reason: str) -> None:
        """Called when disconnected from server."""
        pass
