//! TimeScale - X-axis coordinate system for financial charts
//!
//! Manages the horizontal axis: bar positioning, navigation (pan/zoom),
//! visible range, and time tick generation.
//!
//! # Example
//!
//! ```rust
//! use zengeld_canvas::coords::TimeScale;
//!
//! let mut ts = TimeScale::new(800.0);
//! ts.set_bar_count(500);
//! ts.scroll_to_end();
//!
//! let x = ts.bar_to_x(100);
//! let bar = ts.x_to_bar(400.0);
//! ```

use crate::Bar;

// =============================================================================
// Time Constants
// =============================================================================

/// Seconds in a minute
pub const MINUTE: i64 = 60;
/// Seconds in an hour
pub const HOUR: i64 = 3600;
/// Seconds in a day
pub const DAY: i64 = 86400;

// =============================================================================
// Tick Mark Weight
// =============================================================================

/// Hierarchical weights for time tick marks
///
/// Higher weight = more important = larger font/brighter color.
/// Year=70, Month=60, Day=50, Week=40, Hour=30, etc.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug, Default)]
#[repr(u8)]
pub enum TickMarkWeight {
    /// Sub-minute granularity
    #[default]
    Second = 0,
    /// 1-minute boundaries
    Minute1 = 10,
    /// 5-minute boundaries
    Minute5 = 15,
    /// 30-minute boundaries
    Minute30 = 20,
    /// Hour boundaries
    Hour = 30,
    /// 4-hour boundaries
    Hour4 = 35,
    /// Week boundaries
    Week = 40,
    /// Day boundaries
    Day = 50,
    /// Month boundaries
    Month = 60,
    /// Year boundaries
    Year = 70,
}

impl TickMarkWeight {
    /// Calculate weight based on timestamp boundary
    pub fn from_timestamp(ts: i64, prev_ts: Option<i64>) -> Self {
        let prev = prev_ts.unwrap_or(0);

        // Year boundary
        let year = ts / (365 * DAY);
        let prev_year = prev / (365 * DAY);
        if year != prev_year {
            return TickMarkWeight::Year;
        }

        // Month boundary
        let month = ts / (30 * DAY);
        let prev_month = prev / (30 * DAY);
        if month != prev_month {
            return TickMarkWeight::Month;
        }

        // Week boundary
        let week = ts / (7 * DAY);
        let prev_week = prev / (7 * DAY);
        if week != prev_week {
            return TickMarkWeight::Week;
        }

        // Day boundary
        let day = ts / DAY;
        let prev_day = prev / DAY;
        if day != prev_day {
            return TickMarkWeight::Day;
        }

        // 4-hour boundary
        let hour4 = ts / (4 * HOUR);
        let prev_hour4 = prev / (4 * HOUR);
        if hour4 != prev_hour4 {
            return TickMarkWeight::Hour4;
        }

        // Hour boundary
        let hour = ts / HOUR;
        let prev_hour = prev / HOUR;
        if hour != prev_hour {
            return TickMarkWeight::Hour;
        }

        // 30-minute boundary
        let min30 = ts / (30 * MINUTE);
        let prev_min30 = prev / (30 * MINUTE);
        if min30 != prev_min30 {
            return TickMarkWeight::Minute30;
        }

        // 5-minute boundary
        let min5 = ts / (5 * MINUTE);
        let prev_min5 = prev / (5 * MINUTE);
        if min5 != prev_min5 {
            return TickMarkWeight::Minute5;
        }

        // Minute boundary
        let min = ts / MINUTE;
        let prev_min = prev / MINUTE;
        if min != prev_min {
            return TickMarkWeight::Minute1;
        }

        TickMarkWeight::Second
    }

    /// Check if major weight (Year/Month)
    pub fn is_major(&self) -> bool {
        matches!(self, TickMarkWeight::Year | TickMarkWeight::Month)
    }

    /// Check if medium weight (Day/Week)
    pub fn is_medium(&self) -> bool {
        matches!(self, TickMarkWeight::Day | TickMarkWeight::Week)
    }
}

// =============================================================================
// Time Tick
// =============================================================================

