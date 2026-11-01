"""Educational visualization of the legacy Orion star-motion dataset.

The original project's x/y coordinates and proper motions have not yet been
matched to a documented astronomical catalogue or reference frame. This is
an illustrative linear projected-coordinate model, NOT precise astrometry.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt

# Degrees in one milliarcsecond. Input proper motions are in mas/yr.
DEGREES_PER_MAS = 1.0 / 3_600_000.0
DEFAULT_YEARS = (-100_000, 0, 100_000, 500_000)
DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "orion_legacy.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "figures" / "orion_evolution.png"


@dataclass(frozen=True)
class Star:
    label: str
    x_deg: float
    y_deg: float
    temperature_k: float
    apparent_magnitude: float
    pm_x_mas_per_year: float
    pm_y_mas_per_year: float


def load_stars(path: Path) -> list[Star]:
    """Read the original project's nine data points from a CSV file."""
    stars: list[Star] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "star_id", "x_deg", "y_deg", "temperature_k",
            "apparent_magnitude", "pm_x_mas_per_year", "pm_y_mas_per_year"
        }
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")
        for index, row in enumerate(reader, start=2):
            try:
                star = Star(
                    label=row["star_id"],
                    x_deg=float(row["x_deg"]),
                    y_deg=float(row["y_deg"]),
                    temperature_k=float(row["temperature_k"]),
                    apparent_magnitude=float(row["apparent_magnitude"]),
                    pm_x_mas_per_year=float(row["pm_x_mas_per_year"]),
                    pm_y_mas_per_year=float(row["pm_y_mas_per_year"]),
                )
            except (TypeError, ValueError, KeyError) as exc:
                raise ValueError(f"Invalid data on CSV line {index}: {exc}") from exc
            if star.temperature_k <= 0:
                raise ValueError(f"Temperature must be positive on CSV line {index}")
            stars.append(star)
    if not stars:
        raise ValueError("The data file contains no stars")
    return stars


def propagate(star: Star, years: float) -> tuple[float, float]:
    """Displacement: delta(deg) = mu(mas/yr) * years / 3.6e6.

    This simple projected-coordinate model is not suitable for precision
    RA/Dec propagation, which requires a reference frame, epoch, and
    additional astrometric parameters.
    """
    return (
        star.x_deg + star.pm_x_mas_per_year * years * DEGREES_PER_MAS,
        star.y_deg + star.pm_y_mas_per_year * years * DEGREES_PER_MAS,
    )


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def illustrative_color(temperature_k: float) -> str:
    """Illustrative warm-to-cool palette (NOT calibrated blackbody RGB)."""
    anchors = [
        (3000.0, "#ffaf78"),
        (4500.0, "#ffdec1"),
        (6500.0, "#fffaf2"),
        (12000.0, "#dbe7ff"),
        (30000.0, "#a3c8ff"),
        (40000.0, "#91baff"),
    ]
    t = max(anchors[0][0], min(float(temperature_k), anchors[-1][0]))
    for (t0, c0), (t1, c1) in zip(anchors[:-1], anchors[1:]):
        if t <= t1:
            fraction = (t - t0) / (t1 - t0)
            rgb0, rgb1 = _hex_to_rgb(c0), _hex_to_rgb(c1)
            channels = tuple(round(a + fraction * (b - a)) for a, b in zip(rgb0, rgb1))
            return "#{:02x}{:02x}{:02x}".format(*channels)
    return anchors[-1][1]


def marker_area(apparent_magnitude: float) -> float:
    """Display area in points squared, not a calibrated flux model."""
    return max(8.0, min(260.0, 80.0 * 10 ** (-0.28 * (apparent_magnitude - 1.5))))


def make_figure(
    stars: Sequence[Star],
    years: Sequence[int],
    output: Path,
    show_paths: bool = True,
) -> None:
    if not years:
        raise ValueError("Please provide at least one time offset")
    if not stars:
        raise ValueError("Please provide at least one star")

    # The same coordinate window is used in each panel for fair comparison.
    positions = [propagate(star, year) for star in stars for year in years]
    positions.extend((star.x_deg, star.y_deg) for star in stars)
    xs, ys = zip(*positions)
    padding = 2.0
    xlim = (min(xs) - padding, max(xs) + padding)
    ylim = (min(ys) - padding, max(ys) + padding)

    ncols = len(years)
    with plt.style.context("dark_background"):
        fig, axes = plt.subplots(1, ncols, figsize=(5.2 * ncols, 6.4), sharex=True, sharey=True)
        if ncols == 1:
            axes = [axes]
        fig.patch.set_facecolor("#0c1427")
        for ax, year in zip(axes, years):
            ax.set_facecolor("#0c1427")
            for star in stars:
                new_x, new_y = propagate(star, year)
                if show_paths and year != 0:
                    ax.plot([star.x_deg, new_x], [star.y_deg, new_y],
                            color="#86a6c8", alpha=0.45, linewidth=0.9, zorder=1)
                    ax.scatter(star.x_deg, star.y_deg, s=9, facecolors="none",
                               edgecolors="#7c8ca0", linewidths=0.65, zorder=2)
                ax.scatter(new_x, new_y, s=marker_area(star.apparent_magnitude),
                           color=illustrative_color(star.temperature_k),
                           marker="*", edgecolors="none", zorder=3)
            prefix = "+" if year > 0 else ""
            ax.set_title(f"{prefix}{year:,} years", fontsize=13, weight="bold", pad=15)
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("Legacy X coordinate (degrees)", fontsize=9)
            ax.grid(color="#657b9e", alpha=0.16, linewidth=0.7)
            ax.tick_params(colors="#a8b6d0", labelsize=8)
        axes[0].set_ylabel("Legacy Y coordinate (degrees)", fontsize=9)
        fig.suptitle("Orion: Illustrative Stellar Proper Motion", fontsize=19,
                     weight="bold", y=0.975)
        fig.text(0.5, 0.04,
                 "Legacy classroom dataset · linear proper motion · not a validated astronomical forecast",
                 ha="center", fontsize=9, color="#c4cfdf")
        fig.subplots_adjust(left=0.05, right=0.99, bottom=0.17, top=0.85, wspace=0.10)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=165, facecolor=fig.get_facecolor())
        plt.close(fig)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Input CSV path")
    parser.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS),
                        help="Year offsets relative to the unknown original epoch")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output PNG path")
    parser.add_argument("--no-paths", action="store_true", help="Hide displacement segments")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    stars = load_stars(args.data)
    make_figure(stars, args.years, args.output, show_paths=not args.no_paths)
    print(f"Created {args.output} using {len(stars)} stars")


if __name__ == "__main__":
    main()
