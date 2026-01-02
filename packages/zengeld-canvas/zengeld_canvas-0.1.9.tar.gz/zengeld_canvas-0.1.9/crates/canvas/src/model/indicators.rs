//! Indicator System - comprehensive indicator and strategy visualization
//!
//! This module provides a complete system for rendering externally-computed indicators,
//! signals, and strategies. Computation happens in Python/JS/Rust - this library only renders.
//!
//! # Features
//!
//! - **Multi-vector indicators**: Bollinger (3 lines), MACD (3 components), Ichimoku (5 lines)
//! - **Multiple visualization types**: Lines, areas, histograms, bands, emojis, primitives
//! - **Strategies**: Composite objects with indicators, signals, and primitives
//! - **Presets + Constructor**: Ready-made configurations + full customization
//!
//! # Example
//!
//! ```rust
//! use zengeld_canvas::model::indicators::*;
//!
//! // Simple moving average
//! let sma = Indicator::line("sma_20", "SMA 20", "#2196F3")
//!     .values(vec![100.0, 101.0, 102.0]);
//!
//! // Bollinger Bands (multi-vector)
//! let bb = Indicator::bollinger("bb_20", 20);
//! // Later: bb.set_vectors(vec![middle_values, upper_values, lower_values]);
//!
//! // MACD (3 components with different styles)
//! let macd = Indicator::macd("macd_12_26_9", 12, 26, 9);
//! // Later: macd.set_vectors(vec![macd_line, signal_line, histogram]);
//! ```

use serde::{Deserialize, Serialize};

// =============================================================================
// Placement
// =============================================================================

/// Where to place the indicator on the chart
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
#[derive(Default)]
pub enum IndicatorPlacement {
    /// Overlay on main price chart (e.g., MA, Bollinger Bands)
    #[default]
    Overlay,
    /// Overlay at bottom of main chart with own Y scale (e.g., Volume)
    /// height_ratio is the portion of main chart height to use (0.0-1.0)
    OverlayBottom {
        #[serde(default = "default_overlay_bottom_height")]
        height_ratio: f64,
    },
    /// Separate sub-pane below main chart (e.g., RSI, MACD)
    SubPane {
        #[serde(default = "default_height_ratio")]
        height_ratio: f64,
    },
}

fn default_height_ratio() -> f64 {
    0.15
}
fn default_overlay_bottom_height() -> f64 {
    0.2
}

impl IndicatorPlacement {
    pub fn overlay() -> Self {
        Self::Overlay
    }
    pub fn overlay_bottom(height_ratio: f64) -> Self {
        Self::OverlayBottom {
            height_ratio: height_ratio.clamp(0.1, 0.5),
        }
    }
    pub fn subpane(height_ratio: f64) -> Self {
        Self::SubPane {
            height_ratio: height_ratio.clamp(0.05, 0.5),
        }
    }
    pub fn is_overlay(&self) -> bool {
        matches!(self, Self::Overlay)
    }
    pub fn is_overlay_bottom(&self) -> bool {
        matches!(self, Self::OverlayBottom { .. })
    }
    pub fn is_subpane(&self) -> bool {
        matches!(self, Self::SubPane { .. })
    }
    /// Height ratio for SubPane, 0.0 for Overlay
    pub fn height_ratio(&self) -> f64 {
        match self {
            Self::Overlay => 0.0,
            Self::OverlayBottom { height_ratio } => *height_ratio,
            Self::SubPane { height_ratio } => *height_ratio,
        }
    }
}

// =============================================================================
// Y-Axis Range
// =============================================================================

/// Y-axis range configuration
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
#[derive(Default)]
pub enum IndicatorRange {
    /// Auto-scale to fit data
    #[default]
    Auto,
    /// Fixed range (e.g., RSI: 0-100)
    Fixed { min: f64, max: f64 },
    /// Symmetric around zero (e.g., MACD)
    Symmetric,
    /// Same as price (for overlays)
    Price,
}

impl IndicatorRange {
    pub fn auto() -> Self {
        Self::Auto
    }
    pub fn fixed(min: f64, max: f64) -> Self {
        Self::Fixed { min, max }
    }
    pub fn symmetric() -> Self {
        Self::Symmetric
    }
    pub fn price() -> Self {
        Self::Price
    }
}

// =============================================================================
// Reference Level (horizontal lines like overbought/oversold)
// =============================================================================

/// Reference line for sub-pane indicators
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IndicatorLevel {
    pub value: f64,
    pub label: Option<String>,
    pub color: String,
    #[serde(default = "default_level_style")]
    pub style: String,
    #[serde(default = "default_level_width")]
    pub width: f64,
}

fn default_level_style() -> String {
    "dashed".to_string()
}
fn default_level_width() -> f64 {
    1.0
}

impl IndicatorLevel {
    pub fn new(value: f64, color: &str) -> Self {
        Self {
            value,
            label: None,
            color: color.to_string(),
            style: default_level_style(),
            width: default_level_width(),
        }
    }
    pub fn with_label(mut self, label: &str) -> Self {
        self.label = Some(label.to_string());
        self
    }
    pub fn with_width(mut self, width: f64) -> Self {
        self.width = width;
        self
    }
    pub fn solid(mut self) -> Self {
        self.style = "solid".to_string();
        self
    }
    pub fn dotted(mut self) -> Self {
        self.style = "dotted".to_string();
        self
    }
    pub fn dashed(mut self) -> Self {
        self.style = "dashed".to_string();
        self
    }
}

// =============================================================================
// Vector Style - style for each line/component of a multi-vector indicator
// =============================================================================

/// Style for a single vector/component of an indicator
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum VectorStyle {
    /// Line (most common)
    Line {
        color: String,
        #[serde(default = "default_line_width")]
        width: f64,
        #[serde(default)]
        dashed: bool,
    },
    /// Filled area
    Area {
        color: String,
        #[serde(default = "default_fill_alpha")]
        fill_alpha: f64,
        #[serde(default = "default_line_width")]
        line_width: f64,
    },
    /// Histogram bars
    Histogram {
        #[serde(default = "default_up_color")]
        up_color: String,
        #[serde(default = "default_down_color")]
        down_color: String,
        #[serde(default = "default_bar_width_ratio")]
        bar_width_ratio: f64,
    },
    /// Dots/circles
    Dots {
        color: String,
        #[serde(default = "default_dot_radius")]
        radius: f64,
        #[serde(default)]
        filled: bool,
    },
    /// Step line (discrete values)
    Step {
        color: String,
        #[serde(default = "default_line_width")]
        width: f64,
    },
    /// Cloud/fill between this vector and another
    Cloud {
        color_above: String,
        color_below: String,
        #[serde(default = "default_fill_alpha")]
        fill_alpha: f64,
        /// Index of the vector to fill between
        fill_to_vector: usize,
    },
    /// Hidden (computed but not rendered, e.g., intermediate values)
    Hidden,
}

