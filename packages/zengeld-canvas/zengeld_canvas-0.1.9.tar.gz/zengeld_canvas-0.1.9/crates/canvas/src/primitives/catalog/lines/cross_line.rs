//! Cross Line primitive
//!
//! A crosshair consisting of a horizontal and vertical line
//! crossing at a single point. Extends across the entire chart.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Cross Line - intersecting horizontal and vertical lines
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CrossLine {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar index
    pub bar: f64,
    /// Center price
    pub price: f64,
    /// Show price label
    #[serde(default = "default_true")]
    pub show_price_label: bool,
    /// Show bar/time label
    #[serde(default = "default_true")]
    pub show_bar_label: bool,
}

fn default_true() -> bool {
    true
}

impl CrossLine {
    /// Create a new cross line
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "cross_line".to_string(),
                display_name: "Cross Line".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar,
            price,
            show_price_label: true,
            show_bar_label: true,
        }
    }
}

impl Primitive for CrossLine {
    fn type_id(&self) -> &'static str {
        "cross_line"
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
        let cx = ctx.bar_to_x(self.bar);
        let cy = ctx.price_to_y(self.price);
        let crisp_x = crisp(cx, dpr);
        let crisp_y = crisp(cy, dpr);

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

        // Draw horizontal line across entire chart
        ctx.begin_path();
        ctx.move_to(0.0, crisp_y);
        ctx.line_to(ctx.chart_width(), crisp_y);
        ctx.stroke();

        // Draw vertical line across entire chart
        ctx.begin_path();
        ctx.move_to(crisp_x, 0.0);
        ctx.line_to(crisp_x, ctx.chart_height());
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

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);

        // Position text offset from the cross center
        let text_offset = 8.0 + text.font_size / 2.0;

        // h_align + v_align control quadrant placement
        let x_offset = match text.h_align {
            TextAlign::Start => -text_offset, // left
            TextAlign::Center => 0.0,         // center
            TextAlign::End => text_offset,    // right
        };

        let y_offset = match text.v_align {
            TextAlign::Start => -text_offset, // above
            TextAlign::Center => 0.0,         // center
            TextAlign::End => text_offset,    // below
        };

        Some(TextAnchor::new(
            x + x_offset,
            y + y_offset,
            &self.data.color.stroke,
        ))
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

fn create_cross_line(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar, price) = points.first().copied().unwrap_or((0.0, 0.0));
    Box::new(CrossLine::new(bar, price, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "cross_line",
        display_name: "Cross Line",
        kind: PrimitiveKind::Line,
        factory: create_cross_line,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
