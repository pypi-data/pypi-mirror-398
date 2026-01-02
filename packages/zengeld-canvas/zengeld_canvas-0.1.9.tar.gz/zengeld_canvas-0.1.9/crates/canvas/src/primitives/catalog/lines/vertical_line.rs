//! Vertical Line primitive
//!
//! A vertical line at a specific bar/time.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Vertical Line at a bar index
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VerticalLine {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Bar index (f64 for sub-bar precision)
    pub bar_idx: f64,
    /// Show time label on scale
    #[serde(default = "default_true")]
    pub show_time_label: bool,
}

fn default_true() -> bool {
    true
}

impl VerticalLine {
    /// Create a new vertical line
    pub fn new(bar_idx: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "vertical_line".to_string(),
                display_name: "Vertical Line".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar_idx,
            show_time_label: true,
        }
    }

    /// Create from integer bar index
    pub fn from_bar(bar_idx: usize, color: &str) -> Self {
        Self::new(bar_idx as f64, color)
    }
}

impl Primitive for VerticalLine {
    fn type_id(&self) -> &'static str {
        "vertical_line"
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
        // Return (bar, 0) - price doesn't matter for vertical line
        vec![(self.bar_idx, 0.0)]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some((bar, _)) = points.first() {
            self.bar_idx = *bar;
        }
    }

    fn translate(&mut self, bar_delta: f64, _price_delta: f64) {
        self.bar_idx += bar_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar_idx);
        let crisp_x = crisp(x, dpr);

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

        // Draw vertical line across entire chart
        ctx.begin_path();
        ctx.move_to(crisp_x, 0.0);
        ctx.line_to(crisp_x, ctx.chart_height());
        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);

        // Selection rendering handled by UI layer
        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar_idx);
        let chart_height = ctx.chart_height();

        // v_align: Start=top, Center=center, End=bottom
        let y = match text.v_align {
            TextAlign::Start => 50.0,
            TextAlign::Center => chart_height / 2.0,
            TextAlign::End => chart_height - 50.0,
        };

        // h_align: Start=left of line, Center=on line, End=right of line
        let text_offset = 8.0 + text.font_size / 2.0;
        let x_offset = match text.h_align {
            TextAlign::Start => -text_offset,
            TextAlign::Center => 0.0,
            TextAlign::End => text_offset,
        };

        Some(TextAnchor::new(x + x_offset, y, &self.data.color.stroke))
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

fn create_vertical_line(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let bar_idx = points.first().map(|(b, _)| *b).unwrap_or(0.0);
    Box::new(VerticalLine::new(bar_idx, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "vertical_line",
        display_name: "Vertical Line",
        kind: PrimitiveKind::Line,
        factory: create_vertical_line,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
