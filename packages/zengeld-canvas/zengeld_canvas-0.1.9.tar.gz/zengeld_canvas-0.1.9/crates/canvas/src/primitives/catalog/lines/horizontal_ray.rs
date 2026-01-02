//! Horizontal Ray primitive
//!
//! A horizontal line from a single point extending infinitely to the right.
//! Useful for marking support/resistance levels from a specific bar.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Horizontal Ray - horizontal line extending right from a point
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HorizontalRay {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Starting bar index
    pub bar: f64,
    /// Price level
    pub price: f64,
    /// Show price label on the right
    #[serde(default = "default_true")]
    pub show_price_label: bool,
}

fn default_true() -> bool {
    true
}

impl HorizontalRay {
    /// Create a new horizontal ray
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "horizontal_ray".to_string(),
                display_name: "Horizontal Ray".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            show_price_label: true,
        }
    }
}

impl Primitive for HorizontalRay {
    fn type_id(&self) -> &'static str {
        "horizontal_ray"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Line
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar, self.price)]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.bar = bar;
            self.price = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar += bar_delta;
        self.price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let crisp_y = crisp(y, dpr);

        // Set stroke style
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Set line dash based on style
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw horizontal ray from point to right edge
        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), crisp_y);
        ctx.line_to(ctx.chart_width(), crisp_y);
        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let y = ctx.price_to_y(self.price);
        let start_x = ctx.bar_to_x(self.bar);
        let chart_width = ctx.chart_width();

        // h_align: Start=at bar, Center=middle of ray, End=right edge
        let x = match text.h_align {
            TextAlign::Start => start_x + 50.0,
            TextAlign::Center => (start_x + chart_width) / 2.0,
            TextAlign::End => chart_width - 50.0,
        };

        // v_align: Start=above, Center=on line, End=below
        let text_offset = 8.0 + text.font_size / 2.0;
        let y_offset = match text.v_align {
            TextAlign::Start => -text_offset,
            TextAlign::Center => 0.0,
            TextAlign::End => text_offset,
        };

        Some(TextAnchor::new(x, y + y_offset, &self.data.color.stroke))
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

fn create_horizontal_ray(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar, price) = points.first().copied().unwrap_or((0.0, 0.0));
    Box::new(HorizontalRay::new(bar, price, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "horizontal_ray",
        display_name: "Horizontal Ray",
        kind: PrimitiveKind::Line,
        factory: create_horizontal_ray,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
