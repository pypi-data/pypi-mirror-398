//! Global Chart Configuration System
//!
//! Provides a unified configuration system for all chart rendering elements.
//! This allows full customization of colors, fonts, sizes, and styling
//! for headless/SVG rendering without UI dependencies.

// =============================================================================
// Color Configuration
// =============================================================================

/// RGBA color with 0.0-1.0 components
#[derive(Clone, Debug, PartialEq)]
pub struct Color {
    pub r: f64,
    pub g: f64,
    pub b: f64,
    pub a: f64,
}

impl Color {
    pub const fn rgba(r: f64, g: f64, b: f64, a: f64) -> Self {
        Self { r, g, b, a }
    }

    pub const fn rgb(r: f64, g: f64, b: f64) -> Self {
        Self { r, g, b, a: 1.0 }
    }

    /// Parse hex color string (#RGB, #RGBA, #RRGGBB, #RRGGBBAA)
    pub fn from_hex(hex: &str) -> Option<Self> {
        let hex = hex.trim_start_matches('#');
        match hex.len() {
            3 => {
                let r = u8::from_str_radix(&hex[0..1], 16).ok()? as f64 / 15.0;
                let g = u8::from_str_radix(&hex[1..2], 16).ok()? as f64 / 15.0;
                let b = u8::from_str_radix(&hex[2..3], 16).ok()? as f64 / 15.0;
                Some(Self::rgb(r, g, b))
            }
            4 => {
                let r = u8::from_str_radix(&hex[0..1], 16).ok()? as f64 / 15.0;
                let g = u8::from_str_radix(&hex[1..2], 16).ok()? as f64 / 15.0;
                let b = u8::from_str_radix(&hex[2..3], 16).ok()? as f64 / 15.0;
                let a = u8::from_str_radix(&hex[3..4], 16).ok()? as f64 / 15.0;
                Some(Self::rgba(r, g, b, a))
            }
            6 => {
                let r = u8::from_str_radix(&hex[0..2], 16).ok()? as f64 / 255.0;
                let g = u8::from_str_radix(&hex[2..4], 16).ok()? as f64 / 255.0;
                let b = u8::from_str_radix(&hex[4..6], 16).ok()? as f64 / 255.0;
                Some(Self::rgb(r, g, b))
            }
            8 => {
                let r = u8::from_str_radix(&hex[0..2], 16).ok()? as f64 / 255.0;
                let g = u8::from_str_radix(&hex[2..4], 16).ok()? as f64 / 255.0;
                let b = u8::from_str_radix(&hex[4..6], 16).ok()? as f64 / 255.0;
                let a = u8::from_str_radix(&hex[6..8], 16).ok()? as f64 / 255.0;
                Some(Self::rgba(r, g, b, a))
            }
            _ => None,
        }
    }

    /// Convert to hex string (#RRGGBB or #RRGGBBAA)
    pub fn to_hex(&self) -> String {
        let r = (self.r * 255.0) as u8;
        let g = (self.g * 255.0) as u8;
        let b = (self.b * 255.0) as u8;
        if (self.a - 1.0).abs() < 0.001 {
            format!("#{:02x}{:02x}{:02x}", r, g, b)
        } else {
            let a = (self.a * 255.0) as u8;
            format!("#{:02x}{:02x}{:02x}{:02x}", r, g, b, a)
        }
    }

    /// Apply alpha to existing color
    pub fn with_alpha(mut self, alpha: f64) -> Self {
        self.a = alpha;
        self
    }
}

impl Default for Color {
    fn default() -> Self {
        Self::rgb(0.0, 0.0, 0.0)
    }
}

// =============================================================================
// Font Configuration
// =============================================================================

/// Font weight
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum FontWeight {
    Thin,
    Light,
    #[default]
    Normal,
    Medium,
    SemiBold,
    Bold,
    ExtraBold,
}

impl FontWeight {
    pub fn as_css(&self) -> u16 {
        match self {
            FontWeight::Thin => 100,
            FontWeight::Light => 300,
            FontWeight::Normal => 400,
            FontWeight::Medium => 500,
            FontWeight::SemiBold => 600,
            FontWeight::Bold => 700,
            FontWeight::ExtraBold => 800,
        }
    }
}

