//! Triangle primitive
//!
//! A three-point polygon shape.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Triangle - three-point polygon
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Triangle {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Point 1 bar index
    pub bar1: f64,
    /// Point 1 price
    pub price1: f64,
    /// Point 2 bar index
    pub bar2: f64,
    /// Point 2 price
    pub price2: f64,
    /// Point 3 bar index
    pub bar3: f64,
    /// Point 3 price
    pub price3: f64,
    /// Fill the triangle
    #[serde(default = "default_true")]
    pub fill: bool,
    /// Fill opacity (0.0 - 1.0)
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
}

fn default_true() -> bool {
    true
}

fn default_fill_opacity() -> f64 {
    0.2
}

impl Triangle {
    /// Create a new triangle
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        bar3: f64,
        price3: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "triangle".to_string(),
                display_name: "Triangle".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            bar3,
            price3,
            fill: true,
            fill_opacity: 0.2,
        }
    }

    /// Get center point
    pub fn center(&self) -> (f64, f64) {
        (
            (self.bar1 + self.bar2 + self.bar3) / 3.0,
            (self.price1 + self.price2 + self.price3) / 3.0,
        )
    }
}

impl Primitive for Triangle {
    fn type_id(&self) -> &'static str {
        "triangle"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Shape
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar3, self.price3),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if !points.is_empty() {
            self.bar1 = points[0].0;
            self.price1 = points[0].1;
        }
        if points.len() >= 2 {
            self.bar2 = points[1].0;
            self.price2 = points[1].1;
        }
        if points.len() >= 3 {
            self.bar3 = points[2].0;
            self.price3 = points[2].1;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.bar3 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
        self.price3 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let x3 = ctx.bar_to_x(self.bar3);
        let y3 = ctx.price_to_y(self.price3);

        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(x1, y1);
            ctx.line_to(x2, y2);
            ctx.line_to(x3, y3);
            ctx.close_path();
            ctx.fill();
        }

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.line_to(crisp(x3, dpr), crisp(y3, dpr));
        ctx.close_path();
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Calculate triangle centroid (average of three points)
        let center_bar = (self.bar1 + self.bar2 + self.bar3) / 3.0;
        let center_price = (self.price1 + self.price2 + self.price3) / 3.0;

        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let x3 = ctx.bar_to_x(self.bar3);
        let y3 = ctx.price_to_y(self.price3);

        // Find bounding box
        let min_x = x1.min(x2).min(x3);
        let max_x = x1.max(x2).max(x3);
        let min_y = y1.min(y2).min(y3);
        let max_y = y1.max(y2).max(y3);

        // Position based on alignment
        let x = match text.h_align {
            TextAlign::Start => min_x + 10.0,
            TextAlign::Center => ctx.bar_to_x(center_bar),
            TextAlign::End => max_x - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => min_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => ctx.price_to_y(center_price),
            TextAlign::End => max_y - 10.0 - text.font_size / 2.0,
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

// =============================================================================
// Factory Registration
// =============================================================================

fn create_triangle(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 100.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 * 1.05));
    let (bar3, price3) = points
        .get(2)
        .copied()
        .unwrap_or((bar1 + 5.0, price1 * 0.95));
    Box::new(Triangle::new(
        bar1, price1, bar2, price2, bar3, price3, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "triangle",
        display_name: "Triangle",
        kind: PrimitiveKind::Shape,
        factory: create_triangle,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
