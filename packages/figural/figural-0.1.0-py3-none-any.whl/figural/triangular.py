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


def arange(n: int) -> np.ndarray:
    """Generates the first n triangular numbers.

    Args:
        n (int): The upper bound for the range generation logic.

    Returns:
        np.ndarray: An array containing the first n-1 triangular numbers.

    Examples:
        >>> import figural.triangular as tr
        >>> tr.arange(5)
        array([ 1,  3,  6, 10])
    """
    a = np.arange(1, n)
    return np.cumsum(a)


def ith(i: int) -> int:
    """Calculates the i-th triangular number.

    Args:
        i (int): The index of the triangular number (1-based).

    Returns:
        int: The i-th triangular number.

    Examples:
        >>> import figural.triangular as tr
        >>> tr.ith(1)
        1
        >>> tr.ith(5)
        15
    """
    return (i * (i + 1)) // 2


def is_triangular(x: int | np.ndarray) -> bool | np.ndarray:
    """Checks if a number or array of numbers are triangular numbers.

    Args:
        x (int | np.ndarray): The number(s) to check.

    Returns:
        bool | np.ndarray: True if the number is triangular, False otherwise.
                           Returns a boolean array if input is an array.

    Examples:
        >>> import figural.triangular as tr
        >>> tr.is_triangular(6)
        True
        >>> tr.is_triangular(11)
        False
        >>> tr.is_triangular(np.array([1, 11, 15, 36]))
        array([ True, False,  True,  True])
    """

    if np.any(x < 1):
        return False
    n = (-1 + (1 + 8 * x) ** 0.5) / 2
    return np.floor(n) == n


# ------------------- Drawing functions ------------------- #


def _draw_line_of_points(
    origin, num_points, distance, marker_style="o", ax=None, **kwargs
):
    """
    Draws a line of points.
    """
    if ax is None:
        ax = plt.gca()

    x0, y0 = origin
    x_coords = [x0 + i * distance for i in range(num_points)]
    y_coords = [y0] * num_points
    ax.plot(x_coords, y_coords, linestyle="", marker=marker_style, **kwargs)


def draw_ith(
    N: int,
    distance: float = 0.5,
    marker_style: str = "o",
    markersize: int = 10,
    color: str = "black",
    with_label: bool = False,
    return_tikz: bool = False,
    ax=None,
    show: bool = True,
    draw_contourn: bool = True,
):
    """Draws the ith triangular number

    Args:
        N (int): The index of the triangular number to draw (number of rows).
        distance (float, optional): Distance between consecutive points. Defaults to 0.5.
        marker_style (str, optional): Matplotlib marker style. Defaults to 'o'.
        markersize (int, optional): Size of the markers. Defaults to 10.
        color (str, optional): Color of the markers. Defaults to 'black'.
        with_label (bool, optional): Whether to add a label under the triangle. Defaults to False.
        return_tikz (bool, optional): Whether to return the TikZ code instead of showing the plot. Defaults to False.
        ax (matplotlib.axes.Axes, optional): Axes to draw on. If None, uses current axes. Defaults to None.
        show (bool, optional): Whether to call plt.show() at the end. Defaults to True.
        draw_contourn (bool, optional): Whether to draw a triangle connecting the outer points. Defaults to True.

    Returns:
        str | None: The TikZ code if return_tikz is True, otherwise None.

    Examples:
        >>> draw_ith(3)
        # Displays a plot of the 3rd triangular number
    """
    if ax is None:
        ax = plt.gca()

    x, y = 0, 0
    for i in range(N, 0, -1):
        _draw_line_of_points(
            (x, y), i, distance, marker_style, markersize=markersize, color=color, ax=ax
        )
        x += distance / 2
        y += distance

    if draw_contourn and N > 1:
        p1 = (0, 0)
        p2 = ((N - 1) * distance, 0)
        p3 = ((N - 1) * distance / 2, (N - 1) * distance)

        triangle_x = [p1[0], p2[0], p3[0], p1[0]]
        triangle_y = [p1[1], p2[1], p3[1], p1[1]]

        ax.plot(triangle_x, triangle_y, color="black", linewidth=1, zorder=0)

    if with_label:
        tN = ith(N)
        ax.text(
            (N - 1) * distance / 2,
            -distance / 2,
            f"$T_{{{N}}}={tN}$",
            ha="center",
            va="top",
            fontsize=12,
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
    """Draws a grid of triangular arrangements for a range of numbers.

    Args:
        start (int): The starting index of the triangular numbers.
        end (int): The ending index of the triangular numbers.
        distance (float, optional): Distance between consecutive points. Defaults to 0.5.
        marker_style (str, optional): Matplotlib marker style. Defaults to 'o'.
        markersize (int, optional): Size of the markers. Defaults to 10.
        color (str, optional): Color of the markers. Defaults to 'black'.
        with_label (bool, optional): Whether to add a label under each triangle. Defaults to False.
        return_tikz (bool, optional): Whether to return the TikZ code instead of showing the plot. Defaults to False.
        cols (int, optional): Number of columns in the grid. Defaults to 4.
        draw_grid (bool, optional): Whether to draw a grid around the subplots. Defaults to True.
        draw_contourn (bool, optional): Whether to draw a triangle connecting the outer points. Defaults to True.

    Returns:
        str | None: The TikZ code if return_tikz is True, otherwise None.

    Examples:
        >>> draw_range(1, 5, cols=3)
        # Displays a grid of the first 5 triangular numbers
    """
    num_plots = end - start + 1
    rows = (num_plots + cols - 1) // cols

    if draw_grid:
        plt.subplots_adjust(wspace=0, hspace=0)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    axes = np.atleast_1d(axes).flatten()

    max_N = end
    max_w = (max_N - 1) * distance
    max_h = (max_N - 1) * distance

    bottom_padding = 2.0 * distance
    top_padding = 1.0 * distance

    W_view = max_w + 2 * distance
    H_view = max_h + bottom_padding + top_padding

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

        cx = (N - 1) * distance / 2
        ax.set_xlim(cx - W_view / 2, cx + W_view / 2)
        ax.set_ylim(-bottom_padding, -bottom_padding + H_view)
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