/// Font configuration
#[derive(Clone, Debug)]
pub struct FontConfig {
    /// Font family (e.g., "Arial", "Roboto Mono")
    pub family: String,
    /// Font size in pixels
    pub size: f64,
    /// Font weight
    pub weight: FontWeight,
}

impl Default for FontConfig {
    fn default() -> Self {
        Self {
            family: "Arial".to_string(),
            size: 11.0,
            weight: FontWeight::Normal,
        }
    }
}

// =============================================================================
// Series Configuration
// =============================================================================

/// Candlestick series configuration
#[derive(Clone, Debug)]
pub struct CandlestickConfig {
    /// Up (bullish) candle body color
    pub up_color: String,
    /// Down (bearish) candle body color
    pub down_color: String,
    /// Up candle wick/border color
    pub up_wick_color: String,
    /// Down candle wick/border color
    pub down_wick_color: String,
    /// Border width (0 = no border)
    pub border_width: f64,
    /// Wick width in pixels
    pub wick_width: f64,
}

impl Default for CandlestickConfig {
    fn default() -> Self {
        Self {
            up_color: "#26a69a".to_string(),
            down_color: "#ef5350".to_string(),
            up_wick_color: "#26a69a".to_string(),
            down_wick_color: "#ef5350".to_string(),
            border_width: 0.0,
            wick_width: 1.0,
        }
    }
}

/// Line series configuration
#[derive(Clone, Debug)]
pub struct LineConfig {
    /// Line color
    pub color: String,
    /// Line width in pixels
    pub width: f64,
    /// Line style (solid, dashed, dotted)
    pub style: LineStyleType,
}

impl Default for LineConfig {
    fn default() -> Self {
        Self {
            color: "#2962ff".to_string(),
            width: 2.0,
            style: LineStyleType::Solid,
        }
    }
}

/// Line style types
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum LineStyleType {
    #[default]
    Solid,
    Dashed,
    Dotted,
    DashDot,
}

/// Area series configuration
#[derive(Clone, Debug)]
pub struct AreaConfig {
    /// Line color (top edge)
    pub line_color: String,
    /// Line width
    pub line_width: f64,
    /// Fill color (with alpha for transparency)
    pub fill_color: String,
    /// Fill opacity (0.0 - 1.0)
    pub fill_opacity: f64,
}

impl Default for AreaConfig {
    fn default() -> Self {
        Self {
            line_color: "#2962ff".to_string(),
            line_width: 2.0,
            fill_color: "#2962ff".to_string(),
            fill_opacity: 0.1,
        }
    }
}

/// Histogram/Bar series configuration
#[derive(Clone, Debug)]
pub struct HistogramConfig {
    /// Positive value color
    pub positive_color: String,
    /// Negative value color
    pub negative_color: String,
    /// Border color (None = no border)
    pub border_color: Option<String>,
    /// Border width
    pub border_width: f64,
}

impl Default for HistogramConfig {
    fn default() -> Self {
        Self {
            positive_color: "#26a69a".to_string(),
            negative_color: "#ef5350".to_string(),
            border_color: None,
            border_width: 0.0,
        }
    }
}

// =============================================================================
// Scale Configuration
// =============================================================================

/// Price scale (Y-axis) configuration
#[derive(Clone, Debug)]
pub struct PriceScaleConfig {
    /// Background color
    pub background: String,
    /// Border color (left edge)
    pub border_color: String,
    /// Border width
    pub border_width: f64,
    /// Text color for labels
    pub text_color: String,
    /// Font for labels
    pub font: FontConfig,
    /// Width in pixels
    pub width: f64,
    /// Padding inside the scale
    pub padding: f64,
    /// Tick mark length
    pub tick_length: f64,
}

impl Default for PriceScaleConfig {
    fn default() -> Self {
        Self {
            background: "#1e222d".to_string(),
            border_color: "#2a2e39".to_string(),
            border_width: 1.0,
            text_color: "#b2b5be".to_string(),
            font: FontConfig {
                family: "Arial".to_string(),
                size: 11.0,
                weight: FontWeight::Normal,
            },
            width: 80.0,
            padding: 8.0,
            tick_length: 4.0,
        }
    }
}

/// Time scale (X-axis) configuration
#[derive(Clone, Debug)]
pub struct TimeScaleConfig {
    /// Background color
    pub background: String,
    /// Border color (top edge)
    pub border_color: String,
    /// Border width
    pub border_width: f64,
    /// Text color for labels
    pub text_color: String,
    /// Font for labels
    pub font: FontConfig,
    /// Height in pixels
    pub height: f64,
}

