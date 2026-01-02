//! Fibonacci Trend Extension primitive
//!
//! Uses three points to project Fibonacci extension levels.
//! Point 1 and 2 define the trend, Point 3 is the retracement.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Default extension levels
pub const DEFAULT_EXTENSION_LEVELS: &[f64] = &[
    0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618, 3.618, 4.236,
];

/// Fibonacci Trend Extension - three-point projection
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibTrendExtension {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First point bar (trend start)
    pub bar1: f64,
    /// First point price
    pub price1: f64,
    /// Second point bar (trend end)
    pub bar2: f64,
    /// Second point price
    pub price2: f64,
    /// Third point bar (retracement point)
    pub bar3: f64,
    /// Third point price
    pub price3: f64,
    /// Extension levels
    #[serde(default = "default_extension_levels")]
    pub levels: Vec<f64>,
    /// Show price labels
    #[serde(default = "default_true")]
    pub show_prices: bool,
    /// Show percentage labels
    #[serde(default = "default_true")]
    pub show_percentages: bool,
    /// Extend to right edge
    #[serde(default = "default_true")]
    pub extend_right: bool,
}

fn default_true() -> bool {
    true
}
fn default_extension_levels() -> Vec<f64> {
    DEFAULT_EXTENSION_LEVELS.to_vec()
}

impl FibTrendExtension {
    /// Create a new Fibonacci trend extension
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
                type_id: "fib_trend_extension".to_string(),
                display_name: "Fib Extension".to_string(),
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
            levels: DEFAULT_EXTENSION_LEVELS.to_vec(),
            show_prices: true,
            show_percentages: true,
            extend_right: true,
        }
    }

    /// Get the price at a given extension level
    /// Extensions are calculated from point 3 based on the 1-2 range
    pub fn price_at_level(&self, level: f64) -> f64 {
        let range = self.price2 - self.price1;
        self.price3 + range * level
    }
}

impl Primitive for FibTrendExtension {
    fn type_id(&self) -> &'static str {
        "fib_trend_extension"
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
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let x3 = ctx.bar_to_x(self.bar3);
        let y3 = ctx.price_to_y(self.price3);
        let chart_width = ctx.chart_width();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw trend lines 1-2 and 2-3
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.line_to(crisp(x3, dpr), crisp(y3, dpr));
        ctx.stroke();

        // Draw extension levels from point 3
        // extend_right is always true in current implementation, but
        // we keep the field for future extensibility
        let right_x = chart_width;
        for &level in &self.levels {
            let level_price = self.price_at_level(level);
            let y = ctx.price_to_y(level_price);

            ctx.begin_path();
            ctx.move_to(crisp(x3, dpr), crisp(y, dpr));
            ctx.line_to(crisp(right_x, dpr), crisp(y, dpr));
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        let _ = is_selected;
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

fn create_fib_trend_extension(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 + 10.0));
    let (bar3, price3) = points.get(2).copied().unwrap_or((bar2 + 5.0, price2 - 5.0));
    Box::new(FibTrendExtension::new(
        bar1, price1, bar2, price2, bar3, price3, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_trend_extension",
        display_name: "Fib Extension",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_trend_extension,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
