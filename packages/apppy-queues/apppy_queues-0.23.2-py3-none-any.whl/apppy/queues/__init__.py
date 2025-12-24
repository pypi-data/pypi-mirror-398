import abc


class QueueHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def handle_exception(self, message, exception):
        pass

    @abc.abstractmethod
    async def handle_message(self, message):
        pass


class Queue(metaclass=abc.ABCMeta):  # noqa: B024
    # @abstractmethod
    async def publish(self, message):
        raise NotImplementedError

    # @abstractmethod
    def register_handler(self, handler: QueueHandler):
        raise NotImplementedError

    @abc.abstractmethod
    def startup(self):
        """
        Startup a queue implementation.
        """
        pass

    @abc.abstractmethod
    def shutdown(self):
        """
        Allow graceful shutdown logic for a queue implementation.
        """
        pass
