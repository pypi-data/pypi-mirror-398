import logging
from asyncio import run

from x_model import init_db

from xync_bot import XyncBot
from xync_bot.loader import TOKEN

if __name__ == "__main__":
    from xync_bot.loader import TORM

    logging.basicConfig(level=logging.INFO)

    async def main() -> None:
        cn = await init_db(TORM)
        await XyncBot(TOKEN, cn).start()

    run(main())
