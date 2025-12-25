"""
Manages background tasks.
"""
from asyncio import Task, CancelledError, Queue, create_task, gather
from collections.abc import Coroutine
from typing import Any, Callable, Optional
from aiohttp import web
import logging

class BackgroundTasks:
    """
    Manages asyncio background tasks. An instance of this class is available as an application property with name
    HEA_BACKGROUND_TASKS. BackgroundTasks objects are truthy if having managed any tasks and falsy otherwise.
    """

    def __init__(self, app: web.Application | None = None, queue_size= 0):
        """
        Creates a background task manager with the provided queue size.

        :param queue_size: the queue size. A value of zero means infinite size.
        """
        self.__app = app
        self.__tasks: dict[str, Task] = dict()
        self.__done: dict[str, Exception | None] = dict()
        self.__queue = Queue[Task](queue_size)
        self.__metadata: dict[str, dict[str, Any]] = dict()
        self.__result: dict[str, Any] = dict()
        self.__cancelled: dict[str, bool] = dict()
        self.__logger = logging.getLogger(__name__)

    def contains(self, name: str) -> bool:
        """
        Whether this background task manager is managing a task with the given name.

        :param name: the name of the background task.
        :return True or False.
        """
        return name in self.__tasks or name in self.__done

    async def add(self, coro: Callable[[Optional[web.Application]], Coroutine[Any, Any, None]], name: str | None = None, **metadata) -> str:
        """
        A coroutine for creating a new asyncio task from the given coroutine and adds it to the tasks managed by this
        task manager. If a name is provided, the task will be given the provided name. Otherwise, a name will be
        generated automatically.

        :param coro: the coroutine (required).
        :param name: an optional name.
        :param metadata: any key-value pairs associated with the task.
        :return: the name of the created task.
        """
        self.__logger.debug('Adding coroutine %s...', name)
        task = create_task(coro(self.__app), name=name)
        name_ = task.get_name()
        self.__tasks[name_] = task
        self.__metadata[name_] = metadata
        await self.__queue.put(task)
        self.__logger.debug('Coroutine %s added.', name_)
        return name_

    def metadata(self, name: str, key: str) -> Any:
        """
        Retrieve task metadata.

        :param name: the name of the task.
        :param key: the key of the metadata value of interest.
        :return: the metadata value.
        :raises KeyError: if the given task has no metadata with the given key.
        """
        return self.__metadata[name][key]

    def cancel(self, name: str):
        """
        Requests cancellation of the task with the given name.

        :param name: the name of the task to cancel.
        """
        self.__tasks[name].cancel()

    def cancel_all(self):
        """
        Requests cancellation of all tasks managed by this background task manager.
        """
        for task in self.__tasks.values():
            task.cancel()

    async def join(self, name: str):
        """
        A coroutine for awaiting completion of the task with the given name. This can be called repeatedly for the same
        task; if the task is already done, this coroutine does nothing. An exception raised by a task is logged as an
        error and not re-raised. CancelledError is re-raised after marking the task as done with no result. Attempting
        to join a non-existent task does nothing.

        :param name: the name of the task.
        :raises KeyError: if no task with the given name is managed by this background task manager.
        """
        try:
            await self.__tasks[name]
        except CancelledError:
            raise
        except:  # self._mark_done will check the task's result and handle any exceptions.
            pass
        finally:
            self._mark_done(name)

    async def join_all(self) -> None:
        """
        A coroutine for awaiting completion of all in-progress tasks managed by this backround task manager. Exceptions
        raised by tasks are logged as errors and not re-raised.
        """
        tasks = tuple((k, v) for k, v in self.__tasks.items())
        try:
            await gather(*(task for _, task in tasks))
        except CancelledError:
            raise
        except:  # self._mark_done will check each task's result and handle any exceptions.
            pass
        finally:
            self.cancel_all()
            await gather(*(task for _, task in tasks), return_exceptions=True)
            for name, _ in tasks:
                self._mark_done(name)

    def in_progress(self, name: str) -> bool:
        """
        Returns whether the task is managed by this task manager and is still running.

        :param name: the name of the task.
        :return: True or False.
        """
        return self.contains(name) and not self.done(name)

    def done(self, name: str) -> bool:
        """
        Returns whether the task with the given name is completed.

        :param name: the name of the task to check.
        :return: True or False.
        """
        return name in self.__done

    def succeeded(self, name: str) -> bool:
        """
        Returns whether the task with the given name completed successfully.

        :param name: the name of the task to check.
        :return: True or False.
        """
        return bool(self.done(name) and not self.error(name) and not self.cancelled(name))

    def failed(self, name: str) -> bool:
        """
        Returns whether the task with the given name failed.

        :param name: the name of the task to check.
        :return: True or False.
        """
        return bool(self.done(name) and self.error(name))

    def error(self, name: str) -> Exception | None:
        """
        Returns the exception raised within a failed task.

        :param name: the name of the task to check.
        :return: An exception if the task failed, or None if it succeeded.
        :raises ValueError: if the task is not done or not managed by this background task manager.
        """
        if name not in self.__done:
            raise ValueError(f'{name} not done or not managed by this background task manager.')
        return self.__done[name]

    def cancelled(self, name: str) -> bool:
        """
        Returns whether the task with the given name was cancelled.

        :param name: the name of the task to check.
        :return: True if the task was cancelled, False otherwise.
        :raises ValueError: if the task is not done or not managed by this background task manager.
        """
        if name not in self.__done:
            raise ValueError(f'{name} not done or not managed by this background task manager.')
        return self.__cancelled.get(name, False)

    def result(self, name: str) -> Any:
        if name not in self.__done:
            raise ValueError(f'{name} not done or not managed by this background task manager.')
        return self.__result[name]

    def remove(self, name: str):
        """
        Removes the task with the given name from this task manager. This method does nothing if no task with the given
        name is managed by this background task manager.

        :param name: the name of the task to remove.
        """
        if name in self.__tasks:
            del self.__tasks[name]
        if name in self.__done:
            del self.__done[name]
        if name in self.__metadata:
            del self.__metadata[name]
        if name in self.__cancelled:
            del self.__cancelled[name]
        if name in self.__result:
            del self.__result[name]

    async def clear(self):
        """
        A coroutine that cancels all running tasks and cleans up all resources.
        """
        self.cancel_all()
        await self.join_all()
        while not self.__queue.empty():
            self.__queue.get_nowait()
            self.__queue.task_done()
        self.__tasks.clear()
        self.__done.clear()
        self.__metadata.clear()
        self.__cancelled.clear()
        self.__result.clear()

    async def auto_join(self):
        """
        A coroutine that automatically executes tasks added to this task manager. It runs forever. When wrapped in a
        task, cancelling the task attempts to end all the managed tasks and ends this coroutine.
        """
        async def consumer():
            while task := await self.__queue.get():
                await self.join(task.get_name())
                self.__queue.task_done()


        consumers = [create_task(consumer()) for _ in range(5)]
        try:
            await gather(*consumers)
        except CancelledError:
            for c in consumers:
                c.cancel()
            await gather(*consumers, return_exceptions=True)
            raise



    def __len__(self) -> int:
        """
        Returns the number of tasks managed by this background task manager.

        :return: the number of tasks managed by this background task manager.
        """
        return len(self.__tasks) + len(self.__done)

    def running_tasks(self) -> int:
        """
        Returns the number of running tasks.

        :return: the number of running tasks.
        """
        return len(self.__tasks)

    def done_tasks(self) -> int:
        """
        Returns the number of done tasks.

        :return: the number of done tasks.
        """
        return len(self.__done)

    def _mark_done(self, name: str):
        """
        Marks the task with the given name as done, and logs any exception raised within the task. If there is no task
        with the given name, this method does nothing. If the task was cancelled, it is marked as done with no result,
        and the CancelledError is NOT re-raised. If the task raised an exception, it is marked as done with the
        exception as the result, and the exception is logged as an error. If the task completed successfully, it is
        marked as done with its result.

        :param name: the name of the task to mark done.
        """
        try:
            the_task = self.__tasks.get(name)
            if the_task is None:
                return
            self.__result[name] = the_task.result()
            self.__done[name] = None
            self.__cancelled[name] = False
            self.__logger.debug('Task %s completed successfully', name)
        except CancelledError:
            self.__done[name] = None
            self.__result[name] = None
            self.__cancelled[name] = True
        except Exception as e:
            self.__done[name] = e
            self.__cancelled[name] = False
            self.__result[name] = None
            self.__logger.exception('Task %s failed with exception', name)
        finally:
            self.__tasks.pop(name, None)

    def __str__(self) -> str:
        return f'Background task manager: in-progress tasks: {", ".join(self.__tasks)}; done tasks: {", ".join(self.__done)}'
