'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-01-07 09:04:14 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-01-07 09:04:15 +0100
FilePath     : utils.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

from matplotlib.colors import to_rgba
import colorsys


# Function to lighten or darken a color
def adjust_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> adjust_color('g', 0.3)
    >> adjust_color('#F034A3', 0.6)
    >> adjust_color((.3,.55,.1), 0.5)
    """

    try:
        c = to_rgba(color)
    except ValueError:
        c = (0, 0, 0, 0)
    c = colorsys.rgb_to_hls(c[0], c[1], c[2])
    return colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])
