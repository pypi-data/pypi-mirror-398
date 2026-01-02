//! Polyline primitive
//!
//! A series of connected straight line segments.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Polyline - connected line segments
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Polyline {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Points as (bar, price) pairs
    pub points_data: Vec<(f64, f64)>,
    /// Close the shape (connect last point to first)
    #[serde(default)]
    pub closed: bool,
    /// Fill if closed
    #[serde(default)]
    pub fill: bool,
    /// Fill opacity
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
}

fn default_fill_opacity() -> f64 {
    0.2
}

impl Polyline {
    /// Create a new polyline
    pub fn new(points: Vec<(f64, f64)>, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "polyline".to_string(),
                display_name: "Polyline".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            points_data: points,
            closed: false,
            fill: false,
            fill_opacity: 0.2,
        }
    }

    /// Create a closed polygon
    pub fn polygon(points: Vec<(f64, f64)>, color: &str) -> Self {
        let mut poly = Self::new(points, color);
        poly.closed = true;
        poly.fill = true;
        poly
    }

    /// Add a point
    pub fn add_point(&mut self, bar: f64, price: f64) {
        self.points_data.push((bar, price));
    }

    /// Get center point
    pub fn center(&self) -> (f64, f64) {
        if self.points_data.is_empty() {
            return (0.0, 0.0);
        }
        let sum: (f64, f64) = self
            .points_data
            .iter()
            .fold((0.0, 0.0), |acc, p| (acc.0 + p.0, acc.1 + p.1));
        let n = self.points_data.len() as f64;
        (sum.0 / n, sum.1 / n)
    }
}

impl Primitive for Polyline {
    fn type_id(&self) -> &'static str {
        "polyline"
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
        self.points_data.clone()
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        self.points_data = points.to_vec();
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        for p in &mut self.points_data {
            p.0 += bar_delta;
            p.1 += price_delta;
        }
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        if self.points_data.len() < 2 {
            return;
        }

        let dpr = ctx.dpr();
        let screen_points: Vec<(f64, f64)> = self
            .points_data
            .iter()
            .map(|(b, p)| (ctx.bar_to_x(*b), ctx.price_to_y(*p)))
            .collect();

        // Fill if closed and fill enabled
        if self.closed && self.fill && screen_points.len() >= 3 {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(screen_points[0].0, screen_points[0].1);
            for (x, y) in screen_points.iter().skip(1) {
                ctx.line_to(*x, *y);
            }
            ctx.close_path();
            ctx.fill();
        }

        // Draw stroke
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
        ctx.move_to(
            crisp(screen_points[0].0, dpr),
            crisp(screen_points[0].1, dpr),
        );
        for (x, y) in screen_points.iter().skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        if self.closed {
            ctx.close_path();
        }
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        if self.points_data.is_empty() {
            return None;
        }

        // Calculate bounding box from points
        let min_bar = self
            .points_data
            .iter()
            .map(|p| p.0)
            .fold(f64::INFINITY, f64::min);
        let max_bar = self
            .points_data
            .iter()
            .map(|p| p.0)
            .fold(f64::NEG_INFINITY, f64::max);
        let min_price = self
            .points_data
            .iter()
            .map(|p| p.1)
            .fold(f64::INFINITY, f64::min);
        let max_price = self
            .points_data
            .iter()
            .map(|p| p.1)
            .fold(f64::NEG_INFINITY, f64::max);

        // Convert to screen coordinates
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

// =============================================================================
// Factory Registration
// =============================================================================

fn create_polyline(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    Box::new(Polyline::new(points.to_vec(), color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "polyline",
        display_name: "Polyline",
        kind: PrimitiveKind::Shape,
        factory: create_polyline,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
