import sys
from apyds_bnf import parse
from .orm import initialize_database, insert_or_ignore, Facts, Ideas
from .utility import str_rule_get_str_idea


async def main(addr, engine=None, session=None):
    if engine is None or session is None:
        engine, session = await initialize_database(addr)

    try:
        async with session() as sess:
            for line in sys.stdin:
                data = line.strip()
                if data == "":
                    continue
                if data.startswith("//"):
                    continue

                try:
                    ds = parse(data)
                except Exception as e:
                    print(f"error: {e}")
                    continue

                await insert_or_ignore(sess, Facts, ds)
                if idea := str_rule_get_str_idea(ds):
                    await insert_or_ignore(sess, Ideas, idea)
            await sess.commit()
    finally:
        await engine.dispose()
