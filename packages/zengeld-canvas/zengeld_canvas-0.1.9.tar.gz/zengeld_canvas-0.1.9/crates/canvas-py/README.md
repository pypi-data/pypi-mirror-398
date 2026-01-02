# zengeld-canvas

**High-performance SVG chart rendering engine for financial data visualization**

[![PyPI](https://img.shields.io/pypi/v/zengeld-canvas.svg)](https://pypi.org/project/zengeld-canvas/)
[![Python](https://img.shields.io/pypi/pyversions/zengeld-canvas.svg)](https://pypi.org/project/zengeld-canvas/)

Python bindings for the zengeld-canvas chart rendering engine. Built in Rust with zero runtime dependencies.

## Features

- **96 Drawing Primitives** - Fibonacci, Gann, Pitchforks, Elliott Waves, Patterns, Channels, and more
- **45+ Indicator Presets** - Pre-configured rendering styles for SMA, RSI, MACD, Bollinger, Ichimoku, etc.
- **12 Series Types** - Candlestick, HeikinAshi, Line, Area, Histogram, Baseline, and more
- **14 Multi-Chart Layouts** - Grid, split, and custom layouts for dashboards
- **High Performance** - Native Rust speed via PyO3
- **Theme System** - 4 built-in presets (dark, light, high_contrast, cyberpunk) + runtime customization

## Installation

```bash
pip install zengeld-canvas
```

## Quick Start

```python
from zengeld_canvas import Chart, Bar, UITheme, RuntimeTheme

# Build chart
chart = Chart(800, 600)
chart.bars(bars)
chart.candlesticks()
chart.sma(20, "#2196F3")
svg = chart.render_svg()

# With theme preset
theme = UITheme.cyberpunk()
chart = Chart(800, 600)
chart.bars(bars)
chart.candlesticks()
chart.background(theme.background)
chart.colors(theme.candle_up_body, theme.candle_down_body)
svg = chart.render_svg()

# Runtime theme (modifiable)
runtime = RuntimeTheme.from_preset("dark")
runtime.background = "#1a0a2e"  # Custom background
runtime.candle_up_body = "#00ffff"  # Cyan
```

## Examples

<table>
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/zengeld/zengeld-canvas/main/crates/canvas/chart_output/09_light_theme.svg" width="400"/><br/><b>Light Theme</b></td>
    <td align="center"><img src="https://raw.githubusercontent.com/zengeld/zengeld-canvas/main/crates/canvas/chart_output/09b_high_contrast_theme.svg" width="400"/><br/><b>High Contrast Theme</b></td>
  </tr>
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/zengeld/zengeld-canvas/main/crates/canvas/chart_output/09c_cyberpunk_theme.svg" width="400"/><br/><b>Cyberpunk Theme</b></td>
    <td align="center"><img src="https://raw.githubusercontent.com/zengeld/zengeld-canvas/main/crates/canvas/chart_output/09d_runtime_theme.svg" width="400"/><br/><b>Runtime Custom Theme</b></td>
  </tr>
</table>

## Theme System

Built-in presets: `dark()`, `light()`, `high_contrast()`, `cyberpunk()`

```python
from zengeld_canvas import UITheme, RuntimeTheme

# Static themes
dark = UITheme.dark()
light = UITheme.light()

# Runtime themes (modifiable, JSON support)
runtime = RuntimeTheme.from_preset("dark")
runtime.background = "#1a0a2e"
json_str = runtime.to_json()

# Available presets
presets = RuntimeTheme.presets()  # ["dark", "light", "high_contrast", "cyberpunk"]
```

## Drawing Primitives

| Category | Count | Examples |
|----------|-------|----------|
| Fibonacci | 11 | Retracement, Fan, Arcs, Circles, Channel, Spiral |
| Lines | 9 | TrendLine, HorizontalLine, Ray, ExtendedLine |
| Annotations | 11 | Text, Callout, PriceLabel, Flag, Table |
| Shapes | 10 | Rectangle, Circle, Ellipse, Triangle, Path |
| Elliott Waves | 5 | Impulse, Correction, Triangle, Combo |
| Patterns | 6 | XABCD, HeadShoulders, Cypher, ThreeDrives |
| Gann | 4 | Fan, Box, Square, SquareFixed |
| And more... | 40 | Channels, Pitchforks, Cycles, Projections |

## License

MIT OR Apache-2.0

## Support the Project

If you find this library useful, consider supporting development:

| Currency | Network | Address |
|----------|---------|---------|
| USDT | TRC20 | `TNxMKsvVLYViQ5X5sgCYmkzH4qjhhh5U7X` |
| USDC | Arbitrum | `0xEF3B94Fe845E21371b4C4C5F2032E1f23A13Aa6e` |
| ETH | Ethereum | `0xEF3B94Fe845E21371b4C4C5F2032E1f23A13Aa6e` |
| BTC | Bitcoin | `bc1qjgzthxja8umt5tvrp5tfcf9zeepmhn0f6mnt40` |
| SOL | Solana | `DZJjmH8Cs5wEafz5Ua86wBBkurSA4xdWXa3LWnBUR94c` |

---

<p align="center">
  <a href="https://zen-geldmaschine.net/">
    <img src="https://raw.githubusercontent.com/zengeld/zengeld-canvas/main/assets/author.svg" alt="zengeld" />
  </a>
</p>
