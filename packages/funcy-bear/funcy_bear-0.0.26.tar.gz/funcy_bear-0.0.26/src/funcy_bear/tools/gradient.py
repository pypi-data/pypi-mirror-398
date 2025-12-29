"""A color gradient utility for generating RGB colors based on thresholds."""

from dataclasses import dataclass, field
from typing import NamedTuple

from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet

from funcy_bear.ops.math import clamp, inv_lerp, lerp

RED: RichColor = RichColor.from_rgb(red=255, green=0, blue=0)
YELLOW: RichColor = RichColor.from_rgb(red=255, green=255, blue=0)
GREEN: RichColor = RichColor.from_rgb(red=0, green=255, blue=0)


@dataclass(slots=True)
class DefaultColors:
    """The default colors for the gradient."""

    start: RichColor = RED  # Default Threshold: 0.0
    mid: RichColor = YELLOW  # Default Threshold: 0.7
    end: RichColor = GREEN  # Default Threshold: 1.0


@dataclass(slots=True)
class DefaultThresholds:
    """The default thresholds for the gradient."""

    start: float = 0.0  # Default Color: RED
    mid: float = 0.4  # Default Color: YELLOW
    end: float = 1.0  # Default Color: GREEN


@dataclass(slots=True)
class DefaultColorConfig:
    """Configuration for the default color gradient."""

    colors: DefaultColors = field(default_factory=DefaultColors)
    thresholds: DefaultThresholds = field(default_factory=DefaultThresholds)

    def update_colors(
        self,
        start: RichColor | None = None,
        mid: RichColor | None = None,
        end: RichColor | None = None,
    ) -> None:
        """Update the colors in the configuration."""
        if start is not None:
            self.colors.start = start
        if mid is not None:
            self.colors.mid = mid
        if end is not None:
            self.colors.end = end

    def update_thresholds(
        self,
        start: float | None = None,
        mid: float | None = None,
        end: float | None = None,
    ) -> None:
        """Update the thresholds in the configuration."""
        if start is not None:
            self.thresholds.start = start
        if mid is not None:
            self.thresholds.mid = mid
        if end is not None:
            self.thresholds.end = end


class GradientSegment(NamedTuple):
    """Source and destination colors for gradient interpolation."""

    start_color: ColorTriplet
    end_color: ColorTriplet


RGB_OUTPUT = "rgb({},{},{})"


def clamp_to_rgb(v: float) -> int:
    """Convert a float to an int, clamping to 0-255."""
    return int(clamp(v, 0.0, 255.0))


def lerped_rgb(a: float, b: float, t: float) -> int:
    """Linearly interpolate between two RGB values."""
    return clamp_to_rgb(lerp(a, b, t))


