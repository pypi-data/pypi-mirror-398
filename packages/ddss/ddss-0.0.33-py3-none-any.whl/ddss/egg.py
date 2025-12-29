import asyncio
from sqlalchemy import select
from apyds import Rule
from .orm import initialize_database, insert_or_ignore, Facts, Ideas
from .egraph import Search


async def main(addr, engine=None, session=None):
    if engine is None or session is None:
        engine, session = await initialize_database(addr)

    try:
        search = Search()
        pool = []
        max_fact = -1
        max_idea = -1

        while True:
            count = 0
            begin = asyncio.get_running_loop().time()

            async with session() as sess:
                for i in await sess.scalars(select(Ideas).where(Ideas.id > max_idea)):
                    max_idea = max(max_idea, i.id)
                    pool.append(Rule(i.data))
                for i in await sess.scalars(select(Facts).where(Facts.id > max_fact)):
                    max_fact = max(max_fact, i.id)
                    search.add(Rule(i.data))
                search.rebuild()
                tasks = []
                next_pool = []
                for i in pool:
                    for o in search.execute(i):
                        tasks.append(asyncio.create_task(insert_or_ignore(sess, Facts, str(o))))
                        count += 1
                        if i == o:
                            break
                    else:
                        next_pool.append(i)
                pool = next_pool
                await asyncio.gather(*tasks)
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
