# -----------------------------------------------------------------------------
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or distribute
# this software, either in source code form or as a compiled binary, for any
# purpose, commercial or non-commercial, and by any means.
#
# In jurisdictions that recognize copyright laws, the author or authors of this
# software dedicate any and all copyright interest in the software to the
# public domain. We make this dedication for the benefit of the public at large
# and to the detriment of our heirs and successors. We intend this dedication
# to be an overt act of relinquishment in perpetuity of all present and future
# rights to this software under copyright law.
#
# OPTIONAL ATTRIBUTION:
# Credit to E. Luttmann is appreciated but not required.
#
# For more information, please refer to <https://unlicense.org>
# -----------------------------------------------------------------------------
import unittest
import math

from pycessingame import *

class TestColorFunction(unittest.TestCase):

    def setUp(self):
        # Reset auf Processing-Defaults
        colorMode(RGB)

    # ---------- color() ----------

    def test_color_gray(self):
        self.assertEqual(color(128), (128, 128, 128, 255))

    def test_color_gray_alpha(self):
        self.assertEqual(color(128, 64), (128, 128, 128, 64))

    def test_color_rgb(self):
        self.assertEqual(color(10, 20, 30), (10, 20, 30, 255))

    def test_color_rgba(self):
        self.assertEqual(color(10, 20, 30, 40), (10, 20, 30, 40))

    def test_color_tuple(self):
        self.assertEqual(color((1, 2, 3)), (1, 2, 3, 255))

    def test_color_nested_tuple(self):
        self.assertEqual(color(((10, 20, 30))), (10, 20, 30, 255))

    def test_color_float_rgb(self):
        colorMode(RGB, 1.0)
        self.assertEqual(color(1.0, 0.5, 0.0), (255, 127, 0, 255))

    def test_color_float_alpha(self):
        colorMode(RGB, 1.0)
        self.assertEqual(color(0.5, 0.5), (127, 127, 127, 127))


class TestColorModeHSB(unittest.TestCase):

    def setUp(self):
        colorMode(HSB, 360, 100, 100, 255)

    def test_hsb_red(self):
        c = color(0, 100, 100)
        self.assertEqual(c[:3], (255, 0, 0))

    def test_hsb_green(self):
        c = color(120, 100, 100)
        self.assertEqual(c[:3], (0, 255, 0))

    def test_hsb_blue(self):
        c = color(240, 100, 100)
        self.assertEqual(c[:3], (0, 0, 255))

    def test_hsb_alpha(self):
        c = color(0, 100, 100, 128)
        self.assertEqual(alpha(c), 128)


class TestColorComponents(unittest.TestCase):

    def setUp(self):
        colorMode(RGB)

    def test_rgb_components(self):
        c = color(10, 20, 30, 40)
        self.assertEqual(red(c), 10)
        self.assertEqual(green(c), 20)
        self.assertEqual(blue(c), 30)
        self.assertEqual(alpha(c), 40)

    def test_rgb_components_without_alpha(self):
        c = color(1, 2, 3)
        self.assertEqual(alpha(c), 255)


class TestHSBComponents(unittest.TestCase):

    def test_hsb_components_red(self):
        c = color(255, 0, 0)
        self.assertAlmostEqual(hue(c), 0, delta=2)
        self.assertEqual(saturation(c), 255)
        self.assertEqual(brightness(c), 255)

    def test_hsb_components_green(self):
        c = color(0, 255, 0)
        self.assertAlmostEqual(hue(c), 85, delta=2)   # 120° scaled to 255
        self.assertEqual(saturation(c), 255)
        self.assertEqual(brightness(c), 255)

    def test_hsb_components_gray(self):
        c = color(128)
        self.assertEqual(saturation(c), 0)
        self.assertEqual(brightness(c), 128)

    def test_hsb_components_black(self):
        c = color(0)
        self.assertEqual(brightness(c), 0)
        self.assertEqual(saturation(c), 0)


class TestColorModeIsolation(unittest.TestCase):

    def test_color_mode_does_not_affect_components(self):
        colorMode(HSB, 360, 100, 100)
        c = color(120, 100, 100)  # green
        colorMode(RGB)

        self.assertEqual(red(c), 0)
        self.assertEqual(green(c), 255)
        self.assertEqual(blue(c), 0)

class TestLerpColorRGB(unittest.TestCase):

    def setUp(self):
        colorMode(RGB)

    def test_lerp_rgb_half(self):
        c1 = color(0, 0, 0)
        c2 = color(255, 255, 255)
        self.assertEqual(
            lerpColor(c1, c2, 0.5),
            (127, 127, 127, 255)
        )

    def test_lerp_rgb_zero(self):
        c1 = color(10, 20, 30)
        c2 = color(200, 210, 220)
        self.assertEqual(lerpColor(c1, c2, 0.0), c1)

    def test_lerp_rgb_one(self):
        c1 = color(10, 20, 30)
        c2 = color(200, 210, 220)
        self.assertEqual(lerpColor(c1, c2, 1.0), c2)

    def test_lerp_rgb_alpha(self):
        c1 = color(0, 0, 0, 0)
        c2 = color(0, 0, 0, 255)
        self.assertEqual(
            lerpColor(c1, c2, 0.5),
            (0, 0, 0, 127)
        )

    def test_lerp_rgb_extrapolation(self):
        c1 = color(0, 0, 0)
        c2 = color(100, 100, 100)
        self.assertEqual(
            lerpColor(c1, c2, 1.5),
            (150, 150, 150, 255)
        )

if __name__ == "__main__":
    unittest.main()
