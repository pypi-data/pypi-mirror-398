//! Viewport - Main coordinate system API for financial charts
//!
//! Combines TimeScale (X-axis) and PriceScale (Y-axis) into a unified API
//! for coordinate conversion, navigation, and rendering.
//!
//! # Example
//!
//! ```rust
//! use zengeld_canvas::coords::Viewport;
//! use zengeld_canvas::Bar;
//!
//! let mut vp = Viewport::new(800.0, 600.0);
//! let bars = vec![Bar::new(1000, 100.0, 110.0, 95.0, 105.0)];
//! vp.set_bars(&bars);
//! vp.scroll_to_end();
//!
//! let x = vp.bar_to_x(0);
//! let y = vp.price_to_y(100.5);
//! ```

use super::{PriceScale, PriceScaleMode, TimeScale, TimeTick};
use crate::Bar;

/// Main coordinate system for chart rendering
///
/// Combines:
/// - `TimeScale` - X-axis (bar positioning, navigation, time ticks)
/// - `PriceScale` - Y-axis (price conversion, modes, price ticks)
#[derive(Clone, Debug)]
pub struct Viewport {
    /// X-axis coordinate system
    pub time_scale: TimeScale,
    /// Y-axis coordinate system
    pub price_scale: PriceScale,
    /// Chart height in pixels
    pub chart_height: f64,
}

impl Default for Viewport {
    fn default() -> Self {
        Self::new(800.0, 400.0)
    }
}

impl Viewport {
    /// Create viewport with dimensions
    pub fn new(chart_width: f64, chart_height: f64) -> Self {
        Self {
            time_scale: TimeScale::new(chart_width),
            price_scale: PriceScale::default(),
            chart_height,
        }
    }

    // =========================================================================
    // Dimensions
    // =========================================================================

    /// Get chart width
    #[inline]
    pub fn chart_width(&self) -> f64 {
        self.time_scale.chart_width
    }

    /// Set chart dimensions
    pub fn set_size(&mut self, width: f64, height: f64) {
        self.time_scale.set_chart_width(width);
        self.chart_height = height;
    }

    // =========================================================================
    // Data Management
    // =========================================================================

    /// Set bar count
    pub fn set_bar_count(&mut self, count: usize) {
        self.time_scale.set_bar_count(count);
    }

    /// Set bars and auto-scale price range
    pub fn set_bars(&mut self, bars: &[Bar]) {
        self.time_scale.set_bar_count(bars.len());
        if !bars.is_empty() && self.price_scale.auto_scale {
            self.auto_scale_price(bars);
        }
    }

    /// Auto-scale price range from visible bars
    pub fn auto_scale_price(&mut self, bars: &[Bar]) {
        let (start, end) = self.time_scale.visible_range();
        if start >= end || bars.is_empty() {
            return;
        }

        let mut min = f64::INFINITY;
        let mut max = f64::NEG_INFINITY;

        for bar in bars.iter().take(end.min(bars.len())).skip(start) {
            min = min.min(bar.low);
            max = max.max(bar.high);
        }

        if min.is_finite() && max.is_finite() {
            let range = max - min;
            let padding = range * 0.08;
            self.price_scale.price_min = min - padding;
            self.price_scale.price_max = max + padding;
        }
    }

    /// Auto-scale including indicator values
    pub fn auto_scale_with_indicators(&mut self, bars: &[Bar], indicators: &[&[f64]]) {
        let (start, end) = self.time_scale.visible_range();
        if start >= end || bars.is_empty() {
            return;
        }

        let mut min = f64::INFINITY;
        let mut max = f64::NEG_INFINITY;

        for (i, bar) in bars
            .iter()
            .take(end.min(bars.len()))
            .skip(start)
            .enumerate()
        {
            let bar_idx = start + i;
            min = min.min(bar.low);
            max = max.max(bar.high);

            for values in indicators {
                if bar_idx < values.len() && values[bar_idx].is_finite() {
                    min = min.min(values[bar_idx]);
                    max = max.max(values[bar_idx]);
                }
            }
        }

        if min.is_finite() && max.is_finite() {
            let range = max - min;
            let padding = range * 0.08;
            self.price_scale.price_min = min - padding;
            self.price_scale.price_max = max + padding;
        }
    }

