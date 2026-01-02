# zengeld-canvas Python API Documentation

High-performance SVG chart rendering engine for financial data visualization.

## Installation

```bash
pip install zengeld-canvas
```

## Quick Start

```python
from zengeld_canvas import Chart, Bar

# Create sample OHLCV data
bars = [
    Bar(1704067200 + i * 60, 100.0 + i * 0.5, 102.0 + i * 0.5,
        98.0 + i * 0.5, 101.0 + i * 0.5, 1000.0 * (i + 1))
    for i in range(100)
]

# Create chart
chart = Chart(800, 600)
chart.bars(bars)
chart.candlesticks()
chart.sma(20, "#2196F3")
chart.rsi(14)

# Render to SVG
svg = chart.render_svg()

# Save to file
with open("chart.svg", "w") as f:
    f.write(svg)
```

## API Reference

### Bar

OHLCV bar representing one time period of price data.

```python
bar = Bar(timestamp, open, high, low, close, volume=0.0)
```

**Parameters:**
- `timestamp` (int): Unix timestamp in seconds
- `open` (float): Opening price
- `high` (float): Highest price
- `low` (float): Lowest price
- `close` (float): Closing price
- `volume` (float, optional): Trading volume

**Methods:**
- `is_bullish() -> bool`: Returns True if close > open

---

### Chart

High-level chart builder for creating financial charts.

```python
chart = Chart(width, height)
```

#### Configuration

```python
chart.dpr(2.0)              # Set device pixel ratio
chart.bars(bars)            # Set OHLCV data
```

#### Series Types (3 types)

```python
chart.candlesticks()        # Candlestick chart (default)
chart.line()                # Line chart
chart.area()                # Area chart
```

#### Theme & Styling

```python
chart.colors("#00FF00", "#FF0000")  # Set up/down colors
chart.background("#1a1a2e")         # Set background
chart.grid(False)                   # Hide grid
chart.dark_theme()                  # Dark theme preset
chart.light_theme()                 # Light theme preset
```

---

## Indicators (45+ types)

### Moving Averages (10 types)

```python
chart.sma(20, "#2196F3")       # Simple Moving Average
chart.ema(12, "#E91E63")       # Exponential Moving Average
chart.wma(20, "#FF9800")       # Weighted Moving Average
chart.hma(14, "#9C27B0")       # Hull Moving Average
chart.dema(20, "#00BCD4")      # Double Exponential MA
chart.tema(20, "#4CAF50")      # Triple Exponential MA
chart.kama(10, "#FF5722")      # Kaufman Adaptive MA
chart.trima(20, "#3F51B5")     # Triangular MA
chart.zlema(20, "#795548")     # Zero Lag EMA
chart.mcginley(14, "#607D8B")  # McGinley Dynamic
```

### Band Indicators (5 types)

```python
chart.bollinger(20, 2.0)       # Bollinger Bands
chart.bollinger_filled(20)     # Bollinger Bands (filled)
chart.keltner(20)              # Keltner Channel
chart.donchian(20)             # Donchian Channel
chart.atr_bands(14, 2.0)       # ATR Bands
```

### Oscillators (17 types)

```python
chart.rsi(14)                  # Relative Strength Index
chart.macd(12, 26, 9)          # MACD
chart.macd_default()           # MACD (12, 26, 9)
chart.stochastic(14, 3)        # Stochastic Oscillator
chart.stoch_rsi(14)            # Stochastic RSI
chart.cci(20)                  # Commodity Channel Index
chart.williams_r(14)           # Williams %R
chart.momentum(10)             # Momentum
chart.roc(12)                  # Rate of Change
chart.tsi(25, 13)              # True Strength Index
chart.ultimate_oscillator()    # Ultimate Oscillator
chart.awesome_oscillator()     # Awesome Oscillator
chart.accelerator_oscillator() # Accelerator Oscillator
chart.cmo(14)                  # Chande Momentum Oscillator
chart.dpo(20)                  # Detrended Price Oscillator
chart.kst()                    # Know Sure Thing
chart.rvi(10)                  # Relative Vigor Index
```

### Volatility Indicators (6 types)

```python
chart.atr(14)                  # Average True Range
chart.stddev(20)               # Standard Deviation
chart.historical_volatility(20) # Historical Volatility
chart.choppiness(14)           # Choppiness Index
chart.mass_index()             # Mass Index
chart.ulcer_index(14)          # Ulcer Index
```

### Trend Indicators (12 types)

```python
chart.adx(14)                  # Average Directional Index
chart.aroon(25)                # Aroon
chart.aroon_oscillator(25)     # Aroon Oscillator
chart.vortex(14)               # Vortex Indicator
chart.linear_regression(14, "#2196F3")  # Linear Regression
chart.linear_regression_slope(14)       # Linear Regression Slope
chart.zigzag(5.0)              # ZigZag
chart.trix(15)                 # TRIX
chart.chande_kroll_stop()      # Chande Kroll Stop
chart.psar()                   # Parabolic SAR
chart.supertrend(10, 3.0)      # Supertrend
chart.ichimoku()               # Ichimoku Cloud
```

