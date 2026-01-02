//! Gann Fan primitive
//!
//! Fan lines radiating from a single point at Gann angles.
//! Standard angles: 1x8, 1x4, 1x3, 1x2, 1x1, 2x1, 3x1, 4x1, 8x1

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Gann angle ratios (price units per time unit)
/// Format: (ratio, label)
pub const GANN_FAN_ANGLES: &[(f64, &str)] = &[
    (8.0, "8x1"), // Very steep up
    (4.0, "4x1"),
    (3.0, "3x1"),
    (2.0, "2x1"),
    (1.0, "1x1"), // 45 degrees
    (0.5, "1x2"),
    (0.333, "1x3"),
    (0.25, "1x4"),
    (0.125, "1x8"), // Very shallow
];

/// Gann Fan
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GannFan {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Origin bar
    pub bar1: f64,
    /// Origin price
    pub price1: f64,
    /// Target bar (defines scale)
    pub bar2: f64,
    /// Target price
    pub price2: f64,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Extend lines to chart edge
    #[serde(default = "default_true")]
    pub extend: bool,
    /// Direction: true = upward fan, false = downward fan
    #[serde(default = "default_true")]
    pub upward: bool,
}

fn default_true() -> bool {
    true
}

impl GannFan {
    /// Create a new Gann fan
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "gann_fan".to_string(),
                display_name: "Gann Fan".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            show_labels: true,
            extend: true,
            upward: true,
        }
    }

    /// Get the price scale (price per bar) based on the two points
    pub fn price_per_bar(&self) -> f64 {
        let bar_diff = (self.bar2 - self.bar1).abs();
        let price_diff = (self.price2 - self.price1).abs();
        if bar_diff == 0.0 {
            1.0
        } else {
            price_diff / bar_diff
        }
    }
}

impl Primitive for GannFan {
    fn type_id(&self) -> &'static str {
        "gann_fan"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Gann
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
        if let Some(&(bar, price)) = points.first() {
            self.bar1 = bar;
            self.price1 = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            self.bar2 = bar;
            self.price2 = price;
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
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let chart_width = ctx.chart_width();
        let chart_height = ctx.chart_height();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        let ppb = self.price_per_bar();
        let direction = if self.upward { 1.0 } else { -1.0 };

        // Draw each Gann angle line
        for &(ratio, _) in GANN_FAN_ANGLES {
            let bar_delta = 100.0;
            let price_delta = bar_delta * ppb * ratio * direction;

            let end_bar = self.bar1 + bar_delta;
            let end_price = self.price1 + price_delta;

            let end_x = ctx.bar_to_x(end_bar);
            let end_y = ctx.price_to_y(end_price);

            ctx.begin_path();
            ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));

            if self.extend {
                // Extend ray to chart edge
                let dx = end_x - x1;
                let dy = end_y - y1;
                let len = (dx * dx + dy * dy).sqrt();
                if len > 0.0 {
                    let ext = (chart_width + chart_height) * 2.0;
                    let nx = dx / len;
                    let ny = dy / len;
                    ctx.line_to(crisp(x1 + nx * ext, dpr), crisp(y1 + ny * ext, dpr));
                }
            } else {
                ctx.line_to(crisp(end_x, dpr), crisp(end_y, dpr));
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

        // Position text along the central line (1x1 Gann angle, which is 45 degrees)
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        // Calculate the direction vector
        let dx = x2 - x1;
        let dy = y2 - y1;
        let line_length = (dx * dx + dy * dy).sqrt();

        if line_length < 0.001 {
            // Fallback to origin if points are too close
            return Some(TextAnchor::new(x1, y1, &self.data.color.stroke));
        }

        // Position text at midpoint along the line from point1 to point2
        let t = match text.h_align {
            TextAlign::Start => 0.2,  // Near the start
            TextAlign::Center => 0.5, // Center
            TextAlign::End => 0.8,    // Near the end
        };

        let x = x1 + dx * t;
        let y = y1 + dy * t;

        // Calculate rotation angle
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

        // Calculate perpendicular offset for vertical alignment
        let (mut perp_x, mut perp_y) = (-dy / line_length, dx / line_length);

        if angle_flipped {
            perp_x = -perp_x;
            perp_y = -perp_y;
        }

        let offset = match text.v_align {
            TextAlign::Start => -(text.font_size / 2.0 + 5.0),
            TextAlign::Center => 0.0,
            TextAlign::End => text.font_size / 2.0 + 5.0,
        };

        let final_x = x + perp_x * offset;
        let final_y = y + perp_y * offset;

        Some(TextAnchor::with_rotation(
            final_x,
            final_y,
            &self.data.color.stroke,
            angle,
        ))
    }

    fn level_configs(&self) -> Option<Vec<FibLevelConfig>> {
        None
    }

    fn set_level_configs(&mut self, _configs: Vec<FibLevelConfig>) -> bool {
        false
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

fn create_gann_fan(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 20.0));
    Box::new(GannFan::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "gann_fan",
        display_name: "Gann Fan",
        kind: PrimitiveKind::Gann,
        factory: create_gann_fan,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
