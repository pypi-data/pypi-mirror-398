"""Tests for the ColorGradient utility."""

from __future__ import annotations

import pytest
from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.console import Console

from funcy_bear.tools.gradient import (
    ColorGradient,
    DefaultColorConfig,
    DefaultColors,
    DefaultThresholds,
    GradientSegment,
    clamp_to_rgb,
    lerped_rgb,
)


class TestClampToRgb:
    """Tests for the clamp_to_rgb function."""

    def test_clamps_negative_to_zero(self) -> None:
        """Tests for the clamp_to_rgb function."""
        assert clamp_to_rgb(-10.0) == 0

    def test_clamps_over_255_to_255(self) -> None:
        """Tests for the clamp_to_rgb function."""
        assert clamp_to_rgb(300.0) == 255

    def test_returns_int_for_valid_range(self) -> None:
        """Tests for the clamp_to_rgb function."""
        assert clamp_to_rgb(128.5) == 128

    def test_zero_stays_zero(self) -> None:
        """Tests for the clamp_to_rgb function."""
        assert clamp_to_rgb(0.0) == 0

    def test_255_stays_255(self) -> None:
        """Tests for the clamp_to_rgb function."""
        assert clamp_to_rgb(255.0) == 255


class TestLerpedRgb:
    """Tests for the lerped_rgb function."""

    def test_t_zero_returns_start(self) -> None:
        """Tests for the lerped_rgb function."""
        assert lerped_rgb(0.0, 255.0, 0.0) == 0

    def test_t_one_returns_end(self) -> None:
        """Tests for the lerped_rgb function."""
        assert lerped_rgb(0.0, 255.0, 1.0) == 255

    def test_t_half_returns_midpoint(self) -> None:
        """Tests for the lerped_rgb function."""
        assert lerped_rgb(0.0, 255.0, 0.5) == 127

    def test_clamps_result_to_valid_rgb(self) -> None:
        """Tests for the lerped_rgb function."""
        assert lerped_rgb(250.0, 260.0, 1.0) == 255


class TestDefaultColors:
    """Tests for the DefaultColors dataclass."""

    def test_default_values(self) -> None:
        """Tests for the DefaultColors dataclass."""
        colors = DefaultColors()
        assert colors.start.get_truecolor() == ColorTriplet(255, 0, 0)
        assert colors.mid.get_truecolor() == ColorTriplet(255, 255, 0)
        assert colors.end.get_truecolor() == ColorTriplet(0, 255, 0)


class TestDefaultThresholds:
    """Tests for the DefaultThresholds dataclass."""

    def test_default_values(self) -> None:
        """Tests for the DefaultThresholds dataclass."""
        thresholds = DefaultThresholds()
        assert thresholds.start == 0.0
        assert thresholds.mid == 0.4
        assert thresholds.end == 1.0


class TestDefaultColorConfig:
    """Tests for the DefaultColorConfig dataclass."""

    def test_default_config_creation(self) -> None:
        """Tests for the DefaultColorConfig dataclass."""
        config = DefaultColorConfig()
        assert isinstance(config.colors, DefaultColors)
        assert isinstance(config.thresholds, DefaultThresholds)

    def test_update_colors(self) -> None:
        """Tests for the DefaultColorConfig dataclass."""
        config = DefaultColorConfig()
        blue: RichColor = RichColor.from_rgb(red=0, green=0, blue=255)
        config.update_colors(start=blue)
        assert config.colors.start.get_truecolor() == ColorTriplet(0, 0, 255)

    def test_update_colors_partial(self) -> None:
        """Tests for the DefaultColorConfig dataclass."""
        config = DefaultColorConfig()
        original_mid: RichColor = config.colors.mid
        config.update_colors(end=RichColor.from_rgb(red=100, green=100, blue=100))
        assert config.colors.mid == original_mid
        assert config.colors.end.get_truecolor() == ColorTriplet(100, 100, 100)

    def test_update_thresholds(self) -> None:
        """Tests for the DefaultColorConfig dataclass."""
        config = DefaultColorConfig()
        config.update_thresholds(mid=0.5)
        assert config.thresholds.mid == 0.5
        assert config.thresholds.start == 0.0
        assert config.thresholds.end == 1.0


class TestGradientSegment:
    """Tests for the GradientSegment NamedTuple."""

    def test_segment_creation(self) -> None:
        """Tests for the GradientSegment NamedTuple."""
        start = ColorTriplet(255, 0, 0)
        end = ColorTriplet(0, 255, 0)
        segment = GradientSegment(start, end)
        assert segment.start_color == start
        assert segment.end_color == end


