#!/usr/bin/env python3
"""
zengeld-canvas Python Test/Example

Demonstrates the Python API for chart rendering with various themes and primitives.
This script mirrors the Rust chart_gallery example to verify Python bindings work correctly.

Usage:
    1. Build the package: maturin develop
    2. Run this script: python test_chart.py

Output:
    - chart_output_py/*.svg files
"""

import os
import math
from zengeld_canvas import (
    version,
    Bar,
    Chart,
    UITheme,
    RuntimeTheme,
    Viewport,
)


def generate_sample_bars(count: int) -> list[Bar]:
    """Generate sample OHLCV bars with realistic price movement."""
    bars = []
    price = 100.0
    base_volume = 1_000_000.0
    start_time = 1700000000

    for i in range(count):
        # Random walk with trend
        trend = math.sin((i / count) * math.pi * 2.0) * 10.0
        noise = pseudo_random(i) * 4.0 - 2.0
        change = trend * 0.1 + noise

        price += change
        price = max(price, 50.0)

        volatility = 1.0 + pseudo_random(i + 1000) * 2.0
        high = price + volatility
        low = price - volatility

        if pseudo_random(i + 2000) > 0.5:
            open_ = low + pseudo_random(i + 3000) * (high - low)
        else:
            open_ = high - pseudo_random(i + 4000) * (high - low)

        if pseudo_random(i + 5000) > 0.5:
            close = low + pseudo_random(i + 6000) * (high - low)
        else:
            close = high - pseudo_random(i + 7000) * (high - low)

        volume = base_volume * (0.5 + pseudo_random(i + 8000) * 1.5)

        bars.append(Bar(
            timestamp=start_time + (i * 86400),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
        ))

    return bars


def pseudo_random(seed: int) -> float:
    """Simple pseudo-random number generator (deterministic for reproducibility)."""
    x = (seed * 1103515245 + 12345) & 0xFFFFFFFFFFFFFFFF
    x = (x * 1103515245 + 12345) & 0xFFFFFFFFFFFFFFFF
    return ((x >> 16) & 0x7fff) / 32767.0


