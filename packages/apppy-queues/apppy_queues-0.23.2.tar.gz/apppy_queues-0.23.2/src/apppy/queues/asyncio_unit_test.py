import asyncio

from . import QueueHandler
from .asyncio import AsyncioQueue


class AsyncioQueueTestQueueHandler(QueueHandler):
    def __init__(self) -> None:
        self._exception_counter = 0
        self._message_counter = 0

    @property
    def exception_counter(self):
        return self._exception_counter

    @property
    def message_counter(self):
        return self._message_counter

    async def handle_exception(self, message, exception):
        self._exception_counter = self._exception_counter + 1

    async def handle_message(self, message):
        self._message_counter = self._message_counter + 1
        # Raise an exception on the second call
        # to this handler
        if self._message_counter == 2:
            raise Exception("Mimicked QueueHandler exception")


async def test_async_queue():
    queue = AsyncioQueue(lifespan=None, name="test_direct_queue_handler_error")
    queue_handler = AsyncioQueueTestQueueHandler()
    queue.register_handler(queue_handler)
    queue.startup()

    queue.publish(message={})
    await asyncio.sleep(0.1)
    assert queue_handler.exception_counter == 0
    assert queue_handler.message_counter == 1

    queue.publish(message={})
    await asyncio.sleep(0.1)
    assert queue_handler.exception_counter == 1
    assert queue_handler.message_counter == 2

    queue.publish(message={})
    await asyncio.sleep(0.1)
    assert queue_handler.exception_counter == 1
    assert queue_handler.message_counter == 3
