import asyncio
import json
from websockets import connect, ClientConnection

from .bot import Bot
from .types import GameType, GameStateLoop, GameStateEnd, PlayerSide, PieceMovesInfo


DNS = "127.0.0.1"
MATCHMAKER_URL = f"ws://{DNS}:8000/matchmaking/ws"


def _auth_header(bot: Bot) -> dict[str, str]:
    """Build authorization header for WebSocket connections."""
    return {"Authorization": f"Bot {bot.id}:{bot.api_key}"}


def _build_loop_state(
    board: str,
    current_turn: str,
    my_side: str,
    legal_moves: list[dict],
) -> GameStateLoop:
    """Build game state for during gameplay."""
    return GameStateLoop(
        board=board,
        current_turn=PlayerSide(current_turn),
        my_side=PlayerSide(my_side),
        legal_moves=[PieceMovesInfo(**m) for m in legal_moves],
    )


def _build_end_state(
    board: str,
    current_turn: str,
    my_side: str,
    winner: str | None,
) -> GameStateEnd:
    """Build game state for game end."""
    return GameStateEnd(
        board=board,
        current_turn=PlayerSide(current_turn),
        my_side=PlayerSide(my_side),
        winner=PlayerSide(winner) if winner else None,
    )


async def _connect_matchmaker(bot: Bot, matchmaker_url: str) -> ClientConnection:
    """
    Connect to the matchmaker WebSocket.

    Triggers: on_ready()
    """
    headers = _auth_header(bot)
    matchmaker = await connect(matchmaker_url, additional_headers=headers)

    msg = json.loads(await matchmaker.recv())
    assert msg["type"] == "connected", f"Expected 'connected', got {msg}"

    await bot.on_ready()

    return matchmaker


async def _join_queue(
    bot: Bot, matchmaker: ClientConnection, game_type: GameType
) -> None:
    """
    Join the matchmaking queue.

    Triggers: on_queue_entry()
    """
    await matchmaker.send(
        json.dumps({"type": "join_queue", "data": {"game_type": game_type.value}})
    )

    msg = json.loads(await matchmaker.recv())
    assert msg["type"] == "queue_joined", f"Expected 'queue_joined', got {msg}"

    await bot.on_queue_entry()


async def _wait_for_match(bot: Bot, matchmaker: ClientConnection) -> dict:
    """
    Wait until matched with an opponent.

    Triggers: on_queue_exit(), on_match_found(match_id)
    Returns: match data with game_id, game_server_ws, your_side
    """
    while True:
        msg = json.loads(await matchmaker.recv())
        if msg["type"] == "match_found":
            match = msg["data"]
            await bot.on_queue_exit()
            await bot.on_match_found(match["game_id"])
            return match


async def _connect_game_server(bot: Bot, game_server_ws: str) -> ClientConnection:
    """Connect to the game server WebSocket."""
    headers = _auth_header(bot)
    return await connect(game_server_ws, additional_headers=headers)


async def _join_room(bot: Bot, game_ws: ClientConnection, room_id: str) -> None:
    """
    Join a game room.

    Triggers: on_room_joined(room_id)
    """
    await game_ws.send(
        json.dumps({"msg_type": "join_room", "data": {"room_id": room_id}})
    )
    await bot.on_room_joined(room_id)


async def _wait_for_game_start(
    bot: Bot, game_ws: ClientConnection, my_side: str
) -> tuple[str, str, list]:
    """
    Wait for game to start.

    Triggers: on_game_start(state)
    Returns: (board, current_turn, legal_moves)
    """
    while True:
        msg = json.loads(await game_ws.recv())
        if msg.get("msg_type") == "game_start":
            data = msg["data"]
            board = data["board"]
            current_turn = data["current_turn"]
            legal_moves = data["legal_moves"]

            state = _build_loop_state(board, current_turn, my_side, legal_moves)
            await bot.on_game_start(state)

            return board, current_turn, legal_moves


async def _submit_move(game_ws: ClientConnection, from_pos: str, to_pos: str) -> None:
    """Submit a move to the game server."""
    await game_ws.send(
        json.dumps({
            "msg_type": "submit_move",
            "data": {"from_pos": from_pos, "to_pos": to_pos},
        })
    )


async def _game_loop(
    bot: Bot,
    game_ws: ClientConnection,
    my_side: str,
    board: str,
    current_turn: str,
    legal_moves: list,
) -> None:
    """
    Main game loop - handle moves until game ends.

    Triggers: on_move(state), on_game_end(winner, state)
    """
    # Make first move if it's our turn
    if current_turn == my_side and legal_moves:
        state = _build_loop_state(board, current_turn, my_side, legal_moves)
        move = await bot.on_move(state)
        await _submit_move(game_ws, move.from_pos, move.to_pos)

    # Game loop
    while True:
        msg = json.loads(await game_ws.recv())
        msg_type = msg.get("msg_type")
        data = msg.get("data", {})

        if msg_type == "move_made":
            board = data["board"]
            current_turn = data["current_turn"]
            legal_moves = data["legal_moves"]

            # Only move if it's our turn AND have legal moves
            if current_turn == my_side and legal_moves:
                state = _build_loop_state(board, current_turn, my_side, legal_moves)
                move = await bot.on_move(state)
                await _submit_move(game_ws, move.from_pos, move.to_pos)

        elif msg_type == "game_end":
            winner = data.get("winner")
            end_state = _build_end_state(data["board"], current_turn, my_side, winner)
            await bot.on_game_end(winner, end_state)
            return

        elif msg_type == "opponent_disconnected":
            # Win by default
            end_state = _build_end_state(board, current_turn, my_side, my_side)
            await bot.on_game_end(my_side, end_state)
            return


# =============================================================================
# Public API
# =============================================================================


async def run(
    bot: Bot, game_type: GameType, matchmaker_url: str = MATCHMAKER_URL
) -> None:
    """
    Run a bot through one complete game.

    Flow:
        1. Connect to matchmaker    → on_ready()
        2. Join queue               → on_queue_entry()
        3. Wait for match           → on_queue_exit(), on_match_found()
        4. Connect to game server
        5. Join room                → on_room_joined()
        6. Wait for game start      → on_game_start()
        7. Game loop                → on_move() / on_game_end()
        8. Cleanup
    """
    # Phase 1: Matchmaking
    matchmaker = await _connect_matchmaker(bot, matchmaker_url)

    try:
        await _join_queue(bot, matchmaker, game_type)
        match = await _wait_for_match(bot, matchmaker)

        game_id = match["game_id"]
        game_server_ws = match["game_server_ws"]
        my_side = match["your_side"]

        # Phase 2: Game
        game_ws = await _connect_game_server(bot, game_server_ws)

        try:
            await _join_room(bot, game_ws, game_id)
            board, current_turn, legal_moves = await _wait_for_game_start(
                bot, game_ws, my_side
            )
            await _game_loop(bot, game_ws, my_side, board, current_turn, legal_moves)
        finally:
            await game_ws.close()
    finally:
        await matchmaker.close()


def start(bot: Bot, game_type: GameType, matchmaker_url: str = MATCHMAKER_URL) -> None:
    """Sync entry point - runs one complete game."""
    asyncio.run(run(bot, game_type, matchmaker_url))
