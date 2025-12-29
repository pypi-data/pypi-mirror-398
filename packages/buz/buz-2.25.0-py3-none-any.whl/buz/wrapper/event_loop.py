import asyncio
from asyncio import AbstractEventLoop


def __get_event_loop() -> AbstractEventLoop:
    try:
        result = asyncio.get_running_loop()
    except RuntimeError:
        result = asyncio.new_event_loop()
    return result


loop = __get_event_loop()
