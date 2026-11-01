"""Dependency-free tests: python -m unittest discover -s tests -v."""
import unittest

from orion_motion import (
    DEGREES_PER_MAS,
    DEFAULT_DATA,
    illustrative_color,
    load_stars,
    marker_area,
    propagate,
)


class OrionMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stars = load_stars(DEFAULT_DATA)

    def test_original_nine_stars_are_loaded(self):
        self.assertEqual(len(self.stars), 9)
        self.assertEqual(self.stars[0].temperature_k, 3500)

    def test_zero_years_is_identity(self):
        for star in self.stars:
            self.assertEqual(propagate(star, 0), (star.x_deg, star.y_deg))

    def test_linear_displacement_conversion(self):
        star = self.stars[0]
        x, y = propagate(star, 1000)
        self.assertAlmostEqual(
            x - star.x_deg, 1000 * star.pm_x_mas_per_year * DEGREES_PER_MAS
        )
        self.assertAlmostEqual(
            y - star.y_deg, 1000 * star.pm_y_mas_per_year * DEGREES_PER_MAS
        )

    def test_illustrative_color_and_marker_area(self):
        self.assertTrue(illustrative_color(3500).startswith("#"))
        self.assertEqual(len(illustrative_color(3500)), 7)
        self.assertGreater(marker_area(0.5), marker_area(4.0))


if __name__ == "__main__":
    unittest.main()