fn default_line_width() -> f64 {
    1.0
}
fn default_fill_alpha() -> f64 {
    0.3
}
fn default_bar_width_ratio() -> f64 {
    0.8
}
fn default_up_color() -> String {
    "#26a69a".to_string()
}
fn default_down_color() -> String {
    "#ef5350".to_string()
}
fn default_dot_radius() -> f64 {
    3.0
}

impl Default for VectorStyle {
    fn default() -> Self {
        Self::Line {
            color: "#2196F3".to_string(),
            width: 1.0,
            dashed: false,
        }
    }
}

impl VectorStyle {
    pub fn line(color: &str, width: f64) -> Self {
        Self::Line {
            color: color.to_string(),
            width,
            dashed: false,
        }
    }
    pub fn dashed(color: &str, width: f64) -> Self {
        Self::Line {
            color: color.to_string(),
            width,
            dashed: true,
        }
    }
    pub fn area(color: &str, fill_alpha: f64) -> Self {
        Self::Area {
            color: color.to_string(),
            fill_alpha,
            line_width: 1.0,
        }
    }
    pub fn histogram() -> Self {
        Self::Histogram {
            up_color: default_up_color(),
            down_color: default_down_color(),
            bar_width_ratio: default_bar_width_ratio(),
        }
    }
    pub fn histogram_colored(up: &str, down: &str) -> Self {
        Self::Histogram {
            up_color: up.to_string(),
            down_color: down.to_string(),
            bar_width_ratio: default_bar_width_ratio(),
        }
    }
    pub fn dots(color: &str, radius: f64) -> Self {
        Self::Dots {
            color: color.to_string(),
            radius,
            filled: true,
        }
    }
    pub fn step(color: &str, width: f64) -> Self {
        Self::Step {
            color: color.to_string(),
            width,
        }
    }
    pub fn cloud(color_above: &str, color_below: &str, fill_to: usize) -> Self {
        Self::Cloud {
            color_above: color_above.to_string(),
            color_below: color_below.to_string(),
            fill_alpha: default_fill_alpha(),
            fill_to_vector: fill_to,
        }
    }
    pub fn hidden() -> Self {
        Self::Hidden
    }

    pub fn primary_color(&self) -> &str {
        match self {
            Self::Line { color, .. } => color,
            Self::Area { color, .. } => color,
            Self::Histogram { up_color, .. } => up_color,
            Self::Dots { color, .. } => color,
            Self::Step { color, .. } => color,
            Self::Cloud { color_above, .. } => color_above,
            Self::Hidden => "#000000",
        }
    }
}

// =============================================================================
// Indicator Vector - a single data series within a multi-vector indicator
// =============================================================================

/// A single vector (data series) within an indicator
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IndicatorVector {
    /// Name of this vector (e.g., "Upper", "Middle", "Lower" for Bollinger)
    pub name: String,
    /// Visual style
    pub style: VectorStyle,
    /// The actual values (one per bar)
    #[serde(default)]
    pub values: Vec<f64>,
    /// Per-bar color direction: true = up (green), false = down (red)
    /// Used for Volume histogram to color bars based on price direction
    #[serde(default)]
    pub directions: Vec<bool>,
    /// Whether to show in legend
    #[serde(default = "default_true")]
    pub show_in_legend: bool,
}

fn default_true() -> bool {
    true
}

impl IndicatorVector {
    pub fn new(name: &str, style: VectorStyle) -> Self {
        Self {
            name: name.to_string(),
            style,
            values: Vec::new(),
            directions: Vec::new(),
            show_in_legend: true,
        }
    }

    pub fn with_values(mut self, values: Vec<f64>) -> Self {
        self.values = values;
        self
    }

    pub fn with_directions(mut self, directions: Vec<bool>) -> Self {
        self.directions = directions;
        self
    }

    pub fn hide_from_legend(mut self) -> Self {
        self.show_in_legend = false;
        self
    }

    pub fn value_at(&self, index: usize) -> Option<f64> {
        self.values.get(index).copied().filter(|v| !v.is_nan())
    }

    pub fn direction_at(&self, index: usize) -> Option<bool> {
        self.directions.get(index).copied()
    }
}

// =============================================================================
// Indicator - the main multi-vector indicator type
// =============================================================================

/// Multi-vector indicator
///
/// Supports single-line indicators (MA, RSI) and multi-line indicators
/// (Bollinger Bands, MACD, Ichimoku).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Indicator {
    /// Unique identifier
    pub id: String,
    /// Display name
    pub name: String,
    /// Placement: overlay or sub-pane
    pub placement: IndicatorPlacement,
    /// Y-axis range
    pub range: IndicatorRange,
    /// Reference levels (horizontal lines)
    #[serde(default)]
    pub levels: Vec<IndicatorLevel>,
    /// Vector components (each with its own style and values)
    #[serde(default)]
    pub vectors: Vec<IndicatorVector>,
    /// Whether visible
    #[serde(default = "default_true")]
    pub visible: bool,
    /// Precision for display
    #[serde(default = "default_precision")]
    pub precision: u8,
}

fn default_precision() -> u8 {
    2
}