class ColorGradient:
    """Simple 3-color gradient interpolator.

    Maps values within a range to colors along a gradient (default: red -> yellow -> green).
    Useful for visualizing performance metrics, progress bars, or any value-to-color mapping.

    Args:
        config (DefaultColorConfig | None): Configuration for colors and thresholds.
        reverse (bool): If True, reverses the gradient direction.

    Example:
        Basic usage for colorizing benchmark results::

            gradient = ColorGradient(reverse=True)

            # Map write times: fastest (min) -> green, slowest (max) -> red
            write_color = gradient.map_to_rgb(
                fastest_write, slowest_write, result.write_per_run_ms
            )

            # Map read times: same pattern
            read_color = gradient.map_to_rgb(
                fastest_read, slowest_read, result.read_per_run_ms
            )

            # Map sizes: smallest -> green, largest -> red
            size_color = gradient.map_to_rgb(smallest_size, largest_size, result.size_bytes)

        Using with Rich for styled output::

            from rich.console import Console

            console = Console()
            color = gradient.map_to_rgb(0, 100, score)
            console.print(f"[{color}]Score: {score}[/{color}]")

        Custom colors and thresholds::

            config = DefaultColorConfig()
            config.update_colors(
                start=RichColor.from_rgb(0, 0, 255),  # Blue
                mid=RichColor.from_rgb(255, 255, 255),  # White
                end=RichColor.from_rgb(255, 0, 0),  # Red
            )
            config.update_thresholds(mid=0.5)
            gradient = ColorGradient(config=config)
    """

    def __init__(self, config: DefaultColorConfig | None = None, reverse: bool = False) -> None:
        """Initialize the ColorGradient with a configuration and optional reverse flag."""
        self.config: DefaultColorConfig = config or DefaultColorConfig()

        self.start_color: ColorTriplet = self.config.colors.start.get_truecolor()
        self.mid_color: ColorTriplet = self.config.colors.mid.get_truecolor()
        self.end_color: ColorTriplet = self.config.colors.end.get_truecolor()

        self.start_threshold: float = self.config.thresholds.start
        self.mid_threshold: float = self.config.thresholds.mid
        self.end_threshold: float = self.config.thresholds.end

        self.reverse: bool = reverse

        if not (0.0 <= self.start_threshold < self.mid_threshold < self.end_threshold <= 1.0):
            raise ValueError("thresholds must be strictly increasing and between 0 and 1.")

    def flip(self) -> None:
        """Toggle the reverse flag."""
        self.reverse = not self.reverse

    def _get_norm_position(self, _min: float, _max: float, v: float, reverse: bool) -> float:
        """Get the normalized value (a value between [0, 1]) for the gradient.

        Returns:
            float: Normalized value.
        """
        return inv_lerp(_min, _max, v) if not reverse else 1.0 - inv_lerp(_min, _max, v)

    def _get_color_segment(self, norm_position: float) -> GradientSegment:
        """Get the source and destination colors for interpolation.

        Returns:
            GradientSegment: Source and destination colors.
        """
        if norm_position <= self.mid_threshold:
            return GradientSegment(self.start_color, self.mid_color)
        return GradientSegment(self.mid_color, self.end_color)

    def _get_segment_position(self, norm_position: float) -> float:
        """Get the segment position for interpolation.

        Returns:
            float: Segment position.
        """
        if norm_position <= self.mid_threshold:
            return inv_lerp(self.start_threshold, self.mid_threshold, norm_position)
        return inv_lerp(self.mid_threshold, self.end_threshold, norm_position)

    def map_to_rgb(self, _min: float, _max: float, v: float, reverse: bool | None = None) -> str:
        """Get rgb color for a value by linear interpolation.

        Args:
            _min (float): Minimum of input range.
            _max (float): Maximum of input range.
            v (float): Value to map.
            reverse (bool | None): If True, reverses the gradient direction.

        Returns:
            str: RGB color string.
        """
        reverse = reverse if reverse is not None else self.reverse
        norm_position: float = self._get_norm_position(_min, _max, v, reverse)
        color_segment: GradientSegment = self._get_color_segment(norm_position)
        segment_position: float = self._get_segment_position(norm_position)
        return RGB_OUTPUT.format(
            lerped_rgb(color_segment.start_color.red, color_segment.end_color.red, segment_position),
            lerped_rgb(color_segment.start_color.green, color_segment.end_color.green, segment_position),
            lerped_rgb(color_segment.start_color.blue, color_segment.end_color.blue, segment_position),
        )

    def map_to_color(self, _min: float, _max: float, v: float, reverse: bool | None = None) -> ColorTriplet:
        """Get rgb color for a value by linear interpolation.

        Args:
            _min (float): Minimum of input range.
            _max (float): Maximum of input range.
            v (float): Value to map.
            reverse (bool | None): If True, reverses the gradient direction.

        Returns:
            ColorTriplet: RGB color triplet.
        """
        reverse = reverse if reverse is not None else self.reverse
        norm_position: float = self._get_norm_position(_min, _max, v, reverse)
        color_segment: GradientSegment = self._get_color_segment(norm_position)
        segment_position: float = self._get_segment_position(norm_position)
        return ColorTriplet(
            lerped_rgb(color_segment.start_color.red, color_segment.end_color.red, segment_position),
            lerped_rgb(color_segment.start_color.green, color_segment.end_color.green, segment_position),
            lerped_rgb(color_segment.start_color.blue, color_segment.end_color.blue, segment_position),
        )
