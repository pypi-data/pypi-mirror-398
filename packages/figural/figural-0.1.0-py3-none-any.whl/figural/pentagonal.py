import math

import matplotlib.backends.backend_pgf
import matplotlib.pyplot as plt
import numpy as np
import webcolors


def common_texification(text):
    return text


matplotlib.backends.backend_pgf.common_texification = common_texification

if not hasattr(webcolors, "CSS3_HEX_TO_NAMES"):
    css3_names = webcolors.names("css3")
    webcolors.CSS3_HEX_TO_NAMES = {
        webcolors.name_to_hex(name, spec="css3"): name for name in css3_names
    }

import tikzplotlib


def arange(n):
    """Generates the first n-1 pentagonal numbers.

    Args:
        n (int): The upper bound for the index (exclusive).

    Returns:
        np.ndarray: An array containing the first n-1 pentagonal numbers.

    Examples:
    >>> import figural.pentagonal as pn
    >>> pn.arange(5)
    array([ 1,  5, 12, 22, 35])
    """
    if n < 1:
        return np.array([], dtype=int)
    a = np.arange(n) * 3 + 1
    return np.cumsum(a)


def ith(i):
    """Calculates the i-th pentagonal number.

    Args:
        i (int): The index of the pentagonal number (1-based).

    Returns:
        int: The i-th pentagonal number.

    Examples:
        >>> import figural.pentagonal as pn
        >>> pn.ith(1)
        1
        >>> pn.ith(2)
        5
    """
    return (3 * i * i - i) // 2


def is_pentagonal(x: int | np.ndarray) -> bool | np.ndarray:
    """Checks if a number or array of numbers are pentagonal numbers.

    Args:
        x (int | np.ndarray): The number(s) to check.

    Returns:
        bool | np.ndarray: True if the number is pentagonal, False otherwise.
                           Returns a boolean array if input is an array.

    Examples:
    >>> import figural.pentagonal as pn
    >>> pn.is_pentagonal(pn.arange(5))
    array([ True,  True,  True,  True,  True])

    >>> pn.is_pentagonal(6)
    False
    """
    if np.any(x < 1):
        return False
    n = (1 + (1 + 24 * x) ** 0.5) / 6
    return np.floor(n) == n


# ---------- drawing functions ---------- #


def _draw_segment_of_points(
    start, end, num_points, marker_style="o", ax=None, skip_start=False, **kwargs
):
    """
    Draws a segment of points between start and end.
    """
    if ax is None:
        ax = plt.gca()

    x_start, y_start = start
    x_end, y_end = end

    if num_points <= 1:
        if not skip_start:
            ax.plot([x_start], [y_start], linestyle="", marker=marker_style, **kwargs)
        return

    # Generate points
    xs = np.linspace(x_start, x_end, num_points)
    ys = np.linspace(y_start, y_end, num_points)

    if skip_start:
        xs = xs[1:]
        ys = ys[1:]

    ax.plot(xs, ys, linestyle="", marker=marker_style, **kwargs)


def draw_ith(
    N,
    distance=0.5,
    marker_style="o",
    markersize=10,
    color="black",
    with_label: bool = False,
    return_tikz: bool = False,
    ax=None,
    show=True,
    draw_contourn: bool = True,
):
    """Draws the ith pentagonal number.

    Args:
        N (int): The index of the pentagonal number to draw.
        distance (float, optional): Distance between consecutive points. Defaults to 0.5.
        marker_style (str, optional): Matplotlib marker style. Defaults to 'o'.
        markersize (int, optional): Size of the markers. Defaults to 10.
        color (str, optional): Color of the markers. Defaults to 'black'.
        with_label (bool, optional): Whether to add a label under the pentagon. Defaults to False.
        return_tikz (bool, optional): Whether to return the TikZ code instead of showing the plot. Defaults to False.
        ax (matplotlib.axes.Axes, optional): Axes to draw on. If None, uses current axes. Defaults to None.
        show (bool, optional): Whether to call plt.show() at the end. Defaults to True.
        draw_contourn (bool, optional): Whether to draw the outline of the pentagon. Defaults to True.

    Returns:
        str | None: The TikZ code if return_tikz is True, otherwise None.

    Examples:
        >>> draw_ith(3)
        # Displays a plot of the 3rd pentagonal number
    """
    if ax is None:
        ax = plt.gca()

    # Angles for the 4 rays (in radians)
    angles_deg = [-36, -72, -108, -144]
    angles = [math.radians(a) for a in angles_deg]

    phi = (1 + math.sqrt(5)) / 2

    # Draw P1 (center/top vertex)
    ax.plot(
        [0], [0], linestyle="", marker=marker_style, markersize=markersize, color=color
    )

    for k in range(2, N + 1):
        r = (k - 1) * distance

        p1 = (r * math.cos(angles[0]), r * math.sin(angles[0]))
        p2 = (r * phi * math.cos(angles[1]), r * phi * math.sin(angles[1]))
        p3 = (r * phi * math.cos(angles[2]), r * phi * math.sin(angles[2]))
        p4 = (r * math.cos(angles[3]), r * math.sin(angles[3]))

        # Draw segments
        # P1 -> P2 (k points)
        _draw_segment_of_points(
            p1,
            p2,
            k,
            marker_style,
            ax=ax,
            markersize=markersize,
            color=color,
            skip_start=False,
        )
        # P2 -> P3 (k points, skip P2)
        _draw_segment_of_points(
            p2,
            p3,
            k,
            marker_style,
            ax=ax,
            markersize=markersize,
            color=color,
            skip_start=True,
        )
        # P3 -> P4 (k points, skip P3)
        _draw_segment_of_points(
            p3,
            p4,
            k,
            marker_style,
            ax=ax,
            markersize=markersize,
            color=color,
            skip_start=True,
        )

        if draw_contourn:
            # Draw the outline of the k-th pentagon
            p0 = (0, 0)
            pentagon_x = [p0[0], p1[0], p2[0], p3[0], p4[0], p0[0]]
            pentagon_y = [p0[1], p1[1], p2[1], p3[1], p4[1], p0[1]]
            ax.plot(pentagon_x, pentagon_y, color="black", linewidth=1, zorder=0)
    if with_label:
        r_max = (N - 1) * distance
        y_min = r_max * phi * math.sin(math.radians(-72))

        pN = ith(N)
        ax.text(
            0, y_min - distance, f"$P_{{{N}}}={pN}$", ha="center", va="top", fontsize=12
        )

    ax.axis("equal")
    ax.axis("off")

    if return_tikz:
        return tikzplotlib.get_tikz_code()

    if show:
        plt.show()


