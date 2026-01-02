//! Rotated Rectangle primitive
//!
//! A rectangle that can be rotated at any angle.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Rotated Rectangle - rectangle with rotation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RotatedRectangle {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar index
    pub center_bar: f64,
    /// Center price
    pub center_price: f64,
    /// Half-width in bars
    pub half_width: f64,
    /// Half-height in price units
    pub half_height: f64,
    /// Rotation angle in degrees
    pub rotation: f64,
    /// Fill the rectangle
    #[serde(default = "default_true")]
    pub fill: bool,
    /// Fill opacity
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
}

fn default_true() -> bool {
    true
}

fn default_fill_opacity() -> f64 {
    0.2
}

impl RotatedRectangle {
    /// Create a new rotated rectangle
    pub fn new(
        center_bar: f64,
        center_price: f64,
        half_width: f64,
        half_height: f64,
        rotation: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "rotated_rectangle".to_string(),
                display_name: "Rotated Rectangle".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            center_bar,
            center_price,
            half_width,
            half_height,
            rotation,
            fill: true,
            fill_opacity: 0.2,
        }
    }

    /// Create from three points (center, corner, rotation reference)
    pub fn from_points(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64), color: &str) -> Self {
        let center_bar = p1.0;
        let center_price = p1.1;

        // Calculate rotation from p1 to p2
        let dx = p2.0 - p1.0;
        let dy = p2.1 - p1.1;
        let rotation = dy.atan2(dx).to_degrees();

        // p2 defines one corner, calculate dimensions
        let half_width = (dx * dx + dy * dy).sqrt() / 2.0;

        // p3 defines the height (perpendicular distance)
        let dx3 = p3.0 - p1.0;
        let dy3 = p3.1 - p1.1;
        let half_height = (dx3 * dx3 + dy3 * dy3).sqrt().abs() / 2.0;

        Self::new(
            center_bar,
            center_price,
            half_width.max(1.0),
            half_height.max(0.01),
            rotation,
            color,
        )
    }

    /// Get corners in data coordinates
    pub fn corners(&self) -> [(f64, f64); 4] {
        let cos_r = self.rotation.to_radians().cos();
        let sin_r = self.rotation.to_radians().sin();

        let hw = self.half_width;
        let hh = self.half_height;

        // Local corners before rotation
        let local = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)];

        let mut corners = [(0.0, 0.0); 4];
        for (i, (lx, ly)) in local.iter().enumerate() {
            // Rotate and translate
            let rx = lx * cos_r - ly * sin_r + self.center_bar;
            let ry = lx * sin_r + ly * cos_r + self.center_price;
            corners[i] = (rx, ry);
        }
        corners
    }
}

impl Primitive for RotatedRectangle {
    fn type_id(&self) -> &'static str {
        "rotated_rectangle"
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
        let corners = self.corners();
        vec![
            (self.center_bar, self.center_price),
            corners[1], // Top-right corner
            corners[2], // Bottom-right corner
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if !points.is_empty() {
            self.center_bar = points[0].0;
            self.center_price = points[0].1;
        }
        if points.len() >= 2 {
            let dx = points[1].0 - self.center_bar;
            let dy = points[1].1 - self.center_price;
            self.rotation = dy.atan2(dx).to_degrees();
            self.half_width = (dx * dx + dy * dy).sqrt().max(1.0);
        }
        if points.len() >= 3 {
            // Third point for height
            let dx = points[2].0 - self.center_bar;
            let dy = points[2].1 - self.center_price;
            self.half_height = (dx * dx + dy * dy).sqrt().abs().max(0.01);
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.center_bar += bar_delta;
        self.center_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let corners = self.corners();
        let screen_corners: Vec<(f64, f64)> = corners
            .iter()
            .map(|(b, p)| (ctx.bar_to_x(*b), ctx.price_to_y(*p)))
            .collect();

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(screen_corners[0].0, screen_corners[0].1);
            for (x, y) in screen_corners.iter().skip(1) {
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
            crisp(screen_corners[0].0, dpr),
            crisp(screen_corners[0].1, dpr),
        );
        for (x, y) in screen_corners.iter().skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        ctx.close_path();
        ctx.stroke();
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get corners and calculate bounding box
        let corners = self.corners();
        let min_bar = corners.iter().map(|p| p.0).fold(f64::INFINITY, f64::min);
        let max_bar = corners
            .iter()
            .map(|p| p.0)
            .fold(f64::NEG_INFINITY, f64::max);
        let min_price = corners.iter().map(|p| p.1).fold(f64::INFINITY, f64::min);
        let max_price = corners
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

fn create_rotated_rectangle(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    if points.len() >= 3 {
        Box::new(RotatedRectangle::from_points(
            points[0], points[1], points[2], color,
        ))
    } else {
        let (center_bar, center_price) = points.first().copied().unwrap_or((0.0, 100.0));
        Box::new(RotatedRectangle::new(
            center_bar,
            center_price,
            10.0,
            center_price * 0.03,
            0.0,
            color,
        ))
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "rotated_rectangle",
        display_name: "Rotated Rectangle",
        kind: PrimitiveKind::Shape,
        factory: create_rotated_rectangle,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
