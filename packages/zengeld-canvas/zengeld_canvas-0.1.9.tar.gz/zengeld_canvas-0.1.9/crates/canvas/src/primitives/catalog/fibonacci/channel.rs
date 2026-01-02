//! Fibonacci Channel primitive
//!
//! A channel with parallel lines at Fibonacci ratios from the baseline.
//! Uses three points: two define the baseline, third defines the channel width.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Default channel levels
pub const DEFAULT_CHANNEL_LEVELS: &[f64] = &[0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];

/// Fibonacci Channel - parallel lines at Fib ratios
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibChannel {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First baseline point bar
    pub bar1: f64,
    /// First baseline point price
    pub price1: f64,
    /// Second baseline point bar
    pub bar2: f64,
    /// Second baseline point price
    pub price2: f64,
    /// Third point bar (defines channel width)
    pub bar3: f64,
    /// Third point price
    pub price3: f64,
    /// Channel levels
    #[serde(default = "default_levels")]
    pub levels: Vec<f64>,
    /// Show price labels
    #[serde(default = "default_true")]
    pub show_prices: bool,
    /// Extend lines
    #[serde(default = "default_true")]
    pub extend: bool,
}

fn default_true() -> bool {
    true
}
fn default_levels() -> Vec<f64> {
    DEFAULT_CHANNEL_LEVELS.to_vec()
}

impl FibChannel {
    /// Create a new Fibonacci channel
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        bar3: f64,
        price3: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_channel".to_string(),
                display_name: "Fib Channel".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            bar3,
            price3,
            levels: DEFAULT_CHANNEL_LEVELS.to_vec(),
            show_prices: true,
            extend: true,
        }
    }

    /// Calculate the perpendicular offset for channel width
    fn channel_offset(&self) -> (f64, f64) {
        // Vector from point 1 to point 2
        let dx = self.bar2 - self.bar1;
        let dy = self.price2 - self.price1;

        // Point 3 offset from baseline
        // Project point 3 onto the baseline to get perpendicular distance
        let len_sq = dx * dx + dy * dy;
        if len_sq == 0.0 {
            return (0.0, self.price3 - self.price1);
        }

        let t = ((self.bar3 - self.bar1) * dx + (self.price3 - self.price1) * dy) / len_sq;
        let proj_bar = self.bar1 + t * dx;
        let proj_price = self.price1 + t * dy;

        (self.bar3 - proj_bar, self.price3 - proj_price)
    }
}

impl Primitive for FibChannel {
    fn type_id(&self) -> &'static str {
        "fib_channel"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Fibonacci
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar3, self.price3),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.bar1 = bar;
            self.price1 = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            self.bar2 = bar;
            self.price2 = price;
        }
        if let Some(&(bar, price)) = points.get(2) {
            self.bar3 = bar;
            self.price3 = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.bar3 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
        self.price3 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let chart_width = ctx.chart_width();

        // Calculate channel offset (perpendicular from baseline to point 3)
        let (offset_bar, offset_price) = self.channel_offset();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw each channel level line
        for &level in &self.levels {
            let lx1 = ctx.bar_to_x(self.bar1 + offset_bar * level);
            let ly1 = ctx.price_to_y(self.price1 + offset_price * level);
            let lx2 = ctx.bar_to_x(self.bar2 + offset_bar * level);
            let ly2 = ctx.price_to_y(self.price2 + offset_price * level);

            ctx.begin_path();
            if self.extend {
                // Extend the line in both directions
                let dx = lx2 - lx1;
                let dy = ly2 - ly1;
                let len = (dx * dx + dy * dy).sqrt();
                if len > 0.0 {
                    let ext = chart_width * 2.0;
                    let nx = dx / len;
                    let ny = dy / len;
                    ctx.move_to(crisp(lx1 - nx * ext, dpr), crisp(ly1 - ny * ext, dpr));
                    ctx.line_to(crisp(lx2 + nx * ext, dpr), crisp(ly2 + ny * ext, dpr));
                }
            } else {
                ctx.move_to(crisp(lx1, dpr), crisp(ly1, dpr));
                ctx.line_to(crisp(lx2, dpr), crisp(ly2, dpr));
            }
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let x3 = ctx.bar_to_x(self.bar3);
        let y3 = ctx.price_to_y(self.price3);

        // Position text based on alignment within the fib tool area (use all 3 points)
        let x = match text.h_align {
            TextAlign::Start => x1.min(x2).min(x3) + 10.0,
            TextAlign::Center => (x1 + x2 + x3) / 3.0,
            TextAlign::End => x1.max(x2).max(x3) - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => y1.min(y2).min(y3) + 10.0 + text.font_size / 2.0,
            TextAlign::Center => (y1 + y2 + y3) / 3.0,
            TextAlign::End => y1.max(y2).max(y3) - 10.0 - text.font_size / 2.0,
        };

        Some(TextAnchor::new(x, y, &self.data.color.stroke))
    }

    fn level_configs(&self) -> Option<Vec<FibLevelConfig>> {
        Some(
            self.levels
                .iter()
                .map(|&level| FibLevelConfig::new(level))
                .collect(),
        )
    }

    fn set_level_configs(&mut self, configs: Vec<FibLevelConfig>) -> bool {
        self.levels = configs.iter().map(|c| c.level).collect();
        true
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

fn create_fib_channel(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    let (bar3, price3) = points.get(2).copied().unwrap_or((bar1, price1 + 20.0));
    Box::new(FibChannel::new(
        bar1, price1, bar2, price2, bar3, price3, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_channel",
        display_name: "Fib Channel",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_channel,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
