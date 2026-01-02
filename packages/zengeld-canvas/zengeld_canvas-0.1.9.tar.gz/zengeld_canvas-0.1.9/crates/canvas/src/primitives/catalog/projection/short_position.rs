//! Short Position - sell trade visualization

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ShortPosition {
    pub data: PrimitiveData,
    pub bar: f64,
    pub entry_price: f64,
    pub stop_loss: f64,
    pub take_profit: f64,
    #[serde(default)]
    pub quantity: f64,
    #[serde(default = "default_true")]
    pub show_pnl: bool,
}
fn default_true() -> bool {
    true
}

impl ShortPosition {
    pub fn new(bar: f64, entry: f64, stop: f64, target: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "short_position".to_string(),
                display_name: "Short Position".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar,
            entry_price: entry,
            stop_loss: stop,
            take_profit: target,
            quantity: 1.0,
            show_pnl: true,
        }
    }
    pub fn risk_reward(&self) -> f64 {
        let risk = (self.stop_loss - self.entry_price).abs();
        let reward = (self.entry_price - self.take_profit).abs();
        if risk > 0.0 { reward / risk } else { 0.0 }
    }
}

impl Primitive for ShortPosition {
    fn type_id(&self) -> &'static str {
        "short_position"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Trading
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar, self.entry_price),
            (self.bar, self.stop_loss),
            (self.bar, self.take_profit),
        ]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar = b;
            self.entry_price = p;
        }
        if let Some(&(_, p)) = pts.get(1) {
            self.stop_loss = p;
        }
        if let Some(&(_, p)) = pts.get(2) {
            self.take_profit = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar += bd;
        self.entry_price += pd;
        self.stop_loss += pd;
        self.take_profit += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar);
        let entry_y = ctx.price_to_y(self.entry_price);
        let stop_y = ctx.price_to_y(self.stop_loss);
        let target_y = ctx.price_to_y(self.take_profit);
        let chart_width = ctx.chart_width();

        // Draw stop loss zone (red fill) - above entry for shorts
        ctx.set_fill_color("#FF000030");
        ctx.fill_rect(
            crisp(x1, dpr),
            stop_y.min(entry_y),
            chart_width - x1,
            (stop_y - entry_y).abs(),
        );

        // Draw take profit zone (green fill) - below entry for shorts
        ctx.set_fill_color("#00FF0030");
        ctx.fill_rect(
            crisp(x1, dpr),
            target_y.min(entry_y),
            chart_width - x1,
            (target_y - entry_y).abs(),
        );

        // Set line dash based on style
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw entry line (white)
        ctx.set_stroke_width(self.data.width);
        ctx.set_stroke_color("#FFFFFF");
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(entry_y, dpr));
        ctx.line_to(crisp(chart_width, dpr), crisp(entry_y, dpr));
        ctx.stroke();

        // Draw stop loss line (red)
        ctx.set_stroke_color("#FF0000");
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(stop_y, dpr));
        ctx.line_to(crisp(chart_width, dpr), crisp(stop_y, dpr));
        ctx.stroke();

        // Draw take profit line (green)
        ctx.set_stroke_color("#00FF00");
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(target_y, dpr));
        ctx.line_to(crisp(chart_width, dpr), crisp(target_y, dpr));
        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Calculate bounding box from the three price levels
        let x = ctx.bar_to_x(self.bar);
        let entry_y = ctx.price_to_y(self.entry_price);
        let stop_y = ctx.price_to_y(self.stop_loss);
        let target_y = ctx.price_to_y(self.take_profit);

        let left_x = x;
        let right_x = ctx.chart_width();
        let top_y = entry_y.min(stop_y).min(target_y);
        let bottom_y = entry_y.max(stop_y).max(target_y);

        let x_pos = match text.h_align {
            TextAlign::Start => left_x + 10.0,
            TextAlign::Center => (left_x + right_x) / 2.0,
            TextAlign::End => right_x - 10.0,
        };

        let y_pos = match text.v_align {
            TextAlign::Start => top_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => (top_y + bottom_y) / 2.0,
            TextAlign::End => bottom_y - 10.0 - text.font_size / 2.0,
        };

        Some(TextAnchor::new(x_pos, y_pos, &self.data.color.stroke))
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
        type_id: "short_position",
        display_name: "Short Position",
        kind: PrimitiveKind::Trading,
        factory: |points, color| {
            let (b, entry) = points.first().copied().unwrap_or((0.0, 100.0));
            let (_, stop) = points.get(1).copied().unwrap_or((b, entry + 5.0));
            let (_, target) = points.get(2).copied().unwrap_or((b, entry - 10.0));
            Box::new(ShortPosition::new(b, entry, stop, target, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
