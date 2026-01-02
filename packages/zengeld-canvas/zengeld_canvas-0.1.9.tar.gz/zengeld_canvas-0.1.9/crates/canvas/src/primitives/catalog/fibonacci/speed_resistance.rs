//! Fibonacci Speed Resistance Fan primitive
//!
//! Fan lines radiating from a point at Fibonacci-based angles.
//! Also known as speed/resistance arcs - combines price and time analysis.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Default speed resistance levels
pub const DEFAULT_SPEED_LEVELS: &[f64] = &[0.25, 0.333, 0.382, 0.5, 0.618, 0.667, 0.75];

/// Fibonacci Speed Resistance Fan
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibSpeedResistance {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Origin bar
    pub bar1: f64,
    /// Origin price
    pub price1: f64,
    /// Target bar (defines the base)
    pub bar2: f64,
    /// Target price
    pub price2: f64,
    /// Speed levels
    #[serde(default = "default_speed_levels")]
    pub levels: Vec<f64>,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Reverse (flip) the fan
    #[serde(default)]
    pub reverse: bool,
}

fn default_true() -> bool {
    true
}
fn default_speed_levels() -> Vec<f64> {
    DEFAULT_SPEED_LEVELS.to_vec()
}

impl FibSpeedResistance {
    /// Create a new speed resistance fan
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_speed_resistance".to_string(),
                display_name: "Speed Resistance".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            levels: DEFAULT_SPEED_LEVELS.to_vec(),
            show_labels: true,
            reverse: false,
        }
    }
}

impl Primitive for FibSpeedResistance {
    fn type_id(&self) -> &'static str {
        "fib_speed_resistance"
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

        // Draw baseline
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        let price_range = self.price2 - self.price1;

        // Draw fan lines at each speed level
        for &level in &self.levels {
            let level_price = if self.reverse {
                self.price1 + price_range * (1.0 - level)
            } else {
                self.price1 + price_range * level
            };

            let fan_y = ctx.price_to_y(level_price);

            ctx.begin_path();
            ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));

            // Extend ray to chart edge
            let dx = x2 - x1;
            let dy = fan_y - y1;
            let len = (dx * dx + dy * dy).sqrt();
            if len > 0.0 {
                let ext = chart_width * 2.0;
                let nx = dx / len;
                let ny = dy / len;
                ctx.line_to(crisp(x1 + nx * ext, dpr), crisp(y1 + ny * ext, dpr));
            }
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

fn create_fib_speed_resistance(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    Box::new(FibSpeedResistance::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_speed_resistance",
        display_name: "Speed Resistance",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_speed_resistance,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
