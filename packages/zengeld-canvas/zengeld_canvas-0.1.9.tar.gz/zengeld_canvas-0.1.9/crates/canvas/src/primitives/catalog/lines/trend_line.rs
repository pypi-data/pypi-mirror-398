//! Trend Line primitive
//!
//! A simple line between two points. The most basic drawing tool.

use super::super::{
    ExtendMode, LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind,
    PrimitiveMetadata, RenderContext, TextAlign, TextAnchor, crisp, normalize_text_rotation,
};
use serde::{Deserialize, Serialize};

/// Trend Line - line between two points
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrendLine {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First point bar index (f64 for sub-bar precision)
    pub bar1: f64,
    /// First point price
    pub price1: f64,
    /// Second point bar index
    pub bar2: f64,
    /// Second point price
    pub price2: f64,
    /// Line extension mode
    #[serde(default)]
    pub extend: ExtendMode,
    /// Show price labels at endpoints
    #[serde(default)]
    pub show_price_labels: bool,
}

impl TrendLine {
    /// Create a new trend line
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "trend_line".to_string(),
                display_name: "Trend Line".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            extend: ExtendMode::None,
            show_price_labels: false,
        }
    }

    /// Create from integer bar indices (convenience)
    pub fn from_bars(bar1: usize, price1: f64, bar2: usize, price2: f64, color: &str) -> Self {
        Self::new(bar1 as f64, price1, bar2 as f64, price2, color)
    }
}

impl Primitive for TrendLine {
    fn type_id(&self) -> &'static str {
        "trend_line"
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

        // Draw the line (with optional extension)
        ctx.begin_path();

        match self.extend {
            ExtendMode::None => {
                ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
                ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
            }
            ExtendMode::Right => {
                let dx = x2 - x1;
                let dy = y2 - y1;
                let extend_x = ctx.chart_width();
                let t = if dx.abs() > 0.001 {
                    (extend_x - x1) / dx
                } else {
                    1000.0
                };
                let extend_y = y1 + dy * t;

                ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
                ctx.line_to(crisp(extend_x, dpr), crisp(extend_y, dpr));
            }
            ExtendMode::Left => {
                let dx = x2 - x1;
                let dy = y2 - y1;
                let t = if dx.abs() > 0.001 { -x1 / dx } else { -1000.0 };
                let extend_x = 0.0;
                let extend_y = y1 + dy * t;

                ctx.move_to(crisp(extend_x, dpr), crisp(extend_y, dpr));
                ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
            }
            ExtendMode::Both => {
                let dx = x2 - x1;
                let dy = y2 - y1;
                let t_left = if dx.abs() > 0.001 { -x1 / dx } else { -1000.0 };
                let t_right = if dx.abs() > 0.001 {
                    (ctx.chart_width() - x1) / dx
                } else {
                    1000.0
                };

                let left_y = y1 + dy * t_left;
                let right_y = y1 + dy * t_right;

                ctx.move_to(crisp(0.0, dpr), crisp(left_y, dpr));
                ctx.line_to(crisp(ctx.chart_width(), dpr), crisp(right_y, dpr));
            }
        }

        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);

        // Selection rendering handled by UI layer
        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        // Only render if text is set and has content
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get screen coordinates
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        // Calculate line angle for perpendicular offset
        let dx = x2 - x1;
        let dy = y2 - y1;
        let line_length = (dx * dx + dy * dy).sqrt();

        // Calculate line angle and normalize for readability (flip if pointing left)
        let raw_angle = dy.atan2(dx);
        let (angle, angle_flipped) = normalize_text_rotation(raw_angle);

        // Perpendicular unit vector (rotated 90 degrees counter-clockwise)
        // This points "above" the line in screen coordinates
        let (mut perp_x, mut perp_y) = if line_length > 0.001 {
            (-dy / line_length, dx / line_length)
        } else {
            (0.0, -1.0) // Default to up if line is a point
        };

        // When angle is flipped for readability, we also need to flip the perpendicular
        // so that "above" stays visually above the text
        if angle_flipped {
            perp_x = -perp_x;
            perp_y = -perp_y;
        }

        // Horizontal position along line: Start=left point, Center=middle, End=right point
        let t = match text.h_align {
            TextAlign::Start => 0.0,
            TextAlign::Center => 0.5,
            TextAlign::End => 1.0,
        };
        let base_x = x1 + dx * t;
        let base_y = y1 + dy * t;

        // Vertical offset perpendicular to line
        // Note: perpendicular vector points "up" relative to line direction
        // Start = "Сверху" = above line (negative perp direction in screen coords)
        // End = "Снизу" = below line (positive perp direction in screen coords)
        let text_offset = 8.0 + text.font_size / 2.0; // offset from line
        let (offset_x, offset_y) = match text.v_align {
            TextAlign::Start => (-perp_x * text_offset, -perp_y * text_offset), // above line (Сверху)
            TextAlign::Center => (0.0, 0.0),                                    // on line
            TextAlign::End => (perp_x * text_offset, perp_y * text_offset), // below line (Снизу)
        };

        let x = base_x + offset_x;
        let y = base_y + offset_y;

        Some(TextAnchor::with_rotation(
            x,
            y,
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

/// Create trend line from points
fn create_trend_line(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1, price1));
    Box::new(TrendLine::new(bar1, price1, bar2, price2, color))
}

/// Get metadata for registry
pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "trend_line",
        display_name: "Trend Line",
        kind: PrimitiveKind::Line,
        factory: create_trend_line,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
