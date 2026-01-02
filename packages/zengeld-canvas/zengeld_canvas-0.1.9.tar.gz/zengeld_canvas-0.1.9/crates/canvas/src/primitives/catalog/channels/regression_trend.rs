//! Regression Trend primitive
//!
//! A linear regression channel with a center line calculated from price data
//! and parallel lines at standard deviation distances.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Regression Trend - linear regression channel
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RegressionTrend {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Start bar index
    pub bar1: f64,
    /// Start price (for anchor)
    pub price1: f64,
    /// End bar index
    pub bar2: f64,
    /// End price (for anchor)
    pub price2: f64,
    /// Standard deviation multiplier for channel width
    #[serde(default = "default_std_dev")]
    pub std_dev_mult: f64,
    /// Use Upper Pearson's channel (fitted to highs/lows)
    #[serde(default)]
    pub use_upper_deviation: bool,
    /// Show center (regression) line
    #[serde(default = "default_true")]
    pub show_center: bool,
    /// Fill the channel
    #[serde(default = "default_true")]
    pub fill: bool,
    /// Fill opacity (0.0 - 1.0)
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
    /// Extend to right
    #[serde(default)]
    pub extend_right: bool,
}

fn default_true() -> bool {
    true
}

fn default_std_dev() -> f64 {
    2.0
}

fn default_fill_opacity() -> f64 {
    0.2
}

impl RegressionTrend {
    /// Create a new regression trend
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "regression_trend".to_string(),
                display_name: "Regression Trend".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            std_dev_mult: 2.0,
            use_upper_deviation: false,
            show_center: true,
            fill: true,
            fill_opacity: 0.2,
            extend_right: false,
        }
    }

    /// Get the regression line slope and intercept
    /// In a real implementation, this would compute from actual price data
    /// For now, we use the anchor points as the regression line
    pub fn regression_params(&self) -> (f64, f64) {
        // slope = (price2 - price1) / (bar2 - bar1)
        let slope = if (self.bar2 - self.bar1).abs() > 0.001 {
            (self.price2 - self.price1) / (self.bar2 - self.bar1)
        } else {
            0.0
        };
        // intercept: price1 = slope * bar1 + intercept
        let intercept = self.price1 - slope * self.bar1;
        (slope, intercept)
    }

    /// Get price on the regression line at a given bar
    pub fn price_at_bar(&self, bar: f64) -> f64 {
        let (slope, intercept) = self.regression_params();
        slope * bar + intercept
    }

    /// Get the channel offset based on std_dev_mult
    /// In a real implementation, this would be calculated from actual std deviation
    /// For now, we estimate as a percentage of the price range
    pub fn channel_offset(&self) -> f64 {
        let price_range = (self.price2 - self.price1).abs();
        // Estimate std dev as ~15% of price range, multiply by std_dev_mult
        (price_range * 0.15).max(self.price1 * 0.02) * self.std_dev_mult / 2.0
    }
}

impl Primitive for RegressionTrend {
    fn type_id(&self) -> &'static str {
        "regression_trend"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Channel
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if points.len() >= 2 {
            self.bar1 = points[0].0;
            self.price1 = points[0].1;
            self.bar2 = points[1].0;
            self.price2 = points[1].1;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let offset = self.channel_offset();
        let upper_y1 = ctx.price_to_y(self.price1 + offset);
        let upper_y2 = ctx.price_to_y(self.price2 + offset);
        let lower_y1 = ctx.price_to_y(self.price1 - offset);
        let lower_y2 = ctx.price_to_y(self.price2 - offset);

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(x1, upper_y1);
            ctx.line_to(x2, upper_y2);
            ctx.line_to(x2, lower_y2);
            ctx.line_to(x1, lower_y1);
            ctx.close_path();
            ctx.fill();
        }

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Upper band
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(upper_y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(upper_y2, dpr));
        ctx.stroke();

        // Lower band
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(lower_y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(lower_y2, dpr));
        ctx.stroke();

        // Center line (dashed)
        if self.show_center {
            ctx.set_line_dash(&[4.0, 4.0]);
            ctx.begin_path();
            ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
            ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get the main line coordinates
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let dx = x2 - x1;
        let dy = y2 - y1;
        let line_length = (dx * dx + dy * dy).sqrt();

        let raw_angle = dy.atan2(dx);
        let _angle_flipped =
            !(-std::f64::consts::FRAC_PI_2..=std::f64::consts::FRAC_PI_2).contains(&raw_angle);
        let angle = if raw_angle > std::f64::consts::FRAC_PI_2 {
            raw_angle - std::f64::consts::PI
        } else if raw_angle < -std::f64::consts::FRAC_PI_2 {
            raw_angle + std::f64::consts::PI
        } else {
            raw_angle
        };

        let t = match text.h_align {
            TextAlign::Start => 0.0,
            TextAlign::Center => 0.5,
            TextAlign::End => 1.0,
        };
        let base_x = x1 + dx * t;
        let base_y = y1 + dy * t;

        // For channels, position in center of channel height
        // No additional adjustment needed as we're using the center line

        let (perp_x, perp_y) = if line_length > 0.001 {
            (-dy / line_length, dx / line_length)
        } else {
            (0.0, -1.0)
        };

        let text_offset = 8.0 + text.font_size / 2.0;
        let (offset_x, offset_y) = match text.v_align {
            TextAlign::Start => (-perp_x * text_offset, -perp_y * text_offset),
            TextAlign::Center => (0.0, 0.0),
            TextAlign::End => (perp_x * text_offset, perp_y * text_offset),
        };

        Some(TextAnchor::with_rotation(
            base_x + offset_x,
            base_y + offset_y,
            &self.data.color.stroke,
            angle,
        ))
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

// =============================================================================
// Factory Registration
// =============================================================================

fn create_regression_trend(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1 + 20.0, price1));
    Box::new(RegressionTrend::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "regression_trend",
        display_name: "Regression Trend",
        kind: PrimitiveKind::Channel,
        factory: create_regression_trend,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
