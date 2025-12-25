from unittest import TestCase, IsolatedAsyncioTestCase
import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator

from heaserver.service.util import raise_multiple, modified_environ, retry, async_retry, async_retry_context_manager, \
    queued_processing


class ModifiedEnvironmentTestCase(TestCase):
    def test_update_environment_variable(self) -> None:
        """Checks if modifying an environment variable actually modifies it in the context."""
        var_name = next(iter(os.environ.keys()), None)
        if var_name is None:
            self.skipTest('no environment variables available')
        value = os.environ[var_name]
        with modified_environ(**{var_name: 'foobar' + value}):
            self.assertEqual('foobar' + value, os.environ[var_name])

    def test_update_environment_variable_restored_after(self) -> None:
        """
        Checks if modifying an environment variable with the context manager does not modify it outside of the
        context.
        """
        var_name = next(iter(os.environ.keys()), None)
        if var_name is None:
            self.skipTest('no environment variables available')
        value = os.environ[var_name]
        with modified_environ(**{var_name: 'foobar' + value}):
            logging.info(f'{var_name}={os.environ[var_name]}')
        self.assertEqual(value, os.environ[var_name])

    def test_add_environment_variable(self) -> None:
        """Checks if adding the FOO environment variable (and setting it to 'bar') actually adds it in the context."""
        with modified_environ(FOO='bar'):
            self.assertEqual('bar', os.environ.get('FOO'))

    def test_add_environment_variable_removed_after(self) -> None:
        """
        Checks if adding the FOO environment variable (and setting it to 'bar') with the context manager does not
        add it outside of the context.
        """
        with modified_environ(FOO='bar'):
            logging.info(f'FOO={os.environ["FOO"]}')
        self.assertIsNone(os.environ.get('FOO'))

    def test_remove_environment_variable(self) -> None:
        """
        Checks if removing an environment variable actually removes it in the
        context.
        """
        var_name = next(iter(os.environ.keys()), None)
        if var_name is None:
            self.skipTest('no environment variables available')
        with modified_environ(var_name):
            self.assertIsNone(os.environ.get(var_name))

    def test_remove_environment_variable_restored_after(self) -> None:
        """
        Checks if removing the FPS_BROWSER_APP_PROFILE_STRING environment variable with the context manager does not
        remove it outside of the context.
        """
        var_name = next(iter(os.environ.keys()), None)
        if var_name is None:
            self.skipTest('no environment variables available')
        value = os.environ[var_name]
        with modified_environ(var_name):
            logging.info(f'{var_name}={os.environ.get(var_name)}')
        self.assertEqual(value, os.environ.get(var_name))


class ModifiedEnvironmentAsyncTestCase(IsolatedAsyncioTestCase):
    async def test_update_environment_variable_async_access_not_within_context(self) -> None:
        """
        Checks if accessing an environment variable updated with the context manager outside of the context while the
        context is running returns the old value.
        """

        var_name = next(iter(os.environ.keys()), None)
        if var_name is None:
            self.skipTest('no environment variables available')
        value = os.environ[var_name]

        async def change_env():
            nonlocal var_name
            with modified_environ(**{var_name: 'foobar' + value}):
                await asyncio.sleep(1)
                logging.info(f'{var_name}={os.environ[var_name]}')

        task = asyncio.create_task(change_env())

        new_value = os.environ[var_name]

        await task
        self.assertEqual(value, new_value)


class NonAsyncRetryTestCase(TestCase):
    def test_retry_success(self) -> None:
        """Checks if a success on a retry of a function with the retry decorator returns the expected value."""

        tried = False

        @retry(Exception, cooldown=None)
        def foo() -> str:
            nonlocal tried
            if tried:
                return 'foo'
            else:
                tried = True
                raise Exception

        try:
            self.assertEqual('foo', foo())
        except Exception as e:
            raise AssertionError(f'exception raised: {e}') from e

    def test_retry_cooldown(self) -> None:
        """Checks if there is a cooldown when a cooldown is specified in the retry decorator."""
        @retry(Exception, cooldown=1, retries=1)
        def foo() -> None:
            raise Exception

        start = time.perf_counter()

        try:
            foo()
        except:
            pass

        self.assertGreaterEqual(time.perf_counter() - start, 0.9, 'cooldown not long enough')

    def test_retry_retries(self) -> None:
        """Checks if the number of retries that are attempted of a function with the retry decorator is correct."""

        count = 0

        @retry(Exception, retries=5, cooldown=None)
        def foo() -> None:
            nonlocal count
            count += 1
            raise Exception

        try:
            foo()
        except:
            pass

        self.assertEqual(6, count)

    def test_retry_exhausted(self) -> None:
        """Checks if exhausting all the retries of a function raises ``RetryExhaustedError``."""
        @retry(Exception, cooldown=None)
        def foo() -> None:
            raise Exception

        self.assertRaises(Exception, foo)

    def test_retry_different_error(self) -> None:
        """
        Checks if an exception raised by the retrying function not matching an expected exception passed into the
        retry decorator propagates the exception.
        """
        @retry(ValueError, cooldown=None)
        def foo() -> None:
            raise TypeError

        self.assertRaises(TypeError, foo)


