//! Core types and constants for zen-chart
//!
//! This module contains all fundamental data structures, color constants,
//! layout constants, and helper functions used throughout the chart library.

// =============================================================================
// Chart Theme - Color Palette
// =============================================================================

/// Legacy chart color theme - use UITheme for new code
///
/// This struct provides a simplified view of chart colors.
/// For full theme control, use `UITheme` which includes:
/// - UI colors (toolbars, buttons)
/// - Chart colors (grid, scales, crosshair)
/// - Series colors (candles, line, area, etc.)
/// - Full font configuration
///
/// To create from UITheme: `Theme::from_ui_theme(&ui_theme)`
#[derive(Clone, Debug)]
pub struct Theme {
    pub candle_up: &'static str,
    pub candle_down: &'static str,
    pub candle_up_wick: &'static str,
    pub candle_down_wick: &'static str,
    pub grid_color: &'static str,
    pub bg_color: &'static str,
    pub scale_bg: &'static str,
    pub scale_border: &'static str,
    pub text_color: &'static str,
    pub text_muted: &'static str,
    pub crosshair_color: &'static str,
    pub crosshair_label_bg: &'static str,
    pub ma_fast: &'static str,
    pub ma_slow: &'static str,
}

impl Default for Theme {
    fn default() -> Self {
        Self {
            candle_up: "#26a69a",
            candle_down: "#ef5350",
            candle_up_wick: "#26a69a",
            candle_down_wick: "#ef5350",
            grid_color: "#2a2e3999",
            bg_color: "#131722",
            scale_bg: "#1e222d",
            scale_border: "#2a2e39",
            text_color: "#b2b5be",
            text_muted: "#787b86",
            crosshair_color: "#758696",
            crosshair_label_bg: "#363a45",
            ma_fast: "#2962ff",
            ma_slow: "#ff6d00",
        }
    }
}

impl Theme {
    /// Create dark theme (default)
    pub fn dark() -> Self {
        Self::default()
    }

    /// Create light theme
    pub fn light() -> Self {
        Self {
            candle_up: "#26a69a",
            candle_down: "#ef5350",
            candle_up_wick: "#26a69a",
            candle_down_wick: "#ef5350",
            grid_color: "#0000000f",
            bg_color: "#ffffff",
            scale_bg: "#f8f9fa",
            scale_border: "#dee2e6",
            text_color: "#434651",
            text_muted: "#787b86",
            crosshair_color: "#9598a1",
            crosshair_label_bg: "#131722",
            ma_fast: "#2962ff",
            ma_slow: "#ff6d00",
        }
    }
}

// =============================================================================
// Layout Constants
// =============================================================================

/// Height of the time scale area in pixels (CONSTANT)
pub const TIME_SCALE_HEIGHT: f64 = 30.0;

/// Font size for time scale labels
pub const TIME_SCALE_FONT_SIZE: f64 = 12.0;

/// Fixed width for price scale (CONSTANT)
pub const PRICE_SCALE_WIDTH: f64 = 70.0;

/// Max font size for price scale labels (when few digits)
pub const PRICE_SCALE_FONT_SIZE_MAX: f64 = 13.0;

/// Min font size for price scale labels (when many digits)
pub const PRICE_SCALE_FONT_SIZE_MIN: f64 = 9.0;

/// Default font size for price scale labels
pub const PRICE_SCALE_FONT_SIZE: f64 = 12.0;

/// Font specification for price scale (default)
pub const PRICE_SCALE_FONT: &str = "12px 'Trebuchet MS', Arial, sans-serif";

/// Border width for price scale
pub const PRICE_SCALE_BORDER_SIZE: f64 = 1.0;

/// Small tick mark length
pub const PRICE_SCALE_TICK_LENGTH: f64 = 3.0;

/// Padding between tick and text
pub const PRICE_SCALE_PADDING_INNER: f64 = 5.0;

/// Right edge padding
pub const PRICE_SCALE_PADDING_OUTER: f64 = 5.0;

/// Constant for label positioning
pub const PRICE_SCALE_LABEL_OFFSET: f64 = 5.0;

/// Minimum width for price scale (legacy, use PRICE_SCALE_WIDTH)
pub const PRICE_SCALE_MIN_WIDTH: f64 = 50.0;

// =============================================================================
// Sidebar & Toolbar Constants
// =============================================================================

/// Width of the left sidebar panel in pixels (main menu, account, settings)
pub const LEFT_SIDEBAR_WIDTH: f64 = 280.0;

/// Width of the right sidebar panel in pixels
pub const RIGHT_SIDEBAR_WIDTH: f64 = 340.0;

