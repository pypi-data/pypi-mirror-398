# zengeld-canvas

**High-performance SVG chart rendering engine for financial data visualization**

[![Crates.io](https://img.shields.io/crates/v/zengeld-canvas.svg)](https://crates.io/crates/zengeld-canvas)
[![docs.rs](https://docs.rs/zengeld-canvas/badge.svg)](https://docs.rs/zengeld-canvas)

A platform-agnostic rendering library for financial charts. Built in Rust with zero runtime dependencies.

## Features

- **96 Drawing Primitives** - Fibonacci, Gann, Pitchforks, Elliott Waves, Patterns, Channels, and more
- **45+ Indicator Presets** - Pre-configured rendering styles for SMA, RSI, MACD, Bollinger, Ichimoku, etc.
- **12 Series Types** - Candlestick, HeikinAshi, Line, Area, Histogram, Baseline, and more
- **14 Multi-Chart Layouts** - Grid, split, and custom layouts for dashboards
- **Platform Agnostic** - `RenderContext` trait for any rendering backend
- **Zero Dependencies** - Only serde for serialization
- **Theme System** - 4 built-in presets (dark, light, high_contrast, cyberpunk) + runtime customization

## Installation

```bash
cargo add zengeld-canvas
```

## Quick Start

```rust
use zengeld_canvas::{Chart, Bar, UITheme};

// Create chart with builder API
let svg = Chart::new(800, 600)
    .bars(&bars)
    .candlesticks()
    .sma(20, "#2196F3")
    .rsi(14)
    .render_svg();

// With theme preset
let theme = UITheme::cyberpunk();
let svg = Chart::new(800, 600)
    .bars(&bars)
    .candlesticks()
    .background(theme.colors.chart.background)
    .colors(theme.colors.series.candle_up_body, theme.colors.series.candle_down_body)
    .render_svg();
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

Built-in presets: `dark`, `light`, `high_contrast`, `cyberpunk`

```rust
use zengeld_canvas::{UITheme, RuntimeTheme};

// Static themes (compile-time)
let dark = UITheme::dark();
let light = UITheme::light();

// Runtime themes (modifiable, JSON support)
let mut theme = RuntimeTheme::from_preset("dark").unwrap();
theme.colors.chart.background = "#1a0a2e".to_string();
let json = theme.to_json();
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
| Channels | 4 | Parallel, Regression, Disjoint, FlatTopBottom |
| Pitchforks | 4 | Standard, Schiff, Modified, Inside |
| And more... | 32 | Cycles, Projections, Volume, Arrows, Events |

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
