//! Fibonacci Trend Time primitive
//!
//! Vertical lines projected at Fibonacci ratios from a trend.
//! Uses two points to define a time range, then projects Fib levels.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Default trend time levels
pub const DEFAULT_TIME_LEVELS: &[f64] = &[
    0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618,
];

/// Fibonacci Trend Time - vertical lines at Fib ratios of time range
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibTrendTime {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Start bar
    pub bar1: f64,
    /// Start price (for anchor display)
    pub price1: f64,
    /// End bar
    pub bar2: f64,
    /// End price
    pub price2: f64,
    /// Time levels
    #[serde(default = "default_time_levels")]
    pub levels: Vec<f64>,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
}

fn default_true() -> bool {
    true
}
fn default_time_levels() -> Vec<f64> {
    DEFAULT_TIME_LEVELS.to_vec()
}

impl FibTrendTime {
    /// Create new Fibonacci trend time
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_trend_time".to_string(),
                display_name: "Fib Trend Time".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            levels: DEFAULT_TIME_LEVELS.to_vec(),
            show_labels: true,
        }
    }

    /// Get bar position for a level
    pub fn bar_at_level(&self, level: f64) -> f64 {
        self.bar1 + (self.bar2 - self.bar1) * level
    }
}

impl Primitive for FibTrendTime {
    fn type_id(&self) -> &'static str {
        "fib_trend_time"
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
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
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
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let chart_height = ctx.chart_height();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw baseline connecting points
        ctx.set_line_dash(&[4.0, 4.0]);
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Draw vertical lines at each Fibonacci time level
        ctx.set_line_dash(&[]);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        for &level in &self.levels {
            let level_bar = self.bar_at_level(level);
            let level_x = ctx.bar_to_x(level_bar);

            ctx.begin_path();
            ctx.move_to(crisp(level_x, dpr), 0.0);
            ctx.line_to(crisp(level_x, dpr), chart_height);
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

fn create_fib_trend_time(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1 + 20.0, price1));
    Box::new(FibTrendTime::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_trend_time",
        display_name: "Fib Trend Time",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_trend_time,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
