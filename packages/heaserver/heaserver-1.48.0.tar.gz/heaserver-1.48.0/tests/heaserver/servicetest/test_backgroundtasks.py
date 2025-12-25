from unittest import IsolatedAsyncioTestCase
from heaserver.service.backgroundtasks import BackgroundTasks
from asyncio import create_task, sleep, CancelledError


class BackgroundTasksTestCase(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.__background_tasks = BackgroundTasks()

    async def asyncTearDown(self) -> None:
        await self.__background_tasks.clear()

    async def test_contains(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_contains')
        self.assertTrue(self.__background_tasks.contains('test_contains'))

    async def test_does_not_contain(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_contains')
        self.assertTrue(not self.__background_tasks.contains('test_contains2'))

    async def test_cancel(self):
        async def coro(app):
            while True:
                sleep(0.1)

        await self.__background_tasks.add(coro, 'test_cancel')
        self.__background_tasks.cancel('test_cancel')
        with self.assertRaises(CancelledError):
            await self.__background_tasks.join_all()
        self.assertTrue(self.__background_tasks.done('test_cancel'))
        self.assertIsNone(self.__background_tasks.result('test_cancel'))
        self.assertFalse(self.__background_tasks.succeeded('test_cancel'))
        self.assertFalse(self.__background_tasks.failed('test_cancel'))
        self.assertTrue(self.__background_tasks.cancelled('test_cancel'))
        self.assertFalse(self.__background_tasks.in_progress('test_cancel'))

    async def test_cancel_all(self):
        async def coro1(app):
            while True:
                sleep(0.1)

        async def coro2(app):
            while True:
                sleep(0.1)

        await self.__background_tasks.add(coro1, 'test_cancel1')
        await self.__background_tasks.add(coro2, 'test_cancel2')
        self.__background_tasks.cancel_all()
        with self.assertRaises(CancelledError):
            await self.__background_tasks.join_all()
        self.assertTrue(self.__background_tasks.done('test_cancel1'))
        self.assertTrue(self.__background_tasks.done('test_cancel2'))
        self.assertIsNone(self.__background_tasks.result('test_cancel1'))
        self.assertIsNone(self.__background_tasks.result('test_cancel2'))
        self.assertFalse(self.__background_tasks.succeeded('test_cancel1'))
        self.assertFalse(self.__background_tasks.succeeded('test_cancel2'))
        self.assertFalse(self.__background_tasks.failed('test_cancel1'))
        self.assertFalse(self.__background_tasks.failed('test_cancel2'))
        self.assertTrue(self.__background_tasks.cancelled('test_cancel1'))
        self.assertTrue(self.__background_tasks.cancelled('test_cancel2'))
        self.assertFalse(self.__background_tasks.in_progress('test_cancel1'))
        self.assertFalse(self.__background_tasks.in_progress('test_cancel2'))

    async def test_done(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_is_done')
        await self.__background_tasks.join('test_is_done')
        self.assertTrue(self.__background_tasks.done('test_is_done'))

    async def test_done_call_join_multiple_times(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_is_done_twice')
        await self.__background_tasks.join('test_is_done_twice')
        try:
            await self.__background_tasks.join('test_is_done_twice')  # Call join again
        except:
            self.fail('Calling join multiple times raised an exception')

    async def test_done_call_join_all_multiple_times(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_is_done_all_twice')
        await self.__background_tasks.join_all()
        try:
            await self.__background_tasks.join_all()  # Call join_all again
        except:
            self.fail('Calling join_all multiple times raised an exception')

    async def test_succeeded(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_succeeded')
        await self.__background_tasks.join('test_succeeded')
        self.assertTrue(self.__background_tasks.done('test_succeeded'))
        self.assertTrue(self.__background_tasks.succeeded('test_succeeded'))
        self.assertFalse(self.__background_tasks.failed('test_succeeded'))
        self.assertFalse(self.__background_tasks.cancelled('test_succeeded'))
        self.assertFalse(self.__background_tasks.in_progress('test_succeeded'))

    async def test_failed(self):
        async def coro(app):
            raise ValueError

        await self.__background_tasks.add(coro, 'test_failed')
        await self.__background_tasks.join('test_failed')
        self.assertTrue(self.__background_tasks.failed('test_failed'))
        self.assertFalse(self.__background_tasks.succeeded('test_failed'))
        self.assertFalse(self.__background_tasks.cancelled('test_failed'))
        self.assertTrue(self.__background_tasks.done('test_failed'))
        self.assertFalse(self.__background_tasks.in_progress('test_failed'))

    async def test_get_error(self):
        async def coro(app):
            raise ValueError

        await self.__background_tasks.add(coro, 'test_get_error')
        await self.__background_tasks.join('test_get_error')
        self.assertIsInstance(self.__background_tasks.error('test_get_error'), ValueError)

    async def test_remove(self):
        async def coro(app):
            pass

        await self.__background_tasks.add(coro, 'test_remove')
        await self.__background_tasks.join('test_remove')
        self.__background_tasks.remove('test_remove')
        self.assertFalse(self.__background_tasks.contains('test_remove'))

    async def test_len(self):
        async def coro1(app):
            pass

        async def coro2(app):
            pass

        await self.__background_tasks.add(coro1, 'test_len1')
        await self.__background_tasks.add(coro2, 'test_len2')
        await self.__background_tasks.join('test_len1')
        try:
            self.assertEqual(2, len(self.__background_tasks))
        finally:
            await self.__background_tasks.join_all()

    async def test_clear(self):
        async def coro1(app):
            pass

        async def coro2(app):
            pass

        await self.__background_tasks.add(coro1, 'test_clear1')
        await self.__background_tasks.add(coro2, 'test_clear2')
        await self.__background_tasks.join_all()
        await self.__background_tasks.clear()
        self.assertEqual(0, len(self.__background_tasks))

    async def test_auto_join(self):
        async def coro1(app):
            pass

        async def coro2(app):
            pass

        await self.__background_tasks.add(coro1, 'test_clear1')
        await self.__background_tasks.add(coro2, 'test_clear2')
        task = create_task(self.__background_tasks.auto_join())
        while self.__background_tasks.running_tasks() > 0:
            await sleep(0.1)
        task.cancel()
        with self.assertRaises(CancelledError):
            await task
        self.assertTrue(self.__background_tasks.done('test_clear1'))
        self.assertTrue(self.__background_tasks.done('test_clear2'))
        self.assertFalse(self.__background_tasks.in_progress('test_clear1'))
        self.assertFalse(self.__background_tasks.in_progress('test_clear2'))
        self.assertFalse(self.__background_tasks.failed('test_clear1'))
        self.assertFalse(self.__background_tasks.failed('test_clear2'))
        self.assertEqual(2, self.__background_tasks.done_tasks())
        self.assertTrue(self.__background_tasks.succeeded('test_clear1'))
        self.assertTrue(self.__background_tasks.succeeded('test_clear2'))
        self.assertFalse(self.__background_tasks.cancelled('test_clear1'))
        self.assertFalse(self.__background_tasks.cancelled('test_clear2'))

    async def test_done_tasks(self):
        async def coro1(app):
            pass

        async def coro2(app):
            return 'foobar'

        await self.__background_tasks.add(coro1, 'test_done_tasks1')
        await self.__background_tasks.add(coro2, 'test_done_tasks2')
        await self.__background_tasks.join_all()
        self.assertEqual(2, self.__background_tasks.done_tasks())
        self.assertEqual('foobar', self.__background_tasks.result('test_done_tasks2'))
        self.assertIsNone(self.__background_tasks.result('test_done_tasks1'))
        self.assertTrue(self.__background_tasks.succeeded('test_done_tasks2'))
        self.assertTrue(self.__background_tasks.succeeded('test_done_tasks1'))
        self.assertTrue(self.__background_tasks.done('test_done_tasks1'))
        self.assertTrue(self.__background_tasks.done('test_done_tasks2'))
        self.assertFalse(self.__background_tasks.in_progress('test_done_tasks1'))
        self.assertFalse(self.__background_tasks.in_progress('test_done_tasks2'))
        self.assertFalse(self.__background_tasks.failed('test_done_tasks1'))
        self.assertFalse(self.__background_tasks.failed('test_done_tasks2'))
        self.assertEqual(2, self.__background_tasks.done_tasks())

    async def test_auto_join_with_error(self):
        async def coro1(app):
            raise ValueError

        async def coro2(app):
            pass

        await self.__background_tasks.add(coro1, 'test_clear1')
        await self.__background_tasks.add(coro2, 'test_clear2')
        task = create_task(self.__background_tasks.auto_join())
        while self.__background_tasks.running_tasks() > 0:
            await sleep(0.1)
        task.cancel()
        with self.assertRaises(CancelledError):
            await task
        self.assertTrue(self.__background_tasks.failed('test_clear1'))
        self.assertFalse(self.__background_tasks.failed('test_clear2'))
        self.assertTrue(self.__background_tasks.done('test_clear1'))
        self.assertTrue(self.__background_tasks.done('test_clear2'))
        self.assertFalse(self.__background_tasks.in_progress('test_clear1'))
        self.assertFalse(self.__background_tasks.in_progress('test_clear2'))
        self.assertTrue(self.__background_tasks.succeeded('test_clear2') or self.__background_tasks.cancelled('test_clear2'))
        self.assertIsNone(self.__background_tasks.result('test_clear1'))
        self.assertIsNone(self.__background_tasks.result('test_clear2'))
        self.assertEqual(2, self.__background_tasks.done_tasks())

    async def test_auto_join_all_failed(self):
        async def coro1(app):
            raise ValueError

        async def coro2(app):
            raise ValueError

        await self.__background_tasks.add(coro1, 'test_clear1')
        await self.__background_tasks.add(coro2, 'test_clear2')
        task = create_task(self.__background_tasks.auto_join())
        while self.__background_tasks.running_tasks() > 0:
            await sleep(0.1)
        task.cancel()
        with self.assertRaises(CancelledError):
            await task
        self.assertTrue(self.__background_tasks.failed('test_clear1') or self.__background_tasks.cancelled('test_clear1'))
        self.assertTrue(self.__background_tasks.failed('test_clear2') or self.__background_tasks.cancelled('test_clear2'))
        self.assertIsNone(self.__background_tasks.result('test_clear1'))
        self.assertIsNone(self.__background_tasks.result('test_clear2'))
        self.assertTrue(self.__background_tasks.done('test_clear1'))
        self.assertTrue(self.__background_tasks.done('test_clear2'))
        self.assertFalse(self.__background_tasks.in_progress('test_clear1'))
        self.assertFalse(self.__background_tasks.in_progress('test_clear2'))
        self.assertEqual(2, self.__background_tasks.done_tasks())

    async def test_cancellation(self):
        async def coro(app):
            while True:
                await sleep(10)

        await self.__background_tasks.add(coro, 'test_cancellation')
        self.__background_tasks.cancel('test_cancellation')
        with self.assertRaises(CancelledError):
            await self.__background_tasks.join('test_cancellation')
        self.assertTrue(self.__background_tasks.cancelled('test_cancellation'))
        self.assertFalse(self.__background_tasks.in_progress('test_cancellation'))
        self.assertTrue(self.__background_tasks.done('test_cancellation'))
        self.assertIsNone(self.__background_tasks.result('test_cancellation'))
        self.assertFalse(self.__background_tasks.succeeded('test_cancellation'))
        self.assertFalse(self.__background_tasks.failed('test_cancellation'))
