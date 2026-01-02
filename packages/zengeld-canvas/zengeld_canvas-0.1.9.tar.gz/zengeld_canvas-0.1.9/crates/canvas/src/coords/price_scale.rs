//! Price Scale - Nice number tick algorithm for financial charts
//!
//! Uses a [2, 2.5, 2] multiplier pattern to generate professional-looking
//! price tick marks. This module implements the nice number algorithm
//! along with price scale calculations.
//!
//! Supports multiple scale modes:
//! - Normal: Linear absolute price values
//! - Percent: Percentage change from base price
//! - Logarithmic: Log scale for large price ranges

use crate::Bar;
use crate::core::{PRICE_SCALE_FONT_SIZE_MAX, PRICE_SCALE_FONT_SIZE_MIN, PRICE_SCALE_WIDTH};

// =============================================================================
// Price Scale Mode
// =============================================================================

/// Price scale display mode
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum PriceScaleMode {
    /// Normal absolute price values (linear scale)
    #[default]
    Normal,
    /// Percentage change from base price
    Percent,
    /// Logarithmic scale (equal % moves = equal visual distance)
    Logarithmic,
}

impl PriceScaleMode {
    /// Get display name for UI
    pub fn display_name(&self) -> &'static str {
        match self {
            Self::Normal => "Normal",
            Self::Percent => "Percent",
            Self::Logarithmic => "Log",
        }
    }

    /// Cycle to next mode
    pub fn next(&self) -> Self {
        match self {
            Self::Normal => Self::Percent,
            Self::Percent => Self::Logarithmic,
            Self::Logarithmic => Self::Normal,
        }
    }

    /// Get short label for button
    pub fn short_label(&self) -> &'static str {
        match self {
            Self::Normal => "lin",
            Self::Percent => "%",
            Self::Logarithmic => "log",
        }
    }
}

// =============================================================================
// Nice Number Algorithm
// =============================================================================

/// Multiplier pattern for professional-looking tick marks: [2, 2.5, 2]
pub const NICE_MULTIPLIERS: [f64; 3] = [2.0, 2.5, 2.0];

/// Calculate a "nice" number using the [2, 2.5, 2] multiplier pattern
///
/// This produces visually pleasing tick intervals like 1, 2, 5, 10, 20, 50, etc.
/// The algorithm finds the nearest "nice" number that is close to but not less than
/// the input value.
pub fn nice_number(value: f64) -> f64 {
    if value <= 0.0 {
        return 1.0;
    }

    let exp = value.log10().floor();
    let base = 10.0_f64.powf(exp);

    // Start from base and multiply up using [2, 2.5, 2] pattern
    let mut current = base;
    let mut idx = 0;

    while current < value {
        current *= NICE_MULTIPLIERS[idx % 3];
        idx += 1;
        if idx > 10 {
            break;
        } // Safety
    }

    // Take the last value that was <= target, or current if we overshot
    if idx > 0 {
        // Step back one
        let prev_idx = idx - 1;
        let mut check = base;
        for i in 0..prev_idx {
            check *= NICE_MULTIPLIERS[i % 3];
        }
        if check >= value * 0.8 {
            return check;
        }
    }

    current
}

/// Backward-compatible alias for nice_number
#[inline]
pub fn lwc_nice_number(value: f64) -> f64 {
    nice_number(value)
}

/// Calculate nice price step for given range and target tick count
pub fn nice_price_step(range: f64, target_ticks: f64) -> f64 {
    let rough_step = range / target_ticks;
    nice_number(rough_step)
}

/// Determine decimal precision based on step size
pub fn price_precision(step: f64) -> usize {
    if step >= 1.0 {
        0
    } else if step >= 0.1 {
        1
    } else if step >= 0.01 {
        2
    } else if step >= 0.001 {
        3
    } else if step >= 0.0001 {
        4
    } else {
        5
    }
}

/// Format a price value with appropriate precision based on step
pub fn format_price(price: f64, step: f64) -> String {
    let precision = price_precision(step);
    match precision {
        0 => format!("{:.0}", price),
        1 => format!("{:.1}", price),
        2 => format!("{:.2}", price),
        3 => format!("{:.3}", price),
        4 => format!("{:.4}", price),
        _ => format!("{:.5}", price),
    }
}

