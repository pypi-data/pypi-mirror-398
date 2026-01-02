//! Triangle Pattern primitive - consolidation pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Default)]
pub enum TriangleType {
    #[default]
    Symmetrical,
    Ascending,
    Descending,
    Expanding,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrianglePattern {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub price1_top: f64,
    pub price1_bottom: f64,
    pub bar2: f64,
    pub price2_top: f64,
    pub price2_bottom: f64,
    pub triangle_type: TriangleType,
    #[serde(default = "default_true")]
    pub show_labels: bool,
}
fn default_true() -> bool {
    true
}

impl TrianglePattern {
    pub fn new(
        bar1: f64,
        price1_top: f64,
        price1_bottom: f64,
        bar2: f64,
        price2_top: f64,
        price2_bottom: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "triangle_pattern".to_string(),
                display_name: "Triangle Pattern".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1_top,
            price1_bottom,
            bar2,
            price2_top,
            price2_bottom,
            triangle_type: TriangleType::Symmetrical,
            show_labels: true,
        }
    }
}

impl Primitive for TrianglePattern {
    fn type_id(&self) -> &'static str {
        "triangle_pattern"
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
        vec![
            (self.bar1, self.price1_top),
            (self.bar1, self.price1_bottom),
            (self.bar2, self.price2_top),
            (self.bar2, self.price2_bottom),
        ]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar1 = b;
            self.price1_top = p;
        }
        if let Some(&(_, p)) = pts.get(1) {
            self.price1_bottom = p;
        }
        if let Some(&(b, p)) = pts.get(2) {
            self.bar2 = b;
            self.price2_top = p;
        }
        if let Some(&(_, p)) = pts.get(3) {
            self.price2_bottom = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.price1_top += pd;
        self.price1_bottom += pd;
        self.price2_top += pd;
        self.price2_bottom += pd;
    }
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1_top = ctx.price_to_y(self.price1_top);
        let y1_bot = ctx.price_to_y(self.price1_bottom);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2_top = ctx.price_to_y(self.price2_top);
        let y2_bot = ctx.price_to_y(self.price2_bottom);

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw top trendline
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1_top, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2_top, dpr));
        ctx.stroke();

        // Draw bottom trendline
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1_bot, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2_bot, dpr));
        ctx.stroke();

        // Draw vertical bounds
        ctx.set_line_dash(&[3.0, 3.0]);
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1_top, dpr));
        ctx.line_to(crisp(x1, dpr), crisp(y1_bot, dpr));
        ctx.stroke();
        ctx.begin_path();
        ctx.move_to(crisp(x2, dpr), crisp(y2_top, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2_bot, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);

        // Fill triangle area
        ctx.set_fill_color(&format!("{}20", &self.data.color.stroke));
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1_top, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2_top, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2_bot, dpr));
        ctx.line_to(crisp(x1, dpr), crisp(y1_bot, dpr));
        ctx.close_path();
        ctx.fill();

        // Draw label
        if self.show_labels {
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.set_font("11px sans-serif");
            let label = match self.triangle_type {
                TriangleType::Symmetrical => "Sym",
                TriangleType::Ascending => "Asc",
                TriangleType::Descending => "Desc",
                TriangleType::Expanding => "Exp",
            };
            ctx.fill_text(
                label,
                (x1 + x2) / 2.0 - 10.0,
                (y1_top + y1_bot + y2_top + y2_bot) / 4.0,
            );
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
        type_id: "triangle_pattern",
        display_name: "Triangle Pattern",
        kind: PrimitiveKind::Pattern,
        factory: |points, color| {
            let (b1, p1t) = points.first().copied().unwrap_or((0.0, 100.0));
            let (_, p1b) = points.get(1).copied().unwrap_or((b1, 90.0));
            let (b2, p2t) = points.get(2).copied().unwrap_or((b1 + 20.0, 97.0));
            let (_, p2b) = points.get(3).copied().unwrap_or((b2, 93.0));
            Box::new(TrianglePattern::new(b1, p1t, p1b, b2, p2t, p2b, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: true,
    }
}
