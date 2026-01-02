//! Fibonacci Spiral primitive
//!
//! A logarithmic spiral based on the golden ratio (phi = 1.618).
//! Commonly used to identify potential support/resistance areas.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor,
};
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

/// Golden ratio
pub const PHI: f64 = 1.618033988749895;

/// Fibonacci Spiral
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibSpiral {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Center bar
    pub center_bar: f64,
    /// Center price
    pub center_price: f64,
    /// Edge bar (defines initial radius)
    pub edge_bar: f64,
    /// Edge price
    pub edge_price: f64,
    /// Number of rotations
    #[serde(default = "default_rotations")]
    pub rotations: f64,
    /// Clockwise direction
    #[serde(default = "default_true")]
    pub clockwise: bool,
    /// Flip horizontally
    #[serde(default)]
    pub flip_horizontal: bool,
    /// Flip vertically
    #[serde(default)]
    pub flip_vertical: bool,
}

fn default_true() -> bool {
    true
}
fn default_rotations() -> f64 {
    3.0
}

impl FibSpiral {
    /// Create a new Fibonacci spiral
    pub fn new(
        center_bar: f64,
        center_price: f64,
        edge_bar: f64,
        edge_price: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_spiral".to_string(),
                display_name: "Fib Spiral".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            center_bar,
            center_price,
            edge_bar,
            edge_price,
            rotations: 3.0,
            clockwise: true,
            flip_horizontal: false,
            flip_vertical: false,
        }
    }

    /// Calculate spiral points for rendering
    /// Returns points in (bar, price) coordinates
    pub fn spiral_points(&self, num_points: usize) -> Vec<(f64, f64)> {
        let initial_radius_bar = (self.edge_bar - self.center_bar).abs();
        let initial_radius_price = (self.edge_price - self.center_price).abs();

        // Logarithmic spiral: r = a * e^(b*theta)
        // For golden spiral: b = ln(phi) / (pi/2)
        let b = PHI.ln() / (PI / 2.0);

        let mut points = Vec::with_capacity(num_points);
        let max_angle = self.rotations * 2.0 * PI;

        for i in 0..num_points {
            let t = i as f64 / (num_points - 1) as f64;
            let theta = t * max_angle;

            let r = (-b * theta).exp(); // Spiral inward
            let angle = if self.clockwise { theta } else { -theta };

            let mut dx = r * angle.cos();
            let mut dy = r * angle.sin();

            if self.flip_horizontal {
                dx = -dx;
            }
            if self.flip_vertical {
                dy = -dy;
            }

            let bar = self.center_bar + dx * initial_radius_bar;
            let price = self.center_price + dy * initial_radius_price;

            points.push((bar, price));
        }

        points
    }
}

impl Primitive for FibSpiral {
    fn type_id(&self) -> &'static str {
        "fib_spiral"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Fibonacci
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.center_bar, self.center_price),
            (self.edge_bar, self.edge_price),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.center_bar = bar;
            self.center_price = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            self.edge_bar = bar;
            self.edge_price = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.center_bar += bar_delta;
        self.edge_bar += bar_delta;
        self.center_price += price_delta;
        self.edge_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Generate spiral points and convert to screen coordinates
        let spiral_data = self.spiral_points(200);

        if !spiral_data.is_empty() {
            ctx.begin_path();
            let first = spiral_data[0];
            ctx.move_to(ctx.bar_to_x(first.0), ctx.price_to_y(first.1));

            for &(bar, price) in spiral_data.iter().skip(1) {
                ctx.line_to(ctx.bar_to_x(bar), ctx.price_to_y(price));
            }
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x1 = ctx.bar_to_x(self.center_bar);
        let y1 = ctx.price_to_y(self.center_price);
        let x2 = ctx.bar_to_x(self.edge_bar);
        let y2 = ctx.price_to_y(self.edge_price);

        // Position text based on alignment within the fib tool area
        let x = match text.h_align {
            TextAlign::Start => x1.min(x2) + 10.0,
            TextAlign::Center => (x1 + x2) / 2.0,
            TextAlign::End => x1.max(x2) - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => y1.min(y2) + 10.0 + text.font_size / 2.0,
            TextAlign::Center => (y1 + y2) / 2.0,
            TextAlign::End => y1.max(y2) - 10.0 - text.font_size / 2.0,
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

fn create_fib_spiral(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    Box::new(FibSpiral::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_spiral",
        display_name: "Fib Spiral",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_spiral,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
