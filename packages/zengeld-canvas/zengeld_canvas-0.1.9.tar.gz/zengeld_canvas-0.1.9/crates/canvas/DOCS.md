# zengeld-canvas Technical Documentation

This document provides detailed technical information for developers using the zengeld-canvas library.

## Table of Contents

1. [RenderContext Trait](#rendercontext-trait)
2. [Coordinate Systems](#coordinate-systems)
3. [Primitives System](#primitives-system)
4. [Series Rendering](#series-rendering)
5. [Layout System](#layout-system)
6. [Configuration](#configuration)
7. [Signals and Trades](#signals-and-trades)

---

## RenderContext Trait

The `RenderContext` trait is the core abstraction that enables platform-agnostic rendering. Implement this trait for your rendering backend (Canvas2D, SVG, WebGL, Skia, etc.).

### Required Methods

```rust
pub trait RenderContext {
    // Coordinate transforms
    fn bar_to_x(&self, bar: f64) -> f64;
    fn price_to_y(&self, price: f64) -> f64;
    fn x_to_bar(&self, x: f64) -> f64;
    fn y_to_price(&self, y: f64) -> f64;

    // Dimensions
    fn chart_width(&self) -> f64;
    fn chart_height(&self) -> f64;
    fn dpr(&self) -> f64;  // Device pixel ratio

    // Path operations
    fn begin_path(&mut self);
    fn close_path(&mut self);
    fn move_to(&mut self, x: f64, y: f64);
    fn line_to(&mut self, x: f64, y: f64);
    fn arc(&mut self, x: f64, y: f64, radius: f64, start_angle: f64, end_angle: f64);
    fn arc_to(&mut self, x1: f64, y1: f64, x2: f64, y2: f64, radius: f64);
    fn bezier_curve_to(&mut self, cp1x: f64, cp1y: f64, cp2x: f64, cp2y: f64, x: f64, y: f64);
    fn quadratic_curve_to(&mut self, cpx: f64, cpy: f64, x: f64, y: f64);
    fn ellipse(&mut self, x: f64, y: f64, rx: f64, ry: f64, rotation: f64, start: f64, end: f64);
    fn rect(&mut self, x: f64, y: f64, width: f64, height: f64);

    // Style
    fn set_stroke_color(&mut self, color: &str);
    fn set_fill_color(&mut self, color: &str);
    fn set_fill_color_alpha(&mut self, color: &str, alpha: f64);
    fn set_stroke_width(&mut self, width: f64);
    fn set_line_dash(&mut self, segments: &[f64]);
    fn set_line_cap(&mut self, cap: &str);  // "butt", "round", "square"
    fn set_line_join(&mut self, join: &str); // "miter", "round", "bevel"

    // Draw operations
    fn stroke(&mut self);
    fn fill(&mut self);

    // Text
    fn set_font(&mut self, font: &str);
    fn set_text_align(&mut self, align: &str);     // "left", "center", "right"
    fn set_text_baseline(&mut self, baseline: &str); // "top", "middle", "bottom", "alphabetic"
    fn fill_text(&mut self, text: &str, x: f64, y: f64);
    fn measure_text(&self, text: &str) -> f64;

    // State
    fn save(&mut self);
    fn restore(&mut self);
    fn reset_alpha(&mut self);
    fn translate(&mut self, x: f64, y: f64);
    fn rotate(&mut self, angle: f64);
    fn scale(&mut self, x: f64, y: f64);
    fn clip(&mut self);
}
```

### Implementation Example (SVG)

```rust
use zengeld_canvas::RenderContext;

struct SvgContext {
    output: String,
    width: f64,
    height: f64,
    bar_width: f64,
    first_bar: f64,
    price_min: f64,
    price_max: f64,
    current_path: String,
    stroke_color: String,
    fill_color: String,
    stroke_width: f64,
}

impl RenderContext for SvgContext {
    fn bar_to_x(&self, bar: f64) -> f64 {
        (bar - self.first_bar) * self.bar_width
    }

    fn price_to_y(&self, price: f64) -> f64 {
        let range = self.price_max - self.price_min;
        self.height - ((price - self.price_min) / range * self.height)
    }

    fn chart_width(&self) -> f64 { self.width }
    fn chart_height(&self) -> f64 { self.height }
    fn dpr(&self) -> f64 { 1.0 }

    fn begin_path(&mut self) {
        self.current_path.clear();
    }

    fn move_to(&mut self, x: f64, y: f64) {
        self.current_path.push_str(&format!("M{:.2} {:.2} ", x, y));
    }

    fn line_to(&mut self, x: f64, y: f64) {
        self.current_path.push_str(&format!("L{:.2} {:.2} ", x, y));
    }

    fn stroke(&mut self) {
        self.output.push_str(&format!(
            "<path d=\"{}\" stroke=\"{}\" stroke-width=\"{}\" fill=\"none\"/>\n",
            self.current_path, self.stroke_color, self.stroke_width
        ));
    }

    // ... implement remaining methods
}
```

---

## Coordinate Systems

### Viewport

The `Viewport` manages chart dimensions and visible data range.

```rust
use zengeld_canvas::Viewport;

let mut viewport = Viewport::new(800.0, 600.0);

// Set visible bar range
viewport.first_bar = 0.0;
viewport.last_bar = 100.0;
viewport.bar_width = 8.0;

// Chart area dimensions (excluding price scale)
let chart_width = viewport.chart_width();
let chart_height = viewport.chart_height;
```

### PriceScale

Manages price axis calculations and tick generation.

```rust
use zengeld_canvas::{PriceScale, PriceScaleMode};

let mut price_scale = PriceScale::new();

// Configure mode
price_scale.mode = PriceScaleMode::Normal;  // or Logarithmic, Percentage, IndexedTo100

// Set price range
price_scale.set_range(95.0, 105.0);

// Get ticks for rendering
let ticks = price_scale.calculate_ticks(600.0); // chart height
for tick in ticks {
    println!("Price: {}, Y: {}", tick.price, tick.y);
}

// Format price for display
let formatted = format_price(100.5, 2);  // "100.50"
```

### TimeScale

Manages time axis with weight-based tick formatting.

```rust
use zengeld_canvas::{TimeScale, TickMarkWeight, format_time_by_weight};

let time_scale = TimeScale::new();

// Time ticks have different weights (Year, Month, Week, Day, Hour, etc.)
let formatted = format_time_by_weight(1703721600, TickMarkWeight::Day);
// Result: "27" or "Dec 27" depending on weight

// Full date format
let full = format_time_full(1703721600); // "2024-12-27 12:00"
```

---

## Primitives System

### PrimitiveTrait

All drawing tools implement `PrimitiveTrait`:

```rust
pub trait PrimitiveTrait: Send + Sync {
    // Identity
    fn type_id(&self) -> &'static str;
    fn display_name(&self) -> &str;
    fn kind(&self) -> PrimitiveKind;

    // Data access
    fn data(&self) -> &PrimitiveData;
    fn data_mut(&mut self) -> &mut PrimitiveData;

    // Points (anchor coordinates in bar/price space)
    fn points(&self) -> Vec<(f64, f64)>;
    fn set_points(&mut self, points: &[(f64, f64)]);

    // Transform
    fn translate(&mut self, bar_delta: f64, price_delta: f64);

    // Rendering
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool);

    // Serialization
    fn to_json(&self) -> String;
    fn clone_box(&self) -> Box<dyn PrimitiveTrait>;

    // Optional: Text anchor for label positioning
    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> { None }

    // Optional: Fibonacci level configuration
    fn level_configs(&self) -> Option<Vec<FibLevelConfig>> { None }
    fn set_level_configs(&mut self, configs: Vec<FibLevelConfig>) -> bool { false }
}
```

### PrimitiveData

Common data shared by all primitives:

```rust
pub struct PrimitiveData {
    pub type_id: String,
    pub display_name: String,
    pub color: PrimitiveColor,
    pub width: f64,
    pub style: LineStyle,
    pub visible: bool,
    pub locked: bool,
    pub text: Option<PrimitiveText>,
    pub z_index: i32,
}

pub struct PrimitiveColor {
    pub stroke: String,
    pub fill: Option<String>,
}
```

### PrimitiveRegistry

Factory pattern for creating primitives:

```rust
use zengeld_canvas::primitives::PrimitiveRegistry;

let registry = PrimitiveRegistry::new();

// List all available primitives
for meta in registry.all_metadata() {
    println!("{} ({}): {:?}", meta.display_name, meta.type_id, meta.kind);
}

// Create by type_id
let line = registry.create(
    "trend_line",
    &[(10.0, 100.0), (50.0, 150.0)],  // points
    "#2962ff"                           // color
);

// Check capabilities
if meta.has_levels {
    // Fibonacci-type primitive with configurable levels
}
if meta.supports_text {
    // Can have attached text label
}
```

### LineStyle

```rust
pub enum LineStyle {
    Solid,
    Dashed,       // [8, 4]
    Dotted,       // [2, 2]
    LargeDashed,  // [12, 6]
    SparseDotted, // [2, 8]
}
```

### Crisp Rendering

For pixel-perfect lines, use the `crisp` function:

```rust
use zengeld_canvas::crisp;

// Aligns coordinates to device pixels
let x = crisp(100.5, dpr);  // Rounds to nearest half-pixel for 1px lines
```

---

## Series Rendering

### Series Types

```rust
pub enum SeriesType {
    Candlestick,
    Bar,
    Line,
    Area,
    Baseline,
    Histogram,
    // ... more types
}
```

### Data Structures

```rust
// OHLC data
pub struct CandlestickData {
    pub time: i64,      // Unix timestamp
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
}

// Single value data
pub struct LineData {
    pub time: i64,
    pub value: f64,
}

// Area/baseline data
pub struct AreaData {
    pub time: i64,
    pub value: f64,
}

// Histogram data
pub struct HistogramData {
    pub time: i64,
    pub value: f64,
    pub color: Option<String>,
}
```

### Series Options

```rust
pub struct CandlestickStyleOptions {
    pub up_color: String,
    pub down_color: String,
    pub border_up_color: String,
    pub border_down_color: String,
    pub wick_up_color: String,
    pub wick_down_color: String,
    pub border_visible: bool,
    pub wick_visible: bool,
}

pub struct LineStyleOptions {
    pub color: String,
    pub line_width: f64,
    pub line_type: LineType,  // Simple, WithSteps, Curved
    pub crosshair_marker_visible: bool,
}
```

---

## Layout System

### Pane Manager

For multi-pane charts (main chart + indicators):

```rust
use zengeld_canvas::{PaneManager, Pane, SubPane, MAIN_PANE};

let mut manager = PaneManager::new();

// Add indicator panes
let volume_pane = manager.add_pane("volume", 0.2);  // 20% height
let rsi_pane = manager.add_pane("rsi", 0.15);       // 15% height

// Add sub-pane (stacked within a pane)
manager.add_sub_pane(&volume_pane, "obv");

// Get pane geometry
let geometry = manager.calculate_geometry(600.0);  // total height
for (pane_id, pane_geo) in geometry {
    println!("Pane {}: y={}, height={}", pane_id, pane_geo.y, pane_geo.height);
}

// Resize panes
manager.resize_pane(&volume_pane, 0.25);

// Remove pane
manager.remove_pane(&rsi_pane);
```

### Multichart Layout

For multiple chart instances in a grid:

```rust
use zengeld_canvas::{MultichartLayout, CellId, CellBounds};

// Built-in presets
let single = MultichartLayout::single();      // 1 chart
let dual_h = MultichartLayout::dual_horizontal(); // 2 side by side
let dual_v = MultichartLayout::dual_vertical();   // 2 stacked
let quad = MultichartLayout::quad();          // 2x2 grid
let six = MultichartLayout::six_pack();       // 2x3 grid

// Custom grid
let custom = MultichartLayout::grid(3, 4);    // 3 cols x 4 rows

// Get all presets
let presets = MultichartLayout::presets();

// Calculate cell bounds
let bounds = layout.cell_bounds(
    CellId(0),  // first cell
    1920.0,     // container width
    1080.0      // container height
);
println!("Cell: x={}, y={}, w={}, h={}", bounds.x, bounds.y, bounds.width, bounds.height);

// Chart count
let count = layout.chart_count();
```

---

## Configuration

### ChartConfig

Central configuration for chart appearance:

```rust
use zengeld_canvas::ChartConfig;

let config = ChartConfig::default();

// Access sub-configs
let candle_cfg = &config.candlestick;
let grid_cfg = &config.grid;
let crosshair_cfg = &config.crosshair;
```

### Theme

```rust
use zengeld_canvas::Theme;

let dark = Theme::dark();
let light = Theme::light();

// Theme colors
println!("Background: {}", dark.background);
println!("Text: {}", dark.text);
println!("Grid: {}", dark.grid);
```

### Bar Data

```rust
use zengeld_canvas::Bar;

let bar = Bar {
    time: 1703721600,
    open: 100.0,
    high: 105.0,
    low: 98.0,
    close: 103.0,
    volume: 1_000_000.0,
};

// Direction helper
if bar.is_bullish() {
    // close > open
}
```

---

## Signals and Trades

### System Signals

For algorithmic trading visualization:

```rust
use zengeld_canvas::{SystemSignal, SignalType, SignalManager};

let signal = SystemSignal {
    signal_type: SignalType::Buy,
    bar_index: 50,
    price: 100.5,
    label: Some("Entry".to_string()),
    color: Some("#22ab94".to_string()),
};

let mut manager = SignalManager::new();
manager.add_signal(signal);

// Render signals
manager.render(&mut ctx);
```

### Trade Visualization

```rust
use zengeld_canvas::{Trade, TradeDirection, TradeManager};

let trade = Trade {
    entry_bar: 50,
    entry_price: 100.0,
    exit_bar: Some(75),
    exit_price: Some(110.0),
    direction: TradeDirection::Long,
    profit_loss: Some(10.0),
};

let mut manager = TradeManager::new();
manager.add_trade(trade);

// Render trade boxes
manager.render(&mut ctx);
```

---

## Utility Functions

### Color Parsing

```rust
use zengeld_canvas::parse_css_color;

// Parse various color formats
let (r, g, b, a) = parse_css_color("#ff0000").unwrap();     // Hex
let (r, g, b, a) = parse_css_color("#ff000080").unwrap();   // Hex with alpha
let (r, g, b, a) = parse_css_color("rgb(255,0,0)").unwrap(); // RGB
let (r, g, b, a) = parse_css_color("rgba(255,0,0,0.5)").unwrap(); // RGBA
```

### Spline Interpolation

```rust
use zengeld_canvas::catmull_rom_spline;

let points = vec![(0.0, 0.0), (10.0, 50.0), (20.0, 30.0), (30.0, 80.0)];
let smooth = catmull_rom_spline(&points, 10); // 10 segments between points
```

### Price Formatting

```rust
use zengeld_canvas::{format_price, format_indicator_value, price_precision};

let formatted = format_price(100.5678, 2);  // "100.57"
let indicator = format_indicator_value(0.00001234);  // Smart formatting
let precision = price_precision(0.001);  // Returns 3
```

---

## Best Practices

1. **Implement RenderContext fully** - Don't skip methods; primitives may use any of them.

2. **Use crisp() for lines** - Prevents blurry 1px lines on retina displays.

3. **Batch operations** - Group similar drawing operations when possible.

4. **Cache coordinate transforms** - `bar_to_x` and `price_to_y` are called frequently.

5. **Handle DPR** - Always multiply dimensions by `dpr()` for crisp rendering.

6. **State management** - Always pair `save()` with `restore()`.

```rust
ctx.save();
ctx.translate(x, y);
ctx.rotate(angle);
// ... draw
ctx.restore();  // Don't forget!
```

---

## Version History

- **0.1.0** - Initial release
  - 80+ drawing primitives
  - 12 series types
  - Multi-pane and multichart layouts
  - Platform-agnostic RenderContext trait