impl Default for TimeScaleConfig {
    fn default() -> Self {
        Self {
            background: "#1e222d".to_string(),
            border_color: "#2a2e39".to_string(),
            border_width: 1.0,
            text_color: "#b2b5be".to_string(),
            font: FontConfig {
                family: "Arial".to_string(),
                size: 11.0,
                weight: FontWeight::Normal,
            },
            height: 26.0,
        }
    }
}

// =============================================================================
// Grid Configuration
// =============================================================================

/// Grid overlay configuration
#[derive(Clone, Debug)]
pub struct GridConfig {
    /// Show horizontal grid lines
    pub show_horizontal: bool,
    /// Show vertical grid lines
    pub show_vertical: bool,
    /// Grid line color
    pub color: String,
    /// Grid line width
    pub width: f64,
    /// Grid line style
    pub style: LineStyleType,
}

impl Default for GridConfig {
    fn default() -> Self {
        Self {
            show_horizontal: true,
            show_vertical: true,
            color: "#2a2e3966".to_string(),
            width: 1.0,
            style: LineStyleType::Solid,
        }
    }
}

// =============================================================================
// Crosshair Configuration
// =============================================================================

/// Crosshair configuration
#[derive(Clone, Debug)]
pub struct CrosshairConfig {
    /// Crosshair line color
    pub line_color: String,
    /// Crosshair line width
    pub line_width: f64,
    /// Crosshair line style
    pub line_style: LineStyleType,
    /// Label background color
    pub label_background: String,
    /// Label text color
    pub label_text_color: String,
    /// Label font
    pub label_font: FontConfig,
}

impl Default for CrosshairConfig {
    fn default() -> Self {
        Self {
            line_color: "#758696".to_string(),
            line_width: 1.0,
            line_style: LineStyleType::Dashed,
            label_background: "#363a45".to_string(),
            label_text_color: "#d1d4dc".to_string(),
            label_font: FontConfig::default(),
        }
    }
}

// =============================================================================
// Watermark Configuration
// =============================================================================

/// Watermark text configuration
#[derive(Clone, Debug)]
pub struct WatermarkConfig {
    /// Show watermark
    pub visible: bool,
    /// Watermark text lines
    pub lines: Vec<String>,
    /// Text color
    pub color: String,
    /// Font size
    pub font_size: f64,
    /// Horizontal alignment (0.0 = left, 0.5 = center, 1.0 = right)
    pub horizontal_align: f64,
    /// Vertical alignment (0.0 = top, 0.5 = center, 1.0 = bottom)
    pub vertical_align: f64,
}

impl Default for WatermarkConfig {
    fn default() -> Self {
        Self {
            visible: false,
            lines: Vec::new(),
            color: "#787b8633".to_string(),
            font_size: 48.0,
            horizontal_align: 0.5,
            vertical_align: 0.5,
        }
    }
}

// =============================================================================
// Primitive Drawing Configuration
// =============================================================================

/// Default primitive drawing configuration
#[derive(Clone, Debug)]
pub struct PrimitiveConfig {
    /// Default stroke color for new primitives
    pub default_stroke: String,
    /// Default fill color for new primitives
    pub default_fill: Option<String>,
    /// Default line width
    pub default_width: f64,
    /// Default font for text primitives
    pub text_font: FontConfig,
    /// Control point radius (for editing)
    pub control_point_radius: f64,
    /// Control point stroke color
    pub control_point_stroke: String,
    /// Control point fill color
    pub control_point_fill: String,
}

impl Default for PrimitiveConfig {
    fn default() -> Self {
        Self {
            default_stroke: "#2962ff".to_string(),
            default_fill: None,
            default_width: 2.0,
            text_font: FontConfig {
                family: "Arial".to_string(),
                size: 12.0,
                weight: FontWeight::Normal,
            },
            control_point_radius: 4.0,
            control_point_stroke: "#2962ff".to_string(),
            control_point_fill: "#ffffff".to_string(),
        }
    }
}

// =============================================================================
// Legend Configuration
// =============================================================================

/// Legend configuration
#[derive(Clone, Debug)]
pub struct LegendConfig {
    /// Show legend
    pub visible: bool,
    /// Text color
    pub text_color: String,
    /// Font for legend text
    pub font: FontConfig,
    /// Padding from chart edge
    pub padding: f64,
    /// Spacing between items
    pub item_spacing: f64,
}