### Volume Indicators (12 types)

```python
chart.volume()                 # Volume histogram
chart.obv()                    # On Balance Volume
chart.ad_line()                # Accumulation/Distribution
chart.cmf(20)                  # Chaikin Money Flow
chart.chaikin_oscillator()     # Chaikin Oscillator
chart.vpt()                    # Volume Price Trend
chart.force_index(13)          # Force Index
chart.eom(14)                  # Ease of Movement
chart.nvi()                    # Negative Volume Index
chart.pvi()                    # Positive Volume Index
chart.mfi(14)                  # Money Flow Index
chart.vwap()                   # VWAP
```

### Specialized Indicators (12 types)

```python
chart.elder_ray(13)            # Elder Ray
chart.balance_of_power()       # Balance of Power
chart.connors_rsi()            # Connors RSI
chart.coppock_curve()          # Coppock Curve
chart.fisher_transform(10)     # Fisher Transform
chart.smi_ergodic()            # SMI Ergodic
chart.schaff_trend_cycle()     # Schaff Trend Cycle
chart.pgo(14)                  # Pretty Good Oscillator
chart.qstick(14)               # QStick
chart.pivot_points()           # Pivot Points
chart.envelopes(20, 2.5)       # Envelopes
chart.price_channel(20)        # Price Channel
```

### Custom Overlay

```python
chart.overlay("Custom", values, "#FF5722")
```

---

## Signals (7 types)

```python
chart.buy_signal(25, 105.0)              # Buy signal
chart.buy_signal(25, 105.0, "Long")      # With label
chart.sell_signal(45, 125.0)             # Sell signal
chart.entry_signal(30, 110.0)            # Entry signal
chart.exit_signal(50, 120.0)             # Exit signal
chart.take_profit_signal(55, 130.0)      # Take profit
chart.stop_loss_signal(35, 95.0)         # Stop loss
chart.custom_signal(40, 115.0, "Alert")  # Custom signal
```

---

## Drawing Primitives (96 types)

### Lines (9 types)

```python
chart.horizontal_line(100.0)                    # Horizontal line
chart.vertical_line(50)                         # Vertical line
chart.trend_line((10, 100.0), (50, 120.0))      # Trend line
chart.ray((10, 100.0), (50, 120.0))             # Ray
chart.extended_line((10, 100.0), (50, 120.0))   # Extended line
chart.info_line((10, 100.0), (50, 120.0))       # Info line
chart.trend_angle((10, 100.0), (50, 120.0))     # Trend angle
chart.horizontal_ray((10, 100.0), (50, 100.0))  # Horizontal ray
chart.cross_line((50, 100.0))                   # Cross line
```

### Channels (4 types)

```python
chart.parallel_channel((0, 100), (50, 120), (0, 90))
chart.regression_trend((10, 100), (50, 120))
chart.flat_top_bottom((0, 100), (50, 100), (25, 90))
chart.disjoint_channel([(0, 100), (20, 110), (40, 105)])
```

### Shapes (10 types)

```python
chart.rectangle((10, 100), (50, 120))
chart.circle((30, 110), (40, 120))
chart.ellipse((30, 110), (50, 130))
chart.triangle((10, 100), (50, 100), (30, 130))
chart.arc((10, 100), (30, 120), (50, 100))
chart.polyline([(10, 100), (20, 110), (30, 105)])
chart.path([(10, 100), (50, 100), (50, 120), (10, 120)])
chart.rotated_rectangle((10, 100), (50, 120), (20, 80))
chart.curve([(10, 100), (30, 130), (50, 100)])
chart.double_curve([(10, 100), (30, 130), (50, 100)])
```

### Fibonacci (11 types)

```python
chart.fib_retracement((10, 100), (50, 150))
chart.fib_extension((10, 100), (30, 130), (40, 115))
chart.fib_channel((10, 100), (50, 120), (10, 80))
chart.fib_time_zones((10, 100), (30, 100))
chart.fib_speed_resistance((10, 100), (50, 150))
chart.fib_trend_time((10, 100), (30, 130), (50, 115))
chart.fib_circles((10, 100), (50, 150))
chart.fib_spiral((10, 100), (50, 150))
chart.fib_arcs((10, 100), (50, 150))
chart.fib_wedge((10, 100), (50, 150))
chart.fib_fan((10, 100), (50, 150))
```

### Pitchforks (4 types)