class TestColorGradient:
    """Tests for the ColorGradient class."""

    def test_default_initialization(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        assert gradient.start_color == ColorTriplet(255, 0, 0)
        assert gradient.mid_color == ColorTriplet(255, 255, 0)
        assert gradient.end_color == ColorTriplet(0, 255, 0)
        assert gradient.reverse is False

    def test_initialization_with_reverse(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient(reverse=True)
        assert gradient.reverse is True

    def test_initialization_with_custom_config(self) -> None:
        """Tests for the ColorGradient class."""
        config = DefaultColorConfig()
        config.update_thresholds(mid=0.5)
        gradient = ColorGradient(config=config)
        assert gradient.mid_threshold == 0.5

    def test_invalid_thresholds_raises_error(self) -> None:
        """Tests for the ColorGradient class."""
        config = DefaultColorConfig()
        config.update_thresholds(start=0.5, mid=0.3, end=1.0)
        with pytest.raises(ValueError, match="thresholds must be strictly increasing"):
            ColorGradient(config=config)

    def test_flip_toggles_reverse(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        assert gradient.reverse is False
        gradient.flip()
        assert gradient.reverse is True
        gradient.flip()
        assert gradient.reverse is False

    def test_map_to_rgb_at_min_returns_start_color(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        assert gradient.map_to_rgb(0.0, 100.0, 0.0) == "rgb(255,0,0)"

    def test_map_to_rgb_at_max_returns_end_color(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        assert gradient.map_to_rgb(0.0, 100.0, 100.0) == "rgb(0,255,0)"

    def test_map_to_rgb_at_mid_threshold(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        assert gradient.map_to_rgb(0.0, 100.0, 40.0) == "rgb(255,255,0)"

    def test_map_to_rgb_reversed(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        assert gradient.map_to_rgb(0.0, 100.0, 0.0) == "rgb(255,0,0)"
        assert gradient.map_to_rgb(0.0, 100.0, 0.0, reverse=True) == "rgb(0,255,0)"

    def test_map_to_color_returns_color_triplet(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        result: ColorTriplet = gradient.map_to_color(0.0, 100.0, 0.0)
        assert isinstance(result, ColorTriplet)
        assert result == ColorTriplet(255, 0, 0)

    def test_map_to_color_at_max(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        result: ColorTriplet = gradient.map_to_color(0.0, 100.0, 100.0)
        assert result == ColorTriplet(0, 255, 0)

    def test_map_to_color_interpolates_correctly(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        result: ColorTriplet = gradient.map_to_color(0.0, 100.0, 20.0)
        assert result.red == 255
        assert 0 < result.green < 255
        assert result.blue == 0

    def test_map_to_color_with_reverse_override(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient(reverse=False)
        normal: ColorTriplet = gradient.map_to_color(0.0, 100.0, 0.0)
        reversed_via_param: ColorTriplet = gradient.map_to_color(0.0, 100.0, 0.0, reverse=True)
        assert normal != reversed_via_param

    def test_gradient_segment_selection_below_mid(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        segment: GradientSegment = gradient._get_color_segment(0.2)
        assert segment.start_color == gradient.start_color
        assert segment.end_color == gradient.mid_color

    def test_gradient_segment_selection_above_mid(self) -> None:
        """Tests for the ColorGradient class."""
        gradient = ColorGradient()
        segment: GradientSegment = gradient._get_color_segment(0.6)
        assert segment.start_color == gradient.mid_color
        assert segment.end_color == gradient.end_color

    def test_get_norm_position_normal(self) -> None:
        """Test _get_norm_position with reverse=False."""
        gradient = ColorGradient()
        result: float = gradient._get_norm_position(0.0, 100.0, 50.0, reverse=False)
        assert result == 0.5

    def test_get_norm_position_reversed(self) -> None:
        """Test _get_norm_position with reverse=True."""
        gradient = ColorGradient()
        result: float = gradient._get_norm_position(0.0, 100.0, 50.0, reverse=True)
        assert result == 0.5


@pytest.mark.visual
def test_gradients_visual() -> None:
    console = Console()

    health_gradient = ColorGradient()

    console.print("🏥 [bold]Health Meter Demonstration[/bold] 🏥\n")

    # Normal health: Red (low) -> Green (high)
    console.print("[bold green]Normal Health Levels (0% = Critical, 100% = Perfect):[/bold green]")
    for health in range(0, 101, 10):
        color: ColorTriplet = health_gradient.map_to_color(0, 100, health)
        health_bar: str = "█" * (health // 5)
        console.print(f"HP: {health:3d}/100 {health_bar:<20}", style=color.rgb)

    health_scenarios = [
        (5, "💀 Nearly Dead"),
        (25, "🩸 Critical Condition"),
        (50, "⚠️  Wounded"),
        (75, "😐 Recovering"),
        (95, "💪 Almost Full Health"),
        (100, "✨ Perfect Health"),
    ]

    console.print("[bold green]Health Status Examples:[/bold green]")
    for hp, status in health_scenarios:
        color: ColorTriplet = health_gradient.map_to_color(0, 100, hp)
        console.print(f"{status}: {hp}/100 HP", style=color.rgb)

    console.print("\n" + "=" * 50 + "\n")

    # Reversed: Infection/Damage meter (Green = good, Red = bad)
    console.print("[bold red]Infection Level (0% = Healthy, 100% = Critical):[/bold red]")
    health_gradient.reverse = True
    for infection in range(0, 101, 10):
        color: ColorTriplet = health_gradient.map_to_color(0, 100, infection)
        infection_bar: str = "█" * (infection // 5)
        status: str = "🦠" if infection > 70 else "⚠️" if infection > 30 else "✅"
        console.print(f"Infection: {infection:3d}% {infection_bar:<20} {status}", style=color.rgb)

    infected_scenarios: list[tuple[int, str]] = [
        (5, "✅ Healthy"),
        (25, "⚠️ Mild Infection"),
        (50, "🦠 Moderate Infection"),
        (75, "🦠 Severe Infection"),
        (100, "💀 Critical Condition"),
    ]

    console.print("[bold red]Infection Status Examples:[/bold red]")
    for ip, status in infected_scenarios:
        color: ColorTriplet = health_gradient.map_to_color(0, 100, ip)
        console.print(f"{status}: {ip}/100 Infection", style=color.rgb)
