//! Circle primitive
//!
//! A circle/ellipse defined by center and 4 edge points.
//! Uses 5 data-coordinate points: center + 4 edge points (top, right, bottom, left)

use super::super::{
    EllipseParams, LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind,
    PrimitiveMetadata, RenderContext, TextAlign, TextAnchor,
};
use serde::{Deserialize, Serialize};

/// Circle - defined by center and radii in data coordinates
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Circle {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar index
    pub center_bar: f64,
    /// Center price
    pub center_price: f64,
    /// Horizontal radius in bars
    pub radius_bars: f64,
    /// Vertical radius in price units
    pub radius_price: f64,
    /// Fill the circle
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

impl Circle {
    /// Create a new circle
    pub fn new(
        center_bar: f64,
        center_price: f64,
        radius_bars: f64,
        radius_price: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "circle".to_string(),
                display_name: "Circle".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            center_bar,
            center_price,
            radius_bars,
            radius_price,
            fill: true,
            fill_opacity: 0.2,
        }
    }

    /// Create from center and edge point
    pub fn from_points(center_bar: f64, center_price: f64, edge_bar: f64, edge_price: f64) -> Self {
        let radius_bars = (edge_bar - center_bar).abs().max(1.0);
        let radius_price = (edge_price - center_price).abs().max(1.0);
        Self::new(
            center_bar,
            center_price,
            radius_bars,
            radius_price,
            "#2196F3",
        )
    }
}

impl Primitive for Circle {
    fn type_id(&self) -> &'static str {
        "circle"
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

    /// Returns 2 points: center and corner (for TwoPoint behavior)
    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.center_bar, self.center_price),
            (
                self.center_bar + self.radius_bars,
                self.center_price + self.radius_price,
            ),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if !points.is_empty() {
            self.center_bar = points[0].0;
            self.center_price = points[0].1;
        }
        if points.len() >= 2 {
            // Calculate radius from second point (edge)
            self.radius_bars = (points[1].0 - self.center_bar).abs().max(1.0);
            self.radius_price = (points[1].1 - self.center_price).abs().max(1.0);
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.center_bar += bar_delta;
        self.center_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let cx = ctx.bar_to_x(self.center_bar);
        let cy = ctx.price_to_y(self.center_price);

        // Calculate screen-space radii from data coordinates
        let rx = (ctx.bar_to_x(self.center_bar + self.radius_bars) - cx).abs();
        let ry = (ctx.price_to_y(self.center_price + self.radius_price) - cy).abs();

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.ellipse(EllipseParams::full(cx, cy, rx, ry));
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
        ctx.ellipse(EllipseParams::full(cx, cy, rx, ry));
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let cx = ctx.bar_to_x(self.center_bar);
        let cy = ctx.price_to_y(self.center_price);
        let radius_x = (ctx.bar_to_x(self.center_bar + self.radius_bars) - cx).abs();
        let radius_y = (ctx.price_to_y(self.center_price + self.radius_price) - cy).abs();

        // h_align: Start=left edge, Center=center, End=right edge
        let x = match text.h_align {
            TextAlign::Start => cx - radius_x + 10.0,
            TextAlign::Center => cx,
            TextAlign::End => cx + radius_x - 10.0,
        };

        // v_align: Start=top edge, Center=center, End=bottom edge
        let y = match text.v_align {
            TextAlign::Start => cy - radius_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => cy,
            TextAlign::End => cy + radius_y - 10.0 - text.font_size / 2.0,
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

fn create_circle(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (center_bar, center_price) = points.first().copied().unwrap_or((0.0, 0.0));
    if points.len() >= 2 {
        let radius_bars = (points[1].0 - center_bar).abs().max(1.0);
        let radius_price = (points[1].1 - center_price).abs().max(1.0);
        Box::new(Circle::new(
            center_bar,
            center_price,
            radius_bars,
            radius_price,
            color,
        ))
    } else {
        Box::new(Circle::new(
            center_bar,
            center_price,
            10.0,
            center_price * 0.02,
            color,
        ))
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "circle",
        display_name: "Circle",
        kind: PrimitiveKind::Shape,
        factory: create_circle,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
