//! Disjoint Channel primitive
//!
//! A channel with two non-parallel lines (widening or narrowing).
//! Each line has independent endpoints.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Configuration for creating a DisjointChannel with all points specified
#[derive(Clone, Debug)]
pub struct DisjointChannelPoints {
    /// First line - start bar
    pub l1_bar1: f64,
    /// First line - start price
    pub l1_price1: f64,
    /// First line - end bar
    pub l1_bar2: f64,
    /// First line - end price
    pub l1_price2: f64,
    /// Second line - start bar
    pub l2_bar1: f64,
    /// Second line - start price
    pub l2_price1: f64,
    /// Second line - end bar
    pub l2_bar2: f64,
    /// Second line - end price
    pub l2_price2: f64,
    /// Color
    pub color: String,
}

/// Disjoint Channel - non-parallel channel (widening/narrowing)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DisjointChannel {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First line - start bar
    pub line1_bar1: f64,
    /// First line - start price
    pub line1_price1: f64,
    /// First line - end bar
    pub line1_bar2: f64,
    /// First line - end price
    pub line1_price2: f64,
    /// Second line - start bar
    pub line2_bar1: f64,
    /// Second line - start price
    pub line2_price1: f64,
    /// Second line - end bar
    pub line2_bar2: f64,
    /// Second line - end price
    pub line2_price2: f64,
    /// Fill the channel
    #[serde(default = "default_true")]
    pub fill: bool,
    /// Fill opacity
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
    /// Extend lines to the right
    #[serde(default)]
    pub extend_right: bool,
}

fn default_true() -> bool {
    true
}

fn default_fill_opacity() -> f64 {
    0.2
}

impl DisjointChannel {
    /// Create a new disjoint channel
    /// Points define the first line, second line is offset initially
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, offset: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "disjoint_channel".to_string(),
                display_name: "Disjoint Channel".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            line1_bar1: bar1,
            line1_price1: price1,
            line1_bar2: bar2,
            line1_price2: price2,
            line2_bar1: bar1,
            line2_price1: price1 + offset,
            line2_bar2: bar2,
            line2_price2: price2 + offset,
            fill: true,
            fill_opacity: 0.2,
            extend_right: false,
        }
    }

    /// Create with all 4 points specified using a config struct
    pub fn with_points(config: DisjointChannelPoints) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "disjoint_channel".to_string(),
                display_name: "Disjoint Channel".to_string(),
                color: PrimitiveColor::new(&config.color),
                width: 2.0,
                ..Default::default()
            },
            line1_bar1: config.l1_bar1,
            line1_price1: config.l1_price1,
            line1_bar2: config.l1_bar2,
            line1_price2: config.l1_price2,
            line2_bar1: config.l2_bar1,
            line2_price1: config.l2_price1,
            line2_bar2: config.l2_bar2,
            line2_price2: config.l2_price2,
            fill: true,
            fill_opacity: 0.2,
            extend_right: false,
        }
    }
}