def draw_range(
    start: int,
    end: int,
    distance=0.5,
    marker_style="o",
    markersize=10,
    color="black",
    with_label: bool = False,
    return_tikz: bool = False,
    cols: int = 4,
    draw_grid: bool = True,
    draw_contourn: bool = True,
):
    """Draws a grid of pentagonal arrangements for a range of numbers.

    Args:
        start (int): The starting index of the pentagonal numbers.
        end (int): The ending index of the pentagonal numbers.
        distance (float, optional): Distance between consecutive points. Defaults to 0.5.
        marker_style (str, optional): Matplotlib marker style. Defaults to 'o'.
        markersize (int, optional): Size of the markers. Defaults to 10.
        color (str, optional): Color of the markers. Defaults to 'black'.
        with_label (bool, optional): Whether to add a label under each pentagon. Defaults to False.
        return_tikz (bool, optional): Whether to return the TikZ code instead of showing the plot. Defaults to False.
        cols (int, optional): Number of columns in the grid. Defaults to 4.
        draw_grid (bool, optional): Whether to draw a grid around the subplots. Defaults to True.
        draw_contourn (bool, optional): Whether to draw the outline of the pentagon. Defaults to True.

    Returns:
        str | None: The TikZ code if return_tikz is True, otherwise None.

    Examples:
        >>> draw_range(1, 4, cols=2)
        # Displays a grid of the first 4 pentagonal numbers
    """
    num_plots = end - start + 1
    rows = (num_plots + cols - 1) // cols

    if draw_grid:
        plt.subplots_adjust(wspace=0, hspace=0)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    axes = np.atleast_1d(axes).flatten()

    max_N = end
    phi = (1 + math.sqrt(5)) / 2
    r_max = (max_N - 1) * distance

    angles_deg = [-36, -72, -108, -144]
    angles = [math.radians(a) for a in angles_deg]

    xs = [0]  # Top vertex
    ys = [0]

    xs.append(r_max * math.cos(angles[0]))
    ys.append(r_max * math.sin(angles[0]))

    xs.append(r_max * phi * math.cos(angles[1]))
    ys.append(r_max * phi * math.sin(angles[1]))

    xs.append(r_max * phi * math.cos(angles[2]))
    ys.append(r_max * phi * math.sin(angles[2]))

    xs.append(r_max * math.cos(angles[3]))
    ys.append(r_max * math.sin(angles[3]))

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    bottom_padding = 2.0 * distance
    top_padding = 1.0 * distance

    W_view = max_x - min_x + 2 * distance
    H_view = (max_y - min_y) + top_padding + bottom_padding

    center_x = (min_x + max_x) / 2

    for idx, N in enumerate(range(start, end + 1)):
        ax = axes[idx]
        draw_ith(
            N,
            distance,
            marker_style,
            markersize,
            color,
            with_label,
            return_tikz=False,
            ax=ax,
            show=False,
            draw_contourn=draw_contourn,
        )

        r_N = (N - 1) * distance
        y_min_N = r_N * phi * math.sin(math.radians(-72))

        view_bottom = y_min_N - bottom_padding
        view_top = view_bottom + H_view

        ax.set_xlim(center_x - W_view / 2, center_x + W_view / 2)
        ax.set_ylim(view_bottom, view_top)

        ax.set_aspect("equal")

        if draw_grid:
            ax.axis("on")
            ax.set_xticks([])
            ax.set_yticks([])

            row = idx // cols
            col = idx % cols

            ax.spines["top"].set_visible(row == 0)
            ax.spines["bottom"].set_visible(True)
            ax.spines["left"].set_visible(col == 0)
            ax.spines["right"].set_visible(True)
        else:
            ax.axis("off")

    for i in range(num_plots, len(axes)):
        axes[i].axis("off")

    if draw_grid:
        plt.subplots_adjust(wspace=0, hspace=0)

    if return_tikz:
        return tikzplotlib.get_tikz_code()

    plt.show()
