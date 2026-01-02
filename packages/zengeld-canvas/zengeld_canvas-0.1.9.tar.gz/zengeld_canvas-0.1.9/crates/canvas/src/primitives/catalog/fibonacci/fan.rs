//! Fibonacci Fan primitive
//!
//! Fan lines radiating from a point through Fibonacci levels.
//! Similar to speed resistance but with different angle calculations.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Default fan levels
pub const DEFAULT_FAN_LEVELS: &[f64] = &[0.236, 0.382, 0.5, 0.618, 0.786];

/// Fibonacci Fan
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibFan {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Origin bar
    pub bar1: f64,
    /// Origin price
    pub price1: f64,
    /// Target bar
    pub bar2: f64,
    /// Target price
    pub price2: f64,
    /// Fan levels
    #[serde(default = "default_fan_levels")]
    pub levels: Vec<f64>,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Extend rays to edge of chart
    #[serde(default = "default_true")]
    pub extend: bool,
}

fn default_true() -> bool {
    true
}
fn default_fan_levels() -> Vec<f64> {
    DEFAULT_FAN_LEVELS.to_vec()
}

impl FibFan {
    /// Create a new Fibonacci fan
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_fan".to_string(),
                display_name: "Fib Fan".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            levels: DEFAULT_FAN_LEVELS.to_vec(),
            show_labels: true,
            extend: true,
        }
    }

    /// Get the endpoint for a fan line at given level
    /// Level determines where on the vertical price range the line passes through
    pub fn fan_endpoint(&self, level: f64) -> (f64, f64) {
        let price_range = self.price2 - self.price1;
        let fan_price = self.price1 + price_range * level;
        (self.bar2, fan_price)
    }
}

impl Primitive for FibFan {
    fn type_id(&self) -> &'static str {
        "fib_fan"
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

        // Draw baseline from point 1 to point 2
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Draw fan lines at each level
        for &level in &self.levels {
            let (fan_bar, fan_price) = self.fan_endpoint(level);
            let fx = ctx.bar_to_x(fan_bar);
            let fy = ctx.price_to_y(fan_price);

            ctx.begin_path();
            ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));

            if self.extend {
                // Extend the ray to chart edge
                let dx = fx - x1;
                let dy = fy - y1;
                let len = (dx * dx + dy * dy).sqrt();
                if len > 0.0 {
                    let ext = chart_width * 2.0;
                    let nx = dx / len;
                    let ny = dy / len;
                    ctx.line_to(crisp(x1 + nx * ext, dpr), crisp(y1 + ny * ext, dpr));
                }
            } else {
                ctx.line_to(crisp(fx, dpr), crisp(fy, dpr));
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

        // Position text based on alignment within the fib tool area
        let x = match text.h_align {
            TextAlign::Start => x1.min(x2) + 10.0,
            TextAlign::Center => (x1 + x2) / 2.0,
            TextAlign::End => x1.max(x2) - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => y1.min(y2) + 10.0 + text.font_size / 2.0,
            TextAlign::Center => (y1 + y2) / 2.0,
            TextAlign::End => y1.max(y2) - 10.0 - text.font_size / 2.0,
        };

        // Calculate rotation angle for fan tools with angled lines
        let rotation = (y2 - y1).atan2(x2 - x1);

        let mut anchor = TextAnchor::new(x, y, &self.data.color.stroke);
        anchor.rotation = rotation;
        Some(anchor)
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

fn create_fib_fan(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    Box::new(FibFan::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_fan",
        display_name: "Fib Fan",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_fan,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