impl Primitive for DisjointChannel {
    fn type_id(&self) -> &'static str {
        "disjoint_channel"
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
        vec![
            (self.line1_bar1, self.line1_price1),
            (self.line1_bar2, self.line1_price2),
            (self.line2_bar1, self.line2_price1),
            (self.line2_bar2, self.line2_price2),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if !points.is_empty() {
            self.line1_bar1 = points[0].0;
            self.line1_price1 = points[0].1;
        }
        if points.len() >= 2 {
            self.line1_bar2 = points[1].0;
            self.line1_price2 = points[1].1;
        }
        if points.len() >= 3 {
            self.line2_bar1 = points[2].0;
            self.line2_price1 = points[2].1;
        }
        if points.len() >= 4 {
            self.line2_bar2 = points[3].0;
            self.line2_price2 = points[3].1;
        } else if points.len() == 3 {
            // If only 3 points, make second line parallel offset
            let offset = self.line2_price1 - self.line1_price1;
            self.line2_bar2 = self.line1_bar2;
            self.line2_price2 = self.line1_price2 + offset;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.line1_bar1 += bar_delta;
        self.line1_bar2 += bar_delta;
        self.line1_price1 += price_delta;
        self.line1_price2 += price_delta;
        self.line2_bar1 += bar_delta;
        self.line2_bar2 += bar_delta;
        self.line2_price1 += price_delta;
        self.line2_price2 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let l1_x1 = ctx.bar_to_x(self.line1_bar1);
        let l1_y1 = ctx.price_to_y(self.line1_price1);
        let l1_x2 = ctx.bar_to_x(self.line1_bar2);
        let l1_y2 = ctx.price_to_y(self.line1_price2);
        let l2_x1 = ctx.bar_to_x(self.line2_bar1);
        let l2_y1 = ctx.price_to_y(self.line2_price1);
        let l2_x2 = ctx.bar_to_x(self.line2_bar2);
        let l2_y2 = ctx.price_to_y(self.line2_price2);

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(l1_x1, l1_y1);
            ctx.line_to(l1_x2, l1_y2);
            ctx.line_to(l2_x2, l2_y2);
            ctx.line_to(l2_x1, l2_y1);
            ctx.close_path();
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

        // Line 1
        ctx.begin_path();
        ctx.move_to(crisp(l1_x1, dpr), crisp(l1_y1, dpr));
        ctx.line_to(crisp(l1_x2, dpr), crisp(l1_y2, dpr));
        ctx.stroke();

        // Line 2
        ctx.begin_path();
        ctx.move_to(crisp(l2_x1, dpr), crisp(l2_y1, dpr));
        ctx.line_to(crisp(l2_x2, dpr), crisp(l2_y2, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Use line1 as the main line for text positioning
        let x1 = ctx.bar_to_x(self.line1_bar1);
        let y1 = ctx.price_to_y(self.line1_price1);
        let x2 = ctx.bar_to_x(self.line1_bar2);
        let y2 = ctx.price_to_y(self.line1_price2);

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
        let base_x = x1 + dx * t;
        let base_y = y1 + dy * t;

        // For disjoint channels, position text in center between the two lines
        // Get the corresponding point on line2
        let l2_x1 = ctx.bar_to_x(self.line2_bar1);
        let l2_y1 = ctx.price_to_y(self.line2_price1);
        let l2_x2 = ctx.bar_to_x(self.line2_bar2);
        let l2_y2 = ctx.price_to_y(self.line2_price2);

        let _l2_dx = l2_x2 - l2_x1;
        let l2_dy = l2_y2 - l2_y1;
        let line2_point_y = l2_y1 + l2_dy * t;

        // Center text between the two lines
        let adjusted_base_y = (base_y + line2_point_y) / 2.0;

        let (perp_x, perp_y) = if line_length > 0.001 {
            (-dy / line_length, dx / line_length)
        } else {
            (0.0, -1.0)
        };

        let text_offset = 8.0 + text.font_size / 2.0;
        let (offset_x, offset_y) = match text.v_align {
            TextAlign::Start => (-perp_x * text_offset, -perp_y * text_offset),
            TextAlign::Center => (0.0, 0.0),
            TextAlign::End => (perp_x * text_offset, perp_y * text_offset),
        };

        Some(TextAnchor::with_rotation(
            base_x + offset_x,
            adjusted_base_y + offset_y,
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

fn create_disjoint_channel(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 100.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 * 1.05));

    if points.len() >= 4 {
        Box::new(DisjointChannel::with_points(DisjointChannelPoints {
            l1_bar1: bar1,
            l1_price1: price1,
            l1_bar2: bar2,
            l1_price2: price2,
            l2_bar1: points[2].0,
            l2_price1: points[2].1,
            l2_bar2: points[3].0,
            l2_price2: points[3].1,
            color: color.to_string(),
        }))
    } else if points.len() >= 3 {
        // Use third point for initial offset
        let offset = points[2].1 - price1;
        Box::new(DisjointChannel::new(
            bar1, price1, bar2, price2, offset, color,
        ))
    } else {
        // Default offset
        let offset = price1 * 0.05;
        Box::new(DisjointChannel::new(
            bar1, price1, bar2, price2, offset, color,
        ))
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "disjoint_channel",
        display_name: "Disjoint Channel",
        kind: PrimitiveKind::Channel,
        factory: create_disjoint_channel,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
