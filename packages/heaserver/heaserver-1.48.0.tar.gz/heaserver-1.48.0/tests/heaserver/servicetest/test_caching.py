import time
from unittest import TestCase
from heaserver.service.caching import ttl_cache
from datetime import timedelta


class TTLCacheTestCase(TestCase):
    def test_ttl_cache_insomnia(self) -> None:
        """Checks if the ttl_cache decorator actually caches the result in the given time frame."""
        bar = 0

        @ttl_cache
        def foo() -> int:
            nonlocal bar
            bar += 1
            return bar

        foo()
        self.assertEqual(1, foo(), 'value not cached')

    def test_ttl_cache_sleepy(self) -> None:
        """Checks if the ttl_cache decorator does not cache the result beyond the given time frame."""
        bar = 0

        @ttl_cache(ttl=timedelta(milliseconds=10))
        def foo() -> int:
            nonlocal bar
            bar += 1
            return bar

        foo()
        time.sleep(0.2)
        self.assertEqual(2, foo(), 'value still cached')

    def test_decorator_preserves_identity_without_args(self) -> None:
        """
        Checks if the ttl_cache decorator preserves the identity of the function being decorated when the decorator
        is passed no arguments.
        """

        @ttl_cache
        def foo() -> None:
            pass

        self.assertEqual('foo', foo.__name__)

    def test_decorator_preserves_identity_with_args(self) -> None:
        """
        Checks if the ttl_cache decorator preserves the identity of the function being decorated when the decorator
        is passed an argument.
        """

        @ttl_cache(ttl=timedelta(days=1))
        def foo() -> None:
            pass

        self.assertEqual('foo', foo.__name__)

    def test_decorator_preserves_docstring_without_args(self) -> None:
        """
        Checks if the ttl_cache decorator preserves the identity of the function being decorated when the decorator
        is passed no arguments.
        """

        @ttl_cache
        def foo() -> None:
            """foobar"""
            pass

        self.assertEqual('foobar', foo.__doc__)

    def test_decorator_preserves_docstring_with_args(self) -> None:
        """
        Checks if the ttl_cache decorator preserves the identity of the function being decorated when the decorator
        is passed an argument.
        """

        @ttl_cache(ttl=timedelta(days=1))
        def foo() -> None:
            """foobar"""
            pass

        self.assertEqual('foobar', foo.__doc__)
