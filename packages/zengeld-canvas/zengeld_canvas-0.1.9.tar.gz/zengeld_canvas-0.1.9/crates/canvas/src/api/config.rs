//! Chart Configuration API
//!
//! Provides a declarative configuration system for building charts.
//! Covers 100% of library functionality through config structs.
//!
//! # Architecture
//!
//! ```text
//! ChartConfig
//! ├── dimensions (width, height, dpr)
//! ├── theme (colors, background)
//! ├── series (SeriesConfig - all 12 types)
//! ├── overlays (OverlayConfig - indicators on main chart)
//! ├── subpanes (SubpaneConfig - RSI, MACD, etc.)
//! ├── primitives (PrimitiveConfig - 96 drawing tools)
//! ├── signals (SignalConfig - buy/sell markers)
//! └── layout (LayoutConfig - multichart, sync)
//! ```

use crate::layout::PaneId;
use crate::model::{Indicator, SeriesType};
use crate::primitives::{PrimitiveKind, PrimitiveMetadata, PrimitiveRegistry, SignalType};
use serde::{Deserialize, Serialize};

// =============================================================================
// Main Chart Configuration
// =============================================================================

/// Complete chart configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChartConfig {
    /// Canvas dimensions
    pub width: u32,
    pub height: u32,
    pub dpr: f64,

    /// Theme configuration
    pub theme: ThemeConfig,

    /// Main series configuration
    pub series: SeriesConfig,

    /// Indicators (overlays + subpanes unified)
    /// Each Indicator has placement (Overlay or SubPane) and vectors with styles
    #[serde(default)]
    pub indicators: Vec<Indicator>,

    /// Drawing primitives (trend lines, fibonacci, patterns, etc.)
    #[serde(default)]
    pub primitives: Vec<PrimitiveConfig>,

    /// Trading signals (buy/sell markers)
    #[serde(default)]
    pub signals: Vec<SignalConfig>,

    /// Layout configuration (multichart, sync)
    #[serde(default)]
    pub layout: LayoutConfig,
}

impl Default for ChartConfig {
    fn default() -> Self {
        Self {
            width: 800,
            height: 600,
            dpr: 1.0,
            theme: ThemeConfig::default(),
            series: SeriesConfig::default(),
            indicators: Vec::new(),
            primitives: Vec::new(),
            signals: Vec::new(),
            layout: LayoutConfig::default(),
        }
    }
}

impl ChartConfig {
    pub fn new(width: u32, height: u32) -> Self {
        Self {
            width,
            height,
            ..Default::default()
        }
    }
}

// =============================================================================
// Theme Configuration
// =============================================================================

/// Theme/styling configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ThemeConfig {
    /// Background color
    pub background: String,
    /// Grid color
    pub grid_color: String,
    /// Show grid
    pub show_grid: bool,
    /// Up/bullish color
    pub up_color: String,
    /// Down/bearish color
    pub down_color: String,
    /// Text color
    pub text_color: String,
    /// Border color
    pub border_color: String,
}

impl Default for ThemeConfig {
    fn default() -> Self {
        Self {
            background: "#131722".into(),
            grid_color: "#1e222d".into(),
            show_grid: false, // Grid disabled by default
            up_color: "#26a69a".into(),
            down_color: "#ef5350".into(),
            text_color: "#b2b5be".into(),
            border_color: "#2a2e39".into(),
        }
    }
}

impl ThemeConfig {
    /// Dark theme (default)
    pub fn dark() -> Self {
        Self::default()
    }

    /// Light theme
    pub fn light() -> Self {
        Self {
            background: "#ffffff".into(),
            grid_color: "#e0e3eb".into(),
            show_grid: true,
            up_color: "#26a69a".into(),
            down_color: "#ef5350".into(),
            text_color: "#434651".into(),
            border_color: "#dee2e6".into(),
        }
    }
}

// =============================================================================
// Series Configuration (All 12 Types)
// =============================================================================

/// Main series configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SeriesConfig {
    /// Series type
    pub series_type: SeriesType,
    /// Style options (type-specific)
    #[serde(default)]
    pub style: SeriesStyleConfig,
}

