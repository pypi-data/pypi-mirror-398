//! Elliott Double Combination - WXY pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ElliottDoubleCombo {
    pub data: PrimitiveData,
    pub points: [(f64, f64); 7], // Start, W end points, X, Y end points
    #[serde(default = "default_true")]
    pub show_labels: bool,
}
fn default_true() -> bool {
    true
}

impl ElliottDoubleCombo {
    pub fn new(points: [(f64, f64); 7], color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "elliott_double_combo".to_string(),
                display_name: "Elliott Double Combo".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            points,
            show_labels: true,
        }
    }
}

impl Primitive for ElliottDoubleCombo {
    fn type_id(&self) -> &'static str {
        "elliott_double_combo"
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
        for (i, &p) in pts.iter().take(7).enumerate() {
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

        // Draw wave lines connecting all 7 points
        ctx.begin_path();
        ctx.move_to(crisp(screen[0].0, dpr), crisp(screen[0].1, dpr));
        for (x, y) in screen.iter().take(7).skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);

        // Draw wave labels if enabled (W-X-Y pattern)
        if self.show_labels {
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.set_font("12px sans-serif");
            ctx.set_text_align(super::super::render::TextAlign::Center);
            ctx.set_text_baseline(super::super::render::TextBaseline::Middle);

            // Label pattern: Start, W subwaves, X, Y subwaves
            let labels = ["W", "", "", "X", "Y", "", ""];
            for (i, label) in labels.iter().enumerate() {
                if !label.is_empty() {
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
        type_id: "elliott_double_combo",
        display_name: "Elliott Double Combo",
        kind: PrimitiveKind::Pattern,
        factory: |points, color| {
            let mut arr = [(0.0, 0.0); 7];
            for (i, &p) in points.iter().take(7).enumerate() {
                arr[i] = p;
            }
            Box::new(ElliottDoubleCombo::new(arr, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: true,
    }
}