    /// Set price range manually
    pub fn set_price_range(&mut self, min: f64, max: f64) {
        self.price_scale.price_min = min;
        self.price_scale.price_max = max;
    }

    // =========================================================================
    // X-axis: Bar ↔ Pixel (delegated to TimeScale)
    // =========================================================================

    /// Bar index to X pixel
    #[inline]
    pub fn bar_to_x(&self, bar_idx: usize) -> f64 {
        self.time_scale.bar_to_x(bar_idx)
    }

    /// Fractional bar to X pixel
    #[inline]
    pub fn bar_to_x_f64(&self, bar_idx: f64) -> f64 {
        self.time_scale.bar_to_x_f64(bar_idx)
    }

    /// X pixel to bar index
    #[inline]
    pub fn x_to_bar(&self, x: f64) -> Option<usize> {
        self.time_scale.x_to_bar(x)
    }

    /// X pixel to fractional bar
    #[inline]
    pub fn x_to_bar_f64(&self, x: f64) -> f64 {
        self.time_scale.x_to_bar_f64(x)
    }

    /// Bar body width
    #[inline]
    pub fn bar_width(&self) -> f64 {
        self.time_scale.bar_width()
    }

    /// Bar spacing (pixels per bar)
    #[inline]
    pub fn bar_spacing(&self) -> f64 {
        self.time_scale.bar_spacing
    }

    /// Set bar spacing
    pub fn set_bar_spacing(&mut self, spacing: f64) {
        self.time_scale.set_bar_spacing(spacing);
    }

    // =========================================================================
    // Y-axis: Price ↔ Pixel (delegated to PriceScale)
    // =========================================================================

    /// Price to Y pixel (uses current scale mode)
    #[inline]
    pub fn price_to_y(&self, price: f64) -> f64 {
        self.price_scale.price_to_y(price, self.chart_height)
    }

    /// Y pixel to price
    #[inline]
    pub fn y_to_price(&self, y: f64) -> f64 {
        self.price_scale.y_to_price(y, self.chart_height)
    }

    /// Get price range
    pub fn price_range(&self) -> (f64, f64) {
        (self.price_scale.price_min, self.price_scale.price_max)
    }

    // =========================================================================
    // Visible Range
    // =========================================================================

    /// Number of visible bars
    #[inline]
    pub fn visible_bars(&self) -> usize {
        self.time_scale.visible_bars()
    }

    /// Visible range as (start, end)
    #[inline]
    pub fn visible_range(&self) -> (usize, usize) {
        self.time_scale.visible_range()
    }

    /// Visible range as floats
    pub fn visible_range_f64(&self) -> (f64, f64) {
        self.time_scale.visible_range_f64()
    }

    /// Set visible range
    pub fn set_visible_range(&mut self, start: f64, end: f64) {
        self.time_scale.set_visible_range(start, end);
    }

    // =========================================================================
    // Navigation
    // =========================================================================

    /// Pan by bars
    pub fn pan(&mut self, bar_delta: f64) {
        self.time_scale.pan(bar_delta);
    }

    /// Scroll to end (latest bars)
    pub fn scroll_to_end(&mut self) {
        self.time_scale.scroll_to_end();
    }

    /// Scroll to start (oldest bars)
    pub fn scroll_to_start(&mut self) {
        self.time_scale.scroll_to_start();
    }

    /// Fit all bars
    pub fn fit_all(&mut self, min_spacing: f64, max_spacing: f64) {
        self.time_scale.fit_all(min_spacing, max_spacing);
    }

