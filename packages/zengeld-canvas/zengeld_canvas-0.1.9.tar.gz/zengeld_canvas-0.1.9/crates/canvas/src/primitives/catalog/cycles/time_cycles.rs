//! Time Cycles - circular time cycles

use super::super::{
    EllipseParams, LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind,
    PrimitiveMetadata, RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TimeCycles {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub radius_bars: f64,
    /// Vertical radius in price units (for proper ellipse behavior)
    #[serde(default = "default_radius_price")]
    pub radius_price: f64,
    #[serde(default = "default_count")]
    pub count: u8,
}
fn default_count() -> u8 {
    5
}
fn default_radius_price() -> f64 {
    0.0
}

impl TimeCycles {
    pub fn new(bar: f64, price: f64, radius_bars: f64, radius_price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "time_cycles".to_string(),
                display_name: "Time Cycles".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar,
            price,
            radius_bars,
            radius_price,
            count: 5,
        }
    }
}

impl Primitive for TimeCycles {
    fn type_id(&self) -> &'static str {
        "time_cycles"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Measurement
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar, self.price),
            (self.bar + self.radius_bars, self.price + self.radius_price),
        ]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar = b;
            self.price = p;
        }
        if let Some(&(b, p)) = pts.get(1) {
            self.radius_bars = (b - self.bar).abs();
            self.radius_price = (p - self.price).abs();
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar += bd;
        self.price += pd;
    }
    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let cx = ctx.bar_to_x(self.bar);
        let cy = ctx.price_to_y(self.price);

        // Calculate screen-space radii from data coordinates
        let edge_x = ctx.bar_to_x(self.bar + self.radius_bars);
        let edge_y = ctx.price_to_y(self.price + self.radius_price);
        let base_rx = (edge_x - cx).abs();
        let base_ry = (edge_y - cy).abs();

        if base_rx < 0.1 && base_ry < 0.1 {
            return; // Radii too small to render
        }

        // Draw concentric ellipses
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[5.0, 5.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 3.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        for i in 1..=self.count {
            let rx = base_rx * (i as f64);
            let ry = base_ry * (i as f64);
            ctx.begin_path();
            ctx.ellipse(EllipseParams::full(crisp(cx, dpr), crisp(cy, dpr), rx, ry));
            ctx.stroke();
        }

        // Draw vertical line at center to show time axis
        ctx.set_line_dash(&[3.0, 3.0]);
        let chart_top = 0.0;
        let chart_bottom = ctx.canvas_height();
        ctx.begin_path();
        ctx.move_to(crisp(cx, dpr), crisp(chart_top, dpr));
        ctx.line_to(crisp(cx, dpr), crisp(chart_bottom, dpr));
        ctx.stroke();
    }
    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Calculate bounding box of the largest ellipse
        let cx = ctx.bar_to_x(self.bar);
        let cy = ctx.price_to_y(self.price);
        let edge_x = ctx.bar_to_x(self.bar + self.radius_bars);
        let edge_y = ctx.price_to_y(self.price + self.radius_price);
        let max_rx = (edge_x - cx).abs() * self.count as f64;
        let max_ry = (edge_y - cy).abs() * self.count as f64;

        let left_x = cx - max_rx;
        let right_x = cx + max_rx;
        let top_y = cy - max_ry;
        let bottom_y = cy + max_ry;

        let x = match text.h_align {
            TextAlign::Start => left_x + 10.0,
            TextAlign::Center => cx,
            TextAlign::End => right_x - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => top_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => cy,
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

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "time_cycles",
        display_name: "Time Cycles",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 100.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b + 20.0, p + p * 0.05));
            Box::new(TimeCycles::new(b, p, (b2 - b).abs(), (p2 - p).abs(), color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
