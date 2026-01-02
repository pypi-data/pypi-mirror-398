//! Cycle Lines - vertical lines at regular intervals

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CycleLines {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub bar2: f64, // Define the cycle period
    #[serde(default = "default_count")]
    pub count: u8,
    #[serde(default = "default_true")]
    pub extend_left: bool,
    #[serde(default = "default_true")]
    pub extend_right: bool,
}
fn default_count() -> u8 {
    10
}
fn default_true() -> bool {
    true
}

impl CycleLines {
    pub fn new(bar1: f64, bar2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "cycle_lines".to_string(),
                display_name: "Cycle Lines".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            bar2,
            count: 10,
            extend_left: true,
            extend_right: true,
        }
    }
    pub fn period(&self) -> f64 {
        (self.bar2 - self.bar1).abs()
    }
}

impl Primitive for CycleLines {
    fn type_id(&self) -> &'static str {
        "cycle_lines"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Measurement
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar1, 0.0), (self.bar2, 0.0)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, _)) = pts.first() {
            self.bar1 = b;
        }
        if let Some(&(b, _)) = pts.get(1) {
            self.bar2 = b;
        }
    }
    fn translate(&mut self, bd: f64, _pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
    }
    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let x2 = ctx.bar_to_x(self.bar2);
        let period = (x2 - x1).abs();

        if period < 0.1 {
            return; // Period too small to render
        }

        // Draw vertical lines at regular intervals
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[5.0, 5.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 3.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        let chart_top = 0.0;
        let chart_bottom = ctx.canvas_height();

        // Determine starting position and number of lines to draw
        let start_x = if self.extend_left {
            x1.min(x2) - (self.count as f64) * period
        } else {
            x1.min(x2)
        };

        let total_lines = if self.extend_left && self.extend_right {
            self.count * 3
        } else if self.extend_left || self.extend_right {
            self.count * 2
        } else {
            self.count
        };

        for i in 0..total_lines {
            let line_x = start_x + (i as f64) * period;
            ctx.begin_path();
            ctx.move_to(crisp(line_x, dpr), crisp(chart_top, dpr));
            ctx.line_to(crisp(line_x, dpr), crisp(chart_bottom, dpr));
            ctx.stroke();
        }
    }
    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Use bounding box from the two control points
        let x1 = ctx.bar_to_x(self.bar1);
        let x2 = ctx.bar_to_x(self.bar2);
        let left_x = x1.min(x2);
        let right_x = x1.max(x2);

        // Vertical range is the full chart height
        let top_y = 0.0;
        let bottom_y = ctx.canvas_height();

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
    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "cycle_lines",
        display_name: "Cycle Lines",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b1, _) = points.first().copied().unwrap_or((0.0, 0.0));
            let (b2, _) = points.get(1).copied().unwrap_or((b1 + 20.0, 0.0));
            Box::new(CycleLines::new(b1, b2, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