// =============================================================================
// Price Scale
// =============================================================================

/// Price scale configuration and calculations
#[derive(Clone, Debug)]
pub struct PriceScale {
    /// Minimum visible price
    pub price_min: f64,
    /// Maximum visible price
    pub price_max: f64,
    /// Whether auto-scaling is enabled
    pub auto_scale: bool,
    /// Calculated width of the price scale area
    pub width: f64,
    /// Scale mode (Normal, Percent, Logarithmic)
    pub mode: PriceScaleMode,
    /// Base price for percent mode (usually first visible bar's close)
    pub base_price: f64,
}

impl Default for PriceScale {
    fn default() -> Self {
        Self {
            price_min: 0.0,
            price_max: 100.0,
            auto_scale: true,
            width: PRICE_SCALE_WIDTH, // Fixed constant width
            mode: PriceScaleMode::Normal,
            base_price: 100.0,
        }
    }
}

impl PriceScale {
    /// Create a new price scale with the given range
    pub fn new(price_min: f64, price_max: f64) -> Self {
        Self {
            price_min,
            price_max,
            ..Default::default()
        }
    }

    /// Get the current price range
    #[inline]
    pub fn range(&self) -> f64 {
        self.price_max - self.price_min
    }

    /// Calculate nice price step using [2, 2.5, 2] pattern
    ///
    /// Uses approximately 30px between price grid lines.
    pub fn calc_step(&self, chart_height: f64) -> f64 {
        let range = self.range();
        let target_ticks = (chart_height / 30.0).clamp(4.0, 20.0);
        nice_price_step(range, target_ticks)
    }

    /// Get the fixed width constant
    /// Price scale width is ALWAYS fixed at PRICE_SCALE_WIDTH (70px)
    /// Text/font size adapts to fit within this fixed width
    pub fn fixed_width() -> f64 {
        PRICE_SCALE_WIDTH
    }

    /// Format a price using the current step
    pub fn format_price(&self, price: f64, chart_height: f64) -> String {
        let step = self.calc_step(chart_height);
        format_price(price, step)
    }

    /// Calculate dynamic font size based on label length
    ///
    /// Longer labels get smaller font to fit in fixed width.
    /// Returns font size in pixels.
    pub fn calc_font_size(&self, chart_height: f64) -> f64 {
        let step = self.calc_step(chart_height);

        // Find the longest label
        let first = (self.price_min / step).ceil() * step;
        let mut max_len = 0;
        let mut price = first;
        while price < self.price_max {
            let label = format_price(price, step);
            max_len = max_len.max(label.len());
            price += step;
        }

        // Also check the max price label
        let max_label = format_price(self.price_max, step);
        max_len = max_len.max(max_label.len());

        // Dynamic font size: fewer chars = bigger font, more chars = smaller font
        // Available width for text: PRICE_SCALE_WIDTH - borders - padding ≈ 55px
        // At 12px font, roughly 7px per char, so 55/7 ≈ 8 chars max
        // At 9px font, roughly 5px per char, so 55/5 ≈ 11 chars max

        match max_len {
            0..=5 => PRICE_SCALE_FONT_SIZE_MAX, // 13px - short labels
            6..=7 => 12.0,                      // 12px - medium labels
            8..=9 => 11.0,                      // 11px - longer labels
            10..=11 => 10.0,                    // 10px - even longer
            _ => PRICE_SCALE_FONT_SIZE_MIN,     // 9px - very long labels
        }
    }

    /// Calculate auto-scale based on visible bars and optional MA values
    ///
    /// Updates price_min and price_max to fit the visible data with padding.
    pub fn calc_auto_scale(
        &mut self,
        bars: &[Bar],
        visible_range: (usize, usize),
        ma_fast: &[f64],
        ma_slow: &[f64],
    ) {
        if !self.auto_scale {
            return;
        }

        let (start, end) = visible_range;
        if start >= end || bars.is_empty() {
            return;
        }

        let mut min = f64::INFINITY;
        let mut max = f64::NEG_INFINITY;

        for i in start..end.min(bars.len()) {
            let bar = &bars[i];
            min = min.min(bar.low);
            max = max.max(bar.high);

            if i < ma_fast.len() && !ma_fast[i].is_nan() {
                min = min.min(ma_fast[i]);
                max = max.max(ma_fast[i]);
            }
            if i < ma_slow.len() && !ma_slow[i].is_nan() {
                min = min.min(ma_slow[i]);
                max = max.max(ma_slow[i]);
            }
        }

        if min.is_finite() && max.is_finite() {
            let range = max - min;
            let padding = range * 0.08;
            self.price_min = min - padding;
            self.price_max = max + padding;
        }
    }

