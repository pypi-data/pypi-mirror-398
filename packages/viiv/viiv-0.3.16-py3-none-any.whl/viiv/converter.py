#!/usr/bin/env python3
"""
The module is to convert one VsCode Theme snapshot to another VsCode Theme snapshot by replacing colors of HSL values.
"""
import os

import extcolors as E
import numpy as np
from loguru import logger
from peelee import peelee as P
from PIL import Image

import viiv.utils as U


def extract_colors(theme_name) -> list:
    """Extract distinct colors from the theme colors.

    Args:
        theme_name (str): The theme name.

    Returns:
        list: list of distinct colors of the theme.
    """
    theme_data = U.load_theme_data(theme_name)
    colors = theme_data["colors"]
    token_colors = theme_data["tokenColors"]
    assert (
        colors and token_colors
    ), "Not found 'colors' or 'tokenColors' in the theme data of {theme_name}."
    colors_values = colors.values()
    token_colors_values = [t["settings"]["foreground"] for t in token_colors]
    return list(colors_values) + token_colors_values


def _hex_to_hsv(hex_color):
    hls_color = P.hex2hls(hex_color)
    hsv_color = (
        round(hls_color[0] * 255),
        round(hls_color[2] * 100),
        round(hls_color[1] * 100),
    )
    h = hsv_color[0]
    s = hsv_color[1]
    v = hsv_color[2]
    h = h - h % 15
    s = s - s % 10
    v = v - v % 10
    logger.debug((h, s, v))
    return h, s, v


def get_image_path(theme_name, images_root="images"):
    """Get the image path of the theme snapshot."""
    image_path = f"{images_root}{os.sep}{theme_name}-snapshot.jpg"
    return image_path


def load_image(theme_name, image_path=None, color_mode="HSV"):
    """Load the image of the theme snapshot.

    Args:
        theme_name (str): The theme name.
        image_path (str, optional): The image path. Defaults to None.
        color_mode (str, optional): The color mode. Defaults to "HSV".
    Returns:
        Image: The image of the theme snapshot.
    """
    if not image_path:
        image_path = get_image_path(theme_name)
    image_orig = Image.open(image_path)
    if color_mode is not None:
        image_orig = image_orig.convert(color_mode)
    return image_orig


def get_image_data(theme_name, image_path=None, color_mode="HSV"):
    """Get the image data of the theme snapshot.

    Args:
        theme_name (str): The theme name.
        image_path (str, optional): The image path. Defaults to None.
        color_mode (str, optional): The color mode. Defaults to "HSV".
    Returns:
        np.ndarray: The image data of the theme snapshot.
    """
    image = load_image(
        theme_name=theme_name,
        image_path=image_path,
        color_mode=color_mode,
    )
    return np.array(image)


def extract_colors_from_theme_image(theme_name, tolerance=32):
    """Get the image 'RGB' data of the theme snapshot.

    Args:
        theme_name (str): The theme name.
        tolerance (int, optional): The tolerance. Defaults to 32.
    Returns:
        list: The extracted 'RGB' colors in the image.
    """
    image = load_image(theme_name=theme_name, color_mode="RGB")
    colors, _ = E.extract_from_image(image, tolerance=tolerance)
    _colors = [c[0] for c in colors]
    return _colors


def extend_theme_colors(theme_name, slice_total=100, selection_total=10):
    """Extend the theme colors.

    Generate darker and lighter colors for the specific theme color, then select some of the generated colors as extended colors for the specific theme color.
    The total number of the generated darker and lighter colors is 2 * slice_total.
    The total number of the selected extended colors is 2 * selection_total.
    The total number of the final returned extended theme colors is theme_colors_total + theme_colors total * 2 * selection_total.

    Args:
        theme_name (str): The theme name.
        slice_total (int, optional): The slice total to tell how many colors to generate for the specific theme color. Defaults to 100.
        selection_total (int, optional): The selection total to tell how many slice colors of darker colors or lighter colors to select as extended colors for the specific theme color. Defaults to 10.
    Returns:
        list: The extended theme colors in the 'HEX' mode(#RRGGBB).

    """
    theme_colors = extract_colors(theme_name)
    darker_theme_colors = [
        P.darker(c, slice_total)[0:selection_total] for c in theme_colors
    ]
    lighter_theme_colors = [
        P.lighter(c, slice_total)[0:selection_total] for c in theme_colors
    ]
    logger.info(
        tuple(len(c) for c in [theme_colors, darker_theme_colors, lighter_theme_colors])
    )
    theme_colors = (
        theme_colors
        + [c for d_colors in darker_theme_colors for c in d_colors]
        + [c for l_colors in lighter_theme_colors for c in l_colors]
    )
    return list(set(theme_colors))


def remove_alpha(theme_colors):
    """Remove the alpha channel of the theme colors."""
    theme_colors_no_alpha = [c[0:7] for c in theme_colors if c[7:] != "00"]
    return theme_colors_no_alpha