/// A tick mark on the time scale
#[derive(Clone, Debug)]
pub struct TimeTick {
    /// Bar index
    pub bar_idx: usize,
    /// X pixel coordinate
    pub x: f64,
    /// Tick weight for styling
    pub weight: TickMarkWeight,
    /// Formatted label
    pub label: String,
}

// =============================================================================
// TimeScale - X-axis coordinate system
// =============================================================================

/// X-axis coordinate system: bar positioning, navigation, tick generation
///
/// This is the horizontal counterpart to `PriceScale` (Y-axis).
#[derive(Clone, Debug)]
pub struct TimeScale {
    /// Starting bar index (can be fractional for smooth panning)
    pub view_start: f64,

    /// Pixels per bar
    pub bar_spacing: f64,

    /// Ratio of bar body width to spacing (0.0 - 1.0)
    pub bar_width_ratio: f64,

    /// Width of the chart area in pixels
    pub chart_width: f64,

    /// Total number of bars in data
    pub bar_count: usize,
}

impl Default for TimeScale {
    fn default() -> Self {
        Self {
            view_start: 0.0,
            bar_spacing: 8.0,
            bar_width_ratio: 0.8,
            chart_width: 800.0,
            bar_count: 0,
        }
    }
}

impl TimeScale {
    /// Create with chart width
    pub fn new(chart_width: f64) -> Self {
        Self {
            chart_width,
            ..Default::default()
        }
    }

    // =========================================================================
    // Configuration
    // =========================================================================

    /// Set total bar count
    pub fn set_bar_count(&mut self, count: usize) {
        self.bar_count = count;
    }

    /// Set chart width
    pub fn set_chart_width(&mut self, width: f64) {
        self.chart_width = width;
    }

    /// Set bar spacing (pixels per bar)
    pub fn set_bar_spacing(&mut self, spacing: f64) {
        self.bar_spacing = spacing.clamp(2.0, 100.0);
    }

    /// Set bar width ratio
    pub fn set_bar_width_ratio(&mut self, ratio: f64) {
        self.bar_width_ratio = ratio.clamp(0.1, 1.0);
    }

    // =========================================================================
    // Visible Range
    // =========================================================================

    /// Number of bars visible
    #[inline]
    pub fn visible_bars(&self) -> usize {
        ((self.chart_width / self.bar_spacing) as usize).max(1)
    }

    /// Get view_start as safe index
    #[inline]
    pub fn view_start_idx(&self) -> usize {
        if self.view_start < 0.0 {
            0
        } else {
            (self.view_start as usize).min(self.bar_count.saturating_sub(1))
        }
    }

    /// Get visible range as (start, end) - end is exclusive
    #[inline]
    pub fn visible_range(&self) -> (usize, usize) {
        let start = self.view_start_idx();
        let end = ((self.view_start + self.visible_bars() as f64).ceil() as usize + 1)
            .min(self.bar_count);
        (start, end)
    }

    /// Get visible range as floats
    pub fn visible_range_f64(&self) -> (f64, f64) {
        (
            self.view_start,
            self.view_start + self.visible_bars() as f64,
        )
    }

    // =========================================================================
    // Coordinate Conversion
    // =========================================================================

    /// Bar index to X pixel (center of bar)
    #[inline]
    pub fn bar_to_x(&self, bar_idx: usize) -> f64 {
        let relative = bar_idx as f64 - self.view_start;
        relative * self.bar_spacing + self.bar_spacing / 2.0
    }

    /// Fractional bar index to X pixel
    #[inline]
    pub fn bar_to_x_f64(&self, bar_idx: f64) -> f64 {
        let relative = bar_idx - self.view_start;
        relative * self.bar_spacing + self.bar_spacing / 2.0
    }

    /// X pixel to bar index
    #[inline]
    pub fn x_to_bar(&self, x: f64) -> Option<usize> {
        if x < 0.0 || x > self.chart_width {
            return None;
        }
        let bar_idx = (self.view_start + x / self.bar_spacing) as i64;
        if bar_idx >= 0 && (bar_idx as usize) < self.bar_count {
            Some(bar_idx as usize)
        } else {
            None
        }
    }

    /// X pixel to fractional bar index
    #[inline]
    pub fn x_to_bar_f64(&self, x: f64) -> f64 {
        self.view_start + x / self.bar_spacing
    }

