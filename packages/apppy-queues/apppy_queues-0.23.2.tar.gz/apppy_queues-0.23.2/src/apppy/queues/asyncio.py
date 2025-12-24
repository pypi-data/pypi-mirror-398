import asyncio
import queue
from threading import Thread

from fastapi_lifespan_manager import LifespanManager

from apppy.logger import WithLogger
from apppy.queues import Queue, QueueHandler


class AsyncioQueue(Queue, WithLogger):
    def __init__(
        self,
        lifespan: LifespanManager | None,
        name: str,
        maxsize: int = -1,
        shutdown_timeout: int = 2,
    ) -> None:
        ## Queue configuration
        self._queue_name = name
        self._handlers: list[QueueHandler] = []
        self._maxsize = maxsize
        self._shutdown_timeout = shutdown_timeout

        ## Queue internals
        self._native_queue: queue.Queue = queue.Queue(maxsize=self._maxsize)
        # Start a background thread to consume the queue
        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._logger.info("Created AsyncioQueue", extra={"queue_name": self._queue_name})

        if lifespan is not None:
            lifespan.add(self._manage_queue)

    async def _manage_queue(self):
        self.startup()
        yield
        self.shutdown()

    async def _process_queue(self):
        self._logger.info("Started AsyncioQueue processor", extra={"queue_name": self._queue_name})

        while True:
            try:
                message = self._native_queue.get()
                if message is not None:
                    for h in self._handlers:
                        try:
                            # self._logger.debug(
                            #     "Dispatching to handler", extra={"handler": h.__class__.__name__}
                            # )
                            await h.handle_message(message)
                        except BaseException as e:
                            await h.handle_exception(message, e)
            except BaseException as e:
                self._logger.error("Unhandled exception in queue processor", exc_info=e)

    def _worker_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._process_queue())

    def publish(self, message):
        try:
            self._native_queue.put_nowait(message)
        except queue.Full:
            self._logger.warning(
                "Queue is full — dropping message", extra={"queue_name": self._queue_name}
            )

    def register_handler(self, handler: QueueHandler):
        self._handlers.append(handler)
        self._logger.info(
            "Registered handler in asyncio queue",
            extra={"queue_name": self._queue_name, "handler": handler.__class__.__name__},
        )

    def startup(self):
        if self._worker_thread.is_alive():
            self._logger.debug(
                "AsyncioQueue already started", extra={"queue_name": self._queue_name}
            )
            return

        self._worker_thread.start()

    def shutdown(self):
        self._logger.info("Shutting down AsyncioQueue", extra={"queue_name": self._queue_name})
        if not hasattr(self, "_native_queue"):
            return

        self._native_queue.put(None)
        self._worker_thread.join(timeout=self._shutdown_timeout)
