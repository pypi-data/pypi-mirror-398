import unittest

from phrugal.decorated_image import (
    add_dimensions,
    subtract_dimensions,
    scale_dimensions,
)


class TestDimensionHelpers(unittest.TestCase):
    def test_add_dimensions(self):
        dim_a = 1, 2
        dim_b = 2, 3
        self.assertEqual((3, 5), add_dimensions(dim_a, dim_b))

        with self.assertRaises(AssertionError):
            tuple_with_3_elements = (1, 2, 3)
            add_dimensions(dim_a, tuple_with_3_elements)

    def test_subtract_dimensions(self):
        dim_a = 1, 2
        dim_b = 2, 3
        self.assertEqual((-1, -1), subtract_dimensions(dim_a, dim_b))

        with self.assertRaises(AssertionError):
            tuple_with_3_elements = (1, 2, 3)
            subtract_dimensions(dim_a, tuple_with_3_elements)

    def test_scale_dimensions(self):
        dim_a = 10, 2
        scale = -0.5
        self.assertEqual((-5, -1), scale_dimensions(dim_a, scale))