    /// Zoom at anchor point
    pub fn zoom(&mut self, factor: f64, anchor_x: f64) {
        self.time_scale.zoom(factor, anchor_x);
    }

    // =========================================================================
    // Price Scale Mode
    // =========================================================================

    /// Set price scale mode
    pub fn set_price_scale_mode(&mut self, mode: PriceScaleMode) {
        self.price_scale.set_mode(mode);
    }

    /// Toggle price scale mode
    pub fn toggle_price_scale_mode(&mut self) {
        self.price_scale.toggle_mode();
    }

    /// Enable/disable auto-scaling
    pub fn set_auto_scale(&mut self, enabled: bool) {
        self.price_scale.auto_scale = enabled;
    }

    /// Set base price for percent mode
    pub fn set_base_price(&mut self, price: f64) {
        self.price_scale.set_base_price(price);
    }

    // =========================================================================
    // Tick Generation
    // =========================================================================

    /// Generate time ticks
    pub fn time_ticks<F>(&self, bars: &[Bar], measure_text: F) -> Vec<TimeTick>
    where
        F: Fn(&str) -> f64,
    {
        self.time_scale.generate_ticks(bars, measure_text)
    }

    /// Generate price ticks
    pub fn price_ticks(&self) -> Vec<f64> {
        self.price_scale.generate_ticks_for_mode(self.chart_height)
    }

    /// Format price for display
    pub fn format_price(&self, price: f64) -> String {
        self.price_scale.format_label(price, self.chart_height)
    }

    /// Get price step
    pub fn price_step(&self) -> f64 {
        self.price_scale.calc_step(self.chart_height)
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_creation() {
        let vp = Viewport::new(800.0, 400.0);
        assert_eq!(vp.chart_width(), 800.0);
        assert_eq!(vp.chart_height, 400.0);
    }

    #[test]
    fn test_bar_to_x() {
        let mut vp = Viewport::new(800.0, 400.0);
        vp.time_scale.bar_spacing = 10.0;
        vp.time_scale.view_start = 0.0;

        assert!((vp.bar_to_x(0) - 5.0).abs() < 0.001);
        assert!((vp.bar_to_x(1) - 15.0).abs() < 0.001);
    }

    #[test]
    fn test_price_to_y() {
        let mut vp = Viewport::new(800.0, 100.0);
        vp.set_price_range(0.0, 100.0);

        // At price_min (0), Y should be at bottom (100)
        assert!((vp.price_to_y(0.0) - 100.0).abs() < 0.001);
        // At price_max (100), Y should be at top (0)
        assert!((vp.price_to_y(100.0) - 0.0).abs() < 0.001);
        // At midpoint
        assert!((vp.price_to_y(50.0) - 50.0).abs() < 0.001);
    }

    #[test]
    fn test_y_to_price() {
        let mut vp = Viewport::new(800.0, 100.0);
        vp.set_price_range(0.0, 100.0);

        assert!((vp.y_to_price(0.0) - 100.0).abs() < 0.001);
        assert!((vp.y_to_price(100.0) - 0.0).abs() < 0.001);
    }

    #[test]
    fn test_visible_range() {
        let mut vp = Viewport::new(100.0, 400.0);
        vp.time_scale.view_start = 10.0;
        vp.time_scale.bar_spacing = 10.0;
        vp.time_scale.bar_count = 50;

        let (start, end) = vp.visible_range();
        assert_eq!(start, 10);
        assert!(end <= 50 && end > start);
    }

    #[test]
    fn test_navigation() {
        let mut vp = Viewport::new(800.0, 400.0);
        vp.time_scale.bar_count = 100;
        vp.time_scale.bar_spacing = 10.0;

        vp.scroll_to_end();
        assert!(vp.time_scale.view_start > 0.0);

        vp.scroll_to_start();
        assert_eq!(vp.time_scale.view_start, 0.0);
    }
}
