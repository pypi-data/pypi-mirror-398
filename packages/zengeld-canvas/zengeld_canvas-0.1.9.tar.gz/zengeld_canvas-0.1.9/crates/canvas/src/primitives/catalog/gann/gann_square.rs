//! Gann Square primitive
//!
//! A resizable Gann square defined by two points.
//! Shows the classic Gann square with angle divisions and cardinal/ordinal lines.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Gann Square
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GannSquare {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First corner bar
    pub bar1: f64,
    /// First corner price
    pub price1: f64,
    /// Second corner bar
    pub bar2: f64,
    /// Second corner price
    pub price2: f64,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Show cardinal lines (horizontal/vertical through center)
    #[serde(default = "default_true")]
    pub show_cardinal: bool,
    /// Show ordinal lines (diagonals)
    #[serde(default = "default_true")]
    pub show_ordinal: bool,
    /// Number of levels/rings
    #[serde(default = "default_levels")]
    pub levels: u8,
}

fn default_true() -> bool {
    true
}
fn default_levels() -> u8 {
    3
}

impl GannSquare {
    /// Create a new Gann square
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "gann_square".to_string(),
                display_name: "Gann Square".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            show_labels: true,
            show_cardinal: true,
            show_ordinal: true,
            levels: 3,
        }
    }

    /// Get the center of the square
    pub fn center(&self) -> (f64, f64) {
        (
            (self.bar1 + self.bar2) / 2.0,
            (self.price1 + self.price2) / 2.0,
        )
    }
}

impl Primitive for GannSquare {
    fn type_id(&self) -> &'static str {
        "gann_square"
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
        let cx = (x1 + x2) / 2.0;
        let cy = (y1 + y2) / 2.0;

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw outer square
        ctx.begin_path();
        ctx.rect(
            crisp(min_x, dpr),
            crisp(min_y, dpr),
            max_x - min_x,
            max_y - min_y,
        );
        ctx.stroke();

        // Draw inner level squares
        for i in 1..self.levels {
            let ratio = i as f64 / self.levels as f64;
            let half_w = (max_x - min_x) / 2.0 * ratio;
            let half_h = (max_y - min_y) / 2.0 * ratio;
            ctx.begin_path();
            ctx.rect(
                crisp(cx - half_w, dpr),
                crisp(cy - half_h, dpr),
                half_w * 2.0,
                half_h * 2.0,
            );
            ctx.stroke();
        }

        // Draw cardinal lines if enabled
        if self.show_cardinal {
            // Horizontal center line
            ctx.begin_path();
            ctx.move_to(crisp(min_x, dpr), crisp(cy, dpr));
            ctx.line_to(crisp(max_x, dpr), crisp(cy, dpr));
            ctx.stroke();

            // Vertical center line
            ctx.begin_path();
            ctx.move_to(crisp(cx, dpr), crisp(min_y, dpr));
            ctx.line_to(crisp(cx, dpr), crisp(max_y, dpr));
            ctx.stroke();
        }

        // Draw ordinal lines if enabled
        if self.show_ordinal {
            // Main diagonal
            ctx.begin_path();
            ctx.move_to(crisp(min_x, dpr), crisp(min_y, dpr));
            ctx.line_to(crisp(max_x, dpr), crisp(max_y, dpr));
            ctx.stroke();

            // Anti-diagonal
            ctx.begin_path();
            ctx.move_to(crisp(min_x, dpr), crisp(max_y, dpr));
            ctx.line_to(crisp(max_x, dpr), crisp(min_y, dpr));
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

fn create_gann_square(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 - 20.0));
    Box::new(GannSquare::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "gann_square",
        display_name: "Gann Square",
        kind: PrimitiveKind::Gann,
        factory: create_gann_square,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
