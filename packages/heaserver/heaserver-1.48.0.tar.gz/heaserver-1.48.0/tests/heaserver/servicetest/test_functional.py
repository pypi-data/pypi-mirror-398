from unittest import TestCase
from heaserver.service.functional import compose


class ComposeTestCase(TestCase):
    """Tests for the heaserver.service.functional.compose function."""

    def test_compose(self) -> None:
        """Tests if composing 100 successor (f(x) = x + 1) functions and passing in 0 returns 100."""
        self.assertEqual(100, compose(*((lambda x: x + 1,) * 100))(0))