def create_theme_colors_map(
    theme_name,
    target_theme_name,
    extended=False,
    slice_total=100,
    selection_total=10,
):
    if extended:
        theme_colors = extend_theme_colors(
            theme_name, slice_total=100, selection_total=10
        )
    else:
        theme_colors = C.extract_colors(theme_name)
    if extended:
        target_theme_colors = extend_theme_colors(
            target_theme_name, slice_total=slice_total, selection_total=selection_total
        )
    else:
        target_theme_colors = C.extract_colors(target_theme_name)

    theme_colors = remove_alpha(theme_colors)
    target_theme_colors = remove_alpha(target_theme_colors)

    return dict(zip(theme_colors, target_theme_colors))


def convert_theme_snapshot(theme_name: str, target_theme_name: str) -> None:
    """Convert one VsCode Theme snapshot to another VsCode Theme snapshot by replacing colors of HSL values.

    Args:
        theme_name (str): The theme name.
        target_theme_name (str): The target theme name.
    """
    theme_colors = extract_colors(theme_name)
    target_theme_colors = extract_colors(target_theme_name)
    theme_colors_map = dict(zip(theme_colors, target_theme_colors))
    logger.debug(len(theme_colors_map))

    theme_snapshot = U.load_theme_snapshot(theme_name)
    theme_snapshot_hsv = theme_snapshot.convert("HSV")
    theme_snapshot_hsv_data = np.array(theme_snapshot_hsv)
    theme_hue = theme_snapshot_hsv_data[:, :, 0]
    theme_sat = theme_snapshot_hsv_data[:, :, 1]
    theme_val = theme_snapshot_hsv_data[:, :, 2]
    # sort theme_colors_map by the order of the keys hue
    logger.debug(theme_colors_map)
    theme_colors_map = dict(
        sorted(theme_colors_map.items(), key=lambda x: (_hex_to_hsv(x[0])[0]))
    )
    logger.debug(theme_colors_map)
    source_colors = list(theme_colors_map.keys())
    target_colors = list(theme_colors_map.values())
    for index, item in enumerate(theme_colors_map.items()):
        s_color = item[0]
        t_color = item[1]
        logger.debug((s_color, t_color))
        h_previous, s_previous, v_previous = 0, 0, 0
        h_target_previous, s_target_previous, v_target_previous = 0, 0, 0
        if index > 0:
            h_previous, s_previous, v_previous = _hex_to_hsv(source_colors[index - 1])
            h_target_previous, s_target_previous, v_target_previous = _hex_to_hsv(
                target_colors[index - 1]
            )
        h, s, v = _hex_to_hsv(s_color)
        h_half, s_half, v_half = (
            round(0.5 * abs(h - h_previous)),
            round(0.5 * abs(s - s_previous)),
            round(0.5 * abs(v - v_previous)),
        )
        h_target, s_target, v_target = _hex_to_hsv(t_color)
        h_target_half, s_target_half, v_target_half = (
            round(0.5 * abs(h_target - h_target_previous)),
            round(0.5 * abs(s_target - s_target_previous)),
            round(0.5 * abs(v_target - v_target_previous)),
        )

        hue_condition = ((theme_hue[:, :] - theme_hue[:, :] % 15) <= h) & (
            (theme_hue[:, :] - theme_hue[:, :] % 15) >= h_half
        )
        sat_condition = ((theme_sat[:, :] - theme_sat[:, :] % 10) <= s) & (
            (theme_sat[:, :] - theme_sat[:, :] % 10) >= s_half
        )
        val_condition = ((theme_val[:, :] - theme_val[:, :] % 10) <= v) & (
            (theme_val[:, :] - theme_val[:, :] % 10) >= v_half
        )
        hue_half_condition = ((theme_hue[:, :] - theme_hue[:, :] % 15) < h_half) & (
            (theme_hue[:, :] - theme_hue[:, :] % 15) > h_previous
        )
        sat_half_condition = ((theme_sat[:, :] - theme_sat[:, :] % 10) < s_half) & (
            (theme_sat[:, :] - theme_sat[:, :] % 10) > s_previous
        )
        val_half_condition = ((theme_val[:, :] - theme_val[:, :] % 10) < v_half) & (
            (theme_val[:, :] - theme_val[:, :] % 10) > v_previous
        )

        theme_hue[hue_condition] = h_target
        theme_sat[sat_condition] = s_target
        theme_val[val_condition] = v_target
        theme_hue[hue_half_condition] = h_target_half
        theme_sat[sat_half_condition] = s_target_half
        theme_val[val_half_condition] = v_target_half
        theme_snapshot_hsv_data[:, :, 0] = theme_hue
        theme_snapshot_hsv_data[:, :, 1] = theme_sat
        theme_snapshot_hsv_data[:, :, 2] = theme_val
    target_theme_snapshot = Image.fromarray(theme_snapshot_hsv_data, mode="HSV")
    target_theme_snapshot = target_theme_snapshot.convert("RGB")
    return U.save_theme_snapshot(target_theme_name, target_theme_snapshot)


if __name__ == "__main__":
    convert_theme_snapshot("viiv-atom-dark", "viiv-light")
