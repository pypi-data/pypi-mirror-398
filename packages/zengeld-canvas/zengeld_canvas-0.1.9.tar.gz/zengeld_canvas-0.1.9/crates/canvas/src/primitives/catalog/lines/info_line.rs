//! Info Line primitive
//!
//! A line between two points that displays price difference,
//! percentage change, and bar count information.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Info Line - line with price/percentage/bars info display
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct InfoLine {
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
    /// Show price difference
    #[serde(default = "default_true")]
    pub show_price_diff: bool,
    /// Show percentage change
    #[serde(default = "default_true")]
    pub show_percent: bool,
    /// Show bar count
    #[serde(default = "default_true")]
    pub show_bars: bool,
}

fn default_true() -> bool {
    true
}

impl InfoLine {
    /// Create a new info line
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "info_line".to_string(),
                display_name: "Info Line".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            show_price_diff: true,
            show_percent: true,
            show_bars: true,
        }
    }

    /// Calculate the price difference
    pub fn price_diff(&self) -> f64 {
        self.price2 - self.price1
    }

    /// Calculate the percentage change
    pub fn percent_change(&self) -> f64 {
        if self.price1.abs() < 1e-10 {
            0.0
        } else {
            ((self.price2 - self.price1) / self.price1) * 100.0
        }
    }

    /// Calculate the bar count
    pub fn bar_count(&self) -> i64 {
        (self.bar2 - self.bar1).round() as i64
    }

    /// Get formatted info text
    pub fn info_text(&self) -> String {
        let mut parts = Vec::new();

        if self.show_price_diff {
            let diff = self.price_diff();
            let sign = if diff >= 0.0 { "+" } else { "" };
            parts.push(format!("{}{:.2}", sign, diff));
        }

        if self.show_percent {
            let pct = self.percent_change();
            let sign = if pct >= 0.0 { "+" } else { "" };
            parts.push(format!("({}{:.2}%)", sign, pct));
        }

        if self.show_bars {
            let bars = self.bar_count();
            parts.push(format!("{} bars", bars));
        }

        parts.join(" ")
    }
}

impl Primitive for InfoLine {
    fn type_id(&self) -> &'static str {
        "info_line"
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

        // Reset line dash
        ctx.set_line_dash(&[]);

        // Draw info label background and text
        let info_text = self.info_text();
        if !info_text.is_empty() {
            let cx = (x1 + x2) / 2.0;
            let cy = (y1 + y2) / 2.0;

            // Measure text
            ctx.set_font("12px sans-serif");
            let text_width = ctx.measure_text(&info_text);
            let padding = 6.0;
            let bg_width = text_width + padding * 2.0;
            let bg_height = 20.0;

            // Draw background
            ctx.set_fill_color("rgba(30, 30, 30, 0.85)");
            ctx.fill_rect(
                cx - bg_width / 2.0,
                cy - bg_height / 2.0,
                bg_width,
                bg_height,
            );

            // Draw text
            ctx.set_fill_color(&self.data.color.stroke);
            use super::super::render::{TextAlign, TextBaseline};
            ctx.set_text_align(TextAlign::Center);
            ctx.set_text_baseline(TextBaseline::Middle);
            ctx.fill_text(&info_text, cx, cy);
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

fn create_info_line(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1, price1));
    Box::new(InfoLine::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "info_line",
        display_name: "Info Line",
        kind: PrimitiveKind::Line,
        factory: create_info_line,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
