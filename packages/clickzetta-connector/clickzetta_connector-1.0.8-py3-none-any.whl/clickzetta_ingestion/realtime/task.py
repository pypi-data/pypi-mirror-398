from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Optional
import logging


class Task(ABC):
    """
    Task interface for defining task operations.
    """

    @abstractmethod
    def get_id(self) -> int:
        """
        Return current batch id.

        :return: Batch id
        """
        pass

    def get_buffer(self):
        """
        Return current buffer it contains.

        :return: Buffer
        """
        return None

    @abstractmethod
    def skip_call(self, t: Optional[Exception] = None) -> Future:
        """
        Call this function to skip the task real action with target exception or null.

        If this task is a retry task, need to clean up some counts which are defined outside of the task.

        :param t: Exception to skip the task with
        :return: Future
        """
        pass

    @abstractmethod
    def call(self) -> Future:
        """
        Task main method called.

        :return: Future
        """
        pass

    @abstractmethod
    def get_future(self) -> Future:
        """
        Return this future which task holds.

        :return: Future
        """
        pass


class FlushTaskCallException(Exception):
    pass


class AbstractTask(Task):
    LOG = logging.getLogger('Task')

    def __init__(self):
        self.future = Future()

    def __lt__(self, other):
        return self.get_id() < other.get_id()

    def get_future(self) -> Future:
        return self.future

    def call_prepare(self) -> None:
        # do nothing.
        pass

    @abstractmethod
    def call_internal(self) -> None:
        pass

    def skip_call(self, t: Optional[Exception] = None) -> Future:
        if t is None:
            self.future.set_result(True)
        else:
            self.future.set_exception(t)
        return self.future

    def call(self) -> Future:
        try:
            self.call_prepare()
            self.call_internal()
        except Exception as t:
            self.future.set_exception(FlushTaskCallException(t))
        return self.future