impl Indicator {
    /// Create a new empty indicator
    pub fn new(id: &str, name: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            placement: IndicatorPlacement::Overlay,
            range: IndicatorRange::Auto,
            levels: Vec::new(),
            vectors: Vec::new(),
            visible: true,
            precision: 2,
        }
    }

    // =========================================================================
    // Builder Methods
    // =========================================================================

    pub fn placement(mut self, placement: IndicatorPlacement) -> Self {
        self.placement = placement;
        self
    }

    pub fn overlay(mut self) -> Self {
        self.placement = IndicatorPlacement::Overlay;
        self
    }

    pub fn overlay_bottom(mut self, height: f64) -> Self {
        self.placement = IndicatorPlacement::overlay_bottom(height);
        self
    }

    pub fn subpane(mut self, height: f64) -> Self {
        self.placement = IndicatorPlacement::subpane(height);
        self
    }

    pub fn range(mut self, range: IndicatorRange) -> Self {
        self.range = range;
        self
    }

    pub fn fixed_range(mut self, min: f64, max: f64) -> Self {
        self.range = IndicatorRange::fixed(min, max);
        self
    }

    pub fn add_level(mut self, level: IndicatorLevel) -> Self {
        self.levels.push(level);
        self
    }

    pub fn add_vector(mut self, vector: IndicatorVector) -> Self {
        self.vectors.push(vector);
        self
    }

    pub fn precision(mut self, p: u8) -> Self {
        self.precision = p;
        self
    }

    // =========================================================================
    // Single-line convenience (creates one vector)
    // =========================================================================

    /// Create a simple line indicator
    pub fn line(id: &str, name: &str, color: &str) -> Self {
        Self::new(id, name).add_vector(IndicatorVector::new("Value", VectorStyle::line(color, 1.0)))
    }

    /// Set values for single-vector indicator
    pub fn values(mut self, values: Vec<f64>) -> Self {
        if self.vectors.is_empty() {
            self.vectors
                .push(IndicatorVector::new("Value", VectorStyle::default()));
        }
        if let Some(v) = self.vectors.first_mut() {
            v.values = values;
        }
        self
    }

    // =========================================================================
    // Multi-vector setters
    // =========================================================================

    /// Set values for all vectors at once
    ///
    /// `all_values[i]` corresponds to `vectors[i]`
    pub fn set_all_values(&mut self, all_values: Vec<Vec<f64>>) {
        for (i, values) in all_values.into_iter().enumerate() {
            if let Some(vector) = self.vectors.get_mut(i) {
                vector.values = values;
            }
        }
    }

    /// Set values for a specific vector by index
    pub fn set_vector_values(&mut self, index: usize, values: Vec<f64>) {
        if let Some(vector) = self.vectors.get_mut(index) {
            vector.values = values;
        }
    }

    /// Set values for a specific vector by name
    pub fn set_vector_values_by_name(&mut self, name: &str, values: Vec<f64>) {
        if let Some(vector) = self.vectors.iter_mut().find(|v| v.name == name) {
            vector.values = values;
        }
    }

    /// Append a value to each vector (for live updates)
    pub fn push_values(&mut self, values: &[f64]) {
        for (i, &value) in values.iter().enumerate() {
            if let Some(vector) = self.vectors.get_mut(i) {
                vector.values.push(value);
            }
        }
    }

    /// Update last value in each vector (for live bar updates)
    pub fn update_last_values(&mut self, values: &[f64]) {
        for (i, &value) in values.iter().enumerate() {
            if let Some(vector) = self.vectors.get_mut(i) {
                if let Some(last) = vector.values.last_mut() {
                    *last = value;
                } else {
                    vector.values.push(value);
                }
            }
        }
    }

    // =========================================================================
    // Queries
    // =========================================================================

    /// Get number of vectors
    pub fn vector_count(&self) -> usize {
        self.vectors.len()
    }

    /// Get length (number of bars)
    pub fn len(&self) -> usize {
        self.vectors.first().map(|v| v.values.len()).unwrap_or(0)
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.vectors.is_empty()
            || self
                .vectors
                .first()
                .map(|v| v.values.is_empty())
                .unwrap_or(true)
    }

    /// Calculate range across all vectors
    pub fn calculate_range(&self) -> (f64, f64) {
        match &self.range {
            IndicatorRange::Fixed { min, max } => (*min, *max),
            IndicatorRange::Symmetric => {
                let max_abs = self
                    .vectors
                    .iter()
                    .flat_map(|v| v.values.iter())
                    .filter(|v| !v.is_nan() && !v.is_infinite())
                    .map(|v| v.abs())
                    .fold(0.0f64, f64::max);
                (-max_abs, max_abs)
            }
            IndicatorRange::Auto | IndicatorRange::Price => {
                let mut min = f64::INFINITY;
                let mut max = f64::NEG_INFINITY;
                for vector in &self.vectors {
                    for &v in &vector.values {
                        if !v.is_nan() && !v.is_infinite() {
                            min = min.min(v);
                            max = max.max(v);
                        }
                    }
                }
                if min > max {
                    (0.0, 100.0)
                } else {
                    let range = max - min;
                    let padding = range * 0.05;
                    (min - padding, max + padding)
                }
            }
        }
    }
}

// =============================================================================
// Indicator Presets - ready-made multi-vector configurations
// =============================================================================

