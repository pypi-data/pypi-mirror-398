//! Head and Shoulders primitive - reversal pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HeadShoulders {
    pub data: PrimitiveData,
    pub points: [(f64, f64); 7], // Left shoulder start, LS top, LS end/Head start, Head top, Head end/RS start, RS top, RS end
    #[serde(default = "default_true")]
    pub show_neckline: bool,
    #[serde(default)]
    pub inverted: bool,
}
fn default_true() -> bool {
    true
}

impl HeadShoulders {
    pub fn new(points: [(f64, f64); 7], color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "head_shoulders".to_string(),
                display_name: "Head & Shoulders".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            points,
            show_neckline: true,
            inverted: false,
        }
    }
}

impl Primitive for HeadShoulders {
    fn type_id(&self) -> &'static str {
        "head_shoulders"
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
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let screen: Vec<_> = self
            .points
            .iter()
            .map(|(b, p)| (ctx.bar_to_x(*b), ctx.price_to_y(*p)))
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

        // Draw the pattern lines (7 points connected)
        ctx.begin_path();
        ctx.move_to(crisp(screen[0].0, dpr), crisp(screen[0].1, dpr));
        for (x, y) in screen.iter().skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        ctx.stroke();

        // Draw neckline if enabled (connecting points 2 and 4 - the lows)
        if self.show_neckline {
            ctx.set_line_dash(&[6.0, 3.0]);
            ctx.begin_path();
            ctx.move_to(crisp(screen[2].0, dpr), crisp(screen[2].1, dpr));
            ctx.line_to(crisp(screen[4].0, dpr), crisp(screen[4].1, dpr));
            // Extend neckline
            let dx = screen[4].0 - screen[2].0;
            let dy = screen[4].1 - screen[2].1;
            ctx.line_to(
                crisp(screen[4].0 + dx * 0.5, dpr),
                crisp(screen[4].1 + dy * 0.5, dpr),
            );
            ctx.stroke();
            ctx.set_line_dash(&[]);
        }

        // Draw labels - same labels for both regular and inverted patterns
        // The visual difference comes from the point positions, not the labels
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_font("bold 11px sans-serif");
        let labels = ["", "LS", "", "H", "", "RS", ""];
        for (i, (x, y)) in screen.iter().enumerate() {
            if !labels[i].is_empty() {
                let offset = if i == 3 { -15.0 } else { 12.0 };
                ctx.fill_text(labels[i], *x - 8.0, *y + offset);
            }
        }

        let _ = is_selected;
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
        type_id: "head_shoulders",
        display_name: "Head & Shoulders",
        kind: PrimitiveKind::Pattern,
        factory: |points, color| {
            let mut arr = [(0.0, 0.0); 7];
            for (i, &p) in points.iter().take(7).enumerate() {
                arr[i] = p;
            }
            Box::new(HeadShoulders::new(arr, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: true,
    }
}
