from contextlib import asynccontextmanager


def compose_lifespans(*lifespans):
    """Combine multiple asynccontextmanager lifespans into one."""
    lifespans = [ls for ls in lifespans if ls is not None]

    @asynccontextmanager
    async def composed(app):
        async def run(index=0):
            if index == len(lifespans):
                yield
            else:
                async with lifespans[index](app):
                    async for _ in run(index + 1):
                        yield

        async for _ in run():
            yield

    return composed
