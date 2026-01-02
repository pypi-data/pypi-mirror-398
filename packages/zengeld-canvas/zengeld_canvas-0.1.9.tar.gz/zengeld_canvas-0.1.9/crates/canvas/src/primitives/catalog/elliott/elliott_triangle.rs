//! Elliott Triangle - ABCDE corrective pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ElliottTriangle {
    pub data: PrimitiveData,
    pub points: [(f64, f64); 6], // Start, A, B, C, D, E
    #[serde(default = "default_true")]
    pub show_labels: bool,
    #[serde(default = "default_true")]
    pub show_trendlines: bool,
}
fn default_true() -> bool {
    true
}

impl ElliottTriangle {
    pub fn new(points: [(f64, f64); 6], color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "elliott_triangle".to_string(),
                display_name: "Elliott Triangle".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            points,
            show_labels: true,
            show_trendlines: true,
        }
    }
}

impl Primitive for ElliottTriangle {
    fn type_id(&self) -> &'static str {
        "elliott_triangle"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Pattern
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        self.points.to_vec()
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        for (i, &p) in pts.iter().take(6).enumerate() {
            self.points[i] = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        for p in &mut self.points {
            p.0 += bd;
            p.1 += pd;
        }
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();

        // Convert points to screen coordinates
        let screen: Vec<(f64, f64)> = self
            .points
            .iter()
            .map(|(bar, price)| (ctx.bar_to_x(*bar), ctx.price_to_y(*price)))
            .collect();

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

        // Draw wave lines (Start->A->B->C->D->E)
        ctx.begin_path();
        ctx.move_to(crisp(screen[0].0, dpr), crisp(screen[0].1, dpr));
        for (x, y) in screen.iter().take(6).skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        ctx.stroke();

        // Draw converging trendlines if enabled
        if self.show_trendlines {
            ctx.set_line_dash(&[4.0, 4.0]);
            ctx.set_stroke_width(self.data.width * 0.7);

            // Upper trendline connecting peaks (Start, B, D)
            ctx.begin_path();
            ctx.move_to(crisp(screen[0].0, dpr), crisp(screen[0].1, dpr));
            ctx.line_to(crisp(screen[2].0, dpr), crisp(screen[2].1, dpr));
            ctx.line_to(crisp(screen[4].0, dpr), crisp(screen[4].1, dpr));
            ctx.stroke();

            // Lower trendline connecting troughs (A, C, E)
            ctx.begin_path();
            ctx.move_to(crisp(screen[1].0, dpr), crisp(screen[1].1, dpr));
            ctx.line_to(crisp(screen[3].0, dpr), crisp(screen[3].1, dpr));
            ctx.line_to(crisp(screen[5].0, dpr), crisp(screen[5].1, dpr));
            ctx.stroke();
        }

        // Reset line dash
        ctx.set_line_dash(&[]);

        // Draw wave labels if enabled
        if self.show_labels {
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.set_font("12px sans-serif");
            ctx.set_text_align(super::super::render::TextAlign::Center);
            ctx.set_text_baseline(super::super::render::TextBaseline::Middle);

            let labels = ["Start", "A", "B", "C", "D", "E"];
            for (i, label) in labels.iter().enumerate() {
                let (x, y) = screen[i];
                // Position label above or below the point based on vertical direction
                let offset = if i > 0 && screen[i].1 < screen[i - 1].1 {
                    -15.0
                } else {
                    15.0
                };
                ctx.fill_text(label, x, y + offset);
            }
        }
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
        type_id: "elliott_triangle",
        display_name: "Elliott Triangle",
        kind: PrimitiveKind::Pattern,
        factory: |points, color| {
            let mut arr = [(0.0, 0.0); 6];
            for (i, &p) in points.iter().take(6).enumerate() {
                arr[i] = p;
            }
            Box::new(ElliottTriangle::new(arr, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: true,
    }
}
