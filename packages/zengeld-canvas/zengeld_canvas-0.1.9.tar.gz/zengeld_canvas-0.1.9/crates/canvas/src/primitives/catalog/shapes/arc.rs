//! Arc primitive
//!
//! A curved arc segment defined by center, radius, and angle range.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAnchor,
};
use serde::{Deserialize, Serialize};

/// Arc - curved line segment
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Arc {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar index
    pub center_bar: f64,
    /// Center price
    pub center_price: f64,
    /// Radius in bars
    pub radius_bars: f64,
    /// Start angle in degrees (0 = right, 90 = up)
    pub start_angle: f64,
    /// End angle in degrees
    pub end_angle: f64,
}

impl Arc {
    /// Create a new arc
    pub fn new(
        center_bar: f64,
        center_price: f64,
        radius_bars: f64,
        start_angle: f64,
        end_angle: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "arc".to_string(),
                display_name: "Arc".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            center_bar,
            center_price,
            radius_bars,
            start_angle,
            end_angle,
        }
    }

    /// Create a semicircle (180 degrees)
    pub fn semicircle(center_bar: f64, center_price: f64, radius_bars: f64, color: &str) -> Self {
        Self::new(center_bar, center_price, radius_bars, 0.0, 180.0, color)
    }
}

impl Primitive for Arc {
    fn type_id(&self) -> &'static str {
        "arc"
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
        let start_rad = self.start_angle.to_radians();
        let end_rad = self.end_angle.to_radians();
        vec![
            (self.center_bar, self.center_price),
            (
                self.center_bar + self.radius_bars * start_rad.cos(),
                self.center_price,
            ),
            (
                self.center_bar + self.radius_bars * end_rad.cos(),
                self.center_price,
            ),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if !points.is_empty() {
            self.center_bar = points[0].0;
            self.center_price = points[0].1;
        }
        if points.len() >= 2 {
            // Calculate radius and start angle from second point
            let dx = points[1].0 - self.center_bar;
            self.radius_bars = dx.abs().max(1.0);
            self.start_angle = 0.0;
        }
        if points.len() >= 3 {
            // Calculate end angle from third point
            let dx = points[2].0 - self.center_bar;
            let dy = points[2].1 - self.center_price;
            self.end_angle = dy.atan2(dx).to_degrees();
            if self.end_angle < 0.0 {
                self.end_angle += 360.0;
            }
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.center_bar += bar_delta;
        self.center_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let cx = ctx.bar_to_x(self.center_bar);
        let cy = ctx.price_to_y(self.center_price);
        let rx = ctx.bar_to_x(self.center_bar + self.radius_bars);
        let radius = (rx - cx).abs();

        let start_rad = self.start_angle.to_radians();
        let end_rad = self.end_angle.to_radians();

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
        ctx.arc(cx, cy, radius, start_rad, end_rad);
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Use center point as anchor
        let x = ctx.bar_to_x(self.center_bar);
        let y = ctx.price_to_y(self.center_price);

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

fn create_arc(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (center_bar, center_price) = points.first().copied().unwrap_or((0.0, 100.0));
    let radius_bars = if points.len() >= 2 {
        (points[1].0 - center_bar).abs().max(1.0)
    } else {
        10.0
    };
    let end_angle = if points.len() >= 3 {
        let dx = points[2].0 - center_bar;
        let dy = points[2].1 - center_price;
        let mut angle = dy.atan2(dx).to_degrees();
        if angle < 0.0 {
            angle += 360.0;
        }
        angle
    } else {
        180.0
    };
    Box::new(Arc::new(
        center_bar,
        center_price,
        radius_bars,
        0.0,
        end_angle,
        color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "arc",
        display_name: "Arc",
        kind: PrimitiveKind::Shape,
        factory: create_arc,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
