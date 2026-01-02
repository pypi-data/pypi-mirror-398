//! Fibonacci Arcs primitive
//!
//! Curved arcs at Fibonacci ratios from a baseline.
//! Arcs emanate from the second point at Fib ratios of the distance.

use super::super::{
    EllipseParams, LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind,
    PrimitiveMetadata, RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use crate::Viewport;
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

/// Default arc levels
pub const DEFAULT_ARC_LEVELS: &[f64] = &[0.236, 0.382, 0.5, 0.618, 0.786, 1.0];

/// Fibonacci Arcs
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibArcs {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First point bar
    pub bar1: f64,
    /// First point price
    pub price1: f64,
    /// Second point bar (arc center)
    pub bar2: f64,
    /// Second point price
    pub price2: f64,
    /// Arc levels
    #[serde(default = "default_arc_levels")]
    pub levels: Vec<f64>,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Full circle (360) or semi-circle
    #[serde(default)]
    pub full_circle: bool,
}

fn default_true() -> bool {
    true
}
fn default_arc_levels() -> Vec<f64> {
    DEFAULT_ARC_LEVELS.to_vec()
}

impl FibArcs {
    /// Create new Fibonacci arcs
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_arcs".to_string(),
                display_name: "Fib Arcs".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            levels: DEFAULT_ARC_LEVELS.to_vec(),
            show_labels: true,
            full_circle: false,
        }
    }

    /// Get the base radius (distance between points)
    pub fn base_distance(&self, viewport: &Viewport) -> f64 {
        let x1 = viewport.bar_to_x_f64(self.bar1);
        let y1 = viewport.price_to_y(self.price1);
        let x2 = viewport.bar_to_x_f64(self.bar2);
        let y2 = viewport.price_to_y(self.price2);

        ((x2 - x1).powi(2) + (y2 - y1).powi(2)).sqrt()
    }

    /// Get the angle of the baseline
    pub fn baseline_angle(&self, viewport: &Viewport) -> f64 {
        let x1 = viewport.bar_to_x_f64(self.bar1);
        let y1 = viewport.price_to_y(self.price1);
        let x2 = viewport.bar_to_x_f64(self.bar2);
        let y2 = viewport.price_to_y(self.price2);

        (y2 - y1).atan2(x2 - x1)
    }
}

impl Primitive for FibArcs {
    fn type_id(&self) -> &'static str {
        "fib_arcs"
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

        // Calculate base radii from data coordinates for ellipse behavior
        let base_rx = (x2 - x1).abs().max(1.0);
        let base_ry = (y2 - y1).abs().max(1.0);

        let baseline_angle = (y2 - y1).atan2(x2 - x1);

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

        // Draw elliptical arcs at each level, centered at point 2
        for &level in &self.levels {
            let rx = base_rx * level;
            let ry = base_ry * level;
            ctx.begin_path();
            if self.full_circle {
                ctx.ellipse(EllipseParams::full(x2, y2, rx, ry));
            } else {
                // Semi-ellipse facing away from point 1
                let start_angle = baseline_angle - PI / 2.0;
                let end_angle = baseline_angle + PI / 2.0;
                ctx.ellipse(EllipseParams::new(
                    x2,
                    y2,
                    rx,
                    ry,
                    0.0,
                    start_angle,
                    end_angle,
                ));
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

fn create_fib_arcs(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    Box::new(FibArcs::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_arcs",
        display_name: "Fib Arcs",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_arcs,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
