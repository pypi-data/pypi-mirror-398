import abc
import random
import time

from iker.common.utils import logger
from iker.common.utils.dtutils import dt_utc_now

__all__ = [
    "Attempt",
    "Retry",
    "RetryWrapper",
    "retry",
    "retry_exponent",
    "retry_random",
]


class Attempt(object):
    def __init__(
        self,
        number: int,
        prev_wait: int,
        next_wait: int,
        start_ts: float,
        check_ts: float,
        last_exception: Exception,
    ):
        """
        Represents an attempt in retrying.

        :param number: The attempt number (1-based).
        :param prev_wait: The wait time before the previous attempt (in seconds).
        :param next_wait: The wait time before the next attempt (in seconds).
        :param start_ts: The start timestamp of the first attempt.
        :param check_ts: The timestamp at which the current attempt is checked.
        :param last_exception: The exception raised during the last attempt, if any.
        """
        self.number = number
        self.prev_wait = prev_wait
        self.next_wait = next_wait
        self.start_ts = start_ts
        self.check_ts = check_ts
        self.last_exception = last_exception


class Retry(abc.ABC):
    @abc.abstractmethod
    def on_attempt(self, attempt: Attempt):
        """
        Called before each retry attempt. Can be used to perform custom logic or logging before an attempt is made.

        :param attempt: The current ``Attempt`` instance containing attempt details.
        """
        pass

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        """
        Executes the target operation with retry logic. Must be implemented by subclasses.

        :param args: Positional arguments for the operation.
        :param kwargs: Keyword arguments for the operation.
        :return: The result of the operation.
        """
        pass


class RetryWrapper(object):
    def __init__(
        self,
        cls,
        wait: int = None,
        wait_exponent_init: int = None,
        wait_exponent_max: int = None,
        wait_random_min: int = None,
        wait_random_max: int = None,
        retrials: int = None,
        timeout: int = None,
    ):
        """
        Retry executor that wraps a callable or ``Retry`` instance, providing flexible retry strategies including fixed,
        exponential, and random waits.

        :param cls: The target callable or ``Retry`` instance to execute.
        :param wait: Fixed wait time (in seconds) between retrials.
        :param wait_exponent_init: Initial wait time for exponential backoff.
        :param wait_exponent_max: Maximum wait time for exponential backoff.
        :param wait_random_min: Minimum wait time for random backoff.
        :param wait_random_max: Maximum wait time for random backoff.
        :param retrials: Maximum number of retrials (``None`` for unlimited).
        :param timeout: Maximum total time (in seconds) allowed for all attempts (``None`` for unlimited).
        """
        self.__wrapped = cls
        self.wait = wait
        self.wait_exponent_init = wait_exponent_init
        self.wait_exponent_max = wait_exponent_max
        self.wait_random_min = wait_random_min
        self.wait_random_max = wait_random_max
        self.retrials = retrials
        self.timeout = timeout

    def __call__(self, *args, **kwargs):
        """
        Invokes the wrapped callable or ``Retry`` instance with retry logic.

        :param args: Positional arguments for the operation.
        :param kwargs: Keyword arguments for the operation.
        :return: The result of the operation.
        """
        return self.__run(*args, **kwargs)

    def __next_wait(self, attempt_number: int):
        """
        Determines the wait time before the next retry attempt based on the configured strategy.

        :param attempt_number: The current attempt number (1-based).
        :return: The wait time in seconds, or ``None`` if not applicable.
        """
        if attempt_number <= 0:
            return None
        elif self.wait is not None:
            return self.wait
        elif self.wait_exponent_init is not None and self.wait_exponent_max is not None:
            return min(self.wait_exponent_init * (2 ** (attempt_number - 1)), self.wait_exponent_max)
        elif self.wait_random_min is not None and self.wait_random_max is not None:
            return random.randint(self.wait_random_min, self.wait_random_max)
        else:
            return 0

    def __check_timeout(self, start_ts: float) -> tuple[bool, float]:
        """
        Checks if the retry operation has exceeded the configured timeout.

        :param start_ts: The start timestamp of the first attempt.
        :return: Tuple (``True`` if within timeout, current timestamp).
        """
        current_ts = dt_utc_now().timestamp()
        if self.timeout is None:
            return True, current_ts
        return current_ts < start_ts + self.timeout, current_ts

    def __run(self, *args, **kwargs):
        """
        Runs the retry loop, invoking the wrapped callable or ``Retry`` instance until success, retrials exhausted, or
        timeout reached.

        :param args: Positional arguments for the operation.
        :param kwargs: Keyword arguments for the operation.
        :return: The result of the operation.
        :raises RuntimeError: If all attempts fail or timeout is reached.
        """
        attempt_number = 0
        start_ts = dt_utc_now().timestamp()
        last_exception = None

        while self.retrials is None or attempt_number <= self.retrials:
            attempt_number += 1

            check_result, check_ts = self.__check_timeout(start_ts)
            if not check_result:
                break

            attempt = Attempt(
                attempt_number,
                self.__next_wait(attempt_number - 1),
                self.__next_wait(attempt_number),
                start_ts,
                check_ts,
                last_exception,
            )
            try:
                if isinstance(self.__wrapped, Retry):
                    self.__wrapped.on_attempt(attempt)
                    return self.__wrapped.execute(*args, **kwargs)
                else:
                    return self.__wrapped(*args, **kwargs)
            except Exception as e:
                logger.exception("Function target <%s> failed on attempt <%d>", self.__wrapped, attempt_number)
                last_exception = e
                time.sleep(self.__next_wait(attempt_number))

        raise RuntimeError(
            "failed to execute function target <%s> after <%d> attempts" % (self.__wrapped, attempt_number))


