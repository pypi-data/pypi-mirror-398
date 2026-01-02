//! Trend Angle primitive
//!
//! A trend line that displays the angle of the line in degrees.
//! Useful for measuring the slope of price movements.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use crate::Viewport;
use serde::{Deserialize, Serialize};

/// Trend Angle - trend line with angle measurement
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrendAngle {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First point bar index
    pub bar1: f64,
    /// First point price
    pub price1: f64,
    /// Second point bar index
    pub bar2: f64,
    /// Second point price
    pub price2: f64,
    /// Show angle arc visualization
    #[serde(default = "default_true")]
    pub show_arc: bool,
    /// Show angle value label
    #[serde(default = "default_true")]
    pub show_label: bool,
}

fn default_true() -> bool {
    true
}

impl TrendAngle {
    /// Create a new trend angle
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "trend_angle".to_string(),
                display_name: "Trend Angle".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            show_arc: true,
            show_label: true,
        }
    }

    /// Calculate the angle in degrees (relative to horizontal)
    /// Note: This calculates the visual angle based on screen coordinates,
    /// which depends on the chart's aspect ratio and scale.
    pub fn angle_degrees(&self, viewport: &Viewport) -> f64 {
        let x1 = viewport.bar_to_x_f64(self.bar1);
        let y1 = viewport.price_to_y(self.price1);
        let x2 = viewport.bar_to_x_f64(self.bar2);
        let y2 = viewport.price_to_y(self.price2);

        let dx = x2 - x1;
        let dy = y1 - y2; // Inverted because screen Y is flipped

        if dx.abs() < 1e-10 {
            if dy >= 0.0 { 90.0 } else { -90.0 }
        } else {
            (dy / dx).atan().to_degrees()
        }
    }

    /// Get the arc radius for drawing the angle visualization
    pub fn arc_radius(&self, viewport: &Viewport) -> f64 {
        let x1 = viewport.bar_to_x_f64(self.bar1);
        let y1 = viewport.price_to_y(self.price1);
        let x2 = viewport.bar_to_x_f64(self.bar2);
        let y2 = viewport.price_to_y(self.price2);

        let line_length = ((x2 - x1).powi(2) + (y2 - y1).powi(2)).sqrt();
        // Arc radius is 30% of line length, clamped to reasonable values
        (line_length * 0.3).clamp(20.0, 60.0)
    }

    /// Get formatted angle text
    pub fn angle_text(&self, viewport: &Viewport) -> String {
        format!("{:.1}°", self.angle_degrees(viewport))
    }
}

impl Primitive for TrendAngle {
    fn type_id(&self) -> &'static str {
        "trend_angle"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Line
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if points.len() >= 2 {
            self.bar1 = points[0].0;
            self.price1 = points[0].1;
            self.bar2 = points[1].0;
            self.price2 = points[1].1;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();

        // Convert to screen coordinates
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        // Set stroke style
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Set line dash based on style
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw main line
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Reset line dash for arc and annotations
        ctx.set_line_dash(&[]);

        // Calculate angle for display
        let dx = x2 - x1;
        let dy = y1 - y2; // Inverted because screen Y is flipped
        let angle_rad = if dx.abs() > 0.001 {
            (dy / dx).atan()
        } else if dy >= 0.0 {
            std::f64::consts::FRAC_PI_2
        } else {
            -std::f64::consts::FRAC_PI_2
        };
        let angle_deg = angle_rad.to_degrees();

        // Draw angle arc if enabled
        if self.show_arc {
            let line_length = ((x2 - x1).powi(2) + (y2 - y1).powi(2)).sqrt();
            let arc_radius = (line_length * 0.3).clamp(20.0, 60.0);

            // Draw horizontal reference line (dashed)
            ctx.set_line_dash(&[4.0, 4.0]);
            ctx.begin_path();
            ctx.move_to(x1, y1);
            ctx.line_to(x1 + arc_radius * 1.5, y1);
            ctx.stroke();
            ctx.set_line_dash(&[]);

            // Draw angle arc
            let start_angle = 0.0;
            let end_angle = -angle_rad; // Negative because screen Y is flipped
            ctx.begin_path();
            if end_angle >= start_angle {
                ctx.arc(x1, y1, arc_radius, start_angle, end_angle);
            } else {
                ctx.arc(x1, y1, arc_radius, end_angle, start_angle);
            }
            ctx.stroke();
        }

        // Draw angle label if enabled
        if self.show_label {
            let angle_text = format!("{:.1}°", angle_deg);
            let label_distance = 40.0;
            let label_angle = -angle_rad / 2.0;
            let label_x = x1 + label_distance * label_angle.cos();
            let label_y = y1 - label_distance * label_angle.sin();

            ctx.set_font("12px sans-serif");
            ctx.set_fill_color(&self.data.color.stroke);
            use super::super::render::{TextAlign, TextBaseline};
            ctx.set_text_align(TextAlign::Center);
            ctx.set_text_baseline(TextBaseline::Middle);
            ctx.fill_text(&angle_text, label_x, label_y);
        }

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let dx = x2 - x1;
        let dy = y2 - y1;
        let line_length = (dx * dx + dy * dy).sqrt();

        let raw_angle = dy.atan2(dx);
        let angle_flipped =
            !(-std::f64::consts::FRAC_PI_2..=std::f64::consts::FRAC_PI_2).contains(&raw_angle);
        let angle = if raw_angle > std::f64::consts::FRAC_PI_2 {
            raw_angle - std::f64::consts::PI
        } else if raw_angle < -std::f64::consts::FRAC_PI_2 {
            raw_angle + std::f64::consts::PI
        } else {
            raw_angle
        };

        let (mut perp_x, mut perp_y) = if line_length > 0.001 {
            (-dy / line_length, dx / line_length)
        } else {
            (0.0, -1.0)
        };

        if angle_flipped {
            perp_x = -perp_x;
            perp_y = -perp_y;
        }

        let t = match text.h_align {
            TextAlign::Start => 0.0,
            TextAlign::Center => 0.5,
            TextAlign::End => 1.0,
        };
        let base_x = x1 + dx * t;
        let base_y = y1 + dy * t;

        let text_offset = 8.0 + text.font_size / 2.0;
        let (offset_x, offset_y) = match text.v_align {
            TextAlign::Start => (-perp_x * text_offset, -perp_y * text_offset),
            TextAlign::Center => (0.0, 0.0),
            TextAlign::End => (perp_x * text_offset, perp_y * text_offset),
        };

        Some(TextAnchor::with_rotation(
            base_x + offset_x,
            base_y + offset_y,
            &self.data.color.stroke,
            angle,
        ))
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

fn create_trend_angle(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1, price1));
    Box::new(TrendAngle::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "trend_angle",
        display_name: "Trend Angle",
        kind: PrimitiveKind::Line,
        factory: create_trend_angle,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