impl Default for LegendConfig {
    fn default() -> Self {
        Self {
            visible: true,
            text_color: "#b2b5be".to_string(),
            font: FontConfig::default(),
            padding: 8.0,
            item_spacing: 16.0,
        }
    }
}

// =============================================================================
// Main Chart Configuration
// =============================================================================

/// Complete chart configuration
///
/// This is the main configuration struct that controls all rendering aspects
/// of the chart. Pass this to rendering functions to customize output.
#[derive(Clone, Debug, Default)]
pub struct ChartConfig {
    // Chart background
    /// Background color
    pub background: String,

    // Series defaults
    /// Candlestick series configuration
    pub candlestick: CandlestickConfig,
    /// Line series configuration
    pub line: LineConfig,
    /// Area series configuration
    pub area: AreaConfig,
    /// Histogram series configuration
    pub histogram: HistogramConfig,

    // Scales
    /// Price scale (Y-axis) configuration
    pub price_scale: PriceScaleConfig,
    /// Time scale (X-axis) configuration
    pub time_scale: TimeScaleConfig,

    // Overlays
    /// Grid configuration
    pub grid: GridConfig,
    /// Crosshair configuration
    pub crosshair: CrosshairConfig,
    /// Watermark configuration
    pub watermark: WatermarkConfig,
    /// Legend configuration
    pub legend: LegendConfig,

    // Primitives
    /// Drawing primitive defaults
    pub primitives: PrimitiveConfig,
}

impl ChartConfig {
    /// Create a new dark theme configuration (default)
    pub fn dark() -> Self {
        Self {
            background: "#131722".to_string(),
            ..Default::default()
        }
    }

    /// Create a light theme configuration
    pub fn light() -> Self {
        Self {
            background: "#ffffff".to_string(),
            candlestick: CandlestickConfig::default(),
            line: LineConfig::default(),
            area: AreaConfig::default(),
            histogram: HistogramConfig::default(),
            price_scale: PriceScaleConfig {
                background: "#f8f9fa".to_string(),
                border_color: "#dee2e6".to_string(),
                text_color: "#434651".to_string(),
                ..Default::default()
            },
            time_scale: TimeScaleConfig {
                background: "#f8f9fa".to_string(),
                border_color: "#dee2e6".to_string(),
                text_color: "#434651".to_string(),
                ..Default::default()
            },
            grid: GridConfig {
                color: "#0000000f".to_string(),
                ..Default::default()
            },
            crosshair: CrosshairConfig {
                line_color: "#9598a1".to_string(),
                label_background: "#131722".to_string(),
                label_text_color: "#ffffff".to_string(),
                ..Default::default()
            },
            watermark: WatermarkConfig {
                color: "#43465133".to_string(),
                ..Default::default()
            },
            legend: LegendConfig {
                text_color: "#434651".to_string(),
                ..Default::default()
            },
            primitives: PrimitiveConfig::default(),
        }
    }

    /// Create configuration for transparent background (PNG export)
    pub fn transparent() -> Self {
        Self {
            background: "transparent".to_string(),
            ..Self::dark()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_from_hex() {
        let c = Color::from_hex("#ff0000").unwrap();
        assert!((c.r - 1.0).abs() < 0.01);
        assert!(c.g < 0.01);
        assert!(c.b < 0.01);

        let c = Color::from_hex("#00ff0080").unwrap();
        assert!(c.g > 0.99);
        assert!((c.a - 0.5).abs() < 0.02);
    }

    #[test]
    fn test_color_to_hex() {
        let c = Color::rgb(1.0, 0.0, 0.0);
        assert_eq!(c.to_hex(), "#ff0000");

        let c = Color::rgba(0.0, 1.0, 0.0, 0.5);
        // 0.5 * 255 = 127 = 0x7f
        assert_eq!(c.to_hex(), "#00ff007f");
    }

    #[test]
    fn test_chart_config_dark() {
        let config = ChartConfig::dark();
        assert_eq!(config.background, "#131722");
        assert!(config.grid.show_horizontal);
    }

    #[test]
    fn test_chart_config_light() {
        let config = ChartConfig::light();
        assert_eq!(config.background, "#ffffff");
    }
}