/// Height of the bottom sidebar panel in pixels
pub const BOTTOM_SIDEBAR_HEIGHT: f64 = 200.0;

/// Width of the right toolbar in pixels
pub const RIGHT_TOOLBAR_WIDTH: f64 = 48.0;

/// Width of the left toolbar in pixels
pub const LEFT_TOOLBAR_WIDTH: f64 = 50.0;

/// Height of the bottom toolbar in pixels
pub const BOTTOM_TOOLBAR_HEIGHT: f64 = 32.0;

/// Height of the top toolbar in pixels
pub const TOP_TOOLBAR_HEIGHT: f64 = 40.0;

/// Height of the status bar in pixels (0 = hidden/removed)
pub const STATUS_BAR_HEIGHT: f64 = 0.0;

// =============================================================================
// Data Structures
// =============================================================================

/// OHLCV bar data with timestamp
#[derive(Clone, Copy, Debug, Default)]
pub struct Bar {
    /// Unix timestamp in seconds
    pub timestamp: i64,
    /// Opening price
    pub open: f64,
    /// Highest price
    pub high: f64,
    /// Lowest price
    pub low: f64,
    /// Closing price
    pub close: f64,
    /// Trading volume
    pub volume: f64,
}

impl Bar {
    /// Create a new bar with the given values (without volume, defaults to 0)
    pub fn new(timestamp: i64, open: f64, high: f64, low: f64, close: f64) -> Self {
        Self {
            timestamp,
            open,
            high,
            low,
            close,
            volume: 0.0,
        }
    }

    /// Create a new bar with volume (OHLCV)
    pub fn with_volume(
        timestamp: i64,
        open: f64,
        high: f64,
        low: f64,
        close: f64,
        volume: f64,
    ) -> Self {
        Self {
            timestamp,
            open,
            high,
            low,
            close,
            volume,
        }
    }

    /// Returns true if this bar closed higher than it opened
    #[inline]
    pub fn is_bullish(&self) -> bool {
        self.close >= self.open
    }

    /// Returns the body size (absolute difference between open and close)
    #[inline]
    pub fn body_size(&self) -> f64 {
        (self.close - self.open).abs()
    }

    /// Returns the full range (high - low)
    #[inline]
    pub fn range(&self) -> f64 {
        self.high - self.low
    }
}

// =============================================================================
// Pixel-Perfect Helpers
// =============================================================================

/// Snap a coordinate to pixel boundaries for crisp line rendering
///
/// This ensures 1px lines render sharply by aligning to half-pixel offsets,
/// accounting for the device pixel ratio (DPR).
#[inline]
pub fn crisp(coord: f64, dpr: f64) -> f64 {
    (coord * dpr).floor() / dpr + 0.5 / dpr
}

/// Snap a rectangle to pixel boundaries for crisp rendering
///
/// Returns (x, y, width, height) with coordinates aligned to device pixels.
/// Ensures minimum 1px dimensions even at high DPR.
#[inline]
pub fn crisp_rect(x: f64, y: f64, w: f64, h: f64, dpr: f64) -> (f64, f64, f64, f64) {
    let bx = (x * dpr).floor() / dpr;
    let by = (y * dpr).floor() / dpr;
    let bw = ((x + w) * dpr).floor() / dpr - bx;
    let bh = ((y + h) * dpr).floor() / dpr - by;
    (bx, by, bw.max(1.0 / dpr), bh.max(1.0 / dpr))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bar_is_bullish() {
        let bullish = Bar::new(0, 100.0, 110.0, 95.0, 105.0);
        let bearish = Bar::new(0, 105.0, 110.0, 95.0, 100.0);
        let doji = Bar::new(0, 100.0, 105.0, 95.0, 100.0);

        assert!(bullish.is_bullish());
        assert!(!bearish.is_bullish());
        assert!(doji.is_bullish()); // Equal close/open is considered bullish
    }

    #[test]
    fn test_crisp() {
        // At DPR 1.0, should add 0.5 offset
        let result = crisp(10.0, 1.0);
        assert!((result - 10.5).abs() < 0.001);

        // At DPR 2.0, should align to half-pixels
        let result = crisp(10.3, 2.0);
        assert!((result - 10.25).abs() < 0.001);
    }

    #[test]
    fn test_crisp_rect() {
        let (x, y, w, h) = crisp_rect(10.3, 20.7, 50.5, 30.2, 1.0);
        assert_eq!(x, 10.0);
        assert_eq!(y, 20.0);
        // Width and height should be whole pixels at DPR 1.0
        assert!(w >= 1.0);
        assert!(h >= 1.0);
    }
}