    /// Bar body width in pixels
    #[inline]
    pub fn bar_width(&self) -> f64 {
        self.bar_spacing * self.bar_width_ratio
    }

    // =========================================================================
    // Navigation
    // =========================================================================

    /// Pan by bars (positive = left, negative = right)
    pub fn pan(&mut self, bar_delta: f64) {
        self.view_start -= bar_delta;
    }

    /// Scroll to latest bars
    pub fn scroll_to_end(&mut self) {
        self.view_start = (self.bar_count.saturating_sub(self.visible_bars())) as f64;
    }

    /// Scroll to first bars
    pub fn scroll_to_start(&mut self) {
        self.view_start = 0.0;
    }

    /// Fit all bars in view
    pub fn fit_all(&mut self, min_spacing: f64, max_spacing: f64) {
        if self.bar_count > 0 {
            self.bar_spacing =
                (self.chart_width / self.bar_count as f64).clamp(min_spacing, max_spacing);
            self.view_start = 0.0;
        }
    }

    /// Set visible range by bar indices
    pub fn set_visible_range(&mut self, start: f64, end: f64) {
        let count = end - start;
        if count > 0.0 {
            self.view_start = start;
            self.bar_spacing = self.chart_width / count;
        }
    }

    /// Zoom at anchor point (factor > 1 = zoom in)
    pub fn zoom(&mut self, factor: f64, anchor_x: f64) {
        if factor <= 0.0 || factor == 1.0 {
            return;
        }

        let anchor_bar = self.x_to_bar_f64(anchor_x);
        self.bar_spacing = (self.bar_spacing * factor).clamp(2.0, 100.0);

        let anchor_ratio = anchor_x / self.chart_width;
        let visible = self.visible_bars() as f64;
        self.view_start = anchor_bar - visible * anchor_ratio;
    }

    // =========================================================================
    // Tick Generation
    // =========================================================================

    /// Generate time ticks for visible range
    pub fn generate_ticks<F>(&self, bars: &[Bar], measure_text: F) -> Vec<TimeTick>
    where
        F: Fn(&str) -> f64,
    {
        let mut ticks = Vec::new();
        let (start, end) = self.visible_range();

        if start >= end || bars.is_empty() {
            return ticks;
        }

        // Min spacing between ticks
        let typical_label_width = 50.0;
        let min_spacing_bars = (typical_label_width / self.bar_spacing).ceil().max(1.0) as usize;

        let mut prev_ts: Option<i64> = None;
        let mut candidates: Vec<(usize, f64, TickMarkWeight, i64)> = Vec::new();

        // First pass: find candidates
        for i in start..end {
            if i >= bars.len() {
                break;
            }
            let ts = bars[i].timestamp;
            let x = self.bar_to_x(i);

            if x < -100.0 || x > self.chart_width + 100.0 {
                prev_ts = Some(ts);
                continue;
            }

            let weight = TickMarkWeight::from_timestamp(ts, prev_ts);
            if weight >= TickMarkWeight::Hour {
                candidates.push((i, x, weight, ts));
            }
            prev_ts = Some(ts);
        }

        if candidates.is_empty() {
            return ticks;
        }

        // Sort by weight (higher first)
        candidates.sort_by(|a, b| b.2.cmp(&a.2).then(a.0.cmp(&b.0)));

        let mut selected_indices: Vec<usize> = Vec::new();
        let mut used_positions: Vec<(f64, f64)> = Vec::new();

        for (bar_idx, x, weight, ts) in candidates {
            // Edge margin
            if x < 30.0 || x > self.chart_width - 30.0 {
                continue;
            }

            // Bar spacing check
            let spacing_ok = selected_indices.iter().all(|&sel| {
                (bar_idx as i64 - sel as i64).unsigned_abs() as usize >= min_spacing_bars
            });

            if !spacing_ok {
                continue;
            }

            let label = format_time_by_weight(ts, weight);
            let width = measure_text(&label);
            let half_width = width / 2.0 + 5.0;

            // Pixel collision check
            let conflicts = used_positions
                .iter()
                .any(|(ox, ohw)| (x - ox).abs() < half_width + ohw + 8.0);

            if conflicts {
                continue;
            }

            ticks.push(TimeTick {
                bar_idx,
                x,
                weight,
                label,
            });
            selected_indices.push(bar_idx);
            used_positions.push((x, half_width));
        }

        ticks.sort_by(|a, b| a.x.partial_cmp(&b.x).unwrap_or(std::cmp::Ordering::Equal));
        ticks
    }
}