class AsyncRetryTestCase(IsolatedAsyncioTestCase):
    async def test_retry_success(self) -> None:
        """Checks if a success on a retry of a coroutine with the async_retry decorator returns the expected value."""

        tried = False

        @async_retry(Exception, cooldown=None)
        async def foo() -> str:
            nonlocal tried
            if tried:
                return 'foo'
            else:
                tried = True
                raise Exception

        try:
            self.assertEqual('foo', await foo())
        except Exception as e:
            raise AssertionError(f'exception raised: {e}') from e

    async def test_retry_cooldown(self) -> None:
        """Checks if there is a cooldown when a cooldown is specified in the async_retry decorator."""

        @async_retry(Exception, cooldown=1, retries=1)
        async def foo() -> None:
            raise Exception

        start = time.perf_counter()

        try:
            await foo()
        except Exception:
            pass

        self.assertGreaterEqual(time.perf_counter() - start, 0.9, 'cooldown not long enough')

    async def test_retry_retries(self) -> None:
        """
        Checks if the number of retries that are attempted of a function with the async_retry decorator is correct.
        """

        count = 0

        @async_retry(Exception, retries=5, cooldown=None)
        async def foo() -> None:
            nonlocal count
            count += 1
            raise Exception

        try:
            await foo()
        except:
            pass

        self.assertEqual(6, count)

    async def test_retry_exhausted(self) -> None:
        """Checks if exhausting all the retries of a coroutine raises Exception."""

        @async_retry(Exception, cooldown=None)
        async def foo() -> None:
            raise Exception

        with self.assertRaises(Exception):
            await foo()

    async def test_retry_different_error(self) -> None:
        """
        Checks if an exception raised by the retrying coroutine not matching an expected exception passed into the
        async_retry decorator propagates the exception.
        """

        @async_retry(ValueError, cooldown=None)
        async def foo() -> None:
            raise TypeError

        with self.assertRaises(TypeError):
            await foo()

    async def test_async_context_manager_succeeded(self) -> None:
        num_tries = 0
        @async_retry_context_manager(ValueError, retries=3, cooldown=2)
        class AsyncContextManager:
            async def __aenter__(self):
                nonlocal num_tries
                if num_tries < 3:
                    num_tries += 1
                    raise ValueError("Failure")
                return "Success"

            async def __aexit__(self, exc_type, exc, tb):
                pass

        async with AsyncContextManager() as result:
            self.assertEqual('Success', result)

    async def test_async_context_manager_failed(self) -> None:
        num_tries = 0
        @async_retry_context_manager(ValueError, retries=3, cooldown=2)
        class AsyncContextManager:
            async def __aenter__(self):
                nonlocal num_tries
                if num_tries < 4:
                    num_tries += 1
                    raise ValueError("Failure")
                return "Success"

            async def __aexit__(self, exc_type, exc, tb):
                pass

        with self.assertRaises(ValueError):
            async with AsyncContextManager():
                pass

    async def test_raise_multiple(self) -> None:
        with self.assertRaises(ValueError):
            raise_multiple([ValueError, TypeError, OSError])

    async def test_queued_processing(self) -> None:
        result = set[int]()
        async def process() -> AsyncIterator[int]:
            for i in range(1, 6):
                yield i

        async def process_error(value: int):
            result.add(value)

        await queued_processing(process(), process_error)
        self.assertEqual(set([1, 2, 3, 4, 5]), result)

    async def test_queued_processing_more_than_fit_in_queue(self) -> None:
        result = set[int]()
        async def process() -> AsyncIterator[int]:
            for i in range(1, 1000):
                yield i

        async def process_error(value: int):
            result.add(value)

        await queued_processing(process(), process_error)
        self.assertEqual(set(x for x in range(1, 1000)), result)

    async def test_queued_processing_ignore_exception(self) -> None:
        result = set[int]()
        async def process() -> AsyncIterator[int]:
            for i in range(1, 6):
                yield i

        async def process_error(value: int):
            raise ValueError

        await queued_processing(process(), process_error, exceptions_to_ignore=(ValueError,))
        self.assertEqual(set[int](), result)

    async def test_queued_processing_ignore_exception_different_exception(self) -> None:
        async def process() -> AsyncIterator[int]:
            for i in range(1, 1000):
                yield i

        async def process_error(value: int):
            raise TypeError

        with self.assertRaises(TypeError):
            await queued_processing(process(), process_error, exceptions_to_ignore=(ValueError,))

    async def test_queued_processing_ignore_exception_in_processor_function_True(self) -> None:
        async def process() -> AsyncIterator[int]:
            for i in range(1, 6):
                yield i

        async def process_error(value: int):
            raise ValueError

        def ignore(value: int) -> bool:
            return True
        try:
            await queued_processing(process(), process_error, exceptions_to_ignore=ignore)
        except Exception as e:
            self.fail(f'Exception {e} was raised when it should have been ignored')

    async def test_queued_processing_ignore_exception_in_processor_function_False(self) -> None:
        async def process() -> AsyncIterator[int]:
            for i in range(1, 6):
                yield i

        async def process_error(value: int):
            raise ValueError

        def ignore(value: int) -> bool:
            return False
        with self.assertRaises(ValueError):
            await queued_processing(process(), process_error, exceptions_to_ignore=ignore)

    async def test_queued_processing_ignore_exception_in_itr_function_False(self) -> None:
        async def process() -> AsyncIterator[int]:
            for i in range(1, 6):
                yield i
                raise ValueError

        async def process_error(value: int):
            pass

        def ignore(value: int) -> bool:
            return False
        with self.assertRaises(ValueError):
            await queued_processing(process(), process_error, exceptions_to_ignore=ignore)