    /// Generate price tick values for the grid
    pub fn generate_ticks(&self, chart_height: f64) -> Vec<f64> {
        let step = self.calc_step(chart_height);
        let first = (self.price_min / step).ceil() * step;

        let mut ticks = Vec::new();
        let mut price = first;
        while price < self.price_max {
            ticks.push(price);
            price += step;
        }
        ticks
    }

    // =========================================================================
    // Scale Mode Methods
    // =========================================================================

    /// Set the scale mode
    pub fn set_mode(&mut self, mode: PriceScaleMode) {
        self.mode = mode;
    }

    /// Toggle to next scale mode
    pub fn toggle_mode(&mut self) {
        self.mode = self.mode.next();
    }

    /// Set base price for percent mode
    pub fn set_base_price(&mut self, price: f64) {
        if price > 0.0 {
            self.base_price = price;
        }
    }

    /// Convert price to percentage change from base
    #[inline]
    pub fn price_to_percent(&self, price: f64) -> f64 {
        if self.base_price == 0.0 {
            return 0.0;
        }
        ((price - self.base_price) / self.base_price) * 100.0
    }

    /// Convert percentage back to price
    #[inline]
    pub fn percent_to_price(&self, percent: f64) -> f64 {
        self.base_price * (1.0 + percent / 100.0)
    }

    /// Convert price to Y coordinate using current scale mode
    ///
    /// This is the main method for converting prices to screen coordinates.
    /// Uses inverted Y axis (price increases upward, Y increases downward).
    #[inline]
    pub fn price_to_y(&self, price: f64, chart_height: f64) -> f64 {
        match self.mode {
            PriceScaleMode::Normal => {
                // Linear: Y = height * (1 - (price - min) / range)
                let range = self.price_max - self.price_min;
                if range <= 0.0 {
                    return chart_height / 2.0;
                }
                chart_height * (1.0 - (price - self.price_min) / range)
            }
            PriceScaleMode::Percent => {
                // Percent mode: convert to % then linear scale
                let pct = self.price_to_percent(price);
                let pct_min = self.price_to_percent(self.price_min);
                let pct_max = self.price_to_percent(self.price_max);
                let range = pct_max - pct_min;
                if range <= 0.0 {
                    return chart_height / 2.0;
                }
                chart_height * (1.0 - (pct - pct_min) / range)
            }
            PriceScaleMode::Logarithmic => {
                // Logarithmic: Y = height * (1 - (log(price) - log(min)) / (log(max) - log(min)))
                // Protect against non-positive prices
                let safe_price = price.max(0.0001);
                let safe_min = self.price_min.max(0.0001);
                let safe_max = self.price_max.max(safe_min + 0.0001);

                let log_price = safe_price.ln();
                let log_min = safe_min.ln();
                let log_max = safe_max.ln();
                let log_range = log_max - log_min;

                if log_range <= 0.0 {
                    return chart_height / 2.0;
                }
                chart_height * (1.0 - (log_price - log_min) / log_range)
            }
        }
    }

    /// Convert Y coordinate to price using current scale mode
    #[inline]
    pub fn y_to_price(&self, y: f64, chart_height: f64) -> f64 {
        match self.mode {
            PriceScaleMode::Normal => {
                // Linear: price = max - (y / height) * range
                let range = self.price_max - self.price_min;
                self.price_max - (y / chart_height) * range
            }
            PriceScaleMode::Percent => {
                // Percent mode: invert to get % then convert to price
                let pct_min = self.price_to_percent(self.price_min);
                let pct_max = self.price_to_percent(self.price_max);
                let range = pct_max - pct_min;
                let pct = pct_max - (y / chart_height) * range;
                self.percent_to_price(pct)
            }
            PriceScaleMode::Logarithmic => {
                // Logarithmic: price = exp(log_max - (y / height) * log_range)
                let safe_min = self.price_min.max(0.0001);
                let safe_max = self.price_max.max(safe_min + 0.0001);

                let log_min = safe_min.ln();
                let log_max = safe_max.ln();
                let log_range = log_max - log_min;

                let log_price = log_max - (y / chart_height) * log_range;
                log_price.exp()
            }
        }
    }

