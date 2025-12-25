import asyncio
import logging
import queue
import threading
from freezegun import freeze_time as _freeze_time
from functools import partial
from contextlib import contextmanager
from typing import Any, Callable, Coroutine, TypeVar
from heaobject.error import HEAException
try:
    import pywintypes
    _additional_docker_running_check_logic: Callable[[Exception], bool] = lambda e: e.__cause__ is not None and e.__cause__.args == (2, 'CreateFile', 'The system cannot find the file specified.')
except:
    # TODO: implement Linux logic here.
    # The code below is a sensible default that results in all raised
    # exceptions being propagated up the stack.
    _additional_docker_running_check_logic = lambda e: False


freeze_time = partial(_freeze_time, "2022-05-17", ignore=['asyncio'])
freeze_time.__doc__ = "Context manager that freezes time to 2022-05-17T00:00:00-06:00."

class MaybeDockerIsNotRunning(HEAException):
    """Exception raised to inform the test runner that perhaps Docker is not
    running. The python Docker library raises non-specific errors when there is
    no running Docker daemon, so we cannot be 100% sure."""
    pass

@contextmanager
def maybe_docker_is_not_running():
    """
    Context manager to wrap code that interacts with the Docker daemon to
    suggest to the test runner that the Docker daemon may not be running when
    certain exceptions are raised. The exceptions raised are platform
    dependent. The word maybe in the function name is there because the python
    Docker library raises non-specific errors when there is no running Docker
    daemon, but we do the best we can. The original exception is nested in case
    you need to see it.

    :raises MaybeDockerIsNotRunningException: if the wrapped code raises an
    error suggesting that Docker may not be running. The original exception is
    nested. Otherwise, raised exceptions are propagated up the stack."""
    try:
        yield
    except Exception as e:
        if _additional_docker_running_check_logic(e):
            raise MaybeDockerIsNotRunning from e
        else:
            raise e


T = TypeVar('T')

def run_coroutine_in_new_event_loop(coro: Coroutine[Any, Any, T]) -> T:
    """
    Sets up a new asyncio event loop, runs the provided coroutine in it, shuts down the event loop, and returns the
    result. The event loop and coroutine are executed in separate threads. This is useful for running coroutines in
    synchronous contexts. It blocks the calling thread while waiting for the coroutine to complete and joining the
    event loop thread and coroutine thread.

    :param coro: the coroutine to run in a new event loop (required).
    :return: the result of the coroutine.
    """
    logger = logging.getLogger(__name__)
    loop = asyncio.new_event_loop()
    def loop_in_thread():
        logger.debug("Starting new event loop in thread.")
        try:
            loop.run_forever()
        finally:
            logger.debug("Closing event loop.")
            loop.close()
            logger.debug("Event loop closed.")

    loop_thread = threading.Thread(target=loop_in_thread)
    loop_thread.start()
    result_queue: queue.Queue[T] = queue.Queue()
    try:
        def run_in_thread(loop: asyncio.AbstractEventLoop):
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            try:
                result = future.result()
                logger.debug("Coroutine completed successfully.")
                result_queue.put(result)
            except:
                logger.exception("Error running coroutine")
        run_thread = threading.Thread(target=run_in_thread, args=(loop,))
        run_thread.start()
        run_thread.join()
        return result_queue.get()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        loop_thread.join()
