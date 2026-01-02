//! Double Curve primitive (S-curve)
//!
//! A cubic Bezier curve with two control points, creating an S-shape.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAnchor,
};
use serde::{Deserialize, Serialize};

/// Configuration for creating a DoubleCurve
#[derive(Clone, Debug)]
pub struct DoubleCurveConfig {
    /// Start point bar
    pub start_bar: f64,
    /// Start point price
    pub start_price: f64,
    /// First control point bar
    pub control1_bar: f64,
    /// First control point price
    pub control1_price: f64,
    /// Second control point bar
    pub control2_bar: f64,
    /// Second control point price
    pub control2_price: f64,
    /// End point bar
    pub end_bar: f64,
    /// End point price
    pub end_price: f64,
    /// Color
    pub color: String,
}

/// Double Curve - cubic Bezier (S-curve)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DoubleCurve {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Start point bar
    pub start_bar: f64,
    /// Start point price
    pub start_price: f64,
    /// First control point bar
    pub control1_bar: f64,
    /// First control point price
    pub control1_price: f64,
    /// Second control point bar
    pub control2_bar: f64,
    /// Second control point price
    pub control2_price: f64,
    /// End point bar
    pub end_bar: f64,
    /// End point price
    pub end_price: f64,
}

impl DoubleCurve {
    /// Create a new cubic Bezier curve from a configuration
    pub fn new(config: DoubleCurveConfig) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "double_curve".to_string(),
                display_name: "Double Curve".to_string(),
                color: PrimitiveColor::new(&config.color),
                width: 2.0,
                ..Default::default()
            },
            start_bar: config.start_bar,
            start_price: config.start_price,
            control1_bar: config.control1_bar,
            control1_price: config.control1_price,
            control2_bar: config.control2_bar,
            control2_price: config.control2_price,
            end_bar: config.end_bar,
            end_price: config.end_price,
        }
    }

    /// Evaluate the cubic Bezier curve at parameter t (0..1)
    pub fn evaluate(&self, t: f64) -> (f64, f64) {
        let t2 = t * t;
        let t3 = t2 * t;
        let mt = 1.0 - t;
        let mt2 = mt * mt;
        let mt3 = mt2 * mt;

        let bar = mt3 * self.start_bar
            + 3.0 * mt2 * t * self.control1_bar
            + 3.0 * mt * t2 * self.control2_bar
            + t3 * self.end_bar;

        let price = mt3 * self.start_price
            + 3.0 * mt2 * t * self.control1_price
            + 3.0 * mt * t2 * self.control2_price
            + t3 * self.end_price;

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

impl Primitive for DoubleCurve {
    fn type_id(&self) -> &'static str {
        "double_curve"
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
            (self.end_bar, self.end_price),
            (self.control1_bar, self.control1_price),
            (self.control2_bar, self.control2_price),
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
            // Default control points for S-curve
            let dx = self.end_bar - self.start_bar;
            let dy = self.end_price - self.start_price;
            self.control1_bar = self.start_bar + dx * 0.33;
            self.control1_price = self.start_price + dy * 0.5;
            self.control2_bar = self.start_bar + dx * 0.67;
            self.control2_price = self.end_price - dy * 0.5;
        }
        if points.len() >= 3 {
            self.control1_bar = points[2].0;
            self.control1_price = points[2].1;
        }
        if points.len() >= 4 {
            self.control2_bar = points[3].0;
            self.control2_price = points[3].1;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.start_bar += bar_delta;
        self.start_price += price_delta;
        self.control1_bar += bar_delta;
        self.control1_price += price_delta;
        self.control2_bar += bar_delta;
        self.control2_price += price_delta;
        self.end_bar += bar_delta;
        self.end_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let sx1 = ctx.bar_to_x(self.start_bar);
        let sy1 = ctx.price_to_y(self.start_price);
        let sc1x = ctx.bar_to_x(self.control1_bar);
        let sc1y = ctx.price_to_y(self.control1_price);
        let sc2x = ctx.bar_to_x(self.control2_bar);
        let sc2y = ctx.price_to_y(self.control2_price);
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
        ctx.bezier_curve_to(sc1x, sc1y, sc2x, sc2y, sx2, sy2);
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

fn create_double_curve(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (start_bar, start_price) = points.first().copied().unwrap_or((0.0, 100.0));
    let (end_bar, end_price) = points
        .get(1)
        .copied()
        .unwrap_or((start_bar + 30.0, start_price));

    let dx = end_bar - start_bar;
    let dy = end_price - start_price;

    let (control1_bar, control1_price) = points
        .get(2)
        .copied()
        .unwrap_or((start_bar + dx * 0.33, start_price + dy.abs() * 0.3));
    let (control2_bar, control2_price) = points
        .get(3)
        .copied()
        .unwrap_or((start_bar + dx * 0.67, end_price - dy.abs() * 0.3));

    Box::new(DoubleCurve::new(DoubleCurveConfig {
        start_bar,
        start_price,
        control1_bar,
        control1_price,
        control2_bar,
        control2_price,
        end_bar,
        end_price,
        color: color.to_string(),
    }))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "double_curve",
        display_name: "Double Curve",
        kind: PrimitiveKind::Shape,
        factory: create_double_curve,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
