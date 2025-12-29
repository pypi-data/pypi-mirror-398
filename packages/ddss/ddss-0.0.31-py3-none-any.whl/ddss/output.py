import asyncio
from sqlalchemy import select
from apyds_bnf import unparse
from .orm import initialize_database, Facts, Ideas


async def main(addr, engine=None, session=None):
    if engine is None or session is None:
        engine, session = await initialize_database(addr)

    try:
        max_fact = -1
        max_idea = -1

        while True:
            count = 0
            begin = asyncio.get_running_loop().time()

            async with session() as sess:
                for i in await sess.scalars(select(Ideas).where(Ideas.id > max_idea)):
                    max_idea = max(max_idea, i.id)
                    print("idea:", unparse(i.data))
                    count += 1
                for i in await sess.scalars(select(Facts).where(Facts.id > max_fact)):
                    max_fact = max(max_fact, i.id)
                    print("fact:", unparse(i.data))
                    count += 1
                await sess.commit()

            end = asyncio.get_running_loop().time()
            duration = end - begin
            if count == 0:
                delay = max(0, 0.1 - duration)
                await asyncio.sleep(delay)
    except asyncio.CancelledError:
        pass
    finally:
        await engine.dispose()
