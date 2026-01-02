//! Fibonacci Circles primitive
//!
//! Concentric circles at Fibonacci ratios from a center point.
//! The radius is defined by a second point.

use super::super::{
    EllipseParams, LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind,
    PrimitiveMetadata, RenderContext, TextAlign, TextAnchor, config::FibLevelConfig,
};
use serde::{Deserialize, Serialize};

/// Default circle levels
pub const DEFAULT_CIRCLE_LEVELS: &[f64] = &[
    0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618,
];

/// Fibonacci Circles - concentric circles at Fib ratios
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibCircles {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar
    pub center_bar: f64,
    /// Center price
    pub center_price: f64,
    /// Edge bar (defines radius)
    pub edge_bar: f64,
    /// Edge price
    pub edge_price: f64,
    /// Circle levels
    #[serde(default = "default_circle_levels")]
    pub levels: Vec<f64>,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
}

fn default_true() -> bool {
    true
}
fn default_circle_levels() -> Vec<f64> {
    DEFAULT_CIRCLE_LEVELS.to_vec()
}

impl FibCircles {
    /// Create new Fibonacci circles
    pub fn new(
        center_bar: f64,
        center_price: f64,
        edge_bar: f64,
        edge_price: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_circles".to_string(),
                display_name: "Fib Circles".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            center_bar,
            center_price,
            edge_bar,
            edge_price,
            levels: DEFAULT_CIRCLE_LEVELS.to_vec(),
            show_labels: true,
        }
    }

    /// Get base radius in bar/price space
    pub fn base_radius(&self) -> (f64, f64) {
        (
            (self.edge_bar - self.center_bar).abs(),
            (self.edge_price - self.center_price).abs(),
        )
    }
}

impl Primitive for FibCircles {
    fn type_id(&self) -> &'static str {
        "fib_circles"
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
            (self.center_bar, self.center_price),
            (self.edge_bar, self.edge_price),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.center_bar = bar;
            self.center_price = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            self.edge_bar = bar;
            self.edge_price = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.center_bar += bar_delta;
        self.edge_bar += bar_delta;
        self.center_price += price_delta;
        self.edge_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let cx = ctx.bar_to_x(self.center_bar);
        let cy = ctx.price_to_y(self.center_price);

        // Calculate base radii from data coordinates (for proper zoom behavior)
        let (base_radius_bars, base_radius_price) = self.base_radius();
        let base_rx = (ctx.bar_to_x(self.center_bar + base_radius_bars) - cx).abs();
        let base_ry = (ctx.price_to_y(self.center_price + base_radius_price) - cy).abs();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw concentric ellipses at each level
        // Use separate rx/ry for proper ellipse behavior on zoom
        for &level in &self.levels {
            let rx = base_rx * level;
            let ry = base_ry * level;
            ctx.begin_path();
            ctx.ellipse(EllipseParams::full(cx, cy, rx, ry));
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

        let x1 = ctx.bar_to_x(self.center_bar);
        let y1 = ctx.price_to_y(self.center_price);
        let x2 = ctx.bar_to_x(self.edge_bar);
        let y2 = ctx.price_to_y(self.edge_price);

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

fn create_fib_circles(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    Box::new(FibCircles::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_circles",
        display_name: "Fib Circles",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_circles,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