def retry(wait: int = None, retrials: int = None, timeout: int = None):
    """
    Decorator to apply fixed wait retry logic to a function or callable.

    :param wait: Fixed wait time (in seconds) between retrials.
    :param retrials: Maximum number of retrials (``None`` for unlimited).
    :param timeout: Maximum total time (in seconds) allowed for all attempts (``None`` for unlimited).
    :return: A decorated function with retry logic.
    """

    def wrapper(target):
        return RetryWrapper(target, wait=wait, retrials=retrials, timeout=timeout)

    return wrapper


def retry_exponent(wait_exponent_init: int, wait_exponent_max: int, retrials: int = None, timeout: int = None):
    """
    Decorator to apply exponential backoff retry logic to a function or callable.

    :param wait_exponent_init: Initial wait time for exponential backoff.
    :param wait_exponent_max: Maximum wait time for exponential backoff.
    :param retrials: Maximum number of retrials (``None`` for unlimited).
    :param timeout: Maximum total time (in seconds) allowed for all attempts (``None`` for unlimited).
    :return: A decorated function with retry logic.
    """

    def wrapper(target):
        return RetryWrapper(
            target,
            wait_exponent_init=wait_exponent_init,
            wait_exponent_max=wait_exponent_max,
            retrials=retrials,
            timeout=timeout,
        )

    return wrapper


def retry_random(wait_random_min: int, wait_random_max: int, retrials: int = None, timeout: int = None):
    """
    Decorator to apply random wait retry logic to a function or callable.

    :param wait_random_min: Minimum wait time for random backoff.
    :param wait_random_max: Maximum wait time for random backoff.
    :param retrials: Maximum number of retrials (``None`` for unlimited).
    :param timeout: Maximum total time (in seconds) allowed for all attempts (``None`` for unlimited).
    :return: A decorated function with retry logic.
    """

    def wrapper(target):
        return RetryWrapper(
            target,
            wait_random_min=wait_random_min,
            wait_random_max=wait_random_max,
            retrials=retrials,
            timeout=timeout,
        )

    return wrapper
