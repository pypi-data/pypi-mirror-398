//! Arrow Line primitive - line segment with arrowhead

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ArrowLine {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub price1: f64,
    pub bar2: f64,
    pub price2: f64,
    #[serde(default)]
    pub arrow_start: bool,
    #[serde(default = "default_true")]
    pub arrow_end: bool,
    #[serde(default = "default_arrow_size")]
    pub arrow_size: f64,
}
fn default_true() -> bool {
    true
}
fn default_arrow_size() -> f64 {
    12.0
}

impl ArrowLine {
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "arrow_line".to_string(),
                display_name: "Arrow Line".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            arrow_start: false,
            arrow_end: true,
            arrow_size: 12.0,
        }
    }
}

impl Primitive for ArrowLine {
    fn type_id(&self) -> &'static str {
        "arrow_line"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Annotation
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
        if let Some(&(b, p)) = points.first() {
            self.bar1 = b;
            self.price1 = p;
        }
        if let Some(&(b, p)) = points.get(1) {
            self.bar2 = b;
            self.price2 = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.price1 += pd;
        self.price2 += pd;
    }
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw line
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);

        // Calculate direction
        let dx = x2 - x1;
        let dy = y2 - y1;
        let len = (dx * dx + dy * dy).sqrt();
        if len > 0.0 {
            let nx = dx / len;
            let ny = dy / len;

            ctx.set_fill_color(&self.data.color.stroke);

            // Draw arrowhead at end
            if self.arrow_end {
                let ax = x2;
                let ay = y2;
                let s = self.arrow_size;
                ctx.begin_path();
                ctx.move_to(crisp(ax, dpr), crisp(ay, dpr));
                ctx.line_to(
                    crisp(ax - nx * s - ny * s * 0.4, dpr),
                    crisp(ay - ny * s + nx * s * 0.4, dpr),
                );
                ctx.line_to(
                    crisp(ax - nx * s + ny * s * 0.4, dpr),
                    crisp(ay - ny * s - nx * s * 0.4, dpr),
                );
                ctx.close_path();
                ctx.fill();
            }

            // Draw arrowhead at start
            if self.arrow_start {
                let ax = x1;
                let ay = y1;
                let s = self.arrow_size;
                ctx.begin_path();
                ctx.move_to(crisp(ax, dpr), crisp(ay, dpr));
                ctx.line_to(
                    crisp(ax + nx * s - ny * s * 0.4, dpr),
                    crisp(ay + ny * s + nx * s * 0.4, dpr),
                );
                ctx.line_to(
                    crisp(ax + nx * s + ny * s * 0.4, dpr),
                    crisp(ay + ny * s - nx * s * 0.4, dpr),
                );
                ctx.close_path();
                ctx.fill();
            }
        }

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

        // Calculate midpoint
        let mid_x = (x1 + x2) / 2.0;
        let mid_y = (y1 + y2) / 2.0;

        // Calculate angle for text rotation
        let dx = x2 - x1;
        let dy = y2 - y1;
        let angle = dy.atan2(dx);

        // Offset text perpendicular to the line based on v_align
        let offset = 10.0 + text.font_size / 2.0;
        let perp_offset = match text.v_align {
            TextAlign::Start => -offset, // above the line
            TextAlign::Center => 0.0,
            TextAlign::End => offset, // below the line
        };

        // Calculate perpendicular vector
        let perp_x = -dy / (dx * dx + dy * dy).sqrt();
        let perp_y = dx / (dx * dx + dy * dy).sqrt();

        let text_x = mid_x + perp_x * perp_offset;
        let text_y = mid_y + perp_y * perp_offset;

        Some(TextAnchor::with_rotation(
            text_x,
            text_y,
            &self.data.color.stroke,
            angle,
        ))
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
        type_id: "arrow_line",
        display_name: "Arrow Line",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 0.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 10.0, p1));
            Box::new(ArrowLine::new(b1, p1, b2, p2, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
