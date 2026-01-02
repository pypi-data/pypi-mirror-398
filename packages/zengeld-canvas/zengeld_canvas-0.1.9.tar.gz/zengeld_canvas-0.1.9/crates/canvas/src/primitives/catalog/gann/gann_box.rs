//! Gann Box primitive
//!
//! A rectangular box divided by Gann angles.
//! Shows price/time relationships with diagonal lines.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Gann angle ratios (price/time)
pub const GANN_ANGLES: &[(f64, &str)] = &[
    (8.0, "8x1"),
    (4.0, "4x1"),
    (3.0, "3x1"),
    (2.0, "2x1"),
    (1.0, "1x1"),
    (0.5, "1x2"),
    (0.333, "1x3"),
    (0.25, "1x4"),
    (0.125, "1x8"),
];

/// Gann Box
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GannBox {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Top-left corner bar
    pub bar1: f64,
    /// Top-left corner price
    pub price1: f64,
    /// Bottom-right corner bar
    pub bar2: f64,
    /// Bottom-right corner price
    pub price2: f64,
    /// Show angle labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Show horizontal/vertical grid
    #[serde(default = "default_true")]
    pub show_grid: bool,
    /// Number of grid divisions
    #[serde(default = "default_divisions")]
    pub divisions: u8,
}

fn default_true() -> bool {
    true
}
fn default_divisions() -> u8 {
    4
}

impl GannBox {
    /// Create a new Gann box
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "gann_box".to_string(),
                display_name: "Gann Box".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            show_labels: true,
            show_grid: true,
            divisions: 4,
        }
    }
}

impl Primitive for GannBox {
    fn type_id(&self) -> &'static str {
        "gann_box"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Gann
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

        let min_x = x1.min(x2);
        let max_x = x1.max(x2);
        let min_y = y1.min(y2);
        let max_y = y1.max(y2);

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw box outline
        ctx.begin_path();
        ctx.rect(
            crisp(min_x, dpr),
            crisp(min_y, dpr),
            max_x - min_x,
            max_y - min_y,
        );
        ctx.stroke();

        // Draw grid lines if enabled
        if self.show_grid && self.divisions > 1 {
            let dx = (max_x - min_x) / self.divisions as f64;
            let dy = (max_y - min_y) / self.divisions as f64;

            for i in 1..self.divisions {
                // Vertical grid lines
                let gx = min_x + dx * i as f64;
                ctx.begin_path();
                ctx.move_to(crisp(gx, dpr), crisp(min_y, dpr));
                ctx.line_to(crisp(gx, dpr), crisp(max_y, dpr));
                ctx.stroke();

                // Horizontal grid lines
                let gy = min_y + dy * i as f64;
                ctx.begin_path();
                ctx.move_to(crisp(min_x, dpr), crisp(gy, dpr));
                ctx.line_to(crisp(max_x, dpr), crisp(gy, dpr));
                ctx.stroke();
            }
        }

        // Draw main diagonal (1x1)
        ctx.begin_path();
        ctx.move_to(crisp(min_x, dpr), crisp(min_y, dpr));
        ctx.line_to(crisp(max_x, dpr), crisp(max_y, dpr));
        ctx.stroke();

        // Draw anti-diagonal
        ctx.begin_path();
        ctx.move_to(crisp(min_x, dpr), crisp(max_y, dpr));
        ctx.line_to(crisp(max_x, dpr), crisp(min_y, dpr));
        ctx.stroke();

        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Calculate bounding box
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let left_x = x1.min(x2);
        let right_x = x1.max(x2);
        let top_y = y1.min(y2);
        let bottom_y = y1.max(y2);

        let x = match text.h_align {
            TextAlign::Start => left_x + 10.0,
            TextAlign::Center => (left_x + right_x) / 2.0,
            TextAlign::End => right_x - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => top_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => (top_y + bottom_y) / 2.0,
            TextAlign::End => bottom_y - 10.0 - text.font_size / 2.0,
        };

        Some(TextAnchor::new(x, y, &self.data.color.stroke))
    }

    fn level_configs(&self) -> Option<Vec<FibLevelConfig>> {
        None
    }

    fn set_level_configs(&mut self, _configs: Vec<FibLevelConfig>) -> bool {
        false
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

fn create_gann_box(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 - 10.0));
    Box::new(GannBox::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "gann_box",
        display_name: "Gann Box",
        kind: PrimitiveKind::Gann,
        factory: create_gann_box,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