```python
chart.pitchfork((10, 100), (30, 130), (30, 90))
chart.schiff_pitchfork((10, 100), (30, 130), (30, 90))
chart.modified_schiff((10, 100), (30, 130), (30, 90))
chart.inside_pitchfork((10, 100), (30, 130), (30, 90))
```

### Gann (4 types)

```python
chart.gann_box((10, 100), (50, 150))
chart.gann_square_fixed((10, 100), (50, 150))
chart.gann_square((10, 100), (50, 150))
chart.gann_fan((10, 100), (50, 150))
```

### Patterns (6 types)

```python
chart.xabcd_pattern([(0, 100), (10, 120), (20, 110), (30, 140), (40, 115)])
chart.cypher_pattern([(0, 100), (10, 120), (20, 110), (30, 140), (40, 115)])
chart.head_shoulders([(0, 100), (10, 120), (20, 100), (30, 140), (40, 100), (50, 120), (60, 100)])
chart.abcd_pattern([(0, 100), (10, 120), (20, 110), (30, 130)])
chart.triangle_pattern((10, 100), (50, 100), (30, 130))
chart.three_drives([(0, 100), (10, 120), (20, 105), (30, 130), (40, 110), (50, 140)])
```

### Elliott Waves (5 types)

```python
chart.elliott_impulse([(0, 100), (10, 120), (15, 110), (25, 140), (30, 125), (40, 160)])
chart.elliott_correction([(0, 160), (10, 140), (15, 150), (25, 130)])
chart.elliott_triangle([(0, 100), (10, 120), (20, 105), (30, 115), (40, 110)])
chart.elliott_double_combo([(0, 100), (10, 120), (20, 105), (25, 115), (30, 100), (40, 130)])
chart.elliott_triple_combo([(0, 100), (10, 120), ...])
```

### Arrows (4 types)

```python
chart.arrow_marker((10, 100), (30, 120))
chart.arrow_line((10, 100), (30, 120))
chart.arrow_up((20, 95))
chart.arrow_down((20, 125))
```

### Annotations (11 types)

```python
chart.text((20, 100), "Label")
chart.anchored_text((10, 100), (50, 100), "Range")
chart.note((20, 100), "Note")
chart.price_note((20, 100), "Price note")
chart.signpost((20, 100), "Signpost")
chart.callout((20, 100), "Callout")
chart.comment((20, 100), "Comment")
chart.price_label((20, 100))
chart.sign((20, 100))
chart.flag((20, 100))
chart.table((20, 100))
```

### Cycles (3 types)

```python
chart.cycle_lines((10, 100), (30, 100))
chart.time_cycles((10, 100), (30, 100))
chart.sine_wave((10, 100), (50, 100))
```

### Projections (6 types)

```python
chart.long_position((20, 100), (20, 120), (20, 90))   # entry, tp, sl
chart.short_position((20, 120), (20, 100), (20, 130)) # entry, tp, sl
chart.forecast((10, 100), (50, 120))
chart.bars_pattern((10, 100), (30, 120))
chart.price_projection((10, 100), (30, 130), (50, 110))
chart.projection((10, 100), (50, 120))
```

### Volume Tools (3 types)

```python
chart.anchored_vwap((20, 100))
chart.fixed_volume_profile((10, 100), (50, 150))
chart.anchored_volume_profile((10, 100), (50, 150))
```

### Measurement (3 types)

```python
chart.price_range((10, 100), (50, 150))
chart.date_range((10, 100), (50, 100))
chart.price_date_range((10, 100), (50, 150))
```

### Brushes (2 types)

```python
chart.brush([(10, 100), (20, 110), (30, 105)])
chart.highlighter([(10, 100), (50, 100)])
```

---

## Rendering

```python
svg = chart.render_svg()

# Save to file
with open("chart.svg", "w") as f:
    f.write(svg)

# Display in Jupyter
from IPython.display import SVG, display
display(SVG(svg))
```

---

## Helper Classes

### Theme

```python
from zengeld_canvas import Theme

dark = Theme.dark()
light = Theme.light()

print(dark.bg_color)      # '#131722'
print(dark.candle_up)     # '#26a69a'
print(dark.candle_down)   # '#ef5350'
```

### Viewport

```python
from zengeld_canvas import Viewport

viewport = Viewport(800, 600)
viewport.set_bar_count(100)
viewport.scroll_to_end()
```

### Utility

```python
from zengeld_canvas import version
print(version())  # '0.1.7'
```

---

## Feature Summary

| Category | Count |
|----------|-------|
| Series Types | 3 |
| Moving Averages | 10 |
| Band Indicators | 5 |
| Oscillators | 17 |
| Volatility | 6 |
| Trend | 12 |
| Volume | 12 |
| Specialized | 12 |
| **Total Indicators** | **74** |
| Signal Types | 7 |
| Drawing Primitives | 96 |
| **Total API Methods** | **180+** |

## License

MIT OR Apache-2.0