def save_svg(svg: str, path: str):
    """Save SVG string to file."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"  -> Saved: {path}")


def main():
    print(f"zengeld-canvas Python Test (v{version()})\n")

    # Create output directory
    output_dir = "chart_output_py"
    os.makedirs(output_dir, exist_ok=True)

    # Generate sample data
    bars = generate_sample_bars(200)
    print(f"Generated {len(bars)} sample bars\n")

    # =========================================================================
    # Theme Showcase
    # =========================================================================

    # 01. Dark Theme (default)
    print("01. Dark Theme Chart")
    chart = Chart(800, 400)
    chart.bars(bars)
    chart.candlesticks()
    chart.dark_theme()
    chart.sma(20, "#2196F3")
    chart.ema(50, "#FF9800")
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/01_dark_theme.svg")

    # 02. Light Theme
    print("02. Light Theme Chart")
    light = UITheme.light()
    chart = Chart(800, 400)
    chart.bars(bars)
    chart.candlesticks()
    chart.background(light.background)
    chart.colors(light.candle_up_body, light.candle_down_body)
    chart.sma(20, "#2196F3")
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/02_light_theme.svg")

    # 03. High Contrast Theme
    print("03. High Contrast Theme Chart")
    contrast = UITheme.high_contrast()
    chart = Chart(800, 400)
    chart.bars(bars)
    chart.candlesticks()
    chart.background(contrast.background)
    chart.colors(contrast.candle_up_body, contrast.candle_down_body)
    chart.sma(20, contrast.accent)
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/03_high_contrast.svg")

    # 04. Cyberpunk Theme
    print("04. Cyberpunk Theme Chart")
    cyber = UITheme.cyberpunk()
    chart = Chart(800, 400)
    chart.bars(bars)
    chart.candlesticks()
    chart.background(cyber.background)
    chart.colors(cyber.candle_up_body, cyber.candle_down_body)
    chart.sma(20, cyber.accent)
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/04_cyberpunk.svg")

    # 05. Runtime Theme (custom modified)
    print("05. Runtime Theme (Custom)")
    runtime = RuntimeTheme.from_preset("dark")
    runtime.background = "#1a0a2e"  # Deep purple
    runtime.candle_up_body = "#00ffff"  # Cyan
    runtime.candle_down_body = "#ff00ff"  # Magenta
    chart = Chart(800, 400)
    chart.bars(bars)
    chart.candlesticks()
    chart.background(runtime.background)
    chart.colors(runtime.candle_up_body, runtime.candle_down_body)
    chart.sma(20, "#ffff00")
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/05_runtime_custom.svg")

    # =========================================================================
    # Indicators
    # =========================================================================

    # 06. Chart with MACD
    print("06. Chart with MACD")
    chart = Chart(800, 500)
    chart.bars(bars)
    chart.candlesticks()
    chart.ema(12, "#2196F3")
    chart.ema(26, "#FF9800")
    chart.macd(12, 26, 9)
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/06_with_macd.svg")

    # 07. Chart with RSI
    print("07. Chart with RSI")
    chart = Chart(800, 500)
    chart.bars(bars)
    chart.candlesticks()
    chart.sma(20, "#2196F3")
    chart.rsi(14)
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/07_with_rsi.svg")

    # 08. Chart with Bollinger Bands
    print("08. Chart with Bollinger Bands")
    chart = Chart(800, 400)
    chart.bars(bars)
    chart.candlesticks()
    chart.bollinger(20, 2.0)
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/08_bollinger.svg")

    # =========================================================================
    # Primitives
    # =========================================================================

    # 09. Lines and Shapes
    print("09. Lines and Shapes")
    chart = Chart(1000, 500)
    chart.bars(bars)
    chart.candlesticks()
    chart.trend_line((20.0, bars[20].low), (80.0, bars[80].low))
    chart.horizontal_line(bars[50].high + 5.0)
    chart.vertical_line(100.0)
    chart.rectangle((30.0, bars[30].high), (60.0, bars[45].low))
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/09_lines_shapes.svg")

    # 10. Fibonacci
    print("10. Fibonacci Retracement")
    chart = Chart(1000, 500)
    chart.bars(bars)
    chart.candlesticks()
    chart.fib_retracement((20.0, bars[20].low), (80.0, bars[50].high))
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/10_fibonacci.svg")

    # =========================================================================
    # Signals
    # =========================================================================

    # 11. Trading Signals
    print("11. Trading Signals")
    chart = Chart(1000, 500)
    chart.bars(bars)
    chart.candlesticks()
    chart.sma(10, "#26a69a")
    chart.sma(30, "#ef5350")
    chart.buy_signal(25, bars[25].low - 2.0, "Long")
    chart.sell_signal(60, bars[60].high + 2.0, "Short")
    chart.take_profit_signal(45, bars[45].high + 1.0, "TP1")
    chart.stop_loss_signal(95, bars[95].high + 3.0, "SL")
    svg = chart.render_svg()
    save_svg(svg, f"{output_dir}/11_signals.svg")

    # =========================================================================
    # API Verification
    # =========================================================================

    print("\n--- API Verification ---")

    # Test Viewport
    vp = Viewport(1200.0, 800.0)
    print(f"Viewport: {vp.chart_width}x{vp.chart_height}, bar_width={vp.bar_width:.2f}")

    # Test UITheme presets
    print(f"\nUITheme presets:")
    for name, theme_fn in [("dark", UITheme.dark), ("light", UITheme.light),
                           ("high_contrast", UITheme.high_contrast), ("cyberpunk", UITheme.cyberpunk)]:
        theme = theme_fn()
        print(f"  - {theme.name}: bg={theme.background}, up={theme.candle_up_body}")

    # Test RuntimeTheme
    print(f"\nRuntimeTheme presets: {RuntimeTheme.presets()}")

    # Test JSON serialization
    rt = RuntimeTheme.dark()
    json_str = rt.to_json()
    print(f"\nRuntimeTheme JSON length: {len(json_str)} chars")

    # Test JSON roundtrip
    rt2 = RuntimeTheme.from_json(json_str)
    if rt2:
        print(f"JSON roundtrip: OK (name={rt2.name})")
    else:
        print("JSON roundtrip: FAILED")

    # Test Bar
    bar = Bar(1700000000, 100.0, 105.0, 98.0, 103.0, 1000000.0)
    print(f"\nBar: {bar}")
    print(f"  is_bullish: {bar.is_bullish()}")

    print(f"\n[OK] All charts generated in '{output_dir}/'\n")
    print("Generated files:")
    for i in range(1, 12):
        prefix = "0" if i < 10 else ""
        print(f"  - {prefix}{i}_*.svg")


if __name__ == "__main__":
    main()