impl Indicator {
    /// Simple Moving Average
    pub fn sma(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("SMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("SMA", VectorStyle::line(color, 1.0)))
    }

    /// Exponential Moving Average
    pub fn ema(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("EMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("EMA", VectorStyle::line(color, 1.0)))
    }

    /// Bollinger Bands (3 vectors: middle, upper, lower)
    pub fn bollinger(id: &str, period: u32) -> Self {
        Self::new(id, &format!("BB {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Middle",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::line("#2196F380", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Lower",
                VectorStyle::line("#2196F380", 1.0),
            ))
    }

    /// Bollinger Bands with cloud fill
    pub fn bollinger_filled(id: &str, period: u32) -> Self {
        Self::new(id, &format!("BB {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Middle",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::cloud("#2196F320", "#2196F320", 2),
            ))
            .add_vector(
                IndicatorVector::new("Lower", VectorStyle::line("#2196F380", 1.0))
                    .hide_from_legend(),
            )
    }

    /// Keltner Channels (3 vectors)
    pub fn keltner(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Keltner {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Middle",
                VectorStyle::line("#FF9800", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::line("#FF980080", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Lower",
                VectorStyle::line("#FF980080", 1.0),
            ))
    }

    /// Donchian Channels (2 vectors: upper, lower + fill)
    pub fn donchian(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Donchian {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::line("#4CAF50", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Lower",
                VectorStyle::line("#F44336", 1.0),
            ))
    }

    /// RSI (1 vector + levels)
    pub fn rsi(id: &str, period: u32) -> Self {
        Self::new(id, &format!("RSI {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(
                IndicatorLevel::new(70.0, "#ef535060")
                    .solid()
                    .with_width(0.5)
                    .with_label("Overbought"),
            )
            .add_level(
                IndicatorLevel::new(30.0, "#26a69a60")
                    .solid()
                    .with_width(0.5)
                    .with_label("Oversold"),
            )
            .add_level(
                IndicatorLevel::new(50.0, "#787b8640")
                    .solid()
                    .with_width(0.5),
            )
            .add_vector(IndicatorVector::new(
                "RSI",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Stochastic (2 vectors: %K, %D)
    pub fn stochastic(id: &str, k: u32, d: u32) -> Self {
        Self::new(id, &format!("Stoch ({},{})", k, d))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(80.0, "#ef5350"))
            .add_level(IndicatorLevel::new(20.0, "#26a69a"))
            .add_vector(IndicatorVector::new(
                "%K",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "%D",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// MACD (3 vectors: MACD line, Signal line, Histogram)
    pub fn macd(id: &str, fast: u32, slow: u32, signal: u32) -> Self {
        Self::new(id, &format!("MACD ({},{},{})", fast, slow, signal))
            .subpane(0.2)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "MACD",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#FF9800", 1.0),
            ))
            .add_vector(IndicatorVector::new("Histogram", VectorStyle::histogram()))
    }

    /// MACD default (12, 26, 9)
    pub fn macd_default(id: &str) -> Self {
        Self::macd(id, 12, 26, 9)
    }

    /// Volume histogram (overlay at bottom of main chart with own Y scale)
    pub fn volume(id: &str) -> Self {
        Self::new(id, "Volume")
            .overlay_bottom(0.2) // Volume at bottom 20% of main chart
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new("Volume", VectorStyle::histogram()))
    }

    /// Volume as separate subpane
    pub fn volume_pane(id: &str) -> Self {
        Self::new(id, "Volume")
            .subpane(0.15)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new("Volume", VectorStyle::histogram()))
    }

    /// ATR
    pub fn atr(id: &str, period: u32) -> Self {
        Self::new(id, &format!("ATR {}", period))
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "ATR",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// ADX (3 vectors: ADX, +DI, -DI)
    pub fn adx(id: &str, period: u32) -> Self {
        Self::new(id, &format!("ADX {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(25.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "ADX",
                VectorStyle::line("#9C27B0", 2.0),
            ))
            .add_vector(IndicatorVector::new(
                "+DI",
                VectorStyle::line("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "-DI",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    /// CCI
    pub fn cci(id: &str, period: u32) -> Self {
        Self::new(id, &format!("CCI {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(100.0, "#ef5350"))
            .add_level(IndicatorLevel::new(-100.0, "#26a69a"))
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "CCI",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Williams %R
    pub fn williams_r(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Williams %R {}", period))
            .subpane(0.15)
            .fixed_range(-100.0, 0.0)
            .add_level(IndicatorLevel::new(-20.0, "#ef5350"))
            .add_level(IndicatorLevel::new(-80.0, "#26a69a"))
            .add_vector(IndicatorVector::new(
                "%R",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Ichimoku Cloud (5 vectors)
    pub fn ichimoku(id: &str) -> Self {
        Self::new(id, "Ichimoku")
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Tenkan",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Kijun",
                VectorStyle::line("#ef5350", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Senkou A",
                VectorStyle::line("#26a69a80", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Senkou B",
                VectorStyle::cloud("#26a69a20", "#ef535020", 2),
            ))
            .add_vector(IndicatorVector::new(
                "Chikou",
                VectorStyle::line("#9C27B080", 1.0),
            ))
    }

    /// Parabolic SAR (dots)
    pub fn psar(id: &str) -> Self {
        Self::new(id, "Parabolic SAR")
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "SAR",
                VectorStyle::dots("#FF9800", 2.0),
            ))
    }

    /// Supertrend (2 vectors: line + direction for coloring)
    pub fn supertrend(id: &str, period: u32, multiplier: f64) -> Self {
        Self::new(id, &format!("Supertrend ({}, {})", period, multiplier))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Supertrend",
                VectorStyle::line("#2196F3", 2.0),
            ))
            // Direction vector: 1 = bullish (green), -1 = bearish (red)
            .add_vector(IndicatorVector::new("Direction", VectorStyle::hidden()).hide_from_legend())
    }

    /// VWAP
    pub fn vwap(id: &str) -> Self {
        Self::new(id, "VWAP")
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "VWAP",
                VectorStyle::line("#FF9800", 1.5),
            ))
    }

    /// Pivot Points (7 vectors: PP, R1, R2, R3, S1, S2, S3)
    pub fn pivot_points(id: &str) -> Self {
        Self::new(id, "Pivot Points")
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "PP",
                VectorStyle::line("#787b86", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "R1",
                VectorStyle::dashed("#ef5350", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "R2",
                VectorStyle::dashed("#ef5350", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "R3",
                VectorStyle::dashed("#ef5350", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "S1",
                VectorStyle::dashed("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "S2",
                VectorStyle::dashed("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "S3",
                VectorStyle::dashed("#26a69a", 1.0),
            ))
    }

    // =========================================================================
    // Additional Moving Averages
    // =========================================================================

    /// Weighted Moving Average
    pub fn wma(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("WMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("WMA", VectorStyle::line(color, 1.0)))
    }

    /// Hull Moving Average
    pub fn hma(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("HMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("HMA", VectorStyle::line(color, 1.5)))
    }

    /// Double Exponential Moving Average
    pub fn dema(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("DEMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("DEMA", VectorStyle::line(color, 1.0)))
    }

    /// Triple Exponential Moving Average
    pub fn tema(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("TEMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("TEMA", VectorStyle::line(color, 1.0)))
    }

    /// Kaufman's Adaptive Moving Average
    pub fn kama(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("KAMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("KAMA", VectorStyle::line(color, 1.5)))
    }

    /// Triangular Moving Average
    pub fn trima(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("TRIMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("TRIMA", VectorStyle::line(color, 1.0)))
    }

    /// Zero-Lag EMA
    pub fn zlema(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("ZLEMA {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("ZLEMA", VectorStyle::line(color, 1.0)))
    }

    /// McGinley Dynamic
    pub fn mcginley(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("McGinley {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new("MD", VectorStyle::line(color, 1.5)))
    }

    // =========================================================================
    // Momentum Indicators
    // =========================================================================

    /// Momentum
    pub fn momentum(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Momentum {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Mom",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Rate of Change (ROC)
    pub fn roc(id: &str, period: u32) -> Self {
        Self::new(id, &format!("ROC {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "ROC",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// True Strength Index (TSI)
    pub fn tsi(id: &str, r: u32, s: u32) -> Self {
        Self::new(id, &format!("TSI ({},{})", r, s))
            .subpane(0.15)
            .fixed_range(-100.0, 100.0)
            .add_level(IndicatorLevel::new(25.0, "#ef5350"))
            .add_level(IndicatorLevel::new(-25.0, "#26a69a"))
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "TSI",
                VectorStyle::line("#9C27B0", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Ultimate Oscillator
    pub fn ultimate_oscillator(id: &str) -> Self {
        Self::new(id, "Ultimate Oscillator")
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(70.0, "#ef5350"))
            .add_level(IndicatorLevel::new(30.0, "#26a69a"))
            .add_level(IndicatorLevel::new(50.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "UO",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Awesome Oscillator
    pub fn awesome_oscillator(id: &str) -> Self {
        Self::new(id, "Awesome Oscillator")
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new("AO", VectorStyle::histogram()))
    }

    /// Accelerator Oscillator
    pub fn accelerator_oscillator(id: &str) -> Self {
        Self::new(id, "Accelerator Oscillator")
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new("AC", VectorStyle::histogram()))
    }

    /// Chande Momentum Oscillator (CMO)
    pub fn cmo(id: &str, period: u32) -> Self {
        Self::new(id, &format!("CMO {}", period))
            .subpane(0.15)
            .fixed_range(-100.0, 100.0)
            .add_level(IndicatorLevel::new(50.0, "#ef5350"))
            .add_level(IndicatorLevel::new(-50.0, "#26a69a"))
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "CMO",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Detrended Price Oscillator (DPO)
    pub fn dpo(id: &str, period: u32) -> Self {
        Self::new(id, &format!("DPO {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "DPO",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Know Sure Thing (KST)
    pub fn kst(id: &str) -> Self {
        Self::new(id, "KST")
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "KST",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Relative Vigor Index (RVI)
    pub fn rvi(id: &str, period: u32) -> Self {
        Self::new(id, &format!("RVI {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "RVI",
                VectorStyle::line("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    /// Stochastic RSI
    pub fn stoch_rsi(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Stoch RSI {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(80.0, "#ef5350"))
            .add_level(IndicatorLevel::new(20.0, "#26a69a"))
            .add_vector(IndicatorVector::new(
                "%K",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "%D",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Money Flow Index (MFI)
    pub fn mfi(id: &str, period: u32) -> Self {
        Self::new(id, &format!("MFI {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(80.0, "#ef5350").with_label("Overbought"))
            .add_level(IndicatorLevel::new(20.0, "#26a69a").with_label("Oversold"))
            .add_vector(IndicatorVector::new(
                "MFI",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    // =========================================================================
    // Volume Indicators
    // =========================================================================

    /// On-Balance Volume (OBV)
    pub fn obv(id: &str) -> Self {
        Self::new(id, "OBV")
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "OBV",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Accumulation/Distribution Line
    pub fn ad_line(id: &str) -> Self {
        Self::new(id, "A/D Line")
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "A/D",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Chaikin Money Flow (CMF)
    pub fn cmf(id: &str, period: u32) -> Self {
        Self::new(id, &format!("CMF {}", period))
            .subpane(0.15)
            .fixed_range(-1.0, 1.0)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "CMF",
                VectorStyle::line("#26a69a", 1.0),
            ))
    }

    /// Chaikin Oscillator
    pub fn chaikin_oscillator(id: &str) -> Self {
        Self::new(id, "Chaikin Oscillator")
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "CO",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Volume-Price Trend (VPT)
    pub fn vpt(id: &str) -> Self {
        Self::new(id, "VPT")
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "VPT",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Force Index
    pub fn force_index(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Force {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Force",
                VectorStyle::line("#E91E63", 1.0),
            ))
    }

    /// Ease of Movement (EOM)
    pub fn eom(id: &str, period: u32) -> Self {
        Self::new(id, &format!("EOM {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "EOM",
                VectorStyle::line("#4CAF50", 1.0),
            ))
    }

    /// Negative Volume Index (NVI)
    pub fn nvi(id: &str) -> Self {
        Self::new(id, "NVI")
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "NVI",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    /// Positive Volume Index (PVI)
    pub fn pvi(id: &str) -> Self {
        Self::new(id, "PVI")
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "PVI",
                VectorStyle::line("#26a69a", 1.0),
            ))
    }

    // =========================================================================
    // Volatility Indicators
    // =========================================================================

    /// Standard Deviation
    pub fn stddev(id: &str, period: u32) -> Self {
        Self::new(id, &format!("StdDev {}", period))
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "StdDev",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Historical Volatility
    pub fn historical_volatility(id: &str, period: u32) -> Self {
        Self::new(id, &format!("HV {}", period))
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "HV",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Choppiness Index
    pub fn choppiness(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Choppiness {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(61.8, "#ef5350").with_label("Choppy"))
            .add_level(IndicatorLevel::new(38.2, "#26a69a").with_label("Trending"))
            .add_vector(IndicatorVector::new(
                "CHOP",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Mass Index
    pub fn mass_index(id: &str) -> Self {
        Self::new(id, "Mass Index")
            .subpane(0.15)
            .range(IndicatorRange::Auto)
            .add_level(IndicatorLevel::new(27.0, "#ef5350").with_label("Bulge"))
            .add_level(IndicatorLevel::new(26.5, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Mass",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Ulcer Index
    pub fn ulcer_index(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Ulcer {}", period))
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new(
                "UI",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    // =========================================================================
    // Trend Indicators
    // =========================================================================

    /// Aroon (2 vectors: Up, Down)
    pub fn aroon(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Aroon {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(70.0, "#787b86").dotted())
            .add_level(IndicatorLevel::new(30.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Up",
                VectorStyle::line("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Down",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    /// Aroon Oscillator
    pub fn aroon_oscillator(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Aroon Osc {}", period))
            .subpane(0.15)
            .fixed_range(-100.0, 100.0)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "AO",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Vortex Indicator (2 vectors: VI+, VI-)
    pub fn vortex(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Vortex {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Auto)
            .add_level(IndicatorLevel::new(1.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "VI+",
                VectorStyle::line("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "VI-",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    /// TRIX
    pub fn trix(id: &str, period: u32) -> Self {
        Self::new(id, &format!("TRIX {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "TRIX",
                VectorStyle::line("#9C27B0", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Linear Regression Line
    pub fn linear_regression(id: &str, period: u32, color: &str) -> Self {
        Self::new(id, &format!("LinReg {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "LinReg",
                VectorStyle::line(color, 1.5),
            ))
    }

    /// Linear Regression Slope
    pub fn linear_regression_slope(id: &str, period: u32) -> Self {
        Self::new(id, &format!("LinReg Slope {}", period))
            .subpane(0.12)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Slope",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Chande Kroll Stop (3 vectors: stop_long, stop_short, atr_based)
    pub fn chande_kroll_stop(id: &str) -> Self {
        Self::new(id, "Chande Kroll Stop")
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Stop Long",
                VectorStyle::dashed("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Stop Short",
                VectorStyle::dashed("#ef5350", 1.0),
            ))
    }

    /// ZigZag
    pub fn zigzag(id: &str, deviation: f64) -> Self {
        Self::new(id, &format!("ZigZag {}%", deviation))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "ZigZag",
                VectorStyle::line("#FF9800", 2.0),
            ))
    }

    // =========================================================================
    // Band Indicators
    // =========================================================================

    /// Envelopes (3 vectors: middle, upper, lower)
    pub fn envelopes(id: &str, period: u32, percent: f64) -> Self {
        Self::new(id, &format!("Env ({}, {}%)", period, percent))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Middle",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::dashed("#2196F380", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Lower",
                VectorStyle::dashed("#2196F380", 1.0),
            ))
    }

    /// Price Channels (2 vectors)
    pub fn price_channel(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Price Ch {}", period))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::line("#26a69a", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Lower",
                VectorStyle::line("#ef5350", 1.0),
            ))
    }

    /// Average True Range Bands
    pub fn atr_bands(id: &str, period: u32, multiplier: f64) -> Self {
        Self::new(id, &format!("ATR Bands ({}, {})", period, multiplier))
            .overlay()
            .range(IndicatorRange::Price)
            .add_vector(IndicatorVector::new(
                "Middle",
                VectorStyle::line("#FF9800", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Upper",
                VectorStyle::line("#FF980080", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Lower",
                VectorStyle::line("#FF980080", 1.0),
            ))
    }

    // =========================================================================
    // Specialized Indicators
    // =========================================================================

    /// Elder-Ray (2 vectors: Bull Power, Bear Power)
    pub fn elder_ray(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Elder-Ray {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Bull",
                VectorStyle::histogram_colored("#26a69a", "#26a69a80"),
            ))
            .add_vector(IndicatorVector::new(
                "Bear",
                VectorStyle::histogram_colored("#ef535080", "#ef5350"),
            ))
    }

    /// Balance of Power
    pub fn balance_of_power(id: &str) -> Self {
        Self::new(id, "Balance of Power")
            .subpane(0.15)
            .fixed_range(-1.0, 1.0)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new("BoP", VectorStyle::histogram()))
    }

    /// Market Facilitation Index
    pub fn market_facilitation(id: &str) -> Self {
        Self::new(id, "Market Facilitation")
            .subpane(0.12)
            .range(IndicatorRange::Auto)
            .add_vector(IndicatorVector::new("MFI", VectorStyle::histogram()))
    }

    /// Connors RSI (3 vectors: RSI, UpDown, ROC)
    pub fn connors_rsi(id: &str) -> Self {
        Self::new(id, "Connors RSI")
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(90.0, "#ef5350"))
            .add_level(IndicatorLevel::new(10.0, "#26a69a"))
            .add_level(IndicatorLevel::new(50.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "CRSI",
                VectorStyle::line("#9C27B0", 1.5),
            ))
    }

    /// Coppock Curve
    pub fn coppock_curve(id: &str) -> Self {
        Self::new(id, "Coppock Curve")
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Coppock",
                VectorStyle::line("#2196F3", 1.5),
            ))
    }

    /// Fisher Transform
    pub fn fisher_transform(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Fisher {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "Fisher",
                VectorStyle::line("#E91E63", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#9C27B0", 1.0),
            ))
    }

    /// Relative Volatility Index (RVI)
    pub fn relative_volatility_index(id: &str, period: u32) -> Self {
        Self::new(id, &format!("RVI {}", period))
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(60.0, "#787b86").dotted())
            .add_level(IndicatorLevel::new(40.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "RVI",
                VectorStyle::line("#26a69a", 1.0),
            ))
    }

    /// SMI Ergodic (2 vectors)
    pub fn smi_ergodic(id: &str) -> Self {
        Self::new(id, "SMI Ergodic")
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "SMI",
                VectorStyle::line("#2196F3", 1.0),
            ))
            .add_vector(IndicatorVector::new(
                "Signal",
                VectorStyle::line("#FF9800", 1.0),
            ))
    }

    /// Schaff Trend Cycle
    pub fn schaff_trend_cycle(id: &str) -> Self {
        Self::new(id, "Schaff Trend Cycle")
            .subpane(0.15)
            .fixed_range(0.0, 100.0)
            .add_level(IndicatorLevel::new(75.0, "#ef5350"))
            .add_level(IndicatorLevel::new(25.0, "#26a69a"))
            .add_vector(IndicatorVector::new(
                "STC",
                VectorStyle::line("#9C27B0", 1.5),
            ))
    }

    /// Pretty Good Oscillator (PGO)
    pub fn pgo(id: &str, period: u32) -> Self {
        Self::new(id, &format!("PGO {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(3.0, "#ef5350"))
            .add_level(IndicatorLevel::new(-3.0, "#26a69a"))
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new(
                "PGO",
                VectorStyle::line("#2196F3", 1.0),
            ))
    }

    /// Qstick
    pub fn qstick(id: &str, period: u32) -> Self {
        Self::new(id, &format!("Qstick {}", period))
            .subpane(0.15)
            .range(IndicatorRange::Symmetric)
            .add_level(IndicatorLevel::new(0.0, "#787b86").dotted())
            .add_vector(IndicatorVector::new("Qstick", VectorStyle::histogram()))
    }
}

// =============================================================================
// Signal - visual markers for trading signals
// =============================================================================

/// Type of signal visualization
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum SignalVisual {
    /// Arrow marker
    Arrow {
        direction: ArrowDirection,
        color: String,
        #[serde(default = "default_arrow_size")]
        size: f64,
    },
    /// Emoji/icon
    Emoji {
        emoji: String,
        #[serde(default = "default_emoji_size")]
        size: f64,
    },
    /// Simple dot
    Dot {
        color: String,
        #[serde(default = "default_dot_radius")]
        radius: f64,
    },
    /// Label/text
    Label {
        text: String,
        color: String,
        background: Option<String>,
    },
    /// Flag marker
    Flag {
        color: String,
        label: Option<String>,
    },
    /// Primitive reference (Fibonacci, trend line, etc.)
    Primitive {
        /// Primitive type ID from registry
        primitive_type: String,
        /// Points as [(bar, price), ...]
        points: Vec<(f64, f64)>,
        /// Override color
        color: Option<String>,
    },
}

fn default_arrow_size() -> f64 {
    12.0
}
fn default_emoji_size() -> f64 {
    16.0
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ArrowDirection {
    Up,
    Down,
    Left,
    Right,
}

impl SignalVisual {
    pub fn arrow_up(color: &str) -> Self {
        Self::Arrow {
            direction: ArrowDirection::Up,
            color: color.to_string(),
            size: default_arrow_size(),
        }
    }
    pub fn arrow_down(color: &str) -> Self {
        Self::Arrow {
            direction: ArrowDirection::Down,
            color: color.to_string(),
            size: default_arrow_size(),
        }
    }
    pub fn emoji(emoji: &str) -> Self {
        Self::Emoji {
            emoji: emoji.to_string(),
            size: default_emoji_size(),
        }
    }
    pub fn dot(color: &str, radius: f64) -> Self {
        Self::Dot {
            color: color.to_string(),
            radius,
        }
    }
    pub fn label(text: &str, color: &str) -> Self {
        Self::Label {
            text: text.to_string(),
            color: color.to_string(),
            background: None,
        }
    }
    pub fn flag(color: &str) -> Self {
        Self::Flag {
            color: color.to_string(),
            label: None,
        }
    }
    pub fn fib_retracement(points: Vec<(f64, f64)>, color: Option<&str>) -> Self {
        Self::Primitive {
            primitive_type: "fib_retracement".to_string(),
            points,
            color: color.map(|c| c.to_string()),
        }
    }
    pub fn trend_line(points: Vec<(f64, f64)>, color: Option<&str>) -> Self {
        Self::Primitive {
            primitive_type: "trend_line".to_string(),
            points,
            color: color.map(|c| c.to_string()),
        }
    }
    pub fn horizontal_line(bar: f64, price: f64, color: Option<&str>) -> Self {
        Self::Primitive {
            primitive_type: "horizontal_line".to_string(),
            points: vec![(bar, price)],
            color: color.map(|c| c.to_string()),
        }
    }
}

/// A single signal on the chart
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Signal {
    /// Unique ID (auto-generated if not provided)
    #[serde(default)]
    pub id: u64,
    /// Bar index
    pub bar: f64,
    /// Price level
    pub price: f64,
    /// Signal type (for filtering)
    #[serde(default)]
    pub signal_type: String,
    /// Visual representation
    pub visual: SignalVisual,
    /// Tooltip text
    pub tooltip: Option<String>,
    /// Whether visible
    #[serde(default = "default_true")]
    pub visible: bool,
}

impl Signal {
    pub fn new(bar: f64, price: f64, visual: SignalVisual) -> Self {
        Self {
            id: 0,
            bar,
            price,
            signal_type: String::new(),
            visual,
            tooltip: None,
            visible: true,
        }
    }

    pub fn with_id(mut self, id: u64) -> Self {
        self.id = id;
        self
    }
    pub fn with_type(mut self, t: &str) -> Self {
        self.signal_type = t.to_string();
        self
    }
    pub fn with_tooltip(mut self, t: &str) -> Self {
        self.tooltip = Some(t.to_string());
        self
    }

    // Convenience constructors
    pub fn buy(bar: f64, price: f64) -> Self {
        Self::new(bar, price, SignalVisual::arrow_up("#26a69a")).with_type("buy")
    }
    pub fn sell(bar: f64, price: f64) -> Self {
        Self::new(bar, price, SignalVisual::arrow_down("#ef5350")).with_type("sell")
    }
    pub fn entry(bar: f64, price: f64) -> Self {
        Self::new(bar, price, SignalVisual::emoji("🚀")).with_type("entry")
    }
    pub fn exit(bar: f64, price: f64) -> Self {
        Self::new(bar, price, SignalVisual::emoji("🏁")).with_type("exit")
    }
    pub fn take_profit(bar: f64, price: f64) -> Self {
        Self::new(bar, price, SignalVisual::flag("#26a69a")).with_type("tp")
    }
    pub fn stop_loss(bar: f64, price: f64) -> Self {
        Self::new(bar, price, SignalVisual::flag("#ef5350")).with_type("sl")
    }
}

// =============================================================================
// Strategy - composite object with indicators, signals, and primitives
// =============================================================================

/// A complete trading strategy visualization
///
/// Combines indicators, signals, and primitives into a single manageable unit.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Strategy {
    /// Unique identifier
    pub id: String,
    /// Display name
    pub name: String,
    /// Description
    #[serde(default)]
    pub description: String,
    /// Indicators used by this strategy
    #[serde(default)]
    pub indicators: Vec<Indicator>,
    /// Signals generated by this strategy
    #[serde(default)]
    pub signals: Vec<Signal>,
    /// Primitive drawings (Fibonacci, trend lines, etc.)
    #[serde(default)]
    pub primitives: Vec<StrategyPrimitive>,
    /// Whether visible
    #[serde(default = "default_true")]
    pub visible: bool,
    /// Color theme for this strategy
    #[serde(default)]
    pub theme: Option<StrategyTheme>,
}

/// A primitive drawing within a strategy
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StrategyPrimitive {
    /// Primitive type ID from registry
    pub primitive_type: String,
    /// Points as [(bar, price), ...]
    pub points: Vec<(f64, f64)>,
    /// Override color
    pub color: Option<String>,
    /// Whether visible
    #[serde(default = "default_true")]
    pub visible: bool,
}

impl StrategyPrimitive {
    pub fn new(primitive_type: &str, points: Vec<(f64, f64)>) -> Self {
        Self {
            primitive_type: primitive_type.to_string(),
            points,
            color: None,
            visible: true,
        }
    }

    pub fn with_color(mut self, color: &str) -> Self {
        self.color = Some(color.to_string());
        self
    }

    // Convenience constructors
    pub fn trend_line(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new("trend_line", vec![(bar1, price1), (bar2, price2)])
    }

    pub fn horizontal_line(bar: f64, price: f64) -> Self {
        Self::new("horizontal_line", vec![(bar, price)])
    }

    pub fn fib_retracement(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new("fib_retracement", vec![(bar1, price1), (bar2, price2)])
    }

    pub fn fib_extension(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        bar3: f64,
        price3: f64,
    ) -> Self {
        Self::new(
            "fib_extension",
            vec![(bar1, price1), (bar2, price2), (bar3, price3)],
        )
    }

    pub fn rectangle(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new("rectangle", vec![(bar1, price1), (bar2, price2)])
    }
}

/// Color theme for a strategy
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StrategyTheme {
    pub primary: String,
    pub secondary: String,
    pub buy: String,
    pub sell: String,
    pub profit: String,
    pub loss: String,
}

impl Default for StrategyTheme {
    fn default() -> Self {
        Self {
            primary: "#2196F3".to_string(),
            secondary: "#FF9800".to_string(),
            buy: "#26a69a".to_string(),
            sell: "#ef5350".to_string(),
            profit: "#26a69a".to_string(),
            loss: "#ef5350".to_string(),
        }
    }
}

impl Strategy {
    pub fn new(id: &str, name: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            description: String::new(),
            indicators: Vec::new(),
            signals: Vec::new(),
            primitives: Vec::new(),
            visible: true,
            theme: None,
        }
    }

    pub fn with_description(mut self, desc: &str) -> Self {
        self.description = desc.to_string();
        self
    }

    pub fn with_theme(mut self, theme: StrategyTheme) -> Self {
        self.theme = Some(theme);
        self
    }

    pub fn add_indicator(mut self, indicator: Indicator) -> Self {
        self.indicators.push(indicator);
        self
    }

    pub fn add_signal(mut self, signal: Signal) -> Self {
        self.signals.push(signal);
        self
    }

    pub fn add_primitive(mut self, primitive: StrategyPrimitive) -> Self {
        self.primitives.push(primitive);
        self
    }

    /// Add multiple signals at once
    pub fn add_signals(mut self, signals: impl IntoIterator<Item = Signal>) -> Self {
        self.signals.extend(signals);
        self
    }

    /// Clear all signals
    pub fn clear_signals(&mut self) {
        self.signals.clear();
    }

    /// Set visibility
    pub fn set_visible(&mut self, visible: bool) {
        self.visible = visible;
        for indicator in &mut self.indicators {
            indicator.visible = visible;
        }
        for signal in &mut self.signals {
            signal.visible = visible;
        }
        for primitive in &mut self.primitives {
            primitive.visible = visible;
        }
    }
}

// =============================================================================
// Strategy Presets
// =============================================================================

impl Strategy {
    /// Moving Average Crossover strategy template
    pub fn ma_crossover(id: &str, fast_period: u32, slow_period: u32) -> Self {
        Self::new(id, &format!("MA Cross ({}/{})", fast_period, slow_period))
            .with_description("Buy when fast MA crosses above slow MA, sell when below")
            .add_indicator(Indicator::sma(
                &format!("{}_fast", id),
                fast_period,
                "#26a69a",
            ))
            .add_indicator(Indicator::sma(
                &format!("{}_slow", id),
                slow_period,
                "#ef5350",
            ))
    }

    /// RSI Overbought/Oversold strategy template
    pub fn rsi_strategy(id: &str, period: u32) -> Self {
        Self::new(id, &format!("RSI Strategy ({})", period))
            .with_description("Signals on overbought/oversold RSI levels")
            .add_indicator(Indicator::rsi(&format!("{}_rsi", id), period))
    }

    /// Bollinger Bands Squeeze strategy template
    pub fn bb_squeeze(id: &str, period: u32) -> Self {
        Self::new(id, &format!("BB Squeeze ({})", period))
            .with_description("Trade breakouts from Bollinger Band squeezes")
            .add_indicator(Indicator::bollinger(&format!("{}_bb", id), period))
    }

    /// MACD strategy template
    pub fn macd_strategy(id: &str) -> Self {
        Self::new(id, "MACD Strategy")
            .with_description("Trade MACD line crossovers and histogram divergence")
            .add_indicator(Indicator::macd_default(&format!("{}_macd", id)))
    }
}

// =============================================================================
// Legacy compatibility aliases
// =============================================================================

/// Legacy alias for Indicator
pub type IndicatorSeries = Indicator;

/// Legacy alias for VectorStyle
pub type IndicatorStyle = VectorStyle;

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_indicator() {
        let sma = Indicator::sma("sma_20", 20, "#2196F3").values(vec![100.0, 101.0, 102.0]);

        assert_eq!(sma.id, "sma_20");
        assert!(sma.placement.is_overlay());
        assert_eq!(sma.vector_count(), 1);
        assert_eq!(sma.len(), 3);
    }

    #[test]
    fn test_multi_vector_indicator() {
        let bb = Indicator::bollinger("bb_20", 20);
        assert_eq!(bb.vector_count(), 3);

        let macd = Indicator::macd_default("macd");
        assert_eq!(macd.vector_count(), 3);

        let ichimoku = Indicator::ichimoku("ichimoku");
        assert_eq!(ichimoku.vector_count(), 5);
    }

    #[test]
    fn test_signal_types() {
        let buy = Signal::buy(10.0, 100.0);
        assert_eq!(buy.signal_type, "buy");

        let emoji = Signal::new(10.0, 100.0, SignalVisual::emoji("🎯"));
        assert!(matches!(emoji.visual, SignalVisual::Emoji { .. }));
    }

    #[test]
    fn test_strategy() {
        let strategy = Strategy::ma_crossover("test", 10, 20)
            .add_signal(Signal::buy(50.0, 100.0))
            .add_primitive(StrategyPrimitive::trend_line(0.0, 90.0, 100.0, 110.0));

        assert_eq!(strategy.indicators.len(), 2);
        assert_eq!(strategy.signals.len(), 1);
        assert_eq!(strategy.primitives.len(), 1);
    }

    #[test]
    fn test_set_all_values() {
        let mut bb = Indicator::bollinger("bb", 20);
        bb.set_all_values(vec![
            vec![100.0, 101.0, 102.0], // middle
            vec![110.0, 111.0, 112.0], // upper
            vec![90.0, 91.0, 92.0],    // lower
        ]);

        assert_eq!(bb.vectors[0].values, vec![100.0, 101.0, 102.0]);
        assert_eq!(bb.vectors[1].values, vec![110.0, 111.0, 112.0]);
        assert_eq!(bb.vectors[2].values, vec![90.0, 91.0, 92.0]);
    }

    #[test]
    fn test_json_roundtrip() {
        let indicator = Indicator::macd_default("test");
        let json = serde_json::to_string(&indicator).unwrap();
        let parsed: Indicator = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.id, "test");
        assert_eq!(parsed.vector_count(), 3);
    }
}