impl Default for SeriesConfig {
    fn default() -> Self {
        Self {
            series_type: SeriesType::Candlestick,
            style: SeriesStyleConfig::default(),
        }
    }
}

impl SeriesConfig {
    // === OHLC Series ===

    /// Candlestick chart
    pub fn candlestick() -> Self {
        Self {
            series_type: SeriesType::Candlestick,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Hollow candlestick chart
    pub fn hollow_candlestick() -> Self {
        Self {
            series_type: SeriesType::HollowCandlestick,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Heikin Ashi chart
    pub fn heikin_ashi() -> Self {
        Self {
            series_type: SeriesType::HeikinAshi,
            style: SeriesStyleConfig::default(),
        }
    }

    /// OHLC Bar chart
    pub fn bar() -> Self {
        Self {
            series_type: SeriesType::Bar,
            style: SeriesStyleConfig::default(),
        }
    }

    /// HLC Area chart
    pub fn hlc_area() -> Self {
        Self {
            series_type: SeriesType::HlcArea,
            style: SeriesStyleConfig::default(),
        }
    }

    // === Value Series ===

    /// Line chart
    pub fn line() -> Self {
        Self {
            series_type: SeriesType::Line,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Step line chart
    pub fn step_line() -> Self {
        Self {
            series_type: SeriesType::StepLine,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Line with markers
    pub fn line_with_markers() -> Self {
        Self {
            series_type: SeriesType::LineWithMarkers,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Area chart
    pub fn area() -> Self {
        Self {
            series_type: SeriesType::Area,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Baseline chart
    pub fn baseline(baseline_value: f64) -> Self {
        Self {
            series_type: SeriesType::Baseline,
            style: SeriesStyleConfig {
                baseline_value: Some(baseline_value),
                ..Default::default()
            },
        }
    }

    /// Histogram
    pub fn histogram() -> Self {
        Self {
            series_type: SeriesType::Histogram,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Columns (alias for histogram)
    pub fn columns() -> Self {
        Self {
            series_type: SeriesType::Columns,
            style: SeriesStyleConfig::default(),
        }
    }

    /// Set custom colors
    pub fn with_colors(mut self, up: &str, down: &str) -> Self {
        self.style.up_color = Some(up.into());
        self.style.down_color = Some(down.into());
        self
    }

    /// Set line color (for Line, Area, etc.)
    pub fn with_color(mut self, color: &str) -> Self {
        self.style.color = Some(color.into());
        self
    }

    /// Set line width
    pub fn with_line_width(mut self, width: f64) -> Self {
        self.style.line_width = Some(width);
        self
    }
}

/// Series style options
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct SeriesStyleConfig {
    /// Primary color (for single-color series)
    pub color: Option<String>,
    /// Up/bullish color
    pub up_color: Option<String>,
    /// Down/bearish color
    pub down_color: Option<String>,
    /// Line width
    pub line_width: Option<f64>,
    /// Baseline value (for Baseline series)
    pub baseline_value: Option<f64>,
    /// Show wicks (candlestick)
    pub show_wicks: Option<bool>,
    /// Show borders (candlestick)
    pub show_borders: Option<bool>,
    /// Fill opacity (area charts)
    pub fill_opacity: Option<f64>,
}

/// Line style type
#[derive(Clone, Copy, Debug, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum LineStyleType {
    #[default]
    Solid,
    Dashed,
    Dotted,
}

fn default_line_width() -> f64 {
    1.5
}

// =============================================================================
// Primitive Configuration (96 Drawing Tools)
// =============================================================================

/// Drawing primitive configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrimitiveConfig {
    /// Primitive type ID (matches PrimitiveRegistry)
    pub type_id: String,
    /// Control points [(bar_index, price), ...]
    pub points: Vec<(f64, f64)>,
    /// Color
    #[serde(default = "default_primitive_color")]
    pub color: String,
    /// Line width
    #[serde(default = "default_line_width")]
    pub line_width: f64,
    /// Line style
    #[serde(default)]
    pub line_style: LineStyleType,
    /// Fill color (for shapes)
    pub fill_color: Option<String>,
    /// Fill opacity
    pub fill_opacity: Option<f64>,
    /// Text label
    pub text: Option<String>,
    /// Extend mode (for lines)
    pub extend: Option<ExtendMode>,
    /// Fibonacci/Gann levels
    #[serde(default)]
    pub levels: Vec<LevelConfig>,
    /// Target pane (main or subpane id)
    #[serde(default)]
    pub pane_id: Option<PaneId>,
}

fn default_primitive_color() -> String {
    "#2196F3".into()
}

/// Line extend mode
#[derive(Clone, Copy, Debug, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ExtendMode {
    #[default]
    None,
    Left,
    Right,
    Both,
}

/// Level configuration (for Fibonacci, Gann, etc.)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LevelConfig {
    pub value: f64,
    pub color: String,
    pub visible: bool,
    pub label: Option<String>,
}

impl PrimitiveConfig {
    /// Create a primitive config
    pub fn new(type_id: &str, points: Vec<(f64, f64)>) -> Self {
        Self {
            type_id: type_id.into(),
            points,
            color: default_primitive_color(),
            line_width: 1.5,
            line_style: LineStyleType::Solid,
            fill_color: None,
            fill_opacity: None,
            text: None,
            extend: None,
            levels: Vec::new(),
            pane_id: None,
        }
    }

    // =================================================================
    // Registry Integration
    // =================================================================

    /// Get all available primitive type IDs from the registry
    pub fn available_types() -> Vec<&'static str> {
        let registry = PrimitiveRegistry::global().read().unwrap();
        registry.all().map(|m| m.type_id).collect()
    }

    /// Get available primitives by kind
    pub fn types_by_kind(kind: PrimitiveKind) -> Vec<&'static str> {
        let registry = PrimitiveRegistry::global().read().unwrap();
        registry.by_kind(kind).to_vec()
    }

    /// Get metadata for a primitive type
    pub fn metadata(type_id: &str) -> Option<PrimitiveMetadata> {
        let registry = PrimitiveRegistry::global().read().unwrap();
        registry.get(type_id).cloned()
    }

    /// Check if a type_id is valid (exists in registry)
    pub fn is_valid_type(type_id: &str) -> bool {
        let registry = PrimitiveRegistry::global().read().unwrap();
        registry.get(type_id).is_some()
    }

    /// Create a primitive instance from this config
    pub fn create_primitive(&self) -> Option<Box<dyn crate::primitives::PrimitiveTrait>> {
        let registry = PrimitiveRegistry::global().read().unwrap();
        registry.create(&self.type_id, &self.points, Some(&self.color))
    }

    /// Create config from registry type_id with validation
    pub fn from_registry(type_id: &str, points: Vec<(f64, f64)>) -> Option<Self> {
        if Self::is_valid_type(type_id) {
            Some(Self::new(type_id, points))
        } else {
            None
        }
    }

    // =================================================================
    // Lines (9 types)
    // =================================================================

    pub fn trend_line(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("trend_line", vec![p1, p2])
    }

    pub fn horizontal_line(price: f64) -> Self {
        Self::new("horizontal_line", vec![(0.0, price)])
    }

    pub fn vertical_line(bar_index: f64) -> Self {
        Self::new("vertical_line", vec![(bar_index, 0.0)])
    }

    pub fn ray(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("ray", vec![p1, p2])
    }

    pub fn extended_line(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("extended_line", vec![p1, p2])
    }

    pub fn info_line(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("info_line", vec![p1, p2])
    }

    pub fn trend_angle(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("trend_angle", vec![p1, p2])
    }

    pub fn horizontal_ray(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("horizontal_ray", vec![p1, p2])
    }

    pub fn cross_line(position: (f64, f64)) -> Self {
        Self::new("cross_line", vec![position])
    }

    // =================================================================
    // Channels (4 types)
    // =================================================================

    pub fn parallel_channel(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("parallel_channel", vec![p1, p2, p3])
    }

    pub fn regression_trend(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("regression_trend", vec![p1, p2])
    }

    pub fn flat_top_bottom(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("flat_top_bottom", vec![p1, p2, p3])
    }

    pub fn disjoint_channel(points: Vec<(f64, f64)>) -> Self {
        Self::new("disjoint_channel", points)
    }

    // =================================================================
    // Shapes (10 types)
    // =================================================================

    pub fn rectangle(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("rectangle", vec![p1, p2])
    }

    pub fn circle(center: (f64, f64), edge: (f64, f64)) -> Self {
        Self::new("circle", vec![center, edge])
    }

    pub fn ellipse(center: (f64, f64), edge: (f64, f64)) -> Self {
        Self::new("ellipse", vec![center, edge])
    }

    pub fn triangle(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("triangle", vec![p1, p2, p3])
    }

    pub fn arc(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("arc", vec![p1, p2, p3])
    }

    pub fn polyline(points: Vec<(f64, f64)>) -> Self {
        Self::new("polyline", points)
    }

    pub fn path(points: Vec<(f64, f64)>) -> Self {
        Self::new("path", points)
    }

    pub fn rotated_rectangle(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("rotated_rectangle", vec![p1, p2, p3])
    }

    pub fn curve(points: Vec<(f64, f64)>) -> Self {
        Self::new("curve", points)
    }

    pub fn double_curve(points: Vec<(f64, f64)>) -> Self {
        Self::new("double_curve", points)
    }

    // =================================================================
    // Fibonacci (11 types)
    // =================================================================

    pub fn fib_retracement(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_retracement", vec![p1, p2])
    }

    pub fn fib_extension(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("fib_trend_extension", vec![p1, p2, p3])
    }

    pub fn fib_channel(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("fib_channel", vec![p1, p2, p3])
    }

    pub fn fib_time_zones(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_time_zones", vec![p1, p2])
    }

    pub fn fib_speed_resistance(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_speed_resistance", vec![p1, p2])
    }

    pub fn fib_trend_time(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("fib_trend_time", vec![p1, p2, p3])
    }

    pub fn fib_circles(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_circles", vec![p1, p2])
    }

    pub fn fib_spiral(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_spiral", vec![p1, p2])
    }

    pub fn fib_arcs(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_arcs", vec![p1, p2])
    }

    pub fn fib_wedge(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_wedge", vec![p1, p2])
    }

    pub fn fib_fan(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fib_fan", vec![p1, p2])
    }

    // =================================================================
    // Pitchforks (4 types)
    // =================================================================

    pub fn pitchfork(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("pitchfork", vec![p1, p2, p3])
    }

    pub fn schiff_pitchfork(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("schiff_pitchfork", vec![p1, p2, p3])
    }

    pub fn modified_schiff(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("modified_schiff", vec![p1, p2, p3])
    }

    pub fn inside_pitchfork(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("inside_pitchfork", vec![p1, p2, p3])
    }

    // =================================================================
    // Gann (4 types)
    // =================================================================

    pub fn gann_box(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("gann_box", vec![p1, p2])
    }

    pub fn gann_square_fixed(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("gann_square_fixed", vec![p1, p2])
    }

    pub fn gann_square(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("gann_square", vec![p1, p2])
    }

    pub fn gann_fan(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("gann_fan", vec![p1, p2])
    }

    // =================================================================
    // Arrows (4 types)
    // =================================================================

    pub fn arrow_marker(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("arrow_marker", vec![p1, p2])
    }

    pub fn arrow_line(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("arrow_line", vec![p1, p2])
    }

    pub fn arrow_up(position: (f64, f64)) -> Self {
        Self::new("arrow_up", vec![position])
    }

    pub fn arrow_down(position: (f64, f64)) -> Self {
        Self::new("arrow_down", vec![position])
    }

    // =================================================================
    // Annotations (11 types)
    // =================================================================

    pub fn text(position: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("text", vec![position]);
        config.text = Some(content.into());
        config
    }

    pub fn anchored_text(p1: (f64, f64), p2: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("anchored_text", vec![p1, p2]);
        config.text = Some(content.into());
        config
    }

    pub fn note(position: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("note", vec![position]);
        config.text = Some(content.into());
        config
    }

    pub fn price_note(position: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("price_note", vec![position]);
        config.text = Some(content.into());
        config
    }

    pub fn signpost(position: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("signpost", vec![position]);
        config.text = Some(content.into());
        config
    }

    pub fn callout(position: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("callout", vec![position]);
        config.text = Some(content.into());
        config
    }

    pub fn comment(position: (f64, f64), content: &str) -> Self {
        let mut config = Self::new("comment", vec![position]);
        config.text = Some(content.into());
        config
    }

    pub fn price_label(position: (f64, f64)) -> Self {
        Self::new("price_label", vec![position])
    }

    pub fn sign(position: (f64, f64)) -> Self {
        Self::new("sign", vec![position])
    }

    pub fn flag(position: (f64, f64)) -> Self {
        Self::new("flag", vec![position])
    }

    pub fn table(position: (f64, f64)) -> Self {
        Self::new("table", vec![position])
    }

    // =================================================================
    // Patterns (6 types)
    // =================================================================

    pub fn xabcd_pattern(points: Vec<(f64, f64)>) -> Self {
        Self::new("xabcd_pattern", points)
    }

    pub fn cypher_pattern(points: Vec<(f64, f64)>) -> Self {
        Self::new("cypher_pattern", points)
    }

    pub fn head_shoulders(points: Vec<(f64, f64)>) -> Self {
        Self::new("head_shoulders", points)
    }

    pub fn abcd_pattern(points: Vec<(f64, f64)>) -> Self {
        Self::new("abcd_pattern", points)
    }

    pub fn triangle_pattern(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("triangle_pattern", vec![p1, p2, p3])
    }

    pub fn three_drives(points: Vec<(f64, f64)>) -> Self {
        Self::new("three_drives", points)
    }

    // =================================================================
    // Elliott (5 types)
    // =================================================================

    pub fn elliott_impulse(points: Vec<(f64, f64)>) -> Self {
        Self::new("elliott_impulse", points)
    }

    pub fn elliott_correction(points: Vec<(f64, f64)>) -> Self {
        Self::new("elliott_correction", points)
    }

    pub fn elliott_triangle(points: Vec<(f64, f64)>) -> Self {
        Self::new("elliott_triangle", points)
    }

    pub fn elliott_double_combo(points: Vec<(f64, f64)>) -> Self {
        Self::new("elliott_double_combo", points)
    }

    pub fn elliott_triple_combo(points: Vec<(f64, f64)>) -> Self {
        Self::new("elliott_triple_combo", points)
    }

    // =================================================================
    // Cycles (3 types)
    // =================================================================

    pub fn cycle_lines(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("cycle_lines", vec![p1, p2])
    }

    pub fn time_cycles(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("time_cycles", vec![p1, p2])
    }

    pub fn sine_wave(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("sine_wave", vec![p1, p2])
    }

    // =================================================================
    // Projection (6 types)
    // =================================================================

    pub fn long_position(entry: (f64, f64), tp: (f64, f64), sl: (f64, f64)) -> Self {
        Self::new("long_position", vec![entry, tp, sl])
    }

    pub fn short_position(entry: (f64, f64), tp: (f64, f64), sl: (f64, f64)) -> Self {
        Self::new("short_position", vec![entry, tp, sl])
    }

    pub fn forecast(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("forecast", vec![p1, p2])
    }

    pub fn bars_pattern(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("bars_pattern", vec![p1, p2])
    }

    pub fn price_projection(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> Self {
        Self::new("price_projection", vec![p1, p2, p3])
    }

    pub fn projection(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("projection", vec![p1, p2])
    }

    // =================================================================
    // Volume (3 types)
    // =================================================================

    pub fn anchored_vwap(position: (f64, f64)) -> Self {
        Self::new("anchored_vwap", vec![position])
    }

    pub fn fixed_volume_profile(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("fixed_volume_profile", vec![p1, p2])
    }

    pub fn anchored_volume_profile(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("anchored_volume_profile", vec![p1, p2])
    }

    // =================================================================
    // Measurement (3 types)
    // =================================================================

    pub fn price_range(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("price_range", vec![p1, p2])
    }

    pub fn date_range(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("date_range", vec![p1, p2])
    }

    pub fn price_date_range(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("price_date_range", vec![p1, p2])
    }

    // =================================================================
    // Brushes (2 types)
    // =================================================================

    pub fn brush(points: Vec<(f64, f64)>) -> Self {
        Self::new("brush", points)
    }

    pub fn highlighter(points: Vec<(f64, f64)>) -> Self {
        Self::new("highlighter", points)
    }

    // =================================================================
    // Icons (2 types)
    // =================================================================

    pub fn image(position: (f64, f64)) -> Self {
        Self::new("image", vec![position])
    }

    pub fn emoji(position: (f64, f64)) -> Self {
        Self::new("emoji", vec![position])
    }

    // =================================================================
    // Events (9 types) - Strategy-generated markers
    // =================================================================

    /// Crossover event (MA cross, MACD cross, etc.)
    pub fn crossover(position: (f64, f64)) -> Self {
        Self::new("crossover", vec![position])
    }

    /// Breakdown event (level breakout/breakdown)
    pub fn breakdown(position: (f64, f64)) -> Self {
        Self::new("breakdown", vec![position])
    }

    /// Divergence event (RSI/MACD divergence)
    pub fn divergence(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("divergence", vec![p1, p2])
    }

    /// Pattern match event (detected chart pattern)
    pub fn pattern_match(points: Vec<(f64, f64)>) -> Self {
        Self::new("pattern_match", points)
    }

    /// Zone event (supply/demand zone, order block)
    pub fn zone_event(p1: (f64, f64), p2: (f64, f64)) -> Self {
        Self::new("zone_event", vec![p1, p2])
    }

    /// Volume event (spike, climax, dry-up)
    pub fn volume_event(position: (f64, f64)) -> Self {
        Self::new("volume_event", vec![position])
    }

    /// Trend event (trend change, reversal, continuation)
    pub fn trend_event(position: (f64, f64)) -> Self {
        Self::new("trend_event", vec![position])
    }

    /// Momentum event (momentum shift, exhaustion)
    pub fn momentum_event(position: (f64, f64)) -> Self {
        Self::new("momentum_event", vec![position])
    }

    /// Custom event (user-defined strategy event)
    pub fn custom_event(position: (f64, f64), label: &str) -> Self {
        let mut config = Self::new("custom_event", vec![position]);
        config.text = Some(label.into());
        config
    }

    // =================================================================
    // Builder Methods
    // =================================================================

    pub fn with_color(mut self, color: &str) -> Self {
        self.color = color.into();
        self
    }

    pub fn with_line_width(mut self, width: f64) -> Self {
        self.line_width = width;
        self
    }

    pub fn with_fill(mut self, color: &str, opacity: f64) -> Self {
        self.fill_color = Some(color.into());
        self.fill_opacity = Some(opacity);
        self
    }

    pub fn with_text(mut self, text: &str) -> Self {
        self.text = Some(text.into());
        self
    }

    pub fn with_extend(mut self, mode: ExtendMode) -> Self {
        self.extend = Some(mode);
        self
    }

    pub fn with_levels(mut self, levels: Vec<LevelConfig>) -> Self {
        self.levels = levels;
        self
    }

    pub fn on_pane(mut self, pane_id: PaneId) -> Self {
        self.pane_id = Some(pane_id);
        self
    }
}

// =============================================================================
// Signal Configuration (Trading Signals)
// =============================================================================

/// Trading signal configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SignalConfig {
    /// Signal type
    pub signal_type: SignalType,
    /// Bar index
    pub bar_index: usize,
    /// Price level
    pub price: f64,
    /// Color override
    pub color: Option<String>,
    /// Size multiplier
    #[serde(default = "default_signal_size")]
    pub size: f64,
    /// Label text
    pub label: Option<String>,
    /// Target pane
    pub pane_id: Option<PaneId>,
}

fn default_signal_size() -> f64 {
    1.0
}

impl SignalConfig {
    pub fn new(signal_type: SignalType, bar_index: usize, price: f64) -> Self {
        Self {
            signal_type,
            bar_index,
            price,
            color: None,
            size: 1.0,
            label: None,
            pane_id: None,
        }
    }

    pub fn buy(bar_index: usize, price: f64) -> Self {
        Self::new(SignalType::Buy, bar_index, price)
    }

    pub fn sell(bar_index: usize, price: f64) -> Self {
        Self::new(SignalType::Sell, bar_index, price)
    }

    pub fn entry(bar_index: usize, price: f64) -> Self {
        Self::new(SignalType::Entry, bar_index, price)
    }

    pub fn exit(bar_index: usize, price: f64) -> Self {
        Self::new(SignalType::Exit, bar_index, price)
    }

    pub fn take_profit(bar_index: usize, price: f64) -> Self {
        Self::new(SignalType::TakeProfit, bar_index, price)
    }

    pub fn stop_loss(bar_index: usize, price: f64) -> Self {
        Self::new(SignalType::StopLoss, bar_index, price)
    }

    pub fn custom(bar_index: usize, price: f64, label: &str) -> Self {
        let mut s = Self::new(SignalType::Custom, bar_index, price);
        s.label = Some(label.into());
        s
    }

    pub fn with_color(mut self, color: &str) -> Self {
        self.color = Some(color.into());
        self
    }

    pub fn with_size(mut self, size: f64) -> Self {
        self.size = size;
        self
    }

    pub fn with_label(mut self, label: &str) -> Self {
        self.label = Some(label.into());
        self
    }

    pub fn on_pane(mut self, pane_id: PaneId) -> Self {
        self.pane_id = Some(pane_id);
        self
    }
}

// =============================================================================
// Layout Configuration (Multichart, Sync)
// =============================================================================

/// Layout configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LayoutConfig {
    /// Layout type
    pub layout_type: LayoutType,
    /// Gap between cells/panes
    #[serde(default = "default_gap")]
    pub gap: f64,
    /// Sync crosshair between charts
    #[serde(default)]
    pub sync_crosshair: bool,
    /// Sync time scale
    #[serde(default)]
    pub sync_time: bool,
    /// Sync price scale
    #[serde(default)]
    pub sync_price: bool,
}

fn default_gap() -> f64 {
    4.0
}

impl Default for LayoutConfig {
    fn default() -> Self {
        Self {
            layout_type: LayoutType::Single,
            gap: 4.0,
            sync_crosshair: false,
            sync_time: false,
            sync_price: false,
        }
    }
}

/// Layout type
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum LayoutType {
    /// Single chart
    Single,
    /// 2x2 grid
    Grid2x2,
    /// 3x3 grid
    Grid3x3,
    /// 1 large + 3 small (2x2 with one spanning)
    OnePlusThree,
    /// Vertical stack (2 rows)
    Vertical2,
    /// Vertical stack (3 rows)
    Vertical3,
    /// Horizontal (2 columns)
    Horizontal2,
    /// Horizontal (3 columns)
    Horizontal3,
    /// Custom layout
    Custom { rows: usize, cols: usize },
}

impl LayoutConfig {
    pub fn single() -> Self {
        Self::default()
    }

    pub fn grid_2x2() -> Self {
        Self {
            layout_type: LayoutType::Grid2x2,
            ..Default::default()
        }
    }

    pub fn grid_3x3() -> Self {
        Self {
            layout_type: LayoutType::Grid3x3,
            ..Default::default()
        }
    }

    pub fn one_plus_three() -> Self {
        Self {
            layout_type: LayoutType::OnePlusThree,
            ..Default::default()
        }
    }

    pub fn vertical(count: usize) -> Self {
        Self {
            layout_type: match count {
                2 => LayoutType::Vertical2,
                3 => LayoutType::Vertical3,
                _ => LayoutType::Custom {
                    rows: count,
                    cols: 1,
                },
            },
            ..Default::default()
        }
    }

    pub fn horizontal(count: usize) -> Self {
        Self {
            layout_type: match count {
                2 => LayoutType::Horizontal2,
                3 => LayoutType::Horizontal3,
                _ => LayoutType::Custom {
                    rows: 1,
                    cols: count,
                },
            },
            ..Default::default()
        }
    }

    pub fn custom(rows: usize, cols: usize) -> Self {
        Self {
            layout_type: LayoutType::Custom { rows, cols },
            ..Default::default()
        }
    }

    pub fn with_sync(mut self) -> Self {
        self.sync_crosshair = true;
        self.sync_time = true;
        self.sync_price = true;
        self
    }

    pub fn with_gap(mut self, gap: f64) -> Self {
        self.gap = gap;
        self
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = ChartConfig::default();
        assert_eq!(config.width, 800);
        assert_eq!(config.height, 600);
        assert_eq!(config.series.series_type, SeriesType::Candlestick);
    }

    #[test]
    fn test_series_config() {
        let candle = SeriesConfig::candlestick();
        assert_eq!(candle.series_type, SeriesType::Candlestick);

        let line = SeriesConfig::line().with_color("#ff0000");
        assert_eq!(line.series_type, SeriesType::Line);
        assert_eq!(line.style.color, Some("#ff0000".into()));
    }

    #[test]
    fn test_indicator_overlay() {
        let sma = Indicator::sma("sma_20", 20, "#2196F3");
        assert_eq!(sma.name, "SMA 20");
        assert!(sma.placement.is_overlay());
    }

    #[test]
    fn test_indicator_subpane() {
        let rsi = Indicator::rsi("rsi_14", 14);
        assert!(rsi.placement.is_subpane());

        let macd = Indicator::macd("macd", 12, 26, 9);
        assert!(macd.placement.is_subpane());
        assert_eq!(macd.vector_count(), 3); // MACD line, Signal line, Histogram
    }

    #[test]
    fn test_primitive_config() {
        let tl = PrimitiveConfig::trend_line((10.0, 100.0), (50.0, 120.0));
        assert_eq!(tl.type_id, "trend_line");
        assert_eq!(tl.points.len(), 2);

        let fib =
            PrimitiveConfig::fib_retracement((10.0, 90.0), (40.0, 130.0)).with_color("#FFD700");
        assert_eq!(fib.color, "#FFD700");
    }

    #[test]
    fn test_signal_config() {
        let buy = SignalConfig::buy(25, 105.0);
        assert_eq!(buy.signal_type, SignalType::Buy);
        assert_eq!(buy.bar_index, 25);

        let custom = SignalConfig::custom(50, 110.0, "Alert").with_color("#9C27B0");
        assert_eq!(custom.label, Some("Alert".into()));
    }

    #[test]
    fn test_layout_config() {
        let grid = LayoutConfig::grid_2x2().with_sync();
        assert!(matches!(grid.layout_type, LayoutType::Grid2x2));
        assert!(grid.sync_crosshair);
    }

    #[test]
    fn test_full_config() {
        let config = ChartConfig {
            width: 1200,
            height: 800,
            dpr: 2.0,
            theme: ThemeConfig::dark(),
            series: SeriesConfig::candlestick(),
            indicators: vec![
                // Overlays
                Indicator::sma("sma_20", 20, "#2196F3"),
                Indicator::ema("ema_50", 50, "#FF9800"),
                Indicator::bollinger("bb_20", 20),
                // Subpanes
                Indicator::rsi("rsi_14", 14),
                Indicator::macd("macd", 12, 26, 9),
                Indicator::volume("vol"),
            ],
            primitives: vec![
                PrimitiveConfig::trend_line((10.0, 100.0), (50.0, 120.0)),
                PrimitiveConfig::fib_retracement((20.0, 90.0), (40.0, 130.0)),
                PrimitiveConfig::horizontal_line(110.0),
            ],
            signals: vec![
                SignalConfig::buy(25, 105.0),
                SignalConfig::sell(45, 125.0),
                SignalConfig::take_profit(60, 135.0),
            ],
            layout: LayoutConfig::single(),
        };

        assert_eq!(config.indicators.len(), 6);
        assert_eq!(config.primitives.len(), 3);
        assert_eq!(config.signals.len(), 3);
    }
}
