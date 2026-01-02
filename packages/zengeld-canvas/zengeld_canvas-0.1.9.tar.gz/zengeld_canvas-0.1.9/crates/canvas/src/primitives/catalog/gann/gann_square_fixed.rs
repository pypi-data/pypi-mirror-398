//! Gann Square Fixed primitive
//!
//! A fixed-size Gann square based on a single point.
//! The square maintains equal price/time units.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Gann Square Fixed
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GannSquareFixed {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar
    pub center_bar: f64,
    /// Center price
    pub center_price: f64,
    /// Size in bars (horizontal)
    pub bar_size: f64,
    /// Size in price (vertical) - typically equal to bar_size * price_per_bar
    pub price_size: f64,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Show spiral numbers
    #[serde(default)]
    pub show_numbers: bool,
}

fn default_true() -> bool {
    true
}

impl GannSquareFixed {
    /// Create a new fixed Gann square
    pub fn new(center_bar: f64, center_price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "gann_square_fixed".to_string(),
                display_name: "Gann Square Fixed".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            center_bar,
            center_price,
            bar_size: 20.0,
            price_size: 10.0,
            show_labels: true,
            show_numbers: false,
        }
    }

    /// Get the corners of the square
    pub fn corners(&self) -> [(f64, f64); 4] {
        let half_bar = self.bar_size / 2.0;
        let half_price = self.price_size / 2.0;
        [
            (self.center_bar - half_bar, self.center_price + half_price), // top-left
            (self.center_bar + half_bar, self.center_price + half_price), // top-right
            (self.center_bar + half_bar, self.center_price - half_price), // bottom-right
            (self.center_bar - half_bar, self.center_price - half_price), // bottom-left
        ]
    }
}

impl Primitive for GannSquareFixed {
    fn type_id(&self) -> &'static str {
        "gann_square_fixed"
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
        // Return center and corner (for two-point creation)
        vec![
            (self.center_bar, self.center_price),
            (
                self.center_bar + self.bar_size / 2.0,
                self.center_price + self.price_size / 2.0,
            ),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.center_bar = bar;
            self.center_price = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            // Second point defines the corner, so calculate size
            self.bar_size = ((bar - self.center_bar).abs() * 2.0).max(1.0);
            self.price_size = ((price - self.center_price).abs() * 2.0).max(1.0);
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.center_bar += bar_delta;
        self.center_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let cx = ctx.bar_to_x(self.center_bar);
        let cy = ctx.price_to_y(self.center_price);

        let corners = self.corners();
        let screen_corners: Vec<(f64, f64)> = corners
            .iter()
            .map(|(bar, price)| (ctx.bar_to_x(*bar), ctx.price_to_y(*price)))
            .collect();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw square outline
        ctx.begin_path();
        ctx.move_to(
            crisp(screen_corners[0].0, dpr),
            crisp(screen_corners[0].1, dpr),
        );
        for &(x, y) in &screen_corners[1..] {
            ctx.line_to(crisp(x, dpr), crisp(y, dpr));
        }
        ctx.close_path();
        ctx.stroke();

        // Draw diagonals
        ctx.begin_path();
        ctx.move_to(
            crisp(screen_corners[0].0, dpr),
            crisp(screen_corners[0].1, dpr),
        );
        ctx.line_to(
            crisp(screen_corners[2].0, dpr),
            crisp(screen_corners[2].1, dpr),
        );
        ctx.stroke();

        ctx.begin_path();
        ctx.move_to(
            crisp(screen_corners[1].0, dpr),
            crisp(screen_corners[1].1, dpr),
        );
        ctx.line_to(
            crisp(screen_corners[3].0, dpr),
            crisp(screen_corners[3].1, dpr),
        );
        ctx.stroke();

        // Draw cardinal lines through center
        let min_x = screen_corners
            .iter()
            .map(|(x, _)| *x)
            .fold(f64::INFINITY, f64::min);
        let max_x = screen_corners
            .iter()
            .map(|(x, _)| *x)
            .fold(f64::NEG_INFINITY, f64::max);
        let min_y = screen_corners
            .iter()
            .map(|(_, y)| *y)
            .fold(f64::INFINITY, f64::min);
        let max_y = screen_corners
            .iter()
            .map(|(_, y)| *y)
            .fold(f64::NEG_INFINITY, f64::max);

        ctx.begin_path();
        ctx.move_to(crisp(min_x, dpr), crisp(cy, dpr));
        ctx.line_to(crisp(max_x, dpr), crisp(cy, dpr));
        ctx.stroke();

        ctx.begin_path();
        ctx.move_to(crisp(cx, dpr), crisp(min_y, dpr));
        ctx.line_to(crisp(cx, dpr), crisp(max_y, dpr));
        ctx.stroke();

        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Calculate bounding box from corners
        let corners = self.corners();
        let left_x = ctx.bar_to_x(corners[3].0); // bottom-left bar
        let right_x = ctx.bar_to_x(corners[1].0); // top-right bar
        let top_y = ctx.price_to_y(corners[0].1); // top-left price
        let bottom_y = ctx.price_to_y(corners[2].1); // bottom-right price

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

fn create_gann_square_fixed(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar, price) = points.first().copied().unwrap_or((0.0, 100.0));
    let mut gann = GannSquareFixed::new(bar, price, color);
    if let Some(&(bar2, price2)) = points.get(1) {
        gann.bar_size = ((bar2 - bar).abs() * 2.0).max(1.0);
        gann.price_size = ((price2 - price).abs() * 2.0).max(1.0);
    }
    Box::new(gann)
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "gann_square_fixed",
        display_name: "Gann Square Fixed",
        kind: PrimitiveKind::Gann,
        factory: create_gann_square_fixed,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
