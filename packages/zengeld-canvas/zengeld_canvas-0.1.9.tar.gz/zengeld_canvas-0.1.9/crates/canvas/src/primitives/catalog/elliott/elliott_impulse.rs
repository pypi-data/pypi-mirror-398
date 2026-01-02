//! Elliott Impulse Wave - 5-wave motive pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ElliottImpulse {
    pub data: PrimitiveData,
    pub points: [(f64, f64); 6], // 0, 1, 2, 3, 4, 5
    #[serde(default = "default_true")]
    pub show_labels: bool,
    #[serde(default)]
    pub degree: WaveDegree,
}
fn default_true() -> bool {
    true
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Default)]
pub enum WaveDegree {
    #[default]
    Intermediate,
    Primary,
    Cycle,
    Supercycle,
    Minor,
    Minute,
    Minuette,
}

impl ElliottImpulse {
    pub fn new(points: [(f64, f64); 6], color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "elliott_impulse".to_string(),
                display_name: "Elliott Impulse Wave".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            points,
            show_labels: true,
            degree: WaveDegree::Intermediate,
        }
    }
}

impl Primitive for ElliottImpulse {
    fn type_id(&self) -> &'static str {
        "elliott_impulse"
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

        // Draw wave lines (0->1->2->3->4->5)
        ctx.begin_path();
        ctx.move_to(crisp(screen[0].0, dpr), crisp(screen[0].1, dpr));
        for (x, y) in screen.iter().take(6).skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);

        // Draw wave labels if enabled
        if self.show_labels {
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.set_font("12px sans-serif");
            ctx.set_text_align(super::super::render::TextAlign::Center);
            ctx.set_text_baseline(super::super::render::TextBaseline::Middle);

            let labels = ["0", "1", "2", "3", "4", "5"];
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

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get all points and find bounding box
        let points = self.points(); // Use the points() method
        if points.is_empty() {
            return None;
        }

        let mut min_bar = f64::MAX;
        let mut max_bar = f64::MIN;
        let mut min_price = f64::MAX;
        let mut max_price = f64::MIN;

        for (bar, price) in &points {
            min_bar = min_bar.min(*bar);
            max_bar = max_bar.max(*bar);
            min_price = min_price.min(*price);
            max_price = max_price.max(*price);
        }

        let left_x = ctx.bar_to_x(min_bar);
        let right_x = ctx.bar_to_x(max_bar);
        let top_y = ctx.price_to_y(max_price);
        let bottom_y = ctx.price_to_y(min_price);

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
        type_id: "elliott_impulse",
        display_name: "Elliott Impulse Wave",
        kind: PrimitiveKind::Pattern,
        factory: |points, color| {
            let mut arr = [(0.0, 0.0); 6];
            for (i, &p) in points.iter().take(6).enumerate() {
                arr[i] = p;
            }
            Box::new(ElliottImpulse::new(arr, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: true,
    }
}
