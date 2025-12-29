"""
color.py - color related functions
"""

import numpy as np
from PIL import ImageColor


def get_random_color():
    """
    Returns a random RGB color.
    :return:
    """
    color = tuple(np.random.randint(0, 256, size=3))
    return color


def clamp(x: int):
    """
    clamp ensures a floor and a ceiling to adhere to RGB values
    0 <= {r,g,b} <= 255
    :param x:
    :return:
    """
    return max(0, min(x, 255))


def get_hex_value(rgb_color):
    """
     Returns a hexadecimal color code from an RGB input
    :param rgb_color:
    :return:
    """
    # The passed in rgb_color should be a tuple with 3 values, it's safe to assume positional values here.
    r, g, b = rgb_color
    hex_value = "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))
    return hex_value


def return_complimentary_color(hex_color):
    """
    Returns complimentary RGB color
    :return:
    """

    if hex_color[0] == "#":
        hex_color = hex_color[1:]
    rgb = (hex_color[0:2], hex_color[2:4], hex_color[4:6])
    comp = ["%02X" % (255 - int(a, 16)) for a in rgb]
    comp_hex = "#" + "".join(comp)
    comp_rgb = ImageColor.getcolor(comp_hex, "RGB")

    return comp_rgb
