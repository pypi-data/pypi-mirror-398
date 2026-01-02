//! Anchored VWAP - volume weighted average price from anchor point

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AnchoredVwap {
    pub data: PrimitiveData,
    pub anchor_bar: f64,
    pub anchor_price: f64,
    #[serde(default = "default_true")]
    pub show_bands: bool,
    #[serde(default = "default_multiplier")]
    pub band_multiplier: f64,
}
fn default_true() -> bool {
    true
}
fn default_multiplier() -> f64 {
    2.0
}

impl AnchoredVwap {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "anchored_vwap".to_string(),
                display_name: "Anchored VWAP".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            anchor_bar: bar,
            anchor_price: price,
            show_bands: true,
            band_multiplier: 2.0,
        }
    }
}

impl Primitive for AnchoredVwap {
    fn type_id(&self) -> &'static str {
        "anchored_vwap"
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
        vec![(self.anchor_bar, self.anchor_price)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.anchor_bar = b;
            self.anchor_price = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.anchor_bar += bd;
        self.anchor_price += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.anchor_bar);
        let y = ctx.price_to_y(self.anchor_price);
        let chart_width = ctx.chart_width();

        // Set up line style
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[10.0 * dpr, 5.0 * dpr]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0 * dpr, 3.0 * dpr]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw VWAP line extending from anchor to right edge
        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), crisp(y, dpr));
        ctx.line_to(crisp(chart_width, dpr), crisp(y, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);

        // Draw anchor marker
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.begin_path();
        ctx.arc(x, y, 4.0 * dpr, 0.0, std::f64::consts::TAU);
        ctx.fill();

        // Draw standard deviation bands if enabled
        if self.show_bands {
            let band_offset = 10.0; // Placeholder, would calculate from data
            ctx.set_global_alpha(0.3);

            // Upper band
            let y_upper = ctx.price_to_y(self.anchor_price + band_offset * self.band_multiplier);
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(y_upper, dpr));
            ctx.line_to(crisp(chart_width, dpr), crisp(y_upper, dpr));
            ctx.stroke();

            // Lower band
            let y_lower = ctx.price_to_y(self.anchor_price - band_offset * self.band_multiplier);
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(y_lower, dpr));
            ctx.line_to(crisp(chart_width, dpr), crisp(y_lower, dpr));
            ctx.stroke();

            ctx.set_global_alpha(1.0);
        }
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
        type_id: "anchored_vwap",
        display_name: "Anchored VWAP",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 100.0));
            Box::new(AnchoredVwap::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
