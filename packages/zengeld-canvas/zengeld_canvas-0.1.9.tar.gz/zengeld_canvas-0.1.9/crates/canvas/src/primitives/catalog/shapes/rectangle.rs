//! Rectangle primitive
//!
//! A rectangular box defined by two corner points (drag to create).

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Rectangle - box defined by two corners
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Rectangle {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Top-left corner bar index
    pub bar1: f64,
    /// Top-left corner price
    pub price1: f64,
    /// Bottom-right corner bar index
    pub bar2: f64,
    /// Bottom-right corner price
    pub price2: f64,
    /// Fill the rectangle
    #[serde(default = "default_true")]
    pub fill: bool,
    /// Fill opacity (0.0 - 1.0)
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
    /// Border radius for rounded corners (0 = sharp)
    #[serde(default)]
    pub border_radius: f64,
}

fn default_true() -> bool {
    true
}

fn default_fill_opacity() -> f64 {
    0.2
}

impl Rectangle {
    /// Create a new rectangle
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "rectangle".to_string(),
                display_name: "Rectangle".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            fill: true,
            fill_opacity: 0.2,
            border_radius: 0.0,
        }
    }

    /// Get normalized corners (min/max)
    pub fn normalized(&self) -> (f64, f64, f64, f64) {
        let min_bar = self.bar1.min(self.bar2);
        let max_bar = self.bar1.max(self.bar2);
        let min_price = self.price1.min(self.price2);
        let max_price = self.price1.max(self.price2);
        (min_bar, min_price, max_bar, max_price)
    }

    /// Get center point
    pub fn center(&self) -> (f64, f64) {
        (
            (self.bar1 + self.bar2) / 2.0,
            (self.price1 + self.price2) / 2.0,
        )
    }

    /// Get width in bars
    pub fn width_bars(&self) -> f64 {
        (self.bar2 - self.bar1).abs()
    }

    /// Get height in price
    pub fn height_price(&self) -> f64 {
        (self.price2 - self.price1).abs()
    }
}

impl Primitive for Rectangle {
    fn type_id(&self) -> &'static str {
        "rectangle"
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

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();

        // Convert to screen coordinates
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let (min_x, max_x) = if x1 < x2 { (x1, x2) } else { (x2, x1) };
        let (min_y, max_y) = if y1 < y2 { (y1, y2) } else { (y2, y1) };
        let width = max_x - min_x;
        let height = max_y - min_y;

        // Fill if enabled
        if self.fill {
            let alpha_hex = (self.fill_opacity * 255.0) as u8;
            let fill_color = format!("{}{:02x}", &self.data.color.stroke[..7], alpha_hex);
            ctx.set_fill_color(&fill_color);
            ctx.fill_rect(min_x, min_y, width, height);
        }

        // Set stroke style
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw rectangle border
        ctx.stroke_rect(crisp(min_x, dpr), crisp(min_y, dpr), width, height);
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get normalized corners
        let (min_bar, min_price, max_bar, max_price) = self.normalized();

        // Convert to screen coordinates
        let left_x = ctx.bar_to_x(min_bar);
        let right_x = ctx.bar_to_x(max_bar);
        let top_y = ctx.price_to_y(max_price);
        let bottom_y = ctx.price_to_y(min_price);

        // h_align: Start=left edge, Center=center, End=right edge
        let x = match text.h_align {
            TextAlign::Start => left_x + 10.0,
            TextAlign::Center => (left_x + right_x) / 2.0,
            TextAlign::End => right_x - 10.0,
        };

        // v_align: Start=top edge, Center=center, End=bottom edge
        let y = match text.v_align {
            TextAlign::Start => top_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => (top_y + bottom_y) / 2.0,
            TextAlign::End => bottom_y - 10.0 - text.font_size / 2.0,
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

fn create_rectangle(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 * 1.05));
    Box::new(Rectangle::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "rectangle",
        display_name: "Rectangle",
        kind: PrimitiveKind::Shape,
        factory: create_rectangle,
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
