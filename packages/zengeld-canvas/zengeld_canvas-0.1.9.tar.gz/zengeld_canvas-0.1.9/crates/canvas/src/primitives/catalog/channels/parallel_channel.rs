//! Parallel Channel primitive
//!
//! Two parallel trend lines forming a channel. Created with 3 clicks:
//! - First two clicks define the main trend line
//! - Third click defines the width of the channel

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Parallel Channel - two parallel trend lines
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ParallelChannel {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First point of main line (bar index)
    pub bar1: f64,
    /// First point of main line (price)
    pub price1: f64,
    /// Second point of main line (bar index)
    pub bar2: f64,
    /// Second point of main line (price)
    pub price2: f64,
    /// Price offset for the parallel line (can be positive or negative)
    pub channel_offset: f64,
    /// Extend lines to the left
    #[serde(default)]
    pub extend_left: bool,
    /// Extend lines to the right
    #[serde(default)]
    pub extend_right: bool,
    /// Fill the channel with semi-transparent color
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

impl ParallelChannel {
    /// Create a new parallel channel
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        channel_offset: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "parallel_channel".to_string(),
                display_name: "Parallel Channel".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            channel_offset,
            extend_left: false,
            extend_right: false,
            fill: true,
            fill_opacity: 0.2,
        }
    }

    /// Get the parallel line points (offset by channel_offset in price)
    pub fn parallel_line(&self) -> ((f64, f64), (f64, f64)) {
        (
            (self.bar1, self.price1 + self.channel_offset),
            (self.bar2, self.price2 + self.channel_offset),
        )
    }

    /// Calculate center line points (middle of channel)
    pub fn center_line(&self) -> ((f64, f64), (f64, f64)) {
        let half_offset = self.channel_offset / 2.0;
        (
            (self.bar1, self.price1 + half_offset),
            (self.bar2, self.price2 + half_offset),
        )
    }
}

impl Primitive for ParallelChannel {
    fn type_id(&self) -> &'static str {
        "parallel_channel"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Channel
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        // Return main line points plus the offset point for the parallel line
        vec![
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar1, self.price1 + self.channel_offset), // Third point for channel width
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if points.len() >= 2 {
            self.bar1 = points[0].0;
            self.price1 = points[0].1;
            self.bar2 = points[1].0;
            self.price2 = points[1].1;
        }
        if points.len() >= 3 {
            // Third point determines channel offset
            self.channel_offset = points[2].1 - self.price1;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
        // channel_offset stays the same (relative)
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let py1 = ctx.price_to_y(self.price1 + self.channel_offset);
        let py2 = ctx.price_to_y(self.price2 + self.channel_offset);

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(x1, y1);
            ctx.line_to(x2, y2);
            ctx.line_to(x2, py2);
            ctx.line_to(x1, py1);
            ctx.close_path();
            ctx.fill();
        }

        // Draw lines
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Main line
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Parallel line
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(py1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(py2, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);
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

        // Calculate center line (middle of channel)
        let offset_y = ctx.price_to_y(self.price1 + self.channel_offset / 2.0) - y1;

        let dx = x2 - x1;
        let dy = y2 - y1;
        let line_length = (dx * dx + dy * dy).sqrt();

        let raw_angle = dy.atan2(dx);
        let _angle_flipped =
            !(-std::f64::consts::FRAC_PI_2..=std::f64::consts::FRAC_PI_2).contains(&raw_angle);
        let angle = if raw_angle > std::f64::consts::FRAC_PI_2 {
            raw_angle - std::f64::consts::PI
        } else if raw_angle < -std::f64::consts::FRAC_PI_2 {
            raw_angle + std::f64::consts::PI
        } else {
            raw_angle
        };

        let t = match text.h_align {
            TextAlign::Start => 0.0,
            TextAlign::Center => 0.5,
            TextAlign::End => 1.0,
        };

        // Position on center line of channel
        let base_x = x1 + dx * t;
        let base_y = y1 + dy * t + offset_y;

        // Optional perpendicular offset based on v_align
        let (perp_x, perp_y) = if line_length > 0.001 {
            (-dy / line_length, dx / line_length)
        } else {
            (0.0, -1.0)
        };

        let text_offset = if text.v_align != TextAlign::Center {
            8.0 + text.font_size / 2.0
        } else {
            0.0
        };

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

fn create_parallel_channel(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1 + 10.0, price1));
    let channel_offset = if points.len() >= 3 {
        points[2].1 - price1
    } else {
        // Default offset: 5% of price
        price1 * 0.05
    };
    Box::new(ParallelChannel::new(
        bar1,
        price1,
        bar2,
        price2,
        channel_offset,
        color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "parallel_channel",
        display_name: "Parallel Channel",
        kind: PrimitiveKind::Channel,
        factory: create_parallel_channel,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
