import operator
import types
import unittest

from pointwise.core import pointwise


class TestPointwise(unittest.TestCase):
    def test_positional_pointwise_add(self):
        f = lambda x: x + 1
        g = lambda x: 2 * x
        h = pointwise(operator.add, f, g)
        self.assertEqual(h(3), (3 + 1) + (2 * 3))

    def test_keyword_pointwise(self):
        def outer(a, b, c=0):
            return a * b + c

        f = lambda x: x + 1
        g = lambda x: x + 2
        c_fn = lambda x: x * 10

        h = pointwise(outer, f, g, c=c_fn)
        self.assertEqual(h(3), (4 * 5) + 30)

    def test_passthrough_args_kwargs(self):
        f = lambda x, y=0, *, scale=1: (x + y) * scale
        g = lambda x, y=0, *, scale=1: (x - y) * scale

        h = pointwise(operator.mul, f, g)
        self.assertEqual(
            h(10, y=4, scale=2),
            f(10, y=4, scale=2) * g(10, y=4, scale=2),
        )

    def test_outer_receives_computed_values(self):
        calls = []

        def outer(*a, **k):
            calls.append((a, k))
            return a, k

        f = lambda x: x + 1
        g = lambda x: x + 2
        h = pointwise(outer, f, g, z=lambda x: x + 3)

        res = h(5)
        self.assertEqual(res, ((6, 7), {"z": 8}))
        self.assertEqual(calls, [((6, 7), {"z": 8})])

    def test_wraps_metadata(self):
        def outer(a, b):
            """outer doc"""
            return a + b

        h = pointwise(outer, lambda x: x, lambda x: x)
        self.assertEqual(h.__name__, outer.__name__)
        self.assertEqual(h.__doc__, outer.__doc__)

    def test_no_inner_functions(self):
        def outer():
            return 123

        h = pointwise(outer)
        self.assertEqual(h(), 123)

    def test_exception_propagates(self):
        def outer(a):
            return a

        def bad(x):
            raise ValueError("boom")

        h = pointwise(outer, bad)
        with self.assertRaises(ValueError):
            h(1)

    def test_returns_function_type(self):
        h = pointwise(lambda a: a, lambda x: x)
        self.assertIsInstance(h, types.FunctionType)


if __name__ == "__main__":
    unittest.main()