    /// Format label for price scale based on current mode
    pub fn format_label(&self, price: f64, chart_height: f64) -> String {
        match self.mode {
            PriceScaleMode::Normal => self.format_price(price, chart_height),
            PriceScaleMode::Percent => {
                let pct = self.price_to_percent(price);
                if pct >= 0.0 {
                    format!("+{:.2}%", pct)
                } else {
                    format!("{:.2}%", pct)
                }
            }
            PriceScaleMode::Logarithmic => {
                // For log scale, still show absolute price but with log-spaced ticks
                self.format_price(price, chart_height)
            }
        }
    }

    /// Generate tick values appropriate for current scale mode
    pub fn generate_ticks_for_mode(&self, chart_height: f64) -> Vec<f64> {
        match self.mode {
            PriceScaleMode::Normal => self.generate_ticks(chart_height),
            PriceScaleMode::Percent => {
                // Generate percent-based ticks, convert back to prices
                let pct_min = self.price_to_percent(self.price_min);
                let pct_max = self.price_to_percent(self.price_max);
                let pct_range = pct_max - pct_min;
                let target_ticks = (chart_height / 30.0).clamp(4.0, 20.0);
                let step = nice_price_step(pct_range, target_ticks);

                let first = (pct_min / step).ceil() * step;
                let mut ticks = Vec::new();
                let mut pct = first;
                while pct < pct_max {
                    ticks.push(self.percent_to_price(pct));
                    pct += step;
                }
                ticks
            }
            PriceScaleMode::Logarithmic => {
                // Generate log-spaced ticks
                let safe_min = self.price_min.max(0.0001);
                let safe_max = self.price_max.max(safe_min + 0.0001);

                let log_min = safe_min.log10();
                let log_max = safe_max.log10();
                let log_range = log_max - log_min;

                let target_ticks = (chart_height / 30.0).clamp(4.0, 20.0);
                let log_step = nice_price_step(log_range, target_ticks);

                let first = (log_min / log_step).ceil() * log_step;
                let mut ticks = Vec::new();
                let mut log_val = first;
                while log_val < log_max {
                    ticks.push(10.0_f64.powf(log_val));
                    log_val += log_step;
                }
                ticks
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_nice_number() {
        // Should produce nice round numbers
        let nice = nice_number(7.0);
        assert!((5.0..=10.0).contains(&nice));

        let nice = nice_number(23.0);
        assert!((20.0..=25.0).contains(&nice));
    }

    #[test]
    fn test_price_precision() {
        assert_eq!(price_precision(10.0), 0);
        assert_eq!(price_precision(1.0), 0);
        assert_eq!(price_precision(0.5), 1);
        assert_eq!(price_precision(0.05), 2);
        assert_eq!(price_precision(0.005), 3);
    }

    #[test]
    fn test_format_price() {
        assert_eq!(format_price(123.456, 1.0), "123");
        assert_eq!(format_price(123.456, 0.1), "123.5");
        assert_eq!(format_price(123.456, 0.01), "123.46");
    }

    #[test]
    fn test_price_scale_step() {
        let scale = PriceScale::new(0.0, 100.0);
        let step = scale.calc_step(300.0);
        // With 300px height and 100 range, should be around 10 ticks
        assert!(step > 5.0 && step < 20.0);
    }

    #[test]
    fn test_generate_ticks() {
        let scale = PriceScale::new(0.0, 100.0);
        let ticks = scale.generate_ticks(300.0);
        assert!(!ticks.is_empty());
        // All ticks should be within range
        for tick in &ticks {
            assert!(*tick >= scale.price_min);
            assert!(*tick <= scale.price_max);
        }
    }
}
