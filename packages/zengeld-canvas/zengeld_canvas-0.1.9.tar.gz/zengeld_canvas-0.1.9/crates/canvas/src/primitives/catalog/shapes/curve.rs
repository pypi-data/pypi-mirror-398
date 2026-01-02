//! Curve primitive (Bezier)
//!
//! A quadratic Bezier curve defined by start, control, and end points.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAnchor,
};
use serde::{Deserialize, Serialize};

/// Curve - quadratic Bezier curve
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Curve {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Start point bar
    pub start_bar: f64,
    /// Start point price
    pub start_price: f64,
    /// Control point bar
    pub control_bar: f64,
    /// Control point price
    pub control_price: f64,
    /// End point bar
    pub end_bar: f64,
    /// End point price
    pub end_price: f64,
}

impl Curve {
    /// Create a new Bezier curve
    pub fn new(
        start_bar: f64,
        start_price: f64,
        control_bar: f64,
        control_price: f64,
        end_bar: f64,
        end_price: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "curve".to_string(),
                display_name: "Curve".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            start_bar,
            start_price,
            control_bar,
            control_price,
            end_bar,
            end_price,
        }
    }

    /// Evaluate the Bezier curve at parameter t (0..1)
    pub fn evaluate(&self, t: f64) -> (f64, f64) {
        let t2 = t * t;
        let mt = 1.0 - t;
        let mt2 = mt * mt;

        let bar = mt2 * self.start_bar + 2.0 * mt * t * self.control_bar + t2 * self.end_bar;
        let price =
            mt2 * self.start_price + 2.0 * mt * t * self.control_price + t2 * self.end_price;

        (bar, price)
    }

    /// Get points along the curve for rendering
    pub fn sample_points(&self, num_points: usize) -> Vec<(f64, f64)> {
        (0..=num_points)
            .map(|i| {
                let t = i as f64 / num_points as f64;
                self.evaluate(t)
            })
            .collect()
    }
}

impl Primitive for Curve {
    fn type_id(&self) -> &'static str {
        "curve"
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
            (self.start_bar, self.start_price),
            (self.control_bar, self.control_price),
            (self.end_bar, self.end_price),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if !points.is_empty() {
            self.start_bar = points[0].0;
            self.start_price = points[0].1;
        }
        if points.len() >= 2 {
            self.end_bar = points[1].0;
            self.end_price = points[1].1;
            // Default control point to midpoint above
            self.control_bar = (self.start_bar + self.end_bar) / 2.0;
            self.control_price = (self.start_price + self.end_price) / 2.0
                + (self.start_price - self.end_price).abs() * 0.3;
        }
        if points.len() >= 3 {
            self.control_bar = points[2].0;
            self.control_price = points[2].1;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.start_bar += bar_delta;
        self.start_price += price_delta;
        self.control_bar += bar_delta;
        self.control_price += price_delta;
        self.end_bar += bar_delta;
        self.end_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let sx1 = ctx.bar_to_x(self.start_bar);
        let sy1 = ctx.price_to_y(self.start_price);
        let scx = ctx.bar_to_x(self.control_bar);
        let scy = ctx.price_to_y(self.control_price);
        let sx2 = ctx.bar_to_x(self.end_bar);
        let sy2 = ctx.price_to_y(self.end_price);

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
        ctx.move_to(sx1, sy1);
        ctx.quadratic_curve_to(scx, scy, sx2, sy2);
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Use midpoint of curve (t=0.5) as text anchor
        let (mid_bar, mid_price) = self.evaluate(0.5);
        let x = ctx.bar_to_x(mid_bar);
        let y = ctx.price_to_y(mid_price);

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

fn create_curve(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (start_bar, start_price) = points.first().copied().unwrap_or((0.0, 100.0));
    let (end_bar, end_price) = points
        .get(1)
        .copied()
        .unwrap_or((start_bar + 20.0, start_price));
    let (control_bar, control_price) = points.get(2).copied().unwrap_or((
        (start_bar + end_bar) / 2.0,
        (start_price + end_price) / 2.0 + (start_price - end_price).abs() * 0.3,
    ));
    Box::new(Curve::new(
        start_bar,
        start_price,
        control_bar,
        control_price,
        end_bar,
        end_price,
        color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "curve",
        display_name: "Curve",
        kind: PrimitiveKind::Shape,
        factory: create_curve,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