// =============================================================================
// Time Formatting
// =============================================================================

/// Format time label based on weight
pub fn format_time_by_weight(ts: i64, weight: TickMarkWeight) -> String {
    let total_days = ts / DAY;
    let year = 1970 + (total_days / 365) as i32;
    let day_of_year = total_days % 365;
    let month = (day_of_year / 30) as i32 + 1;
    let day = (day_of_year % 30) as i32 + 1;
    let hour = ((ts % DAY) / HOUR) as i32;
    let minute = ((ts % HOUR) / MINUTE) as i32;

    match weight {
        TickMarkWeight::Year => format!("{}", year),
        TickMarkWeight::Month => {
            let names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ];
            names[((month - 1) as usize).min(11)].to_string()
        }
        TickMarkWeight::Week | TickMarkWeight::Day => {
            let names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ];
            format!("{} {}", day, names[((month - 1) as usize).min(11)])
        }
        _ => format!("{:02}:{:02}", hour, minute),
    }
}

/// Format full timestamp for display
pub fn format_time_full(ts: i64) -> String {
    let total_days = ts / DAY;
    let day_of_year = total_days % 365;
    let month = (day_of_year / 30) as i32 + 1;
    let day = (day_of_year % 30) as i32 + 1;
    let hour = ((ts % DAY) / HOUR) as i32;
    let minute = ((ts % HOUR) / MINUTE) as i32;

    format!("{:02}.{:02} {:02}:{:02}", day, month, hour, minute)
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_visible_bars() {
        let ts = TimeScale {
            chart_width: 800.0,
            bar_spacing: 10.0,
            ..Default::default()
        };
        assert_eq!(ts.visible_bars(), 80);
    }

    #[test]
    fn test_bar_to_x() {
        let ts = TimeScale {
            view_start: 0.0,
            bar_spacing: 10.0,
            ..Default::default()
        };
        assert!((ts.bar_to_x(0) - 5.0).abs() < 0.001);
        assert!((ts.bar_to_x(1) - 15.0).abs() < 0.001);
    }

    #[test]
    fn test_x_to_bar() {
        let ts = TimeScale {
            view_start: 0.0,
            bar_spacing: 10.0,
            chart_width: 100.0,
            bar_count: 20,
            ..Default::default()
        };
        assert_eq!(ts.x_to_bar(5.0), Some(0));
        assert_eq!(ts.x_to_bar(15.0), Some(1));
        assert_eq!(ts.x_to_bar(-5.0), None);
    }

    #[test]
    fn test_visible_range() {
        let ts = TimeScale {
            view_start: 10.0,
            bar_spacing: 10.0,
            chart_width: 100.0,
            bar_count: 50,
            ..Default::default()
        };
        let (start, end) = ts.visible_range();
        assert_eq!(start, 10);
        assert!(end <= 50 && end > start);
    }

    #[test]
    fn test_tick_weight_ordering() {
        assert!(TickMarkWeight::Year > TickMarkWeight::Month);
        assert!(TickMarkWeight::Month > TickMarkWeight::Day);
        assert!(TickMarkWeight::Day > TickMarkWeight::Hour);
    }

    #[test]
    fn test_zoom() {
        let mut ts = TimeScale::new(800.0);
        ts.bar_count = 100;
        ts.bar_spacing = 10.0;
        let orig = ts.bar_spacing;

        ts.zoom(2.0, 400.0);
        assert!(ts.bar_spacing > orig);
    }

    #[test]
    fn test_fit_all() {
        let mut ts = TimeScale::new(800.0);
        ts.bar_count = 100;
        ts.fit_all(4.0, 50.0);

        assert_eq!(ts.view_start, 0.0);
        assert_eq!(ts.bar_spacing, 8.0);
    }
}
