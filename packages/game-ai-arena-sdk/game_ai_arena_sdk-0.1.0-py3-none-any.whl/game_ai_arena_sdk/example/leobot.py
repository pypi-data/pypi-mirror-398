import asyncio
import random
import sys
from pathlib import Path

# Add parent to path so we can import the SDK
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from game_ai_arena_sdk import Bot, run, GameType, Move, GameStateLoop, GameStateEnd


BOT1_ID = "0bc4ac82-a0c6-48e7-adb4-15f1a855c0c0"
BOT1_KEY = "8q7-wS3msgToDVvdxMB0A1DBRjP9ww7yGFqINO6A0MiviLgTSssGp2ycik50dzzg"

BOT2_ID = "7bc5be4e-b2c4-43b3-9502-4470fff7950d"
BOT2_KEY = "pwxScoLfGEGVF0s_9pRWCJuImmkDPPUbMSmKhCNOnd8S3_d7gFjVbhFSiTjEqeHk"


class RandomBot(Bot):
    """A bot that makes random moves."""

    async def on_move(self, state: GameStateLoop) -> Move:
        # Pick a random piece that can move
        piece = random.choice(state.legal_moves)
        # Pick a random destination
        dest = random.choice(piece.valid_moves)
        return Move(from_pos=piece.pos, to_pos=dest)

    async def on_game_end(self, winner: str | None, state: GameStateEnd) -> None:
        if winner == state.my_side.value:
            print(f"[{self.id[:8]}] I won!")
        elif winner is None:
            print(f"[{self.id[:8]}] Draw!")
        else:
            print(f"[{self.id[:8]}] I lost!")


async def main():
    bot1 = RandomBot(BOT1_ID, BOT1_KEY)
    bot2 = RandomBot(BOT2_ID, BOT2_KEY)

    await asyncio.gather(
        run(bot1, GameType.FLIPFLOP_3X3),
        run(bot2, GameType.FLIPFLOP_3X3),
    )


if __name__ == "__main__":
    asyncio.run(main())
