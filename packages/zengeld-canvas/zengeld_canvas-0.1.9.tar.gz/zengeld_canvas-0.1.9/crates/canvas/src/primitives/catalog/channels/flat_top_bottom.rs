//! Flat Top/Bottom primitive
//!
//! A channel with one sloped line and one horizontal line.
//! Useful for patterns like ascending/descending triangles.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of flat line
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum FlatType {
    /// Flat line on top (descending triangle)
    #[default]
    Top,
    /// Flat line on bottom (ascending triangle)
    Bottom,
}

/// Flat Top/Bottom - channel with one horizontal line
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FlatTopBottom {
    /// Common primitive data
    pub data: PrimitiveData,
    /// First point of sloped line (bar)
    pub bar1: f64,
    /// First point of sloped line (price)
    pub price1: f64,
    /// Second point of sloped line (bar)
    pub bar2: f64,
    /// Second point of sloped line (price)
    pub price2: f64,
    /// Price level of the flat (horizontal) line
    pub flat_price: f64,
    /// Whether the flat line is on top or bottom
    #[serde(default)]
    pub flat_type: FlatType,
    /// Fill the channel
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

impl FlatTopBottom {
    /// Create a new flat top/bottom channel
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        flat_price: f64,
        color: &str,
    ) -> Self {
        // Determine if flat line is on top or bottom
        let flat_type = if flat_price > (price1 + price2) / 2.0 {
            FlatType::Top
        } else {
            FlatType::Bottom
        };

        Self {
            data: PrimitiveData {
                type_id: "flat_top_bottom".to_string(),
                display_name: if flat_type == FlatType::Top {
                    "Flat Top"
                } else {
                    "Flat Bottom"
                }
                .to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            flat_price,
            flat_type,
            fill: true,
            fill_opacity: 0.2,
        }
    }
}

impl Primitive for FlatTopBottom {
    fn type_id(&self) -> &'static str {
        "flat_top_bottom"
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
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar1, self.flat_price), // Third point defines the flat line level
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
            self.flat_price = points[2].1;
            // Update flat type based on position
            self.flat_type = if self.flat_price > (self.price1 + self.price2) / 2.0 {
                FlatType::Top
            } else {
                FlatType::Bottom
            };
            self.data.display_name = if self.flat_type == FlatType::Top {
                "Flat Top".to_string()
            } else {
                "Flat Bottom".to_string()
            };
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
        self.flat_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let flat_y = ctx.price_to_y(self.flat_price);

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(x1, y1);
            ctx.line_to(x2, y2);
            ctx.line_to(x2, flat_y);
            ctx.line_to(x1, flat_y);
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

        // Sloped line
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Flat (horizontal) line
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(flat_y, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(flat_y, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get the sloped line coordinates
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

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

        // For flat top/bottom channels, position text in center of channel height
        // Adjust base_y to be between sloped line and flat line
        let flat_y = ctx.price_to_y(self.flat_price);
        let adjusted_base_y = (base_y + flat_y) / 2.0;

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

fn create_flat_top_bottom(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 100.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 * 1.05));
    let flat_price = if points.len() >= 3 {
        points[2].1
    } else {
        price1 * 1.1 // Default flat line above
    };
    Box::new(FlatTopBottom::new(
        bar1, price1, bar2, price2, flat_price, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "flat_top_bottom",
        display_name: "Flat Top/Bottom",
        kind: PrimitiveKind::Channel,
        factory: create_flat_top_bottom,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
